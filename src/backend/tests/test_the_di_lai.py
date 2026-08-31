"""Thẻ 'dilai' — kết quả tra cứu đi lại hiện trong CHAT.

── VÌ SAO CẦN CẢ TỆP NÀY ──
Trước đó kết quả tra cứu rơi vào nhánh mặc định `kind: "text"`, nghĩa là mô hình đọc
dữ liệu tool rồi TỰ VIẾT LẠI thành đoạn văn. Đó đúng là thứ cả tính năng tra cứu sinh
ra để tránh: mô hình có thể chép sai số hiệu, làm rơi nhãn nguồn, hoặc thêm một con giá
không hề có trong dữ liệu — ngay trên phần cần chứng minh là THẬT.

Nên điều được canh ở đây là: THẺ DỰNG TỪ `data` CỦA TOOL, không từ lời mô hình.
"""

from __future__ import annotations

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.api.app import _di_lai_card
from app.services import dat_cho


def _tin_nhan(ten_tool: str, data: list[dict], message: str = "", loi_mo_hinh: str = "văn của mô hình"):
    """Một lượt hội thoại: người hỏi → agent gọi tool → tool trả → agent viết văn."""
    tm = ToolMessage(
        content=json.dumps({"success": True, "message": message, "data": data}),
        name=ten_tool, tool_call_id="t1",
    )
    return [HumanMessage(content="tìm chuyến bay giúp mình"), AIMessage(content=""),
            tm, AIMessage(content=loi_mo_hinh)]


def _chuyen(ma="VN106", hang="Vietnam Airlines", nguon="aerodatabox"):
    return {
        "ma": ma, "hang": hang, "tu": "SGN", "den": "DAD",
        "khoi_hanh": "05/09/2026 05:45", "ha_canh": "05/09/2026 07:05",
        "gia_vnd": 0, "co_gia": False, "so_diem_dung": 0, "hoan_duoc": False,
        "nguon": nguon, "la_that": nguon != "mo_phong",
        "may_bay": "Airbus A321", "nha_ga": "3", "trang_thai": "Expected",
        "lien_ket": "https://www.google.com/travel/flights?q=x",
        "lien_ket_chi_tiet": "https://www.google.com/search?q=VN106",
        "phut_bay": 80,
    }


@pytest.fixture(autouse=True)
def _nguon_that(monkeypatch):
    """Mặc định coi như đang cắm khoá AeroDataBox."""
    for k in ("amadeus_key", "amadeus_secret"):
        monkeypatch.setattr(dat_cho.settings, k, "", raising=False)
    monkeypatch.setattr(dat_cho.settings, "aerodatabox_key", "khoa", raising=False)


# ── DỰNG TỪ DỮ LIỆU, KHÔNG TỪ LỜI MÔ HÌNH ───────────────────────────────────

def test_dung_the_tu_DU_LIEU_tool():
    card = _di_lai_card(_tin_nhan("tim_chuyen_bay", [_chuyen(), _chuyen(ma="VJ628")]))
    assert card and card["kind"] == "dilai" and card["loai"] == "bay"
    assert [it["ma"] for it in card["items"]] == ["VN106", "VJ628"]


def test_KHONG_lay_gi_tu_van_cua_mo_hinh():
    """Mô hình có thể chép sai số hiệu. Thẻ không được lấy một chữ nào từ đó."""
    card = _di_lai_card(_tin_nhan(
        "tim_chuyen_bay", [_chuyen(ma="VN106")],
        loi_mo_hinh="Mình tìm được chuyến VN999 giá 1.200.000đ nhé!",
    ))
    assert card["items"][0]["ma"] == "VN106", "số hiệu phải theo tool, không theo mô hình"
    assert "VN999" not in json.dumps(card, ensure_ascii=False)
    assert "1.200.000" not in json.dumps(card, ensure_ascii=False)


def test_giu_nguyen_moi_truong_de_ve_giong_khung_tra_cuu():
    """Chat và khung 'Tra cứu đi lại' phải hiện y hệt nhau, nên thẻ không được cắt bớt."""
    card = _di_lai_card(_tin_nhan("tim_chuyen_bay", [_chuyen()]))
    it = card["items"][0]
    for truong in ("ma", "hang", "khoi_hanh", "co_gia", "may_bay", "nha_ga",
                   "lien_ket", "lien_ket_chi_tiet"):
        assert truong in it, f"thiếu {truong!r} thì chat vẽ khác khung tra cứu"


# ── NHÃN NGUỒN ──────────────────────────────────────────────────────────────

def test_nguon_that_thi_nhan_that():
    card = _di_lai_card(_tin_nhan("tim_chuyen_bay", [_chuyen()]))
    assert card["la_that"] is True
    assert "THẬT" in card["nhan"]


def test_KHACH_SAN_lui_ve_mo_phong_thi_NHAN_CUNG_LUI():
    """Chỗ dễ hỏng nhất: nguồn BAY là thật, nhưng khách sạn lui về mô phỏng.

    Nếu nhãn lấy theo nhà cung cấp đang chọn thay vì theo dữ liệu thật sự trả về,
    phòng bịa sẽ đội nhãn 'LỊCH BAY THẬT' ngay trong chat."""
    phong = {"ma": "KS1", "ten": "Riverside", "thanh_pho": "Đà Nẵng",
             "gia_moi_dem_vnd": 900000, "nguon": "mo_phong", "so_sao": 4.0}
    card = _di_lai_card(_tin_nhan("tim_khach_san", [phong]))
    assert card["loai"] == "phong"
    assert card["nguon"] == "mo_phong"
    assert card["la_that"] is False
    assert "MÔ PHỎNG" in card["nhan"]


def test_khong_cam_khoa_thi_bay_cung_mang_nhan_mo_phong(monkeypatch):
    monkeypatch.setattr(dat_cho.settings, "aerodatabox_key", "", raising=False)
    card = _di_lai_card(_tin_nhan("tim_chuyen_bay", [_chuyen(nguon="mo_phong")]))
    assert card["la_that"] is False and "MÔ PHỎNG" in card["nhan"]


# ── KHÔNG DỰNG THẺ RỖNG / THẺ SAI LƯỢT ──────────────────────────────────────

def test_khong_co_ket_qua_thi_KHONG_dung_the():
    """Thẻ rỗng trông như giao diện hỏng. Để mô hình nói 'không có chuyến nào' rõ hơn."""
    assert _di_lai_card(_tin_nhan("tim_chuyen_bay", [])) is None


def test_luot_khong_tra_cuu_thi_tra_None():
    assert _di_lai_card([HumanMessage(content="tóm tắt thư"), AIMessage(content="xong")]) is None


def test_CHI_lay_tool_cua_luot_NAY():
    """Hỏi chuyến bay ở lượt trước, lượt này hỏi chuyện khác — không được hiện lại
    bảng cũ như thể vừa tra."""
    cu = _tin_nhan("tim_chuyen_bay", [_chuyen()])
    moi = cu + [HumanMessage(content="cảm ơn nhé"), AIMessage(content="không có gì")]
    assert _di_lai_card(moi) is None


def test_du_lieu_tool_hong_thi_tra_None_chu_khong_no():
    tm = ToolMessage(content="khong-phai-json", name="tim_chuyen_bay", tool_call_id="t1")
    assert _di_lai_card([HumanMessage(content="tìm vé"), tm]) is None
