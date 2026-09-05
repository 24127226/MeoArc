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


# ── TAXONOMY (8 nhãn ↔ 8 màu FE) ─────────────────────────────────────
HOC_TAP   = Category("hoc_tap",  "Học tập",            "moss",   "trường/phòng ban/giáo vụ/LMS/lớp học")
CONG_VIEC = Category("cong_viec","Công việc",          "sea",    "tuyển dụng/thực tập/công ty/dev/dự án")
HE_THONG  = Category("he_thong", "Cập nhật & Hệ thống","sun",    "thông báo tự động/bảo mật/OTP/no-reply")
CA_NHAN   = Category("ca_nhan",  "Cá nhân",            "cherry", "người thật gửi/bạn bè/gia đình")
MANG_XH   = Category("mang_xh",  "Mạng xã hội",        "sky",    "Facebook/Instagram/TikTok/X/LinkedIn/YouTube")
MUA_SAM   = Category("mua_sam",  "Mua sắm & Ưu đãi",   "terra",  "Shopee/Lazada/Tiki/khuyến mãi/voucher/bản tin")
TAI_CHINH = Category("tai_chinh","Tài chính",          "wine",   "ngân hàng/ví điện tử/hoá đơn/thanh toán")
# Đi lại — thêm sau khi ĐO: vé máy bay và xác nhận đặt phòng không có chỗ nào để về,
# nên chúng rơi vào "Cá nhân/low". Bảy nhãn kia không nhãn nào nhận chúng mà không
# sai nghĩa: một chuyến bay không phải mua sắm, và biên lai chỉ là mặt phụ của nó.
DI_LAI    = Category("di_lai",   "Đi lại",             "jade",   "vé máy bay/khách sạn/đặt chỗ/lịch trình đi lại")

ALL_CATEGORIES = [HOC_TAP, CONG_VIEC, HE_THONG, CA_NHAN, MANG_XH, MUA_SAM, TAI_CHINH, DI_LAI]
_BY_KEY = {c.key: c for c in ALL_CATEGORIES}
_BY_LABEL = {c.label.lower(): c for c in ALL_CATEGORIES}


def tu_ten_nhan(ten: str) -> Category | None:
    """Tên nhãn NGƯỜI DÙNG đã đặt → Category. Không khớp thì None.

    ── VÌ SAO CẦN, VÀ VÌ SAO PHẢI DÙNG CHUNG ──
    Nhãn người dùng đặt phải THẮNG `classify()`. Nếu không thì thao tác gắn nhãn được
    GHI xuống nhà cung cấp rồi KHÔNG BAO GIỜ được đọc lại — nhìn từ ngoài đúng như
    "app quên thao tác trước đó".
    Cả Gmail (nhãn) lẫn Outlook (categories) đều cần luật này. Viết hai bản thì chúng
    sẽ lệch nhau, và lệch ở tầng này rất khó thấy: mỗi nhà cung cấp chỉ sai khi có
    người dùng thật đăng nhập bằng đúng loại tài khoản đó.

    So khớp KHÔNG phân biệt hoa/thường và bỏ khoảng trắng thừa: nhà cung cấp giữ
    nguyên cách người dùng gõ, khớp chặt thì gắn nhãn xong vẫn không nhận ra."""
    return _BY_LABEL.get((ten or "").strip().lower())


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
    # Mảnh có `@` là CỐ Ý neo vào tên người gửi (giaovu@hcmus.edu.vn); mảnh không có
    # `@` chỉ so tên miền. Xem `_khop_dia_chi`.
    (["edu.vn", ".edu", "hcmus", "fit.hcmus", "vnu.edu", "student.", "elearning", "lms.",
      "moodle", "courses.", "classroom.google",
      "giaovu@", "daotao@", "phongdaotao@"],
     HOC_TAP, "gửi từ tên miền giáo dục/nhà trường"),

    # Tài chính — ngân hàng/ví/thanh toán (ĐẶT TRƯỚC mua sắm: 'bank' ưu tiên hơn 'sale')
    (["vietcombank", "techcombank", "vpbank", "acb.com", "mbbank", "bidv", "tpbank", "sacombank",
      "vietinbank", "@momo", "zalopay", "vnpay", "payoo", "shopeepay", "paypal", "stripe.com",
      "banking", "napas"],
     TAI_CHINH, "gửi từ ngân hàng/ví điện tử/cổng thanh toán"),

    # Đi lại — hãng bay, nền tảng đặt phòng/vé
    (["vietnamairlines", "vietjet", "bambooairways", "vietravel", "booking.com", "agoda",
      "airbnb", "traveloka", "expedia", "trip.com", "klook", "hotels.com", "marriott",
      "accor", "vinpearl", "mytour", "vexere", "skyscanner", "kayak.com", "tripadvisor"],
     DI_LAI, "gửi từ hãng bay/nền tảng đặt chỗ"),

    # Mạng xã hội
    (["facebookmail", "facebook.com", "instagram", "tiktok", "twitter.com", "@x.com", "notify.twitter",
      "linkedin.com", "threads.net", "youtube.com", "discord", "reddit", "pinterest", "@zalo"],
     MANG_XH, "gửi từ nền tảng mạng xã hội"),

    # Công việc/Tuyển dụng
    (["topcv", "vietnamworks", "itviec", "careerbuilder", "indeed", "glints", "ybox",
      "recruit", "talent", "jobs.", "workable", "greenhouse.io", "lever.co",
      "hr@", "tuyendung@", "recruit@", "talent@", "hiring@"],
     CONG_VIEC, "gửi từ nền tảng/bộ phận tuyển dụng"),

    # Mua sắm & Ưu đãi — sàn TMĐT + bản tin marketing
    (["shopee", "lazada", "tiki.vn", "sendo", "@grab", "shopeemail", "dienmay", "thegioididong",
      "fptshop", "amazon.", "aliexpress", "temu", "mailchimp", "sendgrid.net", "substack",
      "marketing@", "newsletter@", "promo@", "deals@"],
     MUA_SAM, "gửi từ sàn mua sắm/bản tin khuyến mãi"),

    # Cập nhật & Hệ thống — thông báo tự động, dev-ops, bảo mật
    (["github.com", "gitlab", "vercel", "netlify", "atlassian", "jira", "notion.so", "slack.com",
      "accounts.google", "no-reply@google", "security@", "microsoft", "office365",
      "cloudflare", "aws.amazon", "azure", "digitalocean", "render.com", "railway",
      "supabase", "firebase",
      "openai.com", "anthropic", "figma.com"],
     HE_THONG, "thông báo tự động từ dịch vụ/hệ thống"),
]

# ── Mảnh CHỈ dùng cho TÊN HIỂN THỊ ────────────────────────────────────────
# Thư đại học Việt Nam hiếm khi gửi từ một tên miền nhận ra được — rất nhiều thư đi
# qua hộp cá nhân của cán bộ, hoặc qua chính hộp thư của sinh viên. Thứ duy nhất còn
# lại là cách người gửi TỰ XƯNG: "Giáo vụ", "Phòng CTSV", "CLB Học thuật", "Ban tổ
# chức". Đó là cụm nhiều chữ nên không nhét vào danh sách tên miền được (tên miền
# không có dấu cách), và cũng không nên: chúng chỉ đáng tin ở tên hiển thị.
_TEN_RULES: list[tuple[list[str], Category, str]] = [
    (["giáo vụ", "giao vu", "phòng đào tạo", "phong dao tao", "phòng ctsv", "phong ctsv",
      "thư ký khoa", "thu ky khoa", "khoa cntt", "câu lạc bộ", "cau lac bo", "clb ",
      "ban tổ chức", "ban to chuc", "ban truyền thông", "học vụ", "hoc vu",
      # "GVHD" (giảng viên hướng dẫn) là cách xưng chỉ có trong thư trường lớp. Thiếu
      # nó thì thầy hướng dẫn bàn về chương khoá luận bị xếp vào "Cá nhân" — đúng là
      # người thật, nhưng thứ người dùng cần thấy là VIỆC HỌC.
      "gvhd", "giảng viên", "giang vien",
      "trường đh", "đại học", "dai hoc", "ieee", "springer", "elsevier", "acm"],
     HOC_TAP, "tên người gửi cho thấy là đơn vị trong trường/học thuật"),
    # Tên khách sạn/hãng bay hiếm khi trùng tên miền nào ta biết ("Hanoi La Siesta
    # Premium"), nên bắt bằng CHỮ trong tên: hotel/resort/homestay/airlines.
    (["airlines", "airways", "hotel", "resort", "homestay", "hostel", "villa",
      "khách sạn", "khach san", "hãng hàng không", "du lịch", "travel", "tour "],
     DI_LAI, "tên người gửi cho thấy là hãng bay/nơi lưu trú"),
]

# ── TÍN HIỆU 2: TỪ KHOÁ tiêu đề + nội dung (phụ trợ → confidence medium) ──
_KEYWORD_RULES: list[tuple[str, Category, str]] = [
    (r"(otp|mã xác (thực|minh)|verification code|one-time|security alert|"
     r"cảnh báo bảo mật|đổi mật khẩu|reset password)", HE_THONG, "chứa mã OTP/cảnh báo bảo mật"),
    # ĐẶT TRƯỚC tài chính: xác nhận đặt phòng gần như luôn nhắc chuyện đã thanh toán,
    # mà với người dùng thì đó là CHUYẾN ĐI, biên lai chỉ là mặt phụ. Các cụm ở đây rất
    # đặc thù (`mã đặt chỗ`, `nhận phòng`) nên gần như không cướp nhầm thư khác.
    (r"(mã đặt chỗ|đặt chỗ|đặt phòng|nhận phòng|trả phòng|check-?in|booking|reservation|"
     r"vé máy bay|chuyến bay|lịch bay|hãng bay|boarding|pnr|khách sạn|homestay|"
     r"flight|hotel)", DI_LAI, "nói về vé/đặt chỗ/chuyến đi"),
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


def _khop_dia_chi(needle: str, email_l: str) -> bool:
    """Mảnh chuỗi có khớp địa chỉ người gửi không — và khớp Ở ĐÂU mới tính.

    ── VÌ SAO KHÔNG DÙNG `needle in email_l` ────────────────────────────────
    Bản trước so khớp trên CẢ địa chỉ. Nghe thì rộng rãi, thực tế là một cái bẫy:
    `hcmus` viết ra để khớp `@fit.hcmus.edu.vn`, nhưng nó khớp luôn phần TÊN người
    dùng — nên `meoarc.hcmus@outlook.com.vn` bị gán Học tập với confidence "high",
    và vì luật tên miền chạy trước mọi luật từ khoá, MỌI thư từ tài khoản đó đều
    thành Học tập: xác nhận khách sạn, vé máy bay, tất cả. Đo được trên bộ 46 thư
    demo. Người dùng thấy "AI phân loại dở", nhưng AI không hề tham gia — đây là
    một phép so chuỗi con quá tay.

    Cùng cái bẫy còn nằm sẵn ở chỗ khác: `microsoft.fan@gmail.com` sẽ thành Hệ
    thống, `amazon.deals.vn@gmail.com` thành Mua sắm.

    ── LUẬT MỚI ────────────────────────────────────────────────────────────
    • Mảnh có chứa `@` (`hr@`, `@momo`, `no-reply@google`) → người viết đã CỐ Ý neo
      qua ranh giới địa chỉ, nên so trên cả địa chỉ, đúng như ý họ.
    • Mảnh không có `@` → chỉ so phần TÊN MIỀN (sau dấu `@` cuối). Đó là điều những
      mảnh này vốn muốn nói, chỉ là trước đây không nói được ra.
    """
    if "@" in needle:
        return needle in email_l
    domain = email_l.rsplit("@", 1)[-1] if "@" in email_l else email_l
    return needle in domain


# Tên hiển thị không có đuôi tên miền: người ta ký "GitHub", không ký "github.com".
# Nên so bằng NHÃN ĐẦU của mảnh (`linkedin.com` → `linkedin`, `@momo` → `momo`).
_DAI_TOI_THIEU_TEN = 4


def _khop_ten(needle: str, ten_l: str) -> bool:
    """Mảnh có khớp TÊN HIỂN THỊ người gửi không.

    Chặn dưới 4 ký tự: `edu`, `lms`, `hr` quá ngắn nên khớp bừa vào giữa từ khác —
    `edu` sẽ nuốt "EduMax Academy" (một thư quảng cáo) thành thư nhà trường. Mảnh
    ngắn chỉ đáng tin khi nằm trong TÊN MIỀN, nơi chúng có ranh giới thật.
    """
    goc = needle.strip("@").split(".")[0]
    return len(goc) >= _DAI_TOI_THIEU_TEN and goc in ten_l


def classify(sender_email: str, sender_name: str = "",
             subject: str = "", snippet: str = "") -> Classification:
    """Đoán nhãn cho MỘT email. Ưu tiên: tên miền (high) → từ khoá (medium) →
    người-thật/mặc định (low). Luôn kèm 'reason' để người dùng hiểu vì sao."""
    email_l = (sender_email or "").lower()
    hay = f"{subject}\n{snippet}".lower()

    # 1) Tên miền — tín hiệu mạnh nhất
    for needles, cat, why in _DOMAIN_RULES:
        if any(_khop_dia_chi(n, email_l) for n in needles):
            return Classification(cat, "high", why)

    # 2) TÊN HIỂN THỊ người gửi — thường mang nhiều thông tin hơn cả địa chỉ.
    #
    # Đo trên bộ 46 thư demo: 28 thư (61%) rơi vào "Cá nhân / low" chỉ vì thư được
    # TỰ GỬI CHO CHÍNH MÌNH, nên địa chỉ luôn giống nhau và không nói lên điều gì.
    # Toàn bộ thông tin nằm ở tên hiển thị — "Giáo vụ HCMUS", "GitHub", "LinkedIn",
    # "Vietnam Airlines" — mà trước đây tên chỉ được dùng để dò xem có phải bot không.
    #
    # Không riêng bản demo: bản tin thật cũng ký tên "Shopee", thông báo CI ký tên
    # "GitHub". Bỏ qua tên là bỏ qua thứ người dùng NHÌN THẤY đầu tiên trên mỗi thẻ thư.
    #
    # "medium" chứ không "high": tên hiển thị ai đặt cũng được, không như tên miền đã
    # qua xác thực. Đặt TRƯỚC luật từ khoá vì "ai gửi" nói đúng hơn "trong thư có chữ
    # gì" — một thư của giáo vụ vẫn là việc học kể cả khi nó nhắc chuyện đóng tiền.
    ten_l = (sender_name or "").lower()
    if ten_l:
        for needles, cat, why in _TEN_RULES:
            if any(n.strip("\b") in ten_l for n in needles):
                return Classification(cat, "medium", why)
        for needles, cat, why in _DOMAIN_RULES:
            if any(_khop_ten(n, ten_l) for n in needles):
                # `removeprefix` chứ không cắt theo chỉ số: đếm tay một tiền tố có dấu
                # thì lệch một ký tự là ra "cho thấy ãng bay" — đã dính đúng vậy.
                return Classification(
                    cat, "medium",
                    "tên người gửi cho thấy " + why.removeprefix("gửi từ ")
                    if why.startswith("gửi từ ") else why,
                )

    # 3) Từ khoá tiêu đề/nội dung
    for pat, cat, why in _KEYWORD_RULES:
        if re.search(pat, hay):
            return Classification(cat, "medium", why)

    # 3) Không match: bot lạ → Hệ thống; còn lại là người THẬT → Cá nhân
    if _BOT_PAT.search(email_l) or _BOT_PAT.search((sender_name or "").lower()):
        return Classification(HE_THONG, "low", "thông báo tự động (không rõ loại cụ thể)")
    return Classification(CA_NHAN, "low", "email cá nhân từ người gửi thật")


def category_by_key(key: str) -> Category | None:
    return _BY_KEY.get(key)


# ╔══════════════════════════════════════════════════════════════════╗
# ║ TRỤC THỨ HAI & BA: ĐỘ ƯU TIÊN và TRẠNG THÁI VIỆC (PA1 §4.2.9)     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đặc tả chia nhãn AI thành BA trục độc lập:                        ║
# ║   • Category  — LUÔN gán, đúng 1 trong 7 giá trị (ở trên)         ║
# ║   • Priority  — High / Medium / Low                               ║
# ║   • Status    — Todo / Waiting / Done                             ║
# ║ Hai trục sau CHỈ gán cho thư "mang tính công việc" (task-like);   ║
# ║ thư còn lại phải để NULL, không được nhét giá trị mặc định.       ║
# ║                                                                    ║
# ║ Vì sao null quan trọng: "Low/Done" nghĩa là ĐÃ XÉT rồi kết luận    ║
# ║ việc này nhẹ; null nghĩa là KHÔNG PHẢI việc. Nhét mặc định vào là  ║
# ║ đổ 300 bản tin quảng cáo vào danh sách việc của người dùng.        ║
# ╚══════════════════════════════════════════════════════════════════╝

import unicodedata
from enum import Enum


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(str, Enum):
    TODO = "Todo"
    WAITING = "Waiting"
    DONE = "Done"


# Nhóm gần như không bao giờ sinh việc cho người dùng.
_KHONG_PHAI_VIEC = {MANG_XH.key, MUA_SAM.key}

def _bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt trước khi so khớp. Tiêu đề thư rất hay được gõ không dấu
    ("nhac nop bao cao"), nên các mẫu bên dưới viết KHÔNG DẤU và mọi văn bản đều
    được đưa về không dấu — nhờ vậy bắt được cả hai lối viết bằng một bộ mẫu."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


# Các mẫu dưới đây viết KHÔNG DẤU — xem _bo_dau() ở trên.
# Thư đòi NGƯỜI DÙNG làm gì đó → Todo.
_PAT_CAN_LAM = re.compile(
    r"(deadline|han nop|han chot|due|vui long|yeu cau|phan hoi|reply|"
    r"xac nhan|confirm|nop bai|nop bao cao|nop ban|gui lai|thanh toan|"
    r"action required|phong van|interview|moi hop|meeting|duyet|approve)", re.I)

# Thư báo "bóng đang ở sân người khác" → Waiting.
_PAT_DANG_CHO = re.compile(
    r"(dang cho|cho phan hoi|cho duyet|da gui|dang xu ly|pending|waiting|"
    r"in review|dang xem xet|se phan hoi|we will get back)", re.I)

# Thư báo việc đã xong → Done.
_PAT_XONG = re.compile(
    r"(da hoan tat|hoan thanh|thanh cong|da duyet|approved|completed|"
    r"da thanh toan|da nhan|receipt|merged|da xac nhan)", re.I)

# Dấu hiệu GẤP → đẩy Priority lên High.
_PAT_GAP = re.compile(
    r"(gap|khan|urgent|asap|hom nay|ngay mai|deadline|han chot|"
    r"immediately|canh bao|security alert|qua han|overdue)", re.I)

@dataclass(frozen=True)
class AiLabels:
    """Kết quả một lượt phân tích — ĐỦ CẢ BA trục, gắn vào thư trong CÙNG một thao tác."""
    category: Category
    priority: Priority | None
    status: TaskStatus | None
    task_like: bool
    confidence: str
    reason: str


def analyze(sender_email: str, sender_name: str = "",
            subject: str = "", snippet: str = "") -> AiLabels:
    """Phân tích một thư ra ĐỦ ba nhãn AI (PA1 §4.2.9).

    Trả về một khối duy nhất chứ không phải ba lời gọi riêng: ba trục này là kết quả
    của MỘT lượt suy luận, tách ra gọi lẻ là mở đường cho trạng thái nửa vời — thư có
    Priority mà không có Status, hoặc ngược lại.
    """
    c = classify(sender_email, sender_name, subject, snippet)
    hay = _bo_dau(f"{subject}\n{snippet}")

    # Nhóm mạng xã hội / mua sắm: không phải việc, kể cả khi có chữ "vui lòng".
    if c.category.key in _KHONG_PHAI_VIEC:
        return AiLabels(c.category, None, None, False, c.confidence, c.reason)

    if _PAT_XONG.search(hay):
        status = TaskStatus.DONE
    elif _PAT_DANG_CHO.search(hay):
        status = TaskStatus.WAITING
    elif _PAT_CAN_LAM.search(hay):
        status = TaskStatus.TODO
    else:
        # Không có dấu hiệu nào → không phải việc. Hai trục kia để NULL.
        return AiLabels(c.category, None, None, False, c.confidence, c.reason)

    if _PAT_GAP.search(hay):
        priority = Priority.HIGH
    elif status is TaskStatus.DONE:
        priority = Priority.LOW          # đã xong thì không còn giành sự chú ý
    else:
        priority = Priority.MEDIUM

    return AiLabels(c.category, priority, status, True, c.confidence, c.reason)
