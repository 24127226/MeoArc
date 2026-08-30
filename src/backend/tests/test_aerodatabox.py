"""Nguồn lịch bay THẬT (AeroDataBox). Vẫn CHỈ ĐỌC, vẫn không có đường nào tới tiền.

Nguồn này khác hai nguồn trước ở một điểm sinh ra gần hết các phép kiểm dưới đây:
NÓ KHÔNG CÓ GIÁ. Nó bán dữ liệu bay, không bán vé. Nên rủi ro lớn nhất không còn là
"giá giả đội lốt giá thật" nữa, mà là "thiếu giá bị đọc thành giá bằng 0" — và một
chuyến bay 0 đồng thì người dùng tin ngay.

Rủi ro thứ hai: nguồn này THẬT, nên nhãn của nó phải nói thật. Nhưng khách sạn thì nó
không có, và phần khách sạn lui về mô phỏng — nếu nhãn không lui theo thì phòng bịa sẽ
đội nhãn "LỊCH BAY THẬT".
"""

from __future__ import annotations

import inspect
from datetime import date, datetime

import pytest

from app.services import dat_cho

NGAY = date(2026, 9, 16)


# ── Dàn cảnh: giả lập httpx bằng ĐÚNG hình dạng phản hồi đã tra từ OpenAPI ────

def _mot_chuyen(so="VN 123", den="DAD", gio_di="2026-09-16 06:15+07:00",
                gio_den="2026-09-16 07:35+07:00", **ghi_de):
    """Một mục `departures[]` theo đúng AirportFlightContract của AeroDataBox."""
    muc = {
        "number": so,
        "status": "Scheduled",
        "codeshareStatus": "IsOperator",
        "isCargo": False,
        "movement": {
            "airport": {"iata": "SGN", "name": "Ho Chi Minh City"},
            "scheduledTime": {"utc": "2026-09-15 23:15Z", "local": gio_di},
            "terminal": "1",
            "quality": ["Basic"],
        },
        "arrival": {
            "airport": {"iata": den, "name": "Da Nang"},
            "scheduledTime": {"utc": "2026-09-16 00:35Z", "local": gio_den},
            "quality": ["Basic"],
        },
        "aircraft": {"model": "Airbus A321"},
        "airline": {"name": "Vietnam Airlines", "iata": "VN", "icao": "HVN"},
    }
    muc.update(ghi_de)
    return muc


class _PhanHoi:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def _gia_lap(monkeypatch, chuyen_bay: list[dict]):
    """Cửa sổ đầu (00:00–11:59) trả dữ liệu, cửa sổ sau trả 204 (không có chuyến).

    204 là phản hồi THẬT của API khi khung giờ trống. Để nó vào đây luôn để chắc rằng
    nhánh đó không bị ném lỗi — một sân bay không có chuyến bay đêm là chuyện bình
    thường, không phải sự cố.
    """
    goi = {"n": 0}

    class _Client:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False

        def get(self, url, **kw):
            goi["n"] += 1
            if goi["n"] == 1:
                return _PhanHoi(200, {"departures": chuyen_bay})
            return _PhanHoi(204)

    import httpx
    monkeypatch.setattr(httpx, "Client", _Client)
    return goi


# ── KHÔNG BỊA GIÁ — phần quan trọng nhất của nguồn này ───────────────────────

def test_KHONG_bia_gia_va_noi_ro_la_khong_co(monkeypatch):
    """Thiếu giá phải nói là THIẾU, không được để giao diện đoán từ số 0."""
    _gia_lap(monkeypatch, [_mot_chuyen()])
    ds = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)
    assert len(ds) == 1
    d = ds[0].to_dict()
    assert d["gia_vnd"] == 0
    assert d["co_gia"] is False, "thiếu giá mà không có cờ thì bị đọc thành vé 0 đồng"


def test_mo_phong_van_CO_gia_nen_co_gia_phai_True():
    """Cờ `co_gia` phải phân biệt được hai nguồn, không phải hằng số."""
    ds = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY)
    assert ds[0].to_dict()["co_gia"] is True


# ── ĐỌC GIỜ — định dạng của AeroDataBox không phải ISO chuẩn ─────────────────

def test_doc_duoc_gio_ngan_cach_bang_DAU_CACH():
    """AeroDataBox ghi "2026-09-16 06:15+07:00" (dấu cách), không phải chữ T.
    `fromisoformat` thuần sẽ ném ValueError — đây là chỗ dễ hỏng nhất khi ráp nguồn."""
    g = dat_cho.NhaCungCapAeroDataBox._doc_gio(
        {"utc": "2026-09-15 23:15Z", "local": "2026-09-16 06:15+07:00"}
    )
    assert g == datetime(2026, 9, 16, 6, 15)
    assert g.tzinfo is None, "phải cắt tzinfo cho đồng nhất với phần còn lại của hệ thống"


def test_dung_gio_DIA_PHUONG_chu_khong_phai_UTC():
    """Người dùng hỏi "chuyến 6h sáng" theo giờ sân bay. Lấy nhầm UTC là lệch 7 tiếng."""
    g = dat_cho.NhaCungCapAeroDataBox._doc_gio(
        {"utc": "2026-09-15 23:15Z", "local": "2026-09-16 06:15+07:00"}
    )
    assert g.hour == 6, "lấy nhầm UTC thì ra 23h ngày hôm trước"


@pytest.mark.parametrize("xau", [None, {}, {"local": ""}, {"local": "rac"}])
def test_gio_hong_tra_None_chu_khong_no(xau):
    assert dat_cho.NhaCungCapAeroDataBox._doc_gio(xau) is None


# ── LỌC CHẶNG — gói miễn phí không có endpoint tra theo chặng ────────────────

def test_LOC_dung_san_bay_den(monkeypatch):
    """FIDS trả MỌI chuyến rời SGN. Không lọc thì người hỏi SGN→DAD nhận cả chuyến đi Hà Nội."""
    _gia_lap(monkeypatch, [
        _mot_chuyen(so="VN 123", den="DAD"),
        _mot_chuyen(so="VN 999", den="HAN"),
        _mot_chuyen(so="VJ 456", den="DAD"),
    ])
    ds = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)
    assert {c.ma for c in ds} == {"VN123", "VJ456"}
    assert all(c.den == "DAD" for c in ds)


def test_BO_chuyen_thieu_gio_thay_vi_doan(monkeypatch):
    """Một dòng có giờ SAI tệ hơn một dòng vắng mặt — người dùng ra sân bay theo giờ đó."""
    hong = _mot_chuyen(so="VN 777")
    hong["arrival"]["scheduledTime"] = {}
    _gia_lap(monkeypatch, [_mot_chuyen(so="VN 123"), hong])
    ds = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)
    assert [c.ma for c in ds] == ["VN123"]


def test_khung_gio_trong_tra_204_KHONG_phai_loi(monkeypatch):
    """Sân bay không có chuyến trong 12 tiếng là chuyện thường, không phải sự cố."""
    goi = _gia_lap(monkeypatch, [_mot_chuyen()])
    dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)
    assert goi["n"] == 2, "một ngày cần HAI lời gọi vì API chặn khoảng quá 12 tiếng"


def test_sap_theo_GIO_vi_khong_co_gia_de_sap(monkeypatch):
    _gia_lap(monkeypatch, [
        _mot_chuyen(so="VN 900", gio_di="2026-09-16 09:00+07:00"),
        _mot_chuyen(so="VN 100", gio_di="2026-09-16 05:00+07:00"),
    ])
    ds = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)
    assert [c.ma for c in ds] == ["VN100", "VN900"]


# ── DỮ LIỆU THẬT MỚI CÓ ─────────────────────────────────────────────────────

def test_giu_du_lieu_that_ma_nguon_bia_khong_co(monkeypatch):
    _gia_lap(monkeypatch, [_mot_chuyen()])
    d = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)[0].to_dict()
    assert d["hang"] == "Vietnam Airlines"
    assert d["may_bay"] == "Airbus A321"
    assert d["nha_ga"] == "1"
    assert d["trang_thai"] == "Scheduled"


def test_KHONG_doan_chinh_sach_hoan_ve(monkeypatch):
    """FIDS không có dữ liệu vé. Nói "hoàn được" mà không hoàn là dẫn tới quyết định tiền bạc sai."""
    _gia_lap(monkeypatch, [_mot_chuyen()])
    assert dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)[0].hoan_duoc is False


# ── LINK CHI TIẾT chỉ gắn khi số hiệu là THẬT ───────────────────────────────

def test_nguon_that_co_link_chi_tiet_theo_so_hieu(monkeypatch):
    _gia_lap(monkeypatch, [_mot_chuyen()])
    d = dat_cho.NhaCungCapAeroDataBox("k").tim_chuyen_bay("SGN", "DAD", NGAY)[0].to_dict()
    assert "VN123" in d["lien_ket_chi_tiet"]
    assert d["lien_ket_chi_tiet"].startswith("https://www.google.com/search")


def test_nguon_MO_PHONG_KHONG_duoc_gan_link_chi_tiet():
    """Số hiệu mô phỏng do hàm băm sinh ra. Link tới trang trống làm người dùng kết luận
    CÔNG CỤ hỏng, chứ không kết luận dữ liệu là giả — tệ hơn là không có link."""
    d = dat_cho.NhaCungCapMoPhong().tim_chuyen_bay("SGN", "DAD", NGAY)[0].to_dict()
    assert "lien_ket_chi_tiet" not in d
    assert d["lien_ket"], "link theo CHẶNG thì vẫn phải có — chặng là thật"


# ── CHỌN NGUỒN ──────────────────────────────────────────────────────────────

def test_co_khoa_aerodatabox_thi_dung_nguon_do(monkeypatch):
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "aerodatabox_key", "abc", raising=False)
    assert isinstance(dat_cho.lay_nha_cung_cap(), dat_cho.NhaCungCapAeroDataBox)


def test_khong_khoa_nao_thi_van_lui_ve_MO_PHONG(monkeypatch):
    for k in ("amadeus_key", "amadeus_secret", "aerodatabox_key"):
        monkeypatch.setattr(dat_cho.settings, k, "", raising=False)
    assert isinstance(dat_cho.lay_nha_cung_cap(), dat_cho.NhaCungCapMoPhong)


# ── NHÃN: mỗi nguồn tự khai, không ai suy ra bằng cách so chuỗi ─────────────

def test_moi_nguon_tu_khai_nhan_KHAC_NHAU():
    """Bản trước tầng HTTP so `ten == "amadeus"`, nên nguồn thứ ba lặng lẽ bị dán nhãn
    "mô phỏng" — dữ liệu thật đội nhãn giả mà không có gì báo lỗi."""
    ba = [dat_cho.NhaCungCapMoPhong(), dat_cho.NhaCungCapAmadeus("a", "b"),
          dat_cho.NhaCungCapAeroDataBox("k")]
    assert len({n.nhan for n in ba}) == 3, "ba nguồn phải có ba nhãn phân biệt được"
    assert [n.la_that for n in ba] == [False, True, True]
    assert "không có giá" in dat_cho.NhaCungCapAeroDataBox.nhan.lower(), \
        "nhãn phải nói thẳng là thiếu giá, đừng để người xem tự phát hiện"


# ── RANH GIỚI: nguồn này cũng không được chạm tới đặt vé ────────────────────

def test_KHONG_dung_endpoint_dat_ve():
    src = inspect.getsource(dat_cho.NhaCungCapAeroDataBox).lower()
    assert "/flights/airports/" in src
    for cam in ("booking", "order", "payment", "purchase", "/book"):
        assert cam not in src, f"tầng tra cứu không được có {cam!r}"


def test_khach_san_bao_KHONG_HO_TRO_chu_khong_tra_rong():
    """Rỗng bị đọc thành "hết phòng". Đây là "nguồn không có loại dữ liệu này"."""
    with pytest.raises(NotImplementedError):
        dat_cho.NhaCungCapAeroDataBox("k").tim_khach_san("Đà Nẵng", NGAY, NGAY)
