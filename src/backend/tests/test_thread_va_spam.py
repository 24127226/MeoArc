"""Hai lỗi ĐỒNG BỘ đã bị người dùng phát hiện, khoá lại để không tái diễn.

Cả hai đều thuộc loại IM LẶNG — không ném lỗi, không ghi log, chỉ trả về dữ liệu
sai. Đó là loại tốn nhiều thời gian nhất để lần ra, nên đáng có test riêng.
"""

from __future__ import annotations

import pytest

from app.api.app import _gom_theo_luong
from app.schemas.email import Email
from app.services import gmail_service


def _thu(mid: str, tid: str | None, *, unread: bool = False, subject: str = "x") -> Email:
    return Email(
        id=mid, sender="A", senderEmail="a@b.com", senderInitial="A", to="me",
        subject=subject, preview="", body=[], time="", date="",
        unread=unread, starred=False, category="sea", threadId=tid,
    )


# ── LỖI 1: một cuộc trao đổi bị xé thành nhiều thẻ ──────────────────────────

def test_thu_cung_luong_gop_thanh_mot_dong():
    """Gmail hiện một cuộc trao đổi 3 lượt thành MỘT dòng. Trước đây MeoArc trả về
    ba thư riêng nên hiện thành BA thẻ — hộp thư trông đầy gấp ba lần thật."""
    ra = _gom_theo_luong([_thu("m1", "t1"), _thu("m2", "t1"), _thu("m3", "t1")])
    assert len(ra) == 1
    assert ra[0].threadCount == 3


def test_giu_thu_MOI_NHAT_lam_dai_dien():
    """Danh sách từ Gmail sắp mới→cũ, nên thư ĐẦU TIÊN gặp trong mỗi luồng là thư
    mới nhất. Giữ nhầm thư cũ thì dòng hiện tiêu đề của lượt đầu cuộc trao đổi."""
    ra = _gom_theo_luong([_thu("moi", "t1", subject="Lượt mới nhất"),
                          _thu("cu", "t1", subject="Lượt đầu")])
    assert ra[0].id == "moi"
    assert ra[0].subject == "Lượt mới nhất"


def test_mot_thu_chua_doc_thi_ca_dong_chua_doc():
    """Cả luồng chỉ cần MỘT thư chưa đọc là cả dòng phải hiện chưa đọc — đúng cách
    Gmail làm, và đúng cái người dùng cần biết."""
    ra = _gom_theo_luong([_thu("m1", "t1", unread=False), _thu("m2", "t1", unread=True)])
    assert ra[0].unread is True


def test_cac_luong_khac_nhau_KHONG_bi_gop():
    ra = _gom_theo_luong([_thu("m1", "t1"), _thu("m2", "t2"), _thu("m3", "t3")])
    assert len(ra) == 3
    assert all(e.threadCount == 1 for e in ra)


def test_thu_khong_co_threadId_van_giu_nguyen():
    """Outlook/thư nhập tay có thể thiếu threadId. Thiếu thì để nguyên, KHÔNG được
    gom hết đám không-có-id thành một dòng."""
    ra = _gom_theo_luong([_thu("m1", None), _thu("m2", None)])
    assert len(ra) == 2


# ── LỖI 2: thư mục Thư rác không bao giờ đồng bộ ────────────────────────────

def test_spam_anh_xa_dung_nhan_gmail():
    """Trước đây `_FOLDER_LABEL` KHÔNG có 'spam', mà tra cứu lại là
    `.get(folder, "INBOX")` — nên bấm "Thư rác" thì Gmail được hỏi về INBOX và
    MeoArc hiện lại đúng hộp thư đến. Sai dữ liệu mà không có một dấu hiệu nào."""
    assert gmail_service._FOLDER_LABEL.get("spam") == "SPAM"


@pytest.mark.parametrize("thu_muc", ["trash", "spam"])
def test_thu_muc_bi_gmail_giau_phai_bat_co_includeSpamTrash(thu_muc):
    """Gmail mặc định GIẤU cả thùng rác lẫn thư rác khỏi mọi truy vấn. Không bật cờ
    thì hỏi labelIds=SPAM vẫn trả rỗng — đúng triệu chứng "Gmail có thư mà MeoArc
    không thấy"."""
    src = (gmail_service.__file__)
    noi_dung = open(src, encoding="utf-8").read()
    assert '("TRASH", "SPAM")' in noi_dung, "cờ includeSpamTrash phải bật cho CẢ hai"


def test_suy_thu_muc_tu_nhan_SPAM():
    """Đồng bộ lũy tiến gán thư mục từ nhãn. Thiếu nhánh SPAM thì thư rác bị dồn
    vào 'archive' và không bao giờ hiện ở đúng chỗ."""
    assert gmail_service._folder_from_labels(["SPAM"]) == "spam"
    # SPAM phải được xét TRƯỚC các nhãn khác có thể đi kèm
    assert gmail_service._folder_from_labels(["SPAM", "UNREAD"]) == "spam"


def test_spam_la_the_folder_hop_le():
    """Thiếu trong `_VALID_TAGS` thì mọi thư rác bị gắn nhãn 'inbox' khi trả về."""
    assert "spam" in gmail_service._VALID_TAGS
