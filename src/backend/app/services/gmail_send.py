# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/gmail_send.py — GỬI & TRẢ LỜI thư thật (Nấc 6b)       ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: dựng một bức thư đúng chuẩn rồi nhờ Gmail GỬI đi.        ║
# ║ KHÁI NIỆM: thư email không phải JSON — nó là văn bản theo chuẩn    ║
# ║   MIME/RFC 2822 (các dòng "To:", "Subject:"... rồi tới thân thư).  ║
# ║   Gmail API yêu cầu ta gói nguyên bức thư đó thành base64url rồi   ║
# ║   gửi trong field "raw". Lớp `email.message.EmailMessage` của      ║
# ║   Python lo phần dựng chuẩn MIME giúp ta (khỏi tự nối chuỗi tay).  ║
# ║ Cần quyền gmail.send (đã thêm ở auth_service).                    ║
# ╚══════════════════════════════════════════════════════════════════╝

import base64
from email.message import EmailMessage
import httpx
from app.services import gmail_service
from app.services.gmail_actions import GmailPermissionError  # tái dùng lỗi 403 cho nhất quán

GMAIL_SEND = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
# Lấy header của thư GỐC (khi trả lời) — chỉ cần vài header, nên format=metadata cho nhẹ.
GMAIL_GET = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}"


def _build_raw(
    to: str,
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    extra_headers: dict[str, str] | None = None,
    attachments: list[dict] | None = None,
) -> str:
    """Dựng bức thư MIME rồi mã hoá base64url (đúng thứ Gmail field "raw" cần).

    VÌ SAO base64url (không phải base64 thường): thư có thể chứa ký tự đặc biệt /
    xuống dòng; mã hoá để truyền an toàn qua JSON. 'url-safe' để '+' '/' không phá URL.

    attachments: danh sách {name, content(bytes), mime}. Khi có, EmailMessage tự chuyển
    bức thư thành 'multipart/mixed' (1 phần chữ + mỗi tệp 1 phần) đúng chuẩn.
    """
    msg = EmailMessage()
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)        # nhiều người Cc → nối bằng dấu phẩy theo chuẩn
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    # extra_headers: dùng cho TRẢ LỜI (In-Reply-To / References) để Gmail gom đúng luồng.
    for k, v in (extra_headers or {}).items():
        msg[k] = v
    msg.set_content(body)                # thân thư dạng text thuần (phần "chữ" của email)

    for att in attachments or []:
        # mime kiểu "image/png" → tách thành maintype="image", subtype="png".
        # Thiếu/sai → mặc định application/octet-stream (kiểu "tệp nhị phân chung chung").
        maintype, _, subtype = (att.get("mime") or "application/octet-stream").partition("/")
        msg.add_attachment(
            att["content"],
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=att["name"],
        )
    # as_bytes() = toàn bộ bức thư (header + thân + tệp) dưới dạng bytes → base64url → chuỗi.
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def _post_send(access_token: str, raw: str, thread_id: str | None = None) -> dict:
    """Gọi Gmail API gửi bức thư đã dựng (dùng chung cho gửi mới lẫn trả lời)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    payload: dict = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id  # gắn vào ĐÚNG luồng hội thoại (khi trả lời)
    with httpx.Client(timeout=15) as client:
        r = client.post(GMAIL_SEND, headers=headers, json=payload)
        if r.status_code == 403:         # token thiếu quyền gmail.send → báo rõ lên trên
            raise GmailPermissionError()
        r.raise_for_status()             # các lỗi khác (4xx/5xx) → ném để API trả 500/khác
        gmail_service.invalidate_cache(access_token)  # vừa gửi → thư mục Sent đổi, dọn cache
        return r.json()                  # { id, threadId, labelIds } của thư vừa gửi


def send_email(
    access_token: str,
    to: str,
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[dict] | None = None,
) -> dict:
    """GỬI một thư MỚI (kèm tệp nếu có). Trả dict Gmail ({id, threadId,...}) để FE biết đã gửi."""
    raw = _build_raw(to, subject, body, cc=cc, bcc=bcc, attachments=attachments)
    return _post_send(access_token, raw)


def reply_email(access_token: str, msg_id: str, body: str) -> dict:
    """TRẢ LỜI thư có id=msg_id: tự điền người nhận = người gửi gốc, tiêu đề "Re: …",
    và gắn các header In-Reply-To/References + threadId để Gmail XẾP vào đúng luồng."""
    headers = {"Authorization": f"Bearer {access_token}"}
    # B1: đọc vài header của thư GỐC để biết gửi cho ai, tiêu đề gì, thuộc luồng nào.
    with httpx.Client(timeout=15) as client:
        r = client.get(
            GMAIL_GET.format(id=msg_id),
            headers=headers,
            params={"format": "metadata",
                    "metadataHeaders": ["From", "Subject", "Message-ID", "References"]},
        )
        if r.status_code == 403:
            raise GmailPermissionError()
        r.raise_for_status()
        original = r.json()

    def _h(name: str) -> str:  # lấy 1 header theo tên (không phân biệt hoa thường)
        for h in original.get("payload", {}).get("headers", []):
            if h.get("name", "").lower() == name.lower():
                return h.get("value", "")
        return ""

    from_addr = _h("From")                 # trả lời thì gửi NGƯỢC về người gửi gốc
    subject = _h("Subject")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"          # thêm tiền tố Re: nếu chưa có
    msg_ref = _h("Message-ID")             # mã định danh thư gốc → để Gmail nối luồng
    references = (_h("References") + " " + msg_ref).strip()  # chuỗi nối các thư trong luồng

    raw = _build_raw(
        to=from_addr, subject=subject, body=body,
        extra_headers={"In-Reply-To": msg_ref, "References": references},
    )
    # threadId của thư gốc → bảo Gmail xếp thư trả lời vào CÙNG hội thoại.
    return _post_send(access_token, raw, thread_id=original.get("threadId"))
