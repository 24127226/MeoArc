"""ĐỒNG BỘ TRẠNG THÁI — thao tác của người dùng phải SỐNG SÓT qua lần đọc sau.

Cả tệp này sinh ra từ một họ lỗi có cùng gốc, và đó là gốc đáng ghi lại:

    HỆ THỐNG TÍNH LẠI TRẠNG THÁI DẪN XUẤT MỖI LẦN ĐỌC, THAY VÌ ĐỌC THỨ NGƯỜI DÙNG
    ĐÃ QUYẾT.

Triệu chứng nhìn từ ngoài luôn giống nhau: "app quên thao tác trước đó", "rất thiếu
đồng bộ". Nhưng nguyên nhân nằm ở chỗ khác hẳn với chỗ nhìn thấy lỗi:

  * Gắn nhãn xong, chuyển mục rồi quay lại → nhãn về như cũ.
    `apply_label` GHI nhãn thật xuống Gmail, nhưng `_to_email` lúc đọc lại chạy
    `classify()` trên NỘI DUNG và ghi đè. Ghi rồi không bao giờ đọc.

  * Bấm vào thư thì thư biến mất khỏi danh sách.
    Thư tự gửi mang CẢ INBOX LẪN SENT; `_folder_from_labels` kiểm SENT trước nên
    bản chi tiết suy ra "sent" trong khi danh sách đang ở "inbox".

Nguyên tắc rút ra: BỘ ĐOÁN TỰ ĐỘNG CHỈ ĐƯỢC ĐOÁN KHI CHƯA AI QUYẾT.
"""

from __future__ import annotations

import pytest

from app.services import gmail_service as gs
from app.core.labeling import ALL_CATEGORIES


def _msg(labels: list[str], subject="Nộp báo cáo Testing", sender="giaovu@fit.hcmus.edu.vn"):
    return {
        "id": "m1",
        "labelIds": labels,
        "snippet": "Các nhóm nộp báo cáo trước 23:59 ngày 18/9.",
        "payload": {"headers": [
            {"name": "From", "value": f"Giáo vụ <{sender}>"},
            {"name": "To", "value": "toi@example.com"},
            {"name": "Subject", "value": subject},
            {"name": "Date", "value": "Mon, 1 Sep 2026 10:00:00 +0700"},
        ]},
    }


# ── NHÃN NGƯỜI DÙNG THẮNG BỘ PHÂN LOẠI TỰ ĐỘNG ──────────────────────────────

def test_nhan_nguoi_dung_dat_THANG_bo_phan_loai():
    """Đây chính là lỗi "gắn nhãn xong quay lại thấy nhãn cũ".

    Thư này nội dung là chuyện học tập, nên `classify()` sẽ đoán "Học tập". Nhưng
    người dùng đã gắn tay nhãn "Tài chính" — quyết định của họ phải thắng."""
    tai_chinh = next(c for c in ALL_CATEGORIES if c.label == "Tài chính")
    ban_do = {"Label_99": "Tài chính"}
    e = gs._to_email(_msg(["INBOX", "Label_99"]), "inbox", ban_do)
    assert e.label == "Tài chính"
    assert e.category == tai_chinh.color


def test_CHUA_gan_nhan_thi_bo_phan_loai_van_doan():
    """Bỏ hẳn bộ phân loại thì thư mới về sẽ không có nhãn nào — cũng hỏng.
    Nó chỉ nhường chỗ khi người dùng ĐÃ quyết."""
    e = gs._to_email(_msg(["INBOX"]), "inbox", {})
    assert e.label, "chưa ai gắn nhãn thì vẫn phải có nhãn đoán"


def test_nhan_LA_cua_nguoi_dung_thi_BO_QUA():
    """Giao diện chỉ có 7 màu chip. Đoán màu cho nhãn lạ là bịa thông tin không có."""
    ban_do = {"Label_7": "Du lịch hè 2026"}
    e = gs._to_email(_msg(["INBOX", "Label_7"]), "inbox", ban_do)
    assert e.label != "Du lịch hè 2026"
    assert e.label in {c.label for c in ALL_CATEGORIES}


def test_khong_lay_duoc_ban_do_nhan_thi_van_chay():
    """Bản đồ nhãn là lời gọi PHỤ. Nó hỏng thì lùi về bộ phân loại, đừng làm hỏng cả
    danh sách thư."""
    e = gs._to_email(_msg(["INBOX", "Label_99"]), "inbox", None)
    assert e.label in {c.label for c in ALL_CATEGORIES}


@pytest.mark.parametrize("viet", ["Tài chính", "tài chính", "TÀI CHÍNH", "  Tài chính  "])
def test_so_khop_ten_nhan_KHONG_phan_biet_hoa_thuong_va_khoang_trang(viet):
    """Gmail giữ nguyên cách người dùng gõ. Khớp chặt thì gắn nhãn ở Gmail rồi mà
    MeoArc vẫn không nhận ra — đúng lỗi cũ, chỉ đổi hình dạng."""
    assert gs._nhan_nguoi_dung_dat(["L1"], {"L1": viet}).label == "Tài chính"


# ── THƯ MỤC: thư TỰ GỬI mang cả INBOX lẫn SENT ──────────────────────────────

def test_thu_tu_gui_cho_minh_thuoc_HOP_THU_DEN():
    """Thư demo được gửi từ chính mình tới chính mình nên mang CẢ HAI nhãn.
    Suy ra "sent" thì bấm vào thư là nó rơi khỏi bộ lọc inbox và BIẾN MẤT."""
    assert gs._folder_from_labels(["INBOX", "SENT", "UNREAD"]) == "inbox"


def test_thu_chi_co_SENT_van_la_da_gui():
    assert gs._folder_from_labels(["SENT"]) == "sent"


@pytest.mark.parametrize("nhan,mong_doi", [
    (["SPAM", "INBOX"], "spam"),      # SPAM/TRASH thật sự gỡ thư khỏi inbox
    (["TRASH", "INBOX"], "trash"),
    (["DRAFT"], "drafts"),
    ([], "archive"),
])
def test_thu_tu_uu_tien_thu_muc_khac_van_giu_nguyen(nhan, mong_doi):
    assert gs._folder_from_labels(nhan) == mong_doi


# ── HẠN MỨC: đừng gọi model cho câu văn sẽ bị vứt đi ────────────────────────

def _trang_thai(ten_tool: str | None):
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    msgs = [HumanMessage(content="hỏi gì đó"), AIMessage(content="")]
    if ten_tool:
        msgs.append(ToolMessage(content="{}", name=ten_tool, tool_call_id="t1"))
    msgs.append(AIMessage(content="xong"))
    return {"messages": msgs, "iteration_count": 1}


@pytest.mark.parametrize("tool", ["categorize_emails", "tim_chuyen_bay", "tim_khach_san"])
def test_tool_co_the_rieng_thi_BO_QUA_responder(tool):
    """app.py dựng thẻ cho các tool này TỪ DỮ LIỆU TOOL rồi ghi đè lên đầu ra của
    responder — nên gọi responder là trả tiền cho một câu văn không ai đọc.

    Gói Gemini free chỉ 20 lượt/NGÀY mỗi model, mà một câu có dùng tool tốn 3 lượt.
    Bỏ được lượt thứ ba là hỏi được nhiều hơn 50% mỗi ngày."""
    from app.agent.graph import _should_continue
    assert _should_continue(_trang_thai(tool)) == "end"


def test_tool_KHONG_co_the_rieng_thi_VAN_goi_responder():
    """Bỏ nhầm thì người dùng nhận câu trả lời cụt của agent thay vì phần trình bày."""
    from app.agent.graph import _should_continue
    assert _should_continue(_trang_thai("search_emails")) == "responder"


def test_luot_thuan_van_ban_van_khong_goi_responder():
    from app.agent.graph import _should_continue
    assert _should_continue(_trang_thai(None)) == "end"
