# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/gmail_service.py — ĐỌC GMAIL THẬT (tầng services/)   ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Dùng access_token của user (lưu ở phiên) gọi Gmail API, rồi DỊCH   ║
# ║ mỗi thư Gmail sang khuôn `Email` mà Frontend hiểu.                 ║
# ╚══════════════════════════════════════════════════════════════════╝

import base64
import re
import time
from email.utils import parseaddr, parsedate_to_datetime
import httpx
from app.schemas.email import Email

GMAIL_LIST = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
GMAIL_MSG = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}"

# Gmail không có "category màu" như FE → mình gán tạm 1 màu theo id cho danh sách
# đỡ đơn điệu. (Phân loại thông minh là việc của AI — UC009, để sau.)
_CATS = ["moss", "sea", "sun", "cherry", "sky", "terra", "wine"]


# ── CACHE đơn giản trong bộ nhớ (giảm số lần gọi Gmail) ──────────────────
# Ý tưởng: lưu kết quả kèm MỐC thời gian. Vào lại cùng "khoá" (người + thư mục
# + từ khoá) trong vòng _CACHE_TTL giây → trả lại bản cũ, KHỎI gọi Gmail.
# Đánh đổi: dữ liệu có thể "cũ" tối đa _CACHE_TTL giây (chấp nhận được với email).
# (Dự án thật nên dùng Redis; ở đây dùng dict trong RAM là đủ để học.)
_CACHE_TTL = 60  # giây
_CACHE: dict[tuple, tuple[float, object]] = {}


def _cache_get(key: tuple):
    hit = _CACHE.get(key)
    if hit and (time.time() - hit[0]) < _CACHE_TTL:
        return hit[1]   # còn hạn → dùng lại
    return None         # chưa có, hoặc đã quá hạn


def _cache_set(key: tuple, value) -> None:
    _CACHE[key] = (time.time(), value)  # lưu kèm thời điểm để biết khi nào hết hạn


def _header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _to_email(msg: dict, folder: str = "inbox") -> Email:
    name, addr = parseaddr(_header(msg, "From"))  # tách "Tên <email>" → (tên, email)
    sender = name or addr or "(không tên)"
    raw_date = _header(msg, "Date")
    time_s = date_s = raw_date
    try:
        dt = parsedate_to_datetime(raw_date)
        time_s = dt.strftime("%H:%M")
        date_s = dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    labels = msg.get("labelIds", [])
    snippet = msg.get("snippet", "")
    cat = _CATS[sum(ord(c) for c in msg["id"]) % len(_CATS)]
    return Email(
        id=msg["id"],
        sender=sender,
        senderEmail=addr,
        senderInitial=(sender[:1].upper() or "?"),
        to="",                      # danh sách chưa cần người nhận
        subject=_header(msg, "Subject") or "(không tiêu đề)",
        preview=snippet,
        body=[snippet],             # nấc này chỉ lấy snippet; body đầy đủ để sau
        time=time_s,
        date=date_s,
        unread=("UNREAD" in labels),
        starred=("STARRED" in labels),
        category=cat,               # type: ignore[arg-type]  (cat luôn là 1 trong 7 key hợp lệ)
        folder=folder,              # type: ignore[arg-type]  (gắn đúng thư mục đang xem)
    )


# Ánh xạ "thư mục" của app → "nhãn hệ thống" của Gmail.
_FOLDER_LABEL = {
    "inbox": "INBOX",
    "sent": "SENT",
    "drafts": "DRAFT",
    "trash": "TRASH",
    "starred": "STARRED",
}
# Các giá trị folder hợp lệ để gắn vào Email (khớp kiểu Folder bên schema).
# 'starred' KHÔNG nằm đây (nó là cờ, không phải thư mục) → gắn tạm 'inbox'.
_VALID_TAGS = {"inbox", "sent", "drafts", "archive", "trash"}


def list_messages(
    access_token: str, folder: str = "inbox", q: str | None = None, max_results: int = 30
) -> list[Email]:
    """Lấy danh sách thư theo THƯ MỤC (hoặc theo từ khoá tìm kiếm) rồi dịch sang Email.
    Ánh xạ thư mục → Gmail:
      • inbox/sent/drafts/trash/starred → nhãn INBOX/SENT/DRAFT/TRASH/STARRED
      • archive → thư KHÔNG còn trong inbox/trash/spam (Gmail không có nhãn 'archive')
      • có `q`  → TÌM KIẾM toàn hộp thư (vd "from:github", "has:attachment")
    """
    # CACHE: cùng (người + thư mục + từ khoá) đã lấy trong TTL → trả lại luôn, KHỎI gọi Gmail.
    cache_key = ("list", access_token, folder, q or "")
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict = {"maxResults": max_results}
    if q:
        params["q"] = q
    elif folder == "archive":
        params["q"] = "-in:inbox -in:trash -in:spam"
    else:
        params["labelIds"] = _FOLDER_LABEL.get(folder, "INBOX")
        # Mặc định Gmail KHÔNG trả thùng rác/spam → phải bật cờ này cho thùng rác.
        if params["labelIds"] == "TRASH":
            params["includeSpamTrash"] = "true"

    tag = folder if folder in _VALID_TAGS else "inbox"  # nhãn folder gắn vào mỗi Email

    with httpx.Client(timeout=15) as client:
        # B1: lấy DANH SÁCH id thư (Gmail chỉ trả id, chưa có nội dung).
        listing = client.get(GMAIL_LIST, headers=headers, params=params)
        listing.raise_for_status()
        ids = [m["id"] for m in listing.json().get("messages", [])]

        # B2: với mỗi id, lấy METADATA (From/Subject/Date + nhãn + snippet).
        emails: list[Email] = []
        for mid in ids:
            r = client.get(
                GMAIL_MSG.format(id=mid), headers=headers,
                params={"format": "metadata",
                        "metadataHeaders": ["From", "Subject", "Date"]},
            )
            if r.status_code == 200:
                emails.append(_to_email(r.json(), tag))
        _cache_set(cache_key, emails)  # lưu lại để lần sau (trong TTL) khỏi gọi Gmail
        return emails


# ── Lấy chi tiết 1 thư (thân thư đầy đủ + đính kèm) — UC004 ───────────

def _decode_b64url(data: str) -> str:
    """Gmail cất thân thư dưới dạng base64 (kiểu URL-safe). Giải mã về chữ thường."""
    if not data:
        return ""
    pad = "=" * (-len(data) % 4)  # thêm cho đủ bội số 4 ký tự (yêu cầu của base64)
    try:
        return base64.urlsafe_b64decode(data + pad).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    """Nếu thư chỉ có bản HTML → bỏ thẻ <...> cho ra chữ đọc được (cách thô)."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text)


def _human_size(num: int) -> str:
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num // 1024} KB"
    return f"{num / 1024 / 1024:.1f} MB"


def _extract_body(payload: dict) -> tuple[str, list[dict]]:
    """Thư Gmail gồm nhiều 'mảnh' (parts) lồng nhau. Đi đệ quy qua từng mảnh để:
    lấy phần chữ (ưu tiên text/plain) và gom danh sách tệp đính kèm."""
    plain, html, attachments = "", "", []

    def walk(part: dict) -> None:
        nonlocal plain, html
        filename = part.get("filename", "")
        body = part.get("body", {})
        mime = part.get("mimeType", "")
        if filename:  # mảnh có tên tệp = đính kèm
            attachments.append({"name": filename, "size": _human_size(body.get("size", 0))})
        elif mime == "text/plain" and not plain:
            plain = _decode_b64url(body.get("data", ""))
        elif mime == "text/html" and not html:
            html = _decode_b64url(body.get("data", ""))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return (plain or _strip_html(html)), attachments


def get_message(access_token: str, msg_id: str) -> Email:
    """Lấy 1 thư ĐẦY ĐỦ (thân thư + đính kèm) — dùng khi mở chi tiết."""
    # CACHE: mở lại đúng thư này trong TTL → trả bản cũ, khỏi tải lại từ Gmail.
    cache_key = ("msg", access_token, msg_id)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(timeout=15) as client:
        r = client.get(GMAIL_MSG.format(id=msg_id), headers=headers, params={"format": "full"})
        r.raise_for_status()
        msg = r.json()

    text, attachments = _extract_body(msg.get("payload", {}))
    # Tách thành các đoạn (ngăn bởi dòng trống) cho FE hiển thị từng <p>.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()] or [msg.get("snippet", "")]
    name, addr = parseaddr(_header(msg, "From"))
    sender = name or addr or "(không tên)"
    raw_date = _header(msg, "Date")
    date_s = raw_date
    try:
        date_s = parsedate_to_datetime(raw_date).strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    labels = msg.get("labelIds", [])
    email = Email(
        id=msg["id"],
        sender=sender,
        senderEmail=addr,
        senderInitial=(sender[:1].upper() or "?"),
        to=_header(msg, "To"),
        subject=_header(msg, "Subject") or "(không tiêu đề)",
        preview=msg.get("snippet", ""),
        body=paragraphs,
        time=date_s,
        date=date_s,
        unread=("UNREAD" in labels),
        starred=("STARRED" in labels),
        category=_CATS[sum(ord(c) for c in msg["id"]) % len(_CATS)],  # type: ignore[arg-type]
        attachments=([{"name": a["name"], "size": a["size"]} for a in attachments] or None),  # type: ignore[arg-type]
        folder="inbox",
    )
    _cache_set(cache_key, email)
    return email
