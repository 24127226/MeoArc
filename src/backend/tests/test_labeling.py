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


def test_taxonomy_khop_7_mau_FE():
    """7 nhãn ↔ đúng 7 màu chip FE (moss/sea/sun/cherry/sky/terra/wine), không trùng."""
    colors = [c.color for c in ALL_CATEGORIES]
    assert sorted(colors) == sorted({"moss", "sea", "sun", "cherry", "sky", "terra", "wine"}), \
        f"Màu nhãn lệch bảng màu FE: {colors}"
    assert len(set(colors)) == 7, "Có 2 nhãn trùng màu → FE hiển thị lẫn"


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
