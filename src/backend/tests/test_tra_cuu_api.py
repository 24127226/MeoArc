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
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "", raising=False)


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


@pytest.mark.parametrize("ma", ["SG", "SGNN"])
def test_ma_san_bay_sai_do_dai_bi_tu_choi(monkeypatch, ma):
    _mo_phong(monkeypatch)
    r = c.get("/tra-cuu/chuyen-bay",
              params={"tu": ma, "den": "DAD", "ngay": "16/09/2026"})
    assert r.status_code == 422


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
