"""Endpoint tra cứu — đường KHÔNG qua mô hình, dựng riêng để trình bày.

Điều được canh chặt nhất: MỌI phản hồi phải TỰ KHAI NGUỒN. Một bảng giá mô phỏng
trông y hệt giá thật là thứ nguy hiểm nhất trong cả tính năng — người xem phải phân
biệt được bằng mắt, không phải bằng lời hứa của người trình bày.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import app
from app.services import dat_cho

c = TestClient(app)


def _mo_phong(monkeypatch):
    """Xoá HẾT khoá của MỌI nguồn thật, không riêng Amadeus.

    Bỏ sót một khoá thì cả tệp này đổ ngay khi có người điền khoá đó vào .env —
    và nó đổ trên MÁY CỦA HỌ chứ không đổ trên CI, nên rất khó lần ra."""
    for k in ("amadeus_key", "amadeus_secret", "aerodatabox_key"):
        monkeypatch.setattr(dat_cho.settings, k, "", raising=False)


# ── Khai báo nguồn ───────────────────────────────────────────────────────────

def test_trang_thai_noi_ro_dang_dung_nguon_nao(monkeypatch):
    _mo_phong(monkeypatch)
    d = c.get("/tra-cuu/trang-thai").json()
    assert d["la_that"] is False
    assert "MÔ PHỎNG" in d["nhan"]
    # Chưa có khoá thì phải NÓI CÁCH SỬA, không chỉ báo trạng thái.
    assert "AMADEUS_KEY" in (d["huong_dan"] or "")


def test_trang_thai_KHONG_lo_khoa(monkeypatch):
    """Khoá không bao giờ được rời máy chủ. Endpoint chỉ trả CÓ hay KHÔNG."""
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "khoa-bi-mat-abc", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "bi-mat-xyz", raising=False)
    body = c.get("/tra-cuu/trang-thai").text
    assert "khoa-bi-mat-abc" not in body and "bi-mat-xyz" not in body


def test_moi_ket_qua_deu_kem_nhan_nguon(monkeypatch):
    _mo_phong(monkeypatch)
    d = c.get("/tra-cuu/chuyen-bay",
              params={"tu": "SGN", "den": "DAD", "ngay": "16/09/2026"}).json()
    assert d["nguon"] == "mo_phong"
    assert d["la_that"] is False
    assert "MÔ PHỎNG" in d["nhan"]
    assert d["thoi_diem"]           # có dấu thời gian để đối chiếu lúc trình bày
    assert d["so_ket_qua"] == len(d["ket_qua"])


def test_nguon_that_van_bao_dung_khi_THIEU_GIA(monkeypatch):
    """AeroDataBox là nguồn THẬT nhưng KHÔNG có giá. Hai điều đó độc lập nhau, nên
    `la_that` và `co_gia` phải là hai cờ tách rời — gộp làm một là hoặc phải dán nhãn
    giả cho dữ liệu thật, hoặc phải hứa có giá trong khi không có."""
    for k in ("amadeus_key", "amadeus_secret"):
        monkeypatch.setattr(dat_cho.settings, k, "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "aerodatabox_key", "khoa-that", raising=False)
    d = c.get("/tra-cuu/trang-thai").json()
    assert d["la_that"] is True and d["co_gia"] is False
    assert "không có giá" in d["nhan"].lower()
    assert d["huong_dan"] is None, "đang dùng nguồn thật thì không còn gì phải hướng dẫn"


def test_khach_san_lui_ve_mo_phong_thi_NHAN_CUNG_PHAI_LUI(monkeypatch):
    """Chỗ dễ hỏng nhất của việc thêm nguồn thứ ba.

    AeroDataBox không có khách sạn nên phần này lui về mô phỏng. Nếu nhãn vẫn lấy theo
    nhà cung cấp ĐANG CHỌN thay vì nhà cung cấp ĐÃ DÙNG, thì phòng bịa sẽ đội nhãn
    "LỊCH BAY THẬT" — đúng loại lỗi mà cả tính năng này sinh ra để ngăn."""
    for k in ("amadeus_key", "amadeus_secret"):
        monkeypatch.setattr(dat_cho.settings, k, "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "aerodatabox_key", "khoa-that", raising=False)

    d = c.get("/tra-cuu/khach-san", params={
        "thanh_pho": "Đà Nẵng", "nhan_phong": "16/09/2026", "tra_phong": "18/09/2026",
    }).json()

    assert d["nguon"] == "mo_phong", "khách sạn không đến từ nguồn bay"
    assert d["la_that"] is False
    assert "MÔ PHỎNG" in d["nhan"]
    assert d["so_ket_qua"] > 0, "lui về mô phỏng chứ không phải trả rỗng"


# ── Tra cứu chạy đúng ────────────────────────────────────────────────────────

def test_chuyen_bay_tra_du_truong_can_de_quyet_dinh(monkeypatch):
    _mo_phong(monkeypatch)
    k = c.get("/tra-cuu/chuyen-bay",
              params={"tu": "sgn", "den": "dad", "ngay": "16/09/2026",
                      "so_ket_qua": 3}).json()["ket_qua"]
    assert len(k) == 3
    for x in k:
        # Thiếu bất kỳ trường nào ở đây thì người dùng không đủ dữ kiện để chọn.
        for truong in ("ma", "hang", "khoi_hanh", "ha_canh", "gia_vnd",
                       "so_diem_dung", "hoan_duoc", "nguon"):
            assert truong in x, f"thiếu {truong}"
    assert [x["gia_vnd"] for x in k] == sorted(x["gia_vnd"] for x in k)


def test_ma_san_bay_chu_thuong_van_chay(monkeypatch):
    """Người gõ tay hay viết thường. Bắt lỗi vì hoa/thường là bắt bẻ vô ích."""
    _mo_phong(monkeypatch)
    assert c.get("/tra-cuu/chuyen-bay",
                 params={"tu": "sgn", "den": "dad", "ngay": "16/09/2026"}).status_code == 200


def test_khach_san_tinh_dung_so_dem(monkeypatch):
    _mo_phong(monkeypatch)
    k = c.get("/tra-cuu/khach-san",
              params={"thanh_pho": "Đà Nẵng", "nhan_phong": "16/09/2026",
                      "tra_phong": "18/09/2026"}).json()["ket_qua"]
    assert k[0]["so_dem"] == 2
    assert k[0]["tong_vnd"] == k[0]["gia_moi_dem_vnd"] * 2


# ── Đầu vào hỏng: báo RÕ, không đoán ─────────────────────────────────────────

def test_ngay_sai_dinh_dang_bao_ro_cach_sua(monkeypatch):
    """Đoán nhầm ngày bay là loại nhầm chỉ phát hiện ở sân bay. Thà từ chối."""
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/chuyen-bay",
              params={"tu": "SGN", "den": "DAD", "ngay": "2026-09-16"})
    assert r.status_code == 400
    assert "dd/mm/yyyy" in r.text


def test_tra_phong_truoc_nhan_phong_bi_tu_choi(monkeypatch):
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/khach-san",
              params={"thanh_pho": "Đà Nẵng", "nhan_phong": "18/09/2026",
                      "tra_phong": "16/09/2026"})
    assert r.status_code == 400


@pytest.mark.parametrize("goi", ["Hà Nội", "ha noi", "HAN", "Nội Bài", "sân bay Hà Nội"])
def test_GO_TEN_THANH_PHO_cung_ra_dung_chang(monkeypatch, goi):
    """Bản trước ép đúng 3 ký tự, tức là bắt người dùng TỰ BIẾT "Nội Bài là HAN" —
    họ phải mở Google tra mã rồi mới quay lại gõ, nên công cụ chưa tiết kiệm được gì."""
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/chuyen-bay",
              params={"tu": goi, "den": "Đà Nẵng", "ngay": "16/09/2026"})
    assert r.status_code == 200, r.text
    assert all(k["tu"] == "HAN" and k["den"] == "DAD" for k in r.json()["ket_qua"])


def test_khong_nhan_ra_thi_BAO_CACH_SUA_chu_khong_doan(monkeypatch):
    """Đoán nhầm thành phố là gửi người ta tới sai đầu đất nước, và họ chỉ phát hiện
    ở sân bay. Nên dừng lại kèm ví dụ, không đoán."""
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/chuyen-bay",
              params={"tu": "Xyzzy", "den": "DAD", "ngay": "16/09/2026"})
    assert r.status_code == 400
    assert "điểm đi" in r.text and "Hà Nội" in r.text, "phải kèm ví dụ để người dùng sửa được"


def test_di_va_den_TRUNG_NHAU_bi_tu_choi(monkeypatch):
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/chuyen-bay",
              params={"tu": "Hà Nội", "den": "HAN", "ngay": "16/09/2026"})
    assert r.status_code == 400


def test_endpoint_san_bay_de_giao_dien_goi_y():
    d = c.get("/tra-cuu/san-bay").json()
    ma_list = [x["ma"] for x in d["ket_qua"]]
    for bat_buoc in ("SGN", "HAN", "DAD", "CXR", "PQC"):
        assert bat_buoc in ma_list, f"thiếu sân bay phổ biến {bat_buoc}"
    assert d["pho_bien"] and all({"ma", "ten"} <= set(x) for x in d["pho_bien"])


# ── Ranh giới: CHỈ tra cứu ───────────────────────────────────────────────────

def test_KHONG_co_endpoint_dat_cho_hay_thanh_toan():
    """Router này chỉ được phép ĐỌC. Một endpoint POST lọt vào đây là vượt rào khỏi
    cổng xác nhận — đúng thứ cả thiết kế sinh ra để ngăn."""
    from app.api import dat_cho_routes
    for r in dat_cho_routes.router.routes:
        assert set(r.methods) <= {"GET", "HEAD"}, f"{r.path} có method ghi"


def test_route_nam_trong_API_PREFIXES():
    """Thiếu tiền tố thì bắt-tất-cả của SPA nuốt route: gọi API hỏng sẽ trả về trang
    HTML thay vì lỗi, và đó là loại lỗi rất khó lần vì "có phản hồi 200"."""
    from app.api.spa import API_PREFIXES
    assert "tra-cuu" in API_PREFIXES
