"""test_labeling.py — Độ CHÍNH XÁC của engine tự phân loại nhãn (UC009).

Chuẩn khách quan: người gửi/nội dung ĐÃ BIẾT → nhãn ĐÚNG theo taxonomy công bố.
Đây là "bộ dữ liệu vàng" (golden set) — engine sai 1 ca là FAIL, dùng để đo lại
mỗi khi chỉnh rule (chống hồi quy). KHÔNG cần mạng/LLM/quota.

Chạy: uv run pytest tests/test_labeling.py -v
"""

from __future__ import annotations

import asyncio

import pytest

from app.core.labeling import classify, ALL_CATEGORIES


# (email người gửi, tên, tiêu đề, snippet) → key nhãn mong đợi
GOLDEN: list[tuple[tuple[str, str, str, str], str]] = [
    # Học tập — trường/phòng ban
    (("giaovu@fit.hcmus.edu.vn", "Giáo vụ HCMUS", "Nhắc nộp SRS", "hạn thứ Sáu"), "hoc_tap"),
    (("noreply@classroom.google.com", "Classroom", "Bài tập mới", "môn CNPM"), "hoc_tap"),
    (("info@daotao.university.vn", "Phòng Đào tạo", "Lịch thi học kỳ", ""), "hoc_tap"),
    # Mạng xã hội
    (("notification@facebookmail.com", "Facebook", "Bạn có thông báo mới", "5 lượt thích"), "mang_xh"),
    (("no-reply@mail.instagram.com", "Instagram", "hoạt động mới", "story"), "mang_xh"),
    (("noreply@tiktok.com", "TikTok", "video mới", ""), "mang_xh"),
    (("messaging@linkedin.com", "LinkedIn", "bạn có tin nhắn", "kết nối"), "mang_xh"),
    # Tài chính — ngân hàng/ví (thắng cả khi có chữ 'khuyến mãi')
    (("no-reply@vietcombank.com.vn", "Vietcombank", "Biến động số dư", "GD -50.000đ"), "tai_chinh"),
    (("noreply@momo.vn", "MoMo", "Thanh toán thành công", "hoá đơn điện"), "tai_chinh"),
    (("service@paypal.com", "PayPal", "Receipt", "payment"), "tai_chinh"),
    # Mua sắm & Ưu đãi
    (("no-reply@shopee.vn", "Shopee", "Flash Sale 12.12", "giảm 50%"), "mua_sam"),
    (("noreply@lazada.vn", "Lazada", "Đơn hàng đang giao", ""), "mua_sam"),
    (("news@newsletter.substack.com", "Bản tin", "Weekly digest", ""), "mua_sam"),
    # Cập nhật & Hệ thống
    (("noreply@github.com", "GitHub", "[repo] PR merged", ""), "he_thong"),
    (("no-reply@accounts.google.com", "Google", "Security alert", "thiết bị mới đăng nhập"), "he_thong"),
    (("notifications@vercel.com", "Vercel", "Deployment ready", ""), "he_thong"),
    # Công việc / tuyển dụng
    (("jobs@topcv.vn", "TopCV", "Việc làm phù hợp", "ứng tuyển ngay"), "cong_viec"),
    (("hr@company.com", "HR Team", "Thư mời phỏng vấn", "interview"), "cong_viec"),
    # Cá nhân — người thật (không bot, không domain đặc thù)
    (("thien.nguyen95@gmail.com", "Nguyễn Thiên", "Đi cà phê không?", "cuối tuần rảnh chứ"), "ca_nhan"),
]


@pytest.mark.parametrize("inp,expected", GOLDEN)
def test_golden_set_phan_loai_dung(inp, expected):
    got = classify(*inp)
    assert got.category.key == expected, (
        f"'{inp[1]} <{inp[0]}>' — mong '{expected}', nhận '{got.category.key}' "
        f"(lý do: {got.reason})"
    )


def test_do_chinh_xac_toi_thieu_90():
    """Chỉ số tổng: engine phải đúng >= 90% golden set (chống chỉnh rule làm tụt chất lượng)."""
    correct = sum(1 for inp, exp in GOLDEN if classify(*inp).category.key == exp)
    acc = correct / len(GOLDEN)
    assert acc >= 0.90, f"Độ chính xác {acc:.0%} < 90% ({correct}/{len(GOLDEN)})"


def test_ngan_hang_thang_khuyen_mai():
    """Ca dễ sai: thư ngân hàng có chữ 'ưu đãi' vẫn phải là Tài chính (tên miền thắng từ khoá)."""
    c = classify("no-reply@techcombank.com.vn", "Techcombank", "Ưu đãi thẻ tín dụng", "giảm giá")
    assert c.category.key == "tai_chinh"


def test_moi_phan_loai_co_reason_va_confidence():
    c = classify("noreply@github.com", "GitHub", "x", "")
    assert c.reason and c.confidence in ("high", "medium", "low")
    assert c.confidence == "high", "khớp tên miền phải là high"


def test_taxonomy_khop_8_mau_FE():
    """8 nhãn ↔ đúng 8 màu chip FE, không trùng.

    `jade` (Đi lại) thêm sau khi ĐO: vé máy bay và xác nhận đặt phòng không có nhãn
    nào để về nên rơi vào "Cá nhân". Danh sách này phải khớp 1-1 với
    `src/frontend/src/data/categories.ts` — lệch thì chip hiện ra không có màu, hoặc
    hai nhãn dùng chung một màu và người dùng đọc ra thành một nhóm."""
    colors = [c.color for c in ALL_CATEGORIES]
    assert sorted(colors) == sorted({"moss", "sea", "sun", "cherry", "sky", "terra",
                                     "wine", "jade"}), \
        f"Màu nhãn lệch bảng màu FE: {colors}"
    assert len(set(colors)) == 8, "Có 2 nhãn trùng màu → FE hiển thị lẫn"


# ── Tool categorize_emails + thẻ FE (mạch end-to-end, dữ liệu Gmail GIẢ) ──
def _fake_email(i, sender, sender_email, subject):
    from app.schemas.email import Email
    return Email(id=f"id{i}", sender=sender, senderEmail=sender_email, senderInitial=sender[:1],
                 to="", subject=subject, preview="", body=[""], time="09:00",
                 date="Hôm nay, 09:00", unread=True, starred=False, category="moss",
                 threadId=f"th{i}")


def test_tool_categorize_va_the_FE(monkeypatch):
    import app.tools.email_tools as et
    from app.tools.schemas import CategorizeEmailsInput
    from app.tools.registry import RequestContext
    from app.api.app import _categorize_card
    import json
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    emails = [
        _fake_email(0, "Giáo vụ", "giaovu@fit.hcmus.edu.vn", "Nộp báo cáo"),
        _fake_email(1, "Shopee", "no-reply@shopee.vn", "Flash Sale"),
        _fake_email(2, "GitHub", "noreply@github.com", "PR review"),
    ]
    monkeypatch.setattr(et.gmail_service, "list_messages",
                        lambda tok, q=None, max_results=20, **kw: (emails, None))

    out = asyncio.run(et.categorize_emails(
        CategorizeEmailsInput(limit=20), RequestContext(user_id="qa", access_token="t")))
    d = out.model_dump()
    labels = {it["id"]: it["label"] for it in d["data"]}
    assert labels["id0"] == "Học tập" and labels["id1"] == "Mua sắm & Ưu đãi" and labels["id2"] == "Cập nhật & Hệ thống"
    assert d["summary"], "phải có thống kê số thư theo nhãn"

    # thẻ categorize dựng từ tool → đúng khuôn FE (items có id/sender/subject/category/label)
    tm = ToolMessage(content=json.dumps(d, default=str), name="categorize_emails", tool_call_id="t1")
    card = _categorize_card([HumanMessage(content="phân loại hộp thư"), AIMessage(content=""), tm,
                             AIMessage(content="xong")])
    assert card and card["kind"] == "categorize" and len(card["items"]) == 3
    assert {"id", "sender", "subject", "category", "label"} <= set(card["items"][0])
    # màu chip FE hợp lệ
    assert all(it["category"] in {"moss", "sea", "sun", "cherry", "sky", "terra", "wine"}
               for it in card["items"])


def test_categorize_la_tool_doc_khong_confirm():
    import app.tools.email_tools  # noqa: F401
    from app.tools.registry import tool_registry
    assert tool_registry.get_spec("categorize_emails").requires_confirmation is False


# ══════════════════════════════════════════════════════════════════════════════
# MẢNH TÊN MIỀN CHỈ ĐƯỢC KHỚP PHẦN TÊN MIỀN, KHÔNG KHỚP TÊN NGƯỜI GỬI
#
# Người dùng báo "phân loại tự động khá dở": xác nhận đặt phòng khách sạn và vé máy
# bay đều bị xếp vào Học tập. Đo lại thì AI không hề tham gia — `classify()` là tất
# định, và nó khớp chuỗi con `hcmus` trong `meoarc.hcmus@outlook.com.vn`, tức trong
# TÊN NGƯỜI DÙNG chứ không phải tên miền. Luật tên miền chạy trước mọi luật từ khoá
# và trả về confidence "high", nên MỌI thư từ tài khoản đó đều thành Học tập.
#
# Cùng cái bẫy còn nằm sẵn ở vài chỗ khác (`microsoft`, `amazon.`, `shopee`...), nên
# test khoá cả luật chung chứ không chỉ khoá đúng một ca đã gặp.
# ══════════════════════════════════════════════════════════════════════════════

def test_ten_truong_trong_TEN_NGUOI_GUI_khong_bien_moi_thu_thanh_hoc_tap():
    """Chính ca người dùng gặp, trên chính địa chỉ demo."""
    from app.core.labeling import classify
    for tieu_de, than in [
        ("Xác nhận đặt phòng 19/9 - 21/9", "Khách sạn A, Đà Nẵng. Mã đặt chỗ ABC."),
        ("Xác nhận đặt chỗ — SGN đi HAN ngày 19/9", "Vietnam Airlines, ghế 12A."),
    ]:
        c = classify("meoarc.hcmus@outlook.com.vn", "", tieu_de, than)
        assert c.category.label != "Học tập", f"{tieu_de} → {c.category.label} ({c.reason})"


def test_ten_hang_trong_TEN_NGUOI_GUI_cung_khong_tinh():
    from app.core.labeling import classify
    for addr, khong_duoc in [("microsoft.fan@gmail.com", "Cập nhật & Hệ thống"),
                             ("amazon.deals.vn@gmail.com", "Mua sắm & Ưu đãi"),
                             ("shopee.review@gmail.com", "Mua sắm & Ưu đãi")]:
        assert classify(addr, "", "Chào bạn", "").category.label != khong_duoc


def test_TEN_MIEN_THAT_van_khop_nhu_cu():
    """Phép sửa không được làm mất phần vốn đúng."""
    from app.core.labeling import classify
    for addr, mong_doi in [("giaovu@fit.hcmus.edu.vn", "Học tập"),
                           ("noreply@classroom.google.com", "Học tập"),
                           ("alert@vietcombank.com.vn", "Tài chính"),
                           ("notify@facebookmail.com", "Mạng xã hội"),
                           ("noreply@github.com", "Cập nhật & Hệ thống")]:
        c = classify(addr, "", "", "")
        assert c.category.label == mong_doi and c.confidence == "high", f"{addr} → {c.category.label}"


def test_manh_CO_dau_a_coi_van_neo_vao_ten_nguoi_gui():
    """`hr@`, `@momo`... được viết ra để neo qua ranh giới địa chỉ — giữ nguyên ý đó."""
    from app.core.labeling import classify
    assert classify("hr@fpt.com.vn", "", "", "").category.label == "Công việc"
    assert classify("tuyendung@vng.com.vn", "", "", "").category.label == "Công việc"
    assert classify("no-reply@momo.vn", "", "", "").category.label == "Tài chính"


def test_khong_ro_thi_confidence_THAP_chu_khong_doan_bua():
    """Không đọc ra được gì thì phải là 'low', đừng đoán bừa.

    'low' là tín hiệu cho agent biết chỗ này cần suy luận thêm; một phân loại sai mà
    mang 'high' thì không ai nghi ngờ nó.

    (Ca cũ ở đây là thư đặt chỗ máy bay — hồi đó chưa có nhãn Đi lại nên nó rơi về
    mặc định. Nay đã có nhãn thật nên ca đó chuyển xuống dưới, còn chỗ này dùng một
    lá thư thực sự không có tín hiệu nào.)"""
    from app.core.labeling import classify
    c = classify("ai.do@gmail.com", "Ai Đó", "Chào bạn", "Nhắn chút thôi.")
    assert c.confidence == "low"


def test_thu_DI_LAI_co_nhan_rieng():
    """Chính lý do thêm nhãn: bốn thư đi lại trong bộ demo trước đây rơi vào 'Cá nhân'."""
    from app.core.labeling import classify
    tu_minh = "meoarc.hcmus@outlook.com.vn"
    for ten, tieu_de in [
        ("Vietnam Airlines", "Xác nhận đặt chỗ — SGN đi HAN ngày 19/9"),
        ("Vietnam Airlines", "THAY ĐỔI LỊCH BAY — mã đặt chỗ XKPQ7M"),
        ("Booking.com", "Xác nhận đặt phòng của bạn"),
        ("Hanoi La Siesta Premium", "Xác nhận đặt phòng 19/9 - 21/9"),
    ]:
        c = classify(tu_minh, ten, tieu_de, "")
        assert c.category.label == "Đi lại", f"{ten} → {c.category.label}"


def test_DI_LAI_thang_TAI_CHINH_khi_thu_nhac_ca_hai():
    """Xác nhận đặt phòng gần như luôn nhắc chuyện đã thanh toán. Với người dùng thì
    đó là CHUYẾN ĐI — biên lai chỉ là mặt phụ."""
    from app.core.labeling import classify
    c = classify("ai.do@gmail.com", "Ai Đó", "Xác nhận đặt phòng 19/9",
                 "Bạn đã thanh toán 1.200.000đ. Mã đặt chỗ ABC123.")
    assert c.category.label == "Đi lại"


def test_DI_LAI_khong_cuop_thu_tai_chinh_thuong():
    """Ranh giới ngược lại: sao kê ngân hàng không được biến thành chuyến đi."""
    from app.core.labeling import classify
    c = classify("ai.do@gmail.com", "Ngân hàng ACB", "Sao kê tài khoản tháng 9",
                 "Số dư cuối kỳ 5.000.000đ. Xem chi tiết giao dịch.")
    assert c.category.label == "Tài chính"


# ══════════════════════════════════════════════════════════════════════════════
# TÊN HIỂN THỊ NGƯỜI GỬI LÀ TÍN HIỆU, KHÔNG CHỈ ĐỂ DÒ BOT
#
# Đo trên bộ 46 thư demo: 28 thư (61%) rơi vào "Cá nhân / low" chỉ vì thư được TỰ GỬI
# cho chính mình nên địa chỉ luôn giống nhau và không nói lên gì. Toàn bộ thông tin
# nằm ở tên hiển thị, mà tên trước đây chỉ dùng để dò xem có phải bot không.
# Sau khi đọc tên: còn 15, và 10 trong số đó là người thật — tức đúng.
# ══════════════════════════════════════════════════════════════════════════════

def test_ten_hien_thi_phan_loai_duoc_khi_dia_chi_KHONG_noi_gi():
    """Hộp thư tự gửi cho chính mình — địa chỉ giống hệt nhau ở mọi thư."""
    from app.core.labeling import classify
    tu_minh = "quanpta.meoarc@gmail.com"
    for ten, mong_doi in [("Giáo vụ HCMUS", "Học tập"),
                          ("Phòng Đào tạo HCMUS", "Học tập"),
                          ("CLB Học thuật", "Học tập"),
                          ("Ban tổ chức Hackathon", "Học tập"),
                          ("GitHub", "Cập nhật & Hệ thống"),
                          ("Azure", "Cập nhật & Hệ thống"),
                          ("Shopee", "Mua sắm & Ưu đãi")]:
        c = classify(tu_minh, ten, "Một tiêu đề trung tính", "")
        assert c.category.label == mong_doi, f"{ten} → {c.category.label}"


def test_ten_nguoi_THAT_van_la_ca_nhan():
    """Ranh giới quan trọng: đọc tên không được biến bạn bè thành thông báo hệ thống."""
    from app.core.labeling import classify
    for ten in ["Phạm Thu Trang", "Mẹ", "Lê Anh Đức", "Nguyễn Hoàng Nam"]:
        assert classify("quanpta.meoarc@gmail.com", ten, "hihi", "").category.label == "Cá nhân"


def test_GVHD_la_viec_HOC_chu_khong_phai_ca_nhan():
    """ĐẢO LẠI quyết định hôm qua: bản test trước xếp "Nguyễn Văn Sơn (GVHD)" vào
    Cá nhân, lấy lý do đó là người thật. Đúng là người thật — nhưng thứ người dùng cần
    thấy khi thầy hướng dẫn nhắn về chương khoá luận là VIỆC HỌC, không phải một lá thư
    bạn bè. "GVHD" là cách xưng chỉ có trong thư trường lớp nên rất an toàn để nhận."""
    from app.core.labeling import classify
    c = classify("quanpta.meoarc@gmail.com", "Nguyễn Văn Sơn (GVHD)",
                 "Về bản chỉnh sửa chương 3", "Thầy đã xem qua chương 3.")
    assert c.category.label == "Học tập"


def test_ten_hien_thi_chi_dat_MEDIUM_khong_phai_HIGH():
    """Tên hiển thị ai đặt cũng được, không như tên miền đã qua xác thực. Một phân
    loại sai mà mang 'high' thì không ai nghi ngờ nó."""
    from app.core.labeling import classify
    assert classify("quanpta.meoarc@gmail.com", "GitHub", "", "").confidence == "medium"
    assert classify("noreply@github.com", "GitHub", "", "").confidence == "high"


def test_manh_NGAN_khong_duoc_khop_ten_hien_thi():
    """`edu` (3 ký tự) mà khớp tên thì 'EduMax Academy' — một thư quảng cáo — thành
    thư nhà trường. Mảnh ngắn chỉ đáng tin khi nằm trong TÊN MIỀN, nơi có ranh giới."""
    from app.core.labeling import classify
    c = classify("quanpta.meoarc@gmail.com", "EduMax Academy",
                 "Khoá học lập trình MIỄN PHÍ 100% — chỉ còn 2 ngày!", "")
    assert c.category.label != "Học tập"


def test_TEN_MIEN_van_thang_TEN_HIEN_THI():
    """Thứ tự tín hiệu phải giữ nguyên: tên miền đã xác thực > tên tự xưng."""
    from app.core.labeling import classify
    c = classify("noreply@github.com", "Giáo vụ HCMUS", "", "")
    assert c.category.label == "Cập nhật & Hệ thống" and c.confidence == "high"
