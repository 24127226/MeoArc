"""ĐÍNH KÈM TỆP QUA TRỢ LÝ — và ranh giới an toàn của nó.

Nút kẹp giấy trong khung chat trước đây KHÔNG có `onClick` — thuần hình vẽ. Một nút
bấm không làm gì còn tệ hơn không có nút: người dùng thử, không thấy phản hồi, và kết
luận là ứng dụng hỏng chứ không kết luận là tính năng chưa có.

── QUYẾT ĐỊNH THIẾT KẾ ĐÁNG GIỮ NHẤT ──
Id tệp đi theo NGỮ CẢNH lượt chat, KHÔNG phải tham số của tool. Nghĩa là:

    mô hình quyết định GỬI HAY KHÔNG — không quyết định GỬI CÁI GÌ.

Nếu để `send_email` nhận `attachment_ids` như một tham số bình thường thì mô hình có
thể bịa một id, hoặc tệ hơn, đính một tệp của lượt khác. Ở đây nó chỉ gửi được đúng
những tệp người dùng vừa tự tay chọn trong chính lượt đó.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services import upload_store
from app.tools import email_tools as T
from app.tools.registry import RequestContext
from app.tools.schemas import SendEmailInput


@pytest.fixture(autouse=True)
def _kho_sach():
    upload_store._UPLOADS.clear()
    yield
    upload_store._UPLOADS.clear()


def _ctx(tep: list[str] | None = None) -> RequestContext:
    return RequestContext(user_id="1", access_token="tok", email_provider="gmail",
                          tep_dinh_kem=tep or [])


def _bat_gui(monkeypatch) -> dict:
    """Chặn lời gọi gửi thật, ghi lại tham số để kiểm."""
    ghi: dict = {}

    def gia(provider, token, to, subject, body, cc=None, bcc=None, attachments=None):
        ghi.update(to=to, subject=subject, attachments=attachments)
        return {"id": "m1", "threadId": "t1"}

    monkeypatch.setattr(T.mail, "send_email", gia)
    return ghi


def test_tep_da_tai_len_thi_DI_KEM_thu(monkeypatch):
    ghi = _bat_gui(monkeypatch)
    f = upload_store.save("bao-cao.pdf", b"noi dung", "application/pdf")

    out = asyncio.run(T.send_email(
        SendEmailInput(to=["a@b.com"], subject="Gửi báo cáo", body="Anh xem giúp em."),
        _ctx([f["id"]]),
    ))
    assert out.success
    assert ghi["attachments"] and ghi["attachments"][0]["name"] == "bao-cao.pdf"
    assert ghi["attachments"][0]["content"] == b"noi dung"
    # Câu trả lời phải NÓI RÕ đã kèm gì — người dùng cần xác nhận được bằng mắt.
    assert "bao-cao.pdf" in out.message


def test_KHONG_dinh_kem_thi_khong_doi_hanh_vi_cu(monkeypatch):
    ghi = _bat_gui(monkeypatch)
    out = asyncio.run(T.send_email(
        SendEmailInput(to=["a@b.com"], subject="Chào", body="Xin chào"), _ctx()))
    assert out.success and ghi["attachments"] is None


def test_MO_HINH_khong_chon_duoc_tep():
    """Ranh giới quan trọng nhất của tính năng này.

    `attachment_ids` KHÔNG được là tham số của tool. Nếu là tham số thì mô hình có thể
    bịa một id hoặc đính tệp của lượt khác — và người dùng sẽ không thấy điều đó cho
    tới khi thư đã gửi đi."""
    truong = set(SendEmailInput.model_fields)
    for cam in ("attachment_ids", "attachments", "tep_dinh_kem", "file_ids"):
        assert cam not in truong, (
            f"'{cam}' không được nằm trong schema tool — mô hình sẽ tự chọn được tệp"
        )


def test_tep_HET_HAN_thi_bo_qua_chu_khong_hong_ca_luot(monkeypatch):
    """Kho upload có TTL 30 phút. Người dùng đính tệp rồi để đó nửa tiếng mới bấm Duyệt
    là chuyện thường — khi đó thư vẫn phải gửi được, chỉ là không có tệp."""
    ghi = _bat_gui(monkeypatch)
    out = asyncio.run(T.send_email(
        SendEmailInput(to=["a@b.com"], subject="x", body="y"),
        _ctx(["id-khong-ton-tai"]),
    ))
    assert out.success and ghi["attachments"] is None


def test_dem_dung_so_tep_thuc_su_dinh_duoc(monkeypatch):
    """Một trong hai tệp hết hạn → phải báo 1, không phải 2. Báo thừa thì người dùng
    tưởng đã gửi đủ."""
    _bat_gui(monkeypatch)
    con = upload_store.save("con-han.txt", b"a", "text/plain")
    out = asyncio.run(T.send_email(
        SendEmailInput(to=["a@b.com"], subject="x", body="y"),
        _ctx([con["id"], "da-het-han"]),
    ))
    assert out.data["so_tep"] == "1"


def test_gui_thu_VAN_phai_qua_cong_xac_nhan():
    """Đính kèm không được làm nhẹ đi lớp bảo vệ: gửi thư vẫn là hành động không hoàn
    tác, vẫn phải chờ người dùng bấm duyệt."""
    from app.tools.registry import tool_registry, ToolCategory
    assert tool_registry.get_spec("send_email").category == ToolCategory.WRITE_DESTRUCTIVE
