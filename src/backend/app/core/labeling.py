# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/labeling.py — ENGINE TỰ PHÂN LOẠI EMAIL (UC009)          ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mục tiêu: KHÔNG bắt người dùng gắn nhãn tay từng thư. Máy tự đoán  ║
# ║ nhãn theo TÍN HIỆU MẠNH NHẤT = tên miền người gửi, phụ trợ là từ   ║
# ║ khoá tiêu đề/nội dung. Tất định (regex/map) → 0 quota, tức thì,     ║
# ║ GIẢI THÍCH ĐƯỢC (mỗi phân loại kèm 'reason' để người dùng tin).    ║
# ║                                                                    ║
# ║ Vì sao TẤT ĐỊNH (rule) chứ không nhét LLM vào trong tool: tên miền  ║
# ║ gửi phân loại đúng ~70-80% (github→Hệ thống, facebookmail→Mạng xã   ║
# ║ hội, shopee→Mua sắm) — nhanh, miễn phí, không sai vặt. Mỗi kết quả  ║
# ║ kèm 'confidence': thư KHỚP TÊN MIỀN = high (chắc); thư lạ = low. Số  ║
# ║ ít 'low' (mơ hồ) để AGENT ĐANG LÁI tự tinh chỉnh bằng suy luận —    ║
# ║ agent trong app HOẶC agent ngoài qua MCP. Đúng tinh thần agent-     ║
# ║ native: TOOL cấp dữ kiện tất định, SUY LUẬN thuộc về agent.         ║
# ║                                                                    ║
# ║ 7 nhãn khớp 1-1 với 7 màu chip FE (data/categories.ts) — hiện đại   ║
# ║ hoá cho bối cảnh sinh viên VN 2026; 'label' cũng là TÊN NHÃN THẬT   ║
# ║ áp lên Gmail.                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str        # định danh nội bộ
    label: str      # tên hiển thị = TÊN NHÃN áp lên Gmail
    color: str      # màu chip FE (khớp data/categories.ts)
    desc: str       # mô tả để LLM/hiển thị


# ── TAXONOMY (7 nhãn ↔ 7 màu FE) ─────────────────────────────────────
HOC_TAP   = Category("hoc_tap",  "Học tập",            "moss",   "trường/phòng ban/giáo vụ/LMS/lớp học")
CONG_VIEC = Category("cong_viec","Công việc",          "sea",    "tuyển dụng/thực tập/công ty/dev/dự án")
HE_THONG  = Category("he_thong", "Cập nhật & Hệ thống","sun",    "thông báo tự động/bảo mật/OTP/no-reply")
CA_NHAN   = Category("ca_nhan",  "Cá nhân",            "cherry", "người thật gửi/bạn bè/gia đình")
MANG_XH   = Category("mang_xh",  "Mạng xã hội",        "sky",    "Facebook/Instagram/TikTok/X/LinkedIn/YouTube")
MUA_SAM   = Category("mua_sam",  "Mua sắm & Ưu đãi",   "terra",  "Shopee/Lazada/Tiki/khuyến mãi/voucher/bản tin")
TAI_CHINH = Category("tai_chinh","Tài chính",          "wine",   "ngân hàng/ví điện tử/hoá đơn/thanh toán")

ALL_CATEGORIES = [HOC_TAP, CONG_VIEC, HE_THONG, CA_NHAN, MANG_XH, MUA_SAM, TAI_CHINH]
_BY_KEY = {c.key: c for c in ALL_CATEGORIES}


@dataclass(frozen=True)
class Classification:
    category: Category
    confidence: str   # "high" (khớp tên miền) | "medium" (khớp từ khoá) | "low" (đoán mặc định)
    reason: str       # câu giải thích ngắn cho người dùng


# ── TÍN HIỆU 1: TÊN MIỀN người gửi (mạnh nhất → confidence high) ──────
# Thứ tự có ý nghĩa: rule đứng trước thắng. Đặt cái ĐẶC THÙ trước cái chung.
# Mỗi mục: (danh sách mảnh chuỗi trong email/domain, category, lý do).
_DOMAIN_RULES: list[tuple[list[str], Category, str]] = [
    # Học tập — trường/giáo dục
    (["edu.vn", ".edu", "hcmus", "fit.hcmus", "vnu.edu", "student.", "giaovu", "daotao",
      "phongdaotao", "elearning", "lms.", "moodle", "courses.", "classroom.google"],
     HOC_TAP, "gửi từ tên miền giáo dục/nhà trường"),

    # Tài chính — ngân hàng/ví/thanh toán (ĐẶT TRƯỚC mua sắm: 'bank' ưu tiên hơn 'sale')
    (["vietcombank", "techcombank", "vpbank", "acb.com", "mbbank", "bidv", "tpbank", "sacombank",
      "vietinbank", "@momo", "zalopay", "vnpay", "payoo", "shopeepay", "paypal", "stripe.com",
      "banking", "napas"],
     TAI_CHINH, "gửi từ ngân hàng/ví điện tử/cổng thanh toán"),

    # Mạng xã hội
    (["facebookmail", "facebook.com", "instagram", "tiktok", "twitter.com", "@x.com", "notify.twitter",
      "linkedin.com", "threads.net", "youtube.com", "discord", "reddit", "pinterest", "@zalo"],
     MANG_XH, "gửi từ nền tảng mạng xã hội"),

    # Công việc/Tuyển dụng
    (["topcv", "vietnamworks", "itviec", "careerbuilder", "indeed", "glints", "ybox",
      "recruit", "talent", "hr@", "tuyendung", "jobs.", "workable", "greenhouse.io", "lever.co"],
     CONG_VIEC, "gửi từ nền tảng/bộ phận tuyển dụng"),

    # Mua sắm & Ưu đãi — sàn TMĐT + bản tin marketing
    (["shopee", "lazada", "tiki.vn", "sendo", "@grab", "shopeemail", "dienmay", "thegioididong",
      "fptshop", "amazon.", "aliexpress", "temu", "newsletter", "mailchimp", "sendgrid.net",
      "substack", "marketing@", "promo", "deals@"],
     MUA_SAM, "gửi từ sàn mua sắm/bản tin khuyến mãi"),

    # Cập nhật & Hệ thống — thông báo tự động, dev-ops, bảo mật
    (["github.com", "gitlab", "vercel", "netlify", "atlassian", "jira", "notion.so", "slack.com",
      "accounts.google", "no-reply@google", "security@", "microsoft", "office365",
      "cloudflare", "aws.amazon", "digitalocean", "render.com", "railway", "supabase", "firebase",
      "openai.com", "anthropic", "figma.com"],
     HE_THONG, "thông báo tự động từ dịch vụ/hệ thống"),
]

# ── TÍN HIỆU 2: TỪ KHOÁ tiêu đề + nội dung (phụ trợ → confidence medium) ──
_KEYWORD_RULES: list[tuple[str, Category, str]] = [
    (r"(otp|mã xác (thực|minh)|verification code|one-time|security alert|"
     r"cảnh báo bảo mật|đổi mật khẩu|reset password)", HE_THONG, "chứa mã OTP/cảnh báo bảo mật"),
    (r"(hoá đơn|hóa đơn|invoice|receipt|biên lai|thanh toán|payment|sao kê|statement|"
     r"số dư|dư nợ|chuyển khoản|giao dịch)", TAI_CHINH, "nói về hoá đơn/thanh toán/giao dịch"),
    (r"(tuyển dụng|internship|thực tập|ứng tuyển|phỏng vấn|interview|offer thư mời|hồ sơ ứng)",
     CONG_VIEC, "liên quan tuyển dụng/công việc"),
    (r"(giảm giá|khuyến mãi|\bsale\b|voucher|mã giảm|flash ?sale|ưu đãi|\bdeal\b|black ?friday|"
     r"đơn hàng|vận chuyển|shipping|giao hàng)", MUA_SAM, "chứa khuyến mãi/đơn hàng"),
    (r"(bài tập|deadline|báo cáo|đồ án|môn học|lịch thi|lịch học|học phần|\bsrs\b|"
     r"assignment|lecture|semester)", HOC_TAP, "liên quan việc học/nhà trường"),
    (r"(kết bạn|friend request|đã (thích|bình luận|nhắc)|tagged you|mention|story|reels?)",
     MANG_XH, "hoạt động mạng xã hội"),
]

# Dấu hiệu gửi TỰ ĐỘNG (bot) — để phân biệt "người thật" với "hệ thống"
_BOT_PAT = re.compile(r"(no-?reply|do-?not-?reply|noreply|donotreply|notification|notifications|"
                      r"mailer|auto|robot|system)", re.I)


def classify(sender_email: str, sender_name: str = "",
             subject: str = "", snippet: str = "") -> Classification:
    """Đoán nhãn cho MỘT email. Ưu tiên: tên miền (high) → từ khoá (medium) →
    người-thật/mặc định (low). Luôn kèm 'reason' để người dùng hiểu vì sao."""
    email_l = (sender_email or "").lower()
    hay = f"{subject}\n{snippet}".lower()

    # 1) Tên miền — tín hiệu mạnh nhất
    for needles, cat, why in _DOMAIN_RULES:
        if any(n in email_l for n in needles):
            return Classification(cat, "high", why)

    # 2) Từ khoá tiêu đề/nội dung
    for pat, cat, why in _KEYWORD_RULES:
        if re.search(pat, hay):
            return Classification(cat, "medium", why)

    # 3) Không match: bot lạ → Hệ thống; còn lại là người THẬT → Cá nhân
    if _BOT_PAT.search(email_l) or _BOT_PAT.search((sender_name or "").lower()):
        return Classification(HE_THONG, "low", "thông báo tự động (không rõ loại cụ thể)")
    return Classification(CA_NHAN, "low", "email cá nhân từ người gửi thật")


def category_by_key(key: str) -> Category | None:
    return _BY_KEY.get(key)
