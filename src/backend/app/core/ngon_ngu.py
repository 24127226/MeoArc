# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/ngon_ngu.py — DỊCH CHỮ NGƯỜI DÙNG ĐỌC (vi/en)            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ VÌ SAO BACKEND CŨNG PHẢI DỊCH:                                     ║
# ║ Dịch mỗi frontend thì bấm "English" xong khung thành tiếng Anh,     ║
# ║ nhưng thẻ trả lời vẫn "Đây là những việc bạn đang mắc:" và nhãn     ║
# ║ vẫn "Học tập". Chữ Anh bao quanh chữ Việt LỘ HƠN HẲN so với để      ║
# ║ nguyên cả cụm tiếng Việt — dịch nửa vời làm mọi thứ tệ hơn.        ║
# ║                                                                    ║
# ║ Thiếu khoá thì trả về CHÍNH KHOÁ, không phải chuỗi rỗng: một thẻ    ║
# ║ hiện ra "the.lichtrinh.dan" là lỗi nhìn thấy ngay và sửa được, còn  ║
# ║ một thẻ trống thì trông như hệ thống hỏng.                          ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

MAC_DINH = "vi"

# khoá → {vi, en}. Đặt tên theo `khu-vuc.ten` để tìm bằng mắt được.
TU_DIEN: dict[str, dict[str, str]] = {
    # ── Nhãn phân loại (hiện trên thẻ categorize + digest) ──────────────
    "nhan.hoc_tap": {"vi": "Học tập", "en": "Study"},
    "nhan.cong_viec": {"vi": "Công việc", "en": "Work"},
    "nhan.he_thong": {"vi": "Cập nhật & Hệ thống", "en": "Updates & System"},
    "nhan.ca_nhan": {"vi": "Cá nhân", "en": "Personal"},
    "nhan.mang_xh": {"vi": "Mạng xã hội", "en": "Social"},
    "nhan.mua_sam": {"vi": "Mua sắm & Ưu đãi", "en": "Shopping & Deals"},
    "nhan.tai_chinh": {"vi": "Tài chính", "en": "Finance"},

    # ── Gợi ý hành động (hiện trên từng dòng thẻ triage) ────────────────
    "goiy.todo": {"vi": "Cần bạn xử lý", "en": "Needs your action"},
    "goiy.waiting": {"vi": "Đang chờ người khác", "en": "Waiting on someone"},
    "goiy.done": {"vi": "Đã xong — có thể lưu trữ", "en": "Done — safe to archive"},

    # ── Thẻ digest ─────────────────────────────────────────────────────
    "the.digest.dan": {
        "vi": "Đây là báo cáo nhanh hộp thư của bạn:",
        "en": "Here is a quick report on your mailbox:",
    },
    "the.digest.tieude": {"vi": "Tóm tắt hộp thư", "en": "Mailbox summary"},
    "the.digest.tong": {"vi": "Tổng thư", "en": "Total"},
    "the.digest.chuadoc": {"vi": "Chưa đọc", "en": "Unread"},
    "the.digest.canxuly": {"vi": "Cần xử lý", "en": "Needs action"},
    "pham_vi.hom_nay": {"vi": "hôm nay", "en": "today"},

    # ── Thẻ triage ─────────────────────────────────────────────────────
    "the.triage.dan": {
        "vi": "Mình đã phân loại theo độ ưu tiên kèm gợi ý hành động:",
        "en": "I sorted them by priority with a suggested action for each:",
    },
    "the.triage.tieude": {"vi": "Phân loại {n} thư cần theo dõi",
                          "en": "Triaged {n} messages to follow up"},
    "nhom.cao": {"vi": "Ưu tiên cao", "en": "High priority"},
    "nhom.thuong": {"vi": "Bình thường", "en": "Normal"},

    # ── Thẻ lịch trình ─────────────────────────────────────────────────
    "the.lich.dan_viec": {"vi": "Đây là những việc bạn đang mắc:",
                          "en": "Here is what you currently owe:"},
    "the.lich.dan_dilai": {
        "vi": "Mình rà trong hộp thư và thấy những việc phải đi xa:",
        "en": "I scanned your mailbox and found trips you need to make:",
    },
    "the.lich.tieude_viec": {"vi": "{n} việc sắp tới", "en": "{n} upcoming tasks"},
    "the.lich.tieude_dilai": {"vi": "{n} việc cần đi xa", "en": "{n} trips required"},
    "the.lich.tieude_apluc": {"vi": "Áp lực {n} ngày tới", "en": "Workload over {n} days"},
    "the.lich.khong_quatai": {"vi": "Không ngày nào quá tải.",
                              "en": "No day is overloaded."},
    "the.lich.co_quatai": {"vi": "Có {n} ngày quá tải.", "en": "{n} day(s) are overloaded."},
    "the.lich.nang_nhat": {"vi": " Nặng nhất là {ngay} với {n} việc.",
                           "en": " The heaviest is {ngay} with {n} tasks."},

    # ── Thông báo lỗi trong khung chat ─────────────────────────────────
    "loi.qua_tai": {
        "vi": "⏳ Mô hình AI của Google đang quá tải nhất thời (lỗi 503). Trợ lý đã tự "
              "thử lại qua toàn bộ các khoá dự phòng rồi mà vẫn kẹt, nên đây là phía "
              "Google đông chứ KHÔNG phải bạn hết lượt. Thử lại sau vài giây là được.",
        "en": "⏳ Google's AI model is momentarily overloaded (error 503). The assistant "
              "already retried across every fallback key and still could not get "
              "through, so this is Google being busy — NOT you running out of quota. "
              "Try again in a few seconds.",
    },
    "loi.het_quota": {
        "vi": "🚦 Gemini đã hết lượt miễn phí trên TẤT CẢ các khoá đã cấu hình. Chờ ít "
              "phút rồi thử lại, hoặc thêm khoá từ một project khác.",
        "en": "🚦 Gemini has run out of free quota on ALL configured keys. Wait a few "
              "minutes and try again, or add a key from a different project.",
    },
    "loi.model_go": {
        "vi": "🚫 Model AI đang cấu hình đã bị Google gỡ (404), không phải bạn hết lượt.",
        "en": "🚫 The configured AI model was retired by Google (404) — this is not a "
              "quota problem.",
    },
    "loi.chung": {
        "vi": "Xin lỗi, agent đang gặp trục trặc: {chi_tiet}",
        "en": "Sorry, the assistant hit a problem: {chi_tiet}",
    },
}


def dich(khoa: str, ngon: str | None = None, **thay_the: object) -> str:
    """Lấy chuỗi theo ngôn ngữ. Thiếu khoá → trả về chính khoá (xem đầu file).

    `**thay_the` điền vào các chỗ `{ten}` trong chuỗi. Điền hỏng (thiếu khoá, sai tên)
    thì trả về chuỗi CHƯA điền chứ không ném lỗi: một dòng dẫn hiện ra dấu ngoặc nhọn
    là xấu, nhưng một ngoại lệ ở đây làm hỏng cả lượt chat — đắt hơn nhiều.
    """
    ng = ngon if ngon in ("vi", "en") else MAC_DINH
    mau = TU_DIEN.get(khoa, {}).get(ng)
    if mau is None:
        return khoa
    if not thay_the:
        return mau
    try:
        return mau.format(**thay_the)
    except Exception:
        return mau


# ── ÁNH XẠ NGƯỢC: chuỗi tiếng Việt CHUẨN → khoá ──────────────────────────────
# `labeling.Category.label` và `_GOI_Y_HANH_DONG` giữ nguyên giá trị tiếng Việt làm
# GIÁ TRỊ CHUẨN, vì chúng đã được test khẳng định và được so khớp ở nhiều chỗ. Đổi
# chúng thành khoá là sửa một thứ đang chạy đúng để phục vụ một thứ khác — đúng loại
# thay đổi hay sinh lỗi nhất.
#
# Nên dịch ở ĐIỂM XUẤT RA: giá trị chuẩn đi hết đường xử lý, tới lúc đóng gói cho
# người dùng mới đổi sang ngôn ngữ của họ.
_NGUOC = {
    "Học tập": "nhan.hoc_tap",
    "Công việc": "nhan.cong_viec",
    "Cập nhật & Hệ thống": "nhan.he_thong",
    "Cá nhân": "nhan.ca_nhan",
    "Mạng xã hội": "nhan.mang_xh",
    "Mua sắm & Ưu đãi": "nhan.mua_sam",
    "Tài chính": "nhan.tai_chinh",
    "Cần bạn xử lý": "goiy.todo",
    "Đang chờ người khác": "goiy.waiting",
    "Đã xong — có thể lưu trữ": "goiy.done",
    "Ưu tiên cao": "nhom.cao",
    "Bình thường": "nhom.thuong",
}


def dich_gia_tri(gia_tri: str, ngon: str | None = None) -> str:
    """Dịch một chuỗi tiếng Việt CHUẨN sang ngôn ngữ người dùng.

    Không nằm trong bảng thì trả về nguyên xi — dữ liệu thật (tên người gửi, tiêu đề
    thư) đi qua đây phải giữ nguyên. Dịch tiêu đề thư là bịa dữ liệu: người dùng đối
    chiếu với Gmail sẽ thấy hai thứ khác nhau và không biết cái nào thật.
    """
    if not gia_tri or (ngon or MAC_DINH) == "vi":
        return gia_tri
    khoa = _NGUOC.get(gia_tri)
    return dich(khoa, ngon) if khoa else gia_tri
