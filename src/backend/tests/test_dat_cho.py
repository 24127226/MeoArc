"""Giai đoạn 2 — tra cứu chuyến bay & phòng. VẪN CHỈ ĐỌC, chưa tiêu tiền.

Hai thứ được khoá chặt nhất ở đây:
  1. KHÔNG có đường nào từ tệp này dẫn tới đặt chỗ/thanh toán. Đó là Giai đoạn 3 và phải
     đi qua cổng xác nhận riêng.
  2. Số MÔ PHỎNG luôn tự nhận là mô phỏng. Một bảng giá bịa nhìn y hệt giá thật là thứ
     khiến người dùng ra quyết định tiền bạc dựa trên con số không tồn tại.
"""

from __future__ import annotations

import inspect
from datetime import date

import pytest

from app.services import dat_cho
from app.tools import email_tools as T
from app.tools.registry import tool_registry, ToolCategory, RequestContext
from app.tools.schemas import TimChuyenBayInput, TimKhachSanInput

CTX = RequestContext(user_id="1", access_token="x", email_provider="gmail")
NGAY = date(2026, 9, 16)


# ── RANH GIỚI GIAI ĐOẠN — phần quan trọng nhất ───────────────────────────────

def test_KHONG_co_ham_nao_dat_cho_hay_thanh_toan():
    """Quét cả module. Một hàm `dat_ve` lọt vào đây là vượt rào sang Giai đoạn 3 mà
    không đi qua cổng xác nhận — đúng thứ cả lộ trình sinh ra để ngăn."""
    src = inspect.getsource(dat_cho).lower()
    for cam in ("def dat_", "def thanh_toan", "def mua_", "def giu_cho",
                "payment", "charge", "/booking", "purchase"):
        assert cam not in src, f"tầng tra cứu không được có {cam!r}"


def test_amadeus_CHI_dung_endpoint_tra_cuu():
    src = inspect.getsource(dat_cho.NhaCungCapAmadeus)
    assert "/v2/shopping/flight-offers" in src
    assert "/v1/booking" not in src, "endpoint đặt chỗ không được xuất hiện ở giai đoạn này"


def test_hai_tool_la_READ_khong_can_xac_nhan():
    for ten in ("tim_chuyen_bay", "tim_khach_san"):
        s = tool_registry.get_spec(ten)
        assert s.category is ToolCategory.READ
        assert s.requires_confirmation is False


# ── Số mô phỏng phải TỰ NHẬN là mô phỏng ─────────────────────────────────────

def test_moi_ket_qua_deu_mang_nhan_nguon():
    ncc = dat_cho.NhaCungCapMoPhong()
    for c in ncc.tim_chuyen_bay("SGN", "DAD", NGAY):
        assert c.nguon == "mo_phong"
    for k in ncc.tim_khach_san("Đà Nẵng", NGAY, date(2026, 9, 18)):
        assert k.nguon == "mo_phong"


@pytest.mark.asyncio
async def test_tool_NOI_RO_day_la_so_mo_phong():
    """Nhãn phải nằm trong câu trả lời agent đọc được, không chỉ trong trường dữ liệu —
    agent hay tóm tắt rồi bỏ mất trường phụ."""
    ra = await T.tim_chuyen_bay(
        TimChuyenBayInput(tu="SGN", den="DAD", ngay="16/09/2026"), CTX)
    assert ra.success
    assert "MÔ PHỎNG" in ra.message.upper()


# ── Tất định ─────────────────────────────────────────────────────────────────

def test_ket_qua_TAT_DINH():
    """Cùng câu hỏi phải ra cùng bảng. Ngẫu nhiên thì demo mỗi lần một khác và test
    chớp nháy — lúc đó không ai phân biệt được 'giá đổi' với 'mã hỏng'."""
    a = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY)
    b = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY)
    assert [x.to_dict() for x in a] == [x.to_dict() for x in b]


def test_chang_khac_nhau_cho_ket_qua_khac_nhau():
    a = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY)
    b = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "HAN", NGAY)
    assert [x.gia_vnd for x in a] != [x.gia_vnd for x in b]


def test_sap_theo_gia_tang_dan():
    ds = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY, 5)
    assert [c.gia_vnd for c in ds] == sorted(c.gia_vnd for c in ds)


# ── Chọn nhà cung cấp ────────────────────────────────────────────────────────

def test_khong_co_khoa_thi_lui_ve_MO_PHONG(monkeypatch):
    """Thiếu khoá là trạng thái BÌNH THƯỜNG khi trình bày và khi chạy test. Bắt cả
    tính năng chết vì thiếu một khoá không bắt buộc là tự làm khó mình."""
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "", raising=False)
    assert isinstance(dat_cho.lay_nha_cung_cap(), dat_cho.NhaCungCapMoPhong)


def test_co_khoa_thi_dung_AMADEUS(monkeypatch):
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "k", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "s", raising=False)
    assert isinstance(dat_cho.lay_nha_cung_cap(), dat_cho.NhaCungCapAmadeus)


def test_amadeus_KHONG_doan_chinh_sach_hoan():
    """Endpoint tra cứu của Amadeus không phơi chính sách hoàn. Nói 'hoàn được' mà thật
    ra không hoàn là dẫn người dùng tới quyết định tiền bạc dựa trên thông tin bịa."""
    src = inspect.getsource(dat_cho.NhaCungCapAmadeus.tim_chuyen_bay)
    assert "hoan_duoc=False" in src


def test_khach_san_amadeus_DA_NOI_va_KHONG_bia_so_sao():
    """Phần khách sạn Amadeus đã nối (trước đây ném NotImplementedError).

    Amadeus KHÔNG trả số sao ở endpoint hotel-offers. Để 0 và giao diện hiểu là
    "không có dữ liệu" — bịa một con số cho đẹp là nói dối về chất lượng khách sạn,
    và người dùng sẽ chọn dựa trên nó."""
    src = inspect.getsource(dat_cho.NhaCungCapAmadeus.tim_khach_san)
    assert "hotels/by-city" in src and "/v3/shopping/hotel-offers" in src
    assert 'ks.get("rating") or 0' in src, "số sao phải lấy từ dữ liệu, thiếu thì để 0"


def test_khach_san_amadeus_KHONG_doan_thanh_pho():
    """Không tra ra mã thành phố thì DỪNG. Đoán nhầm là trả về khách sạn ở một nơi
    khác hẳn mà nhìn vẫn hợp lý — người dùng không có cách nào phát hiện."""
    src = inspect.getsource(dat_cho.NhaCungCapAmadeus.tim_khach_san)
    assert "raise ValueError" in src


# ── Đầu vào hỏng ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ngay_sai_dinh_dang_thi_BAO_LOI_khong_doan():
    """Đoán nhầm ngày bay là loại nhầm người dùng chỉ phát hiện ở sân bay."""
    ra = await T.tim_chuyen_bay(
        TimChuyenBayInput(tu="SGN", den="DAD", ngay="2026-09-16"), CTX)
    assert ra.success is False
    assert "dd/mm/yyyy" in ra.message


@pytest.mark.asyncio
async def test_tra_phong_truoc_nhan_phong_thi_bao_loi():
    ra = await T.tim_khach_san(TimKhachSanInput(
        thanh_pho="Đà Nẵng", nhan_phong="18/09/2026", tra_phong="16/09/2026"), CTX)
    assert ra.success is False


@pytest.mark.asyncio
async def test_tinh_dung_so_dem_va_tong_tien():
    ra = await T.tim_khach_san(TimKhachSanInput(
        thanh_pho="Đà Nẵng", nhan_phong="16/09/2026", tra_phong="18/09/2026"), CTX)
    assert ra.success
    k = ra.data[0]
    assert k["so_dem"] == 2
    assert k["tong_vnd"] == k["gia_moi_dem_vnd"] * 2
