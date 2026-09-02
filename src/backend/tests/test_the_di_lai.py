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


# ── DIGEST & TRIAGE: gọi ĐÚNG chữ ký `mail.list_messages` ───────────────────

def _mail_gia_dung_chu_ky(monkeypatch, so_thu=3):
    """Giả lập mang ĐÚNG chữ ký thật: `(provider, token, **kw)`.

    Đây là điểm mấu chốt. `mail.list_messages` chỉ nhận tham số THEO TÊN sau hai cái
    đầu; gọi bằng vị trí thì ném TypeError ngay. Bản đầu của tom_tat_ngay và
    phan_loai_uu_tien gọi sai như vậy, và agent dịch lỗi đó thành "em đang gặp sự cố
    kỹ thuật" — nhìn từ giao diện không có cách nào đoán ra nguyên nhân.

    Giả lập nhận `*args` thì test sẽ XANH trên một lời gọi hỏng. Nên nó phải giống
    hàm thật tới mức từ chối đúng những gì hàm thật từ chối."""
    from app.schemas.email import Email
    from app.tools import email_tools as T

    def gia(provider, token, **kw):
        ds = [Email(id=f"m{i}", sender="Giáo vụ HCMUS", senderEmail="gv@hcmus.edu.vn",
                    senderInitial="G", to="me@x.com",
                    subject=f"Nộp báo cáo {i} trước 18/9",
                    preview="Vui lòng nộp trước 23:59 ngày 18/9.",
                    body=["x"], time="10:00", date="02/09/2026 10:00",
                    unread=True, starred=False, category="moss", label="Học tập",
                    folder="inbox")
             for i in range(so_thu)]
        return (ds, None)

    monkeypatch.setattr(T.mail, "list_messages", gia)


def test_digest_chay_duoc_va_dem_dung(monkeypatch):
    import asyncio
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext
    from app.tools.schemas import TomTatNgayInput

    _mail_gia_dung_chu_ky(monkeypatch, so_thu=3)
    out = asyncio.run(T.tom_tat_ngay(TomTatNgayInput(),
                                     RequestContext(user_id="1", access_token="t")))
    assert out.success, out.message
    assert out.data["tong"] == 3 and out.data["chua_doc"] == 3
    assert out.data["thu"], "phải kèm id thư để giao diện gắn nút Mở nhanh"


def test_triage_chay_duoc(monkeypatch):
    import asyncio
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext
    from app.tools.schemas import PhanLoaiUuTienInput

    _mail_gia_dung_chu_ky(monkeypatch, so_thu=2)
    out = asyncio.run(T.phan_loai_uu_tien(PhanLoaiUuTienInput(),
                                          RequestContext(user_id="1", access_token="t")))
    assert out.success, out.message
    assert out.data["nhom"], "thư có hạn nộp thì phải rơi vào một nhóm ưu tiên"


# ── "TUẦN NÀY" ≠ "7 NGÀY TỚI" ───────────────────────────────────────────────

@pytest.mark.parametrize("thu_trong_tuan,so_ngay_mong_doi", [
    (0, 7),  # thứ Hai  → Hai..CN = 7 ngày
    (2, 5),  # thứ Tư   → Tư..CN  = 5 ngày
    (5, 2),  # thứ Bảy  → Bảy, CN = 2 ngày
    (6, 1),  # Chủ nhật → chỉ hôm nay
])
def test_tuan_nay_la_tu_hom_nay_den_het_chu_nhat(monkeypatch, thu_trong_tuan, so_ngay_mong_doi):
    """Hỏi hôm thứ Tư mà trả lời tới thứ Ba tuần sau là trả lời một câu KHÁC với câu
    được hỏi — và người dùng không có cách nào biết mình vừa nhận khoảng thời gian khác."""
    import asyncio
    from datetime import datetime, timedelta
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext
    from app.tools.schemas import ApLucLichTrinhInput

    # Dựng một ngày có đúng thứ mong muốn (02/09/2026 là thứ Tư).
    goc = datetime(2026, 9, 2, 10, 0)
    gia_ngay = goc + timedelta(days=(thu_trong_tuan - goc.weekday()))

    class _DT(datetime):
        @classmethod
        def now(cls, tz=None):
            return gia_ngay

    monkeypatch.setattr(T, "datetime", _DT)
    monkeypatch.setattr(T.mail, "list_messages", lambda p, t, **kw: ([], None))

    out = asyncio.run(T.ap_luc_lich_trinh(
        ApLucLichTrinhInput(pham_vi="tuan_nay"),
        RequestContext(user_id="1", access_token="t")))
    assert len(out.data) == so_ngay_mong_doi, (
        f"weekday={thu_trong_tuan}: ra {len(out.data)} ngày, mong đợi {so_ngay_mong_doi}")
    assert "tuần này" in out.message, "phải NÓI RÕ khoảng đang trả lời để đối chiếu được"


def test_n_ngay_van_giu_hanh_vi_cu(monkeypatch):
    """Không nói rõ thì vẫn là cửa sổ trượt — đừng đổi mặc định dưới chân người dùng."""
    import asyncio
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext
    from app.tools.schemas import ApLucLichTrinhInput

    monkeypatch.setattr(T.mail, "list_messages", lambda p, t, **kw: ([], None))
    out = asyncio.run(T.ap_luc_lich_trinh(
        ApLucLichTrinhInput(), RequestContext(user_id="1", access_token="t")))
    assert len(out.data) == 7 and "7 ngày tới" in out.message


# ── TÌM CỤM TỪ NGUYÊN CỤM ───────────────────────────────────────────────────

@pytest.mark.parametrize("vao,ra", [
    ("học phí", '"học phí"'),               # Gmail tách rời sẽ khớp cả "MIỄN PHÍ"
    ("lịch bảo vệ", '"lịch bảo vệ"'),
    # CÓ dấu hai chấm → để nguyên, kể cả khi nó không phải toán tử Gmail thật.
    # Đây là lựa chọn THẬN TRỌNG có chủ ý: bọc nhầm một truy vấn có toán tử sẽ phá cú
    # pháp và trả về rỗng, còn bỏ sót một cụm có dấu hai chấm thì chỉ kém chính xác
    # một chút. Hỏng im lặng đắt hơn hỏng lộ.
    ("từ:x học phí", "từ:x học phí"),
    ("from:giaovu học phí", "from:giaovu học phí"),   # có toán tử → giữ nguyên
    ('"đã có ngoặc"', '"đã có ngoặc"'),      # đã bọc rồi → không bọc thêm
    ("baocao", "baocao"),                    # một từ → không cần bọc
])
def test_cum_tu_duoc_boc_ngoac_kep(monkeypatch, vao, ra):
    import asyncio
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext
    from app.tools.schemas import SearchEmailsInput

    ghi = {}
    monkeypatch.setattr(T.mail, "list_messages",
                        lambda p, t, **kw: (ghi.update(q=kw.get("q")), ([], None))[1])
    asyncio.run(T.search_emails(SearchEmailsInput(query=vao),
                                RequestContext(user_id="1", access_token="t")))
    assert ghi["q"] == ra, f"{vao!r} → {ghi['q']!r}, mong đợi {ra!r}"
