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
# Tải nội dung 1 tệp đính kèm (Gmail tách riêng phần bytes nặng ra endpoint này).
GMAIL_ATTACH = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/attachments/{aid}"

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


def invalidate_cache(access_token: str) -> None:
    """Xoá MỌI mục cache thuộc về 1 người (nhận diện qua access_token).

    VAI TRÒ: gọi NGAY SAU khi GHI vào Gmail (đánh dấu đọc/gắn sao/lưu trữ/xoá).
    VÌ SAO BẮT BUỘC: cache giữ lại kết quả đọc cũ tới 60s. Nếu vừa "lưu trữ" 1 thư
    mà không dọn cache, lần mở lại hộp thư đến trong 60s sẽ vẫn THẤY thư đó (đọc từ
    cache) → người dùng tưởng hành động thất bại. Dọn cache ép lần đọc kế tiếp phải
    hỏi lại Gmail để lấy trạng thái MỚI nhất.
    """
    # Mọi khoá cache đều có dạng tuple ("list"/"msg", access_token, ...) → phần tử [1]
    # chính là access_token. Lọc ra những khoá của đúng người này rồi xoá.
    stale = [k for k in _CACHE if len(k) > 1 and k[1] == access_token]
    for k in stale:
        _CACHE.pop(k, None)


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
    access_token: str,
    folder: str = "inbox",
    q: str | None = None,
    unread: bool | None = None,
    starred: bool | None = None,
    attachment: bool | None = None,
    page_token: str | None = None,
    max_results: int = 30,
    bypass_cache: bool = False,
) -> tuple[list[Email], str | None]:
    """Lấy danh sách thư theo THƯ MỤC + LỌC + PHÂN TRANG, dịch sang Email.
    Trả về (danh_sách_Email, cursor_trang_kế) — cursor None nghĩa là hết thư.

    Ánh xạ thư mục → Gmail (inbox/sent/drafts/trash/starred → nhãn hệ thống; archive →
    thư ngoài inbox/trash/spam). Bộ lọc nhanh → toán tử Gmail: is:unread / is:starred /
    has:attachment (ghép được với cả thư mục lẫn từ khoá). Phân trang dùng pageToken.
    """
    # CACHE: khoá gồm ĐỦ tiêu chí (kể cả lọc + trang) để không trả nhầm kết quả cũ.
    cache_key = ("list", access_token, folder, q or "",
                 bool(unread), bool(starred), bool(attachment), page_token or "")
    # bypass_cache=True (nút "Làm mới") → KHÔNG đọc cache, ép hỏi Gmail lấy bản mới nhất.
    if not bypass_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    headers = {"Authorization": f"Bearer {access_token}"}
    params: dict = {"maxResults": max_results}
    if page_token:
        params["pageToken"] = page_token

    # Gom các toán tử lọc nhanh → ghép vào q (Gmail cho phép kèm cùng labelIds).
    extra = []
    if unread:
        extra.append("is:unread")
    if starred:
        extra.append("is:starred")
    if attachment:
        extra.append("has:attachment")

    if q:  # có từ khoá → TÌM trên toàn hộp thư (kèm bộ lọc nếu có)
        params["q"] = " ".join([q, *extra])
    elif folder == "archive":
        params["q"] = " ".join(["-in:inbox -in:trash -in:spam", *extra])
    else:
        params["labelIds"] = _FOLDER_LABEL.get(folder, "INBOX")
        if params["labelIds"] == "TRASH":      # Gmail mặc định giấu thùng rác/spam
            params["includeSpamTrash"] = "true"
        if extra:                               # lọc nhanh trong 1 thư mục cụ thể
            params["q"] = " ".join(extra)

    tag = folder if folder in _VALID_TAGS else "inbox"  # nhãn folder gắn vào mỗi Email

    with httpx.Client(timeout=15) as client:
        # B1: lấy DANH SÁCH id thư (Gmail chỉ trả id) + token trang kế (nếu còn).
        listing = client.get(GMAIL_LIST, headers=headers, params=params)
        listing.raise_for_status()
        data = listing.json()
        ids = [m["id"] for m in data.get("messages", [])]
        next_cursor = data.get("nextPageToken")  # None khi đã hết thư

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
        result = (emails, next_cursor)
        _cache_set(cache_key, result)  # lưu lại để lần sau (trong TTL) khỏi gọi Gmail
        return result


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


# ── Tải 1 tệp đính kèm (UC004 — nút Download) ────────────────────────
def get_attachment(
    access_token: str, msg_id: str, filename: str
) -> tuple[bytes | None, str | None, str | None]:
    """Lấy BYTES của tệp đính kèm tên `filename` trong thư `msg_id`.
    Trả (dữ liệu, kiểu MIME, tên tệp) — hoặc (None, None, None) nếu không tìm thấy.

    Hai bước: (1) đọc thư đầy đủ, đi qua các 'mảnh' tìm mảnh có đúng tên tệp để lấy
    `attachmentId`; (2) gọi endpoint attachments lấy bytes (Gmail trả base64url)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    found: dict = {"aid": None, "mime": None, "name": None}

    def walk(part: dict) -> None:
        if found["aid"]:
            return
        if part.get("filename") == filename:           # đúng tệp cần
            found["aid"] = part.get("body", {}).get("attachmentId")
            found["mime"] = part.get("mimeType")
            found["name"] = part.get("filename")
            return
        for child in part.get("parts", []) or []:
            walk(child)

    with httpx.Client(timeout=20) as client:
        r = client.get(GMAIL_MSG.format(id=msg_id), headers=headers, params={"format": "full"})
        r.raise_for_status()
        walk(r.json().get("payload", {}))
        if not found["aid"]:
            return None, None, None
        ar = client.get(
            GMAIL_ATTACH.format(id=msg_id, aid=found["aid"]), headers=headers
        )
        ar.raise_for_status()
        data_b64 = ar.json().get("data", "")

    pad = "=" * (-len(data_b64) % 4)                    # bù cho đủ bội số 4 (yêu cầu base64)
    raw = base64.urlsafe_b64decode(data_b64 + pad)
    return raw, found["mime"], found["name"]
