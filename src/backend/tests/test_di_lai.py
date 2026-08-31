"""Giai đoạn 1 — nhận ra ý định đi lại. CHỈ ĐỀ XUẤT, không đặt gì.

Phép kiểm quan trọng nhất ở đây là những cái NÓI KHÔNG. Đề xuất "cần bay đi Đà Nẵng"
cho một buổi họp Zoom không chỉ vô ích — nó làm người dùng thôi tin vào MỌI đề xuất sau
đó, kể cả những cái đúng. Với một tính năng sắp dẫn tới việc tiêu tiền, mất lòng tin là
hỏng nặng hơn bỏ sót.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core import cam_ket as ck
from app.tools import email_tools as T
from app.tools.registry import tool_registry, ToolCategory, RequestContext
from app.tools.schemas import DeXuatDiLaiInput
from app.schemas.email import Email

CTX = RequestContext(user_id="1", access_token="x", email_provider="gmail")
MOC = datetime(2026, 9, 1, 9, 0)


def _ck(han: datetime, noi_dung="Bảo vệ đồ án", tin=0.88, trang_thai="chua_lam"):
    return ck.CamKet(
        id="ck-1", noi_dung=noi_dung, han=han, bat_dau=None, han_suy_ra=False,
        trang_thai=trang_thai, nguoi_cho="GVHD", email_id="1",
        do_tin_cay=tin, uoc_luong_phut=60, muc_rui_ro=1, muc_uu_tien=2,
    )


# ── Nhận đúng ────────────────────────────────────────────────────────────────

def test_nhan_buoi_bao_ve_o_thanh_pho_khac():
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0))],
        {"1": "Buổi bảo vệ đồ án diễn ra lúc 8h ngày 17/9 tại Đà Nẵng."},
    )
    assert len(y) == 1
    assert y[0].ma_san_bay == "DAD"
    assert y[0].tu_san_bay == "SGN"


def test_buoi_SANG_thi_de_xuat_den_tu_hom_truoc():
    """Bay sáng cùng ngày để kịp buổi 8h là đặt cược vào việc không có chuyến nào trễ."""
    sang = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0))],
        {"1": "Bảo vệ lúc 8h ngày 17/9 tại Đà Nẵng."})
    chieu = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 15, 0))],
        {"1": "Bảo vệ lúc 15h ngày 17/9 tại Đà Nẵng."})
    assert sang[0].nen_den_truoc_ngay == 1
    assert chieu[0].nen_den_truoc_ngay == 0


# ── NÓI KHÔNG — phần quan trọng nhất ─────────────────────────────────────────

@pytest.mark.parametrize("dau_hieu", [
    "qua Zoom", "họp online", "trực tuyến", "trên Google Meet", "hình thức từ xa",
])
def test_TRUC_TUYEN_thi_KHONG_de_xuat_di_lai(dau_hieu):
    """Dấu hiệu trực tuyến phải THẮNG, kể cả khi thư có nêu tên thành phố."""
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0))],
        {"1": f"Buổi bảo vệ {dau_hieu} lúc 8h ngày 17/9, ban tổ chức ở Đà Nẵng."},
    )
    assert y == []


def test_khong_co_dong_tu_CO_MAT_thi_bo_qua():
    """'Nộp báo cáo' thì nộp online được — có nêu Đà Nẵng cũng không phải đi."""
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0), "Nộp báo cáo")],
        {"1": "Nộp báo cáo trước ngày 17/9 cho văn phòng tại Đà Nẵng."},
    )
    assert y == []


def test_cung_thanh_pho_voi_noi_o_thi_KHONG_phai_chuyen_di():
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0))],
        {"1": "Buổi bảo vệ lúc 8h ngày 17/9 tại TP.HCM."},
    )
    assert y == []


def test_khong_co_han_thi_khong_de_xuat():
    """Không biết ngày thì không đề xuất chuyến bay được — đoán ngày bay là chỗ tệ
    nhất để đoán."""
    y = ck.suy_y_dinh_di_lai(
        [_ck(None)], {"1": "Bảo vệ đồ án tại Đà Nẵng, lịch sẽ báo sau."})
    assert y == []


def test_viec_XONG_thi_bo_qua():
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0), trang_thai="xong")],
        {"1": "Bảo vệ lúc 8h ngày 17/9 tại Đà Nẵng."})
    assert y == []


def test_do_tin_cay_KHONG_vuot_do_tin_cay_cua_han():
    """Suy một chuyến bay từ một cái hạn đoán mò thì cả hai đều đoán mò. Độ tin cậy
    phải kế thừa chỗ yếu nhất, không được tự tin hơn nguồn của nó."""
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0), tin=0.45)],
        {"1": "Bảo vệ lúc 8h ngày 17/9 tại Đà Nẵng."})
    assert y[0].do_tin_cay <= 0.45


def test_lay_thanh_pho_xuat_hien_SOM_NHAT():
    """Thư thường nêu nơi diễn ra trước, rồi mới nhắc địa danh phụ (chi nhánh, nơi
    gửi) ở cuối. Lấy nhầm cái sau là đề xuất bay sai thành phố."""
    y = ck.suy_y_dinh_di_lai(
        [_ck(datetime(2026, 9, 17, 8, 0))],
        {"1": "Bảo vệ lúc 8h ngày 17/9 tại Đà Nẵng. Văn phòng chính ở Hà Nội."},
    )
    assert y[0].ma_san_bay == "DAD"


# ── Tool ─────────────────────────────────────────────────────────────────────

def test_tool_la_READ_khong_can_xac_nhan():
    """Đề xuất là việc vô hại — bắt bấm duyệt một lời đề xuất thì cổng xác nhận mất
    thiêng trước khi nó kịp gác việc tiêu tiền thật."""
    s = tool_registry.get_spec("de_xuat_di_lai")
    assert s.category is ToolCategory.READ
    assert s.requires_confirmation is False


def test_tool_KHONG_cham_toi_dat_cho():
    """Giai đoạn 1 tuyệt đối không gọi ra ngoài. Có một dòng gọi API đặt vé lọt vào
    đây là vượt rào ba giai đoạn cùng lúc."""
    import inspect
    src = inspect.getsource(T.de_xuat_di_lai)
    for cam in ("amadeus", "booking", "httpx", "requests.", "thanh_toan", "payment"):
        assert cam not in src.lower(), f"giai đoạn 1 không được chạm tới {cam}"


@pytest.mark.asyncio
async def test_tool_chay_that_tren_hop_thu_gia(monkeypatch):
    sau = datetime.now() + timedelta(days=10)
    e = Email(
        id="1", sender="GVHD", senderEmail="gv@hcmus.edu.vn", senderInitial="G",
        to="me", subject="Lịch bảo vệ đồ án",
        preview="", body=[f"Buổi bảo vệ lúc 8h ngày {sau.day}/{sau.month} tại Đà Nẵng."],
        time="08:00", date="01/09/2026 08:00", unread=True, starred=False,
        category="sea", priority="High",
    )
    monkeypatch.setattr(T.mail, "list_messages", lambda *a, **kw: ([e], None))
    ra = await T.de_xuat_di_lai(DeXuatDiLaiInput(), CTX)
    assert ra.success and len(ra.data) == 1
    assert ra.data[0]["ma_san_bay"] == "DAD"
    assert ra.data[0]["email_id"] == "1"
