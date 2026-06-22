# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/email_service.py — LOGIC lấy email (Nấc 2)            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: trả về danh sách email. Nấc này dùng DỮ LIỆU GIẢ.         ║
# ║ TƯƠNG LAI: thay ruột hàm list_emails() bằng lời gọi Gmail API —     ║
# ║ route ở app/api KHÔNG cần đổi gì (đó là lợi ích của việc tách lớp). ║
# ╚══════════════════════════════════════════════════════════════════╝

from app.schemas.email import Email, Attachment

# Vài email giả, lấy cảm hứng từ dữ liệu mock của Frontend cho dễ đối chiếu.
# Mỗi Email(...) dưới đây sẽ được Pydantic KIỂM TRA đúng kiểu khi tạo.
_FAKE_EMAILS: list[Email] = [
    Email(
        id="1",
        sender="Giáo vụ HCMUS",
        senderEmail="giaovu@fit.hcmus.edu.vn",
        senderInitial="G",
        to="Anh Quân <quanpta.meoarc@gmail.com>",
        subject="Nhắc nộp báo cáo SRS — Nhóm 7",
        preview="Các nhóm vui lòng nộp bản SRS hoàn chỉnh trước 23:59 thứ Sáu...",
        body=[
            "Chào các em,",
            "Các nhóm vui lòng nộp bản SRS hoàn chỉnh trước 23:59 thứ Sáu tuần này.",
        ],
        time="08:42",
        date="Hôm nay, 08:42",
        unread=True,
        starred=True,
        category="moss",
        label="Học tập",
        priority="action",
        tldr="Hạn nộp SRS: 23:59 thứ Sáu.",
        attachments=[Attachment(name="Mau_SRS_Intro2SE.docx", size="248 KB")],
        folder="inbox",
    ),
    Email(
        id="2",
        sender="GitHub",
        senderEmail="notifications@github.com",
        senderInitial="G",
        to="Anh Quân <quanpta.meoarc@gmail.com>",
        subject="[meoarc-frontend] PR #12 đã được review",
        preview="quanpta đã yêu cầu thay đổi trên pull request...",
        body=["quanpta đã review pull request #12.", "Trạng thái: Changes requested."],
        time="08:10",
        date="Hôm nay, 08:10",
        unread=True,
        starred=False,
        category="sea",
        label="Dev",
        priority="action",
        tldr="PR #12 bị Changes requested.",
        folder="inbox",
    ),
    Email(
        id="6",
        sender="Newsletter UX",
        senderEmail="hello@uxweekly.com",
        senderInitial="N",
        to="Anh Quân <quanpta.meoarc@gmail.com>",
        subject='Xu hướng thiết kế "quiet luxury" 2026',
        preview="Tuần này: bảng màu ấm, typography serif...",
        body=["Chào bạn,", "Số tuần này nói về thẩm mỹ quiet luxury."],
        time="T3",
        date="Thứ 3, 09:15",
        unread=False,
        starred=False,
        category="terra",
        label="Bản tin",
        priority="fyi",
        tldr="Bản tin UX tuần này.",
        folder="inbox",
    ),
]


def list_emails(folder: str = "inbox") -> list[Email]:
    """Trả các email thuộc một thư mục. (Giả lập GET /emails của contract.)"""
    # `e.folder or "inbox"`: nếu folder trống thì coi như inbox (đúng quy ước FE).
    return [e for e in _FAKE_EMAILS if (e.folder or "inbox") == folder]
