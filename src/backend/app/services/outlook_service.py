# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/outlook_service.py — ĐỌC/GHI OUTLOOK qua Microsoft    ║
# ║ Graph API. Đối xứng gmail_service nhưng cho provider Microsoft.     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Dịch mỗi message Graph → schema Email chung (FE không cần biết      ║
# ║ nguồn Gmail hay Outlook). Phân loại nhãn dùng CHUNG engine          ║
# ║ classify() → category/label khớp Gmail.                            ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime
from zoneinfo import ZoneInfo
import re
import httpx
from app.schemas.email import Email
from app.core.labeling import classify

GRAPH = "https://graph.microsoft.com/v1.0"
_TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")

# Thư mục app → thư mục Graph (well-known folder names).
_FOLDER = {
    "inbox": "inbox", "sent": "sentitems", "drafts": "drafts",
    "trash": "deleteditems", "archive": "archive",
}


def _hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fmt_local(iso: str) -> tuple[str, str]:
    """ISO UTC của Graph → (giờ 'HH:MM', ngày 'dd/mm/YYYY HH:MM') theo giờ VN."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(_TZ_VN)
        return dt.strftime("%H:%M"), dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso, iso


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _to_email(m: dict, folder: str = "inbox", full: bool = False) -> Email:
    frm = (m.get("from") or m.get("sender") or {}).get("emailAddress", {}) or {}
    to_list = m.get("toRecipients") or []
    to_addr = (to_list[0].get("emailAddress", {}).get("address", "") if to_list else "")
    name = frm.get("name") or frm.get("address") or "(không tên)"
    addr = frm.get("address", "")
    # Thư MÌNH GỬI (sent/drafts): hiện NGƯỜI NHẬN thay vì chính mình.
    display, display_email = (name, addr)
    if folder in ("sent", "drafts") and to_list:
        display = to_list[0].get("emailAddress", {}).get("name") or to_addr or "(chưa có người nhận)"
        display_email = to_addr

    snippet = m.get("bodyPreview", "") or ""
    subject = m.get("subject") or "(không tiêu đề)"
    time_s, date_s = _fmt_local(m.get("receivedDateTime", "") or m.get("sentDateTime", "") or "")
    cls = classify(addr, name, subject if subject != "(không tiêu đề)" else "", snippet)

    html_body = None
    if full:
        b = m.get("body", {}) or {}
        raw = b.get("content", "") or snippet
        is_html = b.get("contentType", "").lower() == "html"
        html_body = raw if is_html else None    # HTML gốc để FE render đúng chuẩn
        text = _strip_html(raw) if is_html else raw
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()] or [snippet]
    else:
        paragraphs = [snippet]

    flag = (m.get("flag") or {}).get("flagStatus")
    atts = [{"name": a.get("name", ""), "size": str(a.get("size", ""))}
            for a in (m.get("attachments") or [])] if full else None
    return Email(
        id=m["id"],
        sender=display,
        senderEmail=display_email,
        senderInitial=(display.lstrip("(")[:1].upper() or "?"),
        to=to_addr,
        subject=subject,
        preview=snippet,
        body=paragraphs,
        time=time_s,
        date=date_s,
        unread=(not m.get("isRead", True)),
        starred=(flag == "flagged"),
        category=cls.category.color,   # type: ignore[arg-type]
        label=cls.category.label,
        folder=folder,                 # type: ignore[arg-type]
        threadId=m.get("conversationId"),
        html=html_body,
        attachments=(atts or None),    # type: ignore[arg-type]
    )


_SELECT = ("id,subject,from,toRecipients,receivedDateTime,sentDateTime,"
           "bodyPreview,isRead,hasAttachments,flag,conversationId")


def list_messages(access_token: str, folder: str = "inbox", q: str | None = None,
                  max_results: int = 30, page_token: str | None = None, **_ignore):
    """Danh sách thư 1 thư mục (hoặc tìm theo q). Trả (list[Email], next_url|None)."""
    tag = folder if folder in _FOLDER else "inbox"
    params = {"$top": max_results, "$select": _SELECT}
    if q:
        params["$search"] = f'"{q}"'                      # tìm toàn hộp thư
        url = f"{GRAPH}/me/messages"
    else:
        params["$orderby"] = "receivedDateTime desc"
        url = f"{GRAPH}/me/mailFolders/{_FOLDER[tag]}/messages"
    # page_token của Graph là URL @odata.nextLink đầy đủ → gọi thẳng.
    with httpx.Client(timeout=15) as c:
        r = c.get(page_token or url, headers=_hdr(access_token),
                  params=None if page_token else params)
        r.raise_for_status()
        data = r.json()
    emails = [_to_email(m, tag) for m in data.get("value", [])]
    return emails, data.get("@odata.nextLink")


def get_message(access_token: str, msg_id: str) -> Email:
    with httpx.Client(timeout=15) as c:
        r = c.get(f"{GRAPH}/me/messages/{msg_id}",
                  headers=_hdr(access_token), params={"$expand": "attachments($select=name,size)"})
        r.raise_for_status()
    return _to_email(r.json(), "inbox", full=True)


def send_email(access_token: str, to: str, subject: str, body: str,
               cc=None, bcc=None, **_ignore) -> dict:
    def _recips(s):
        return [{"emailAddress": {"address": a.strip()}} for a in
                (s if isinstance(s, list) else str(s).split(",")) if str(a).strip()]
    msg = {"subject": subject, "body": {"contentType": "Text", "content": body},
           "toRecipients": _recips(to)}
    if cc:
        msg["ccRecipients"] = _recips(cc)
    if bcc:
        msg["bccRecipients"] = _recips(bcc)
    with httpx.Client(timeout=15) as c:
        r = c.post(f"{GRAPH}/me/sendMail", headers=_hdr(access_token),
                   json={"message": msg, "saveToSentItems": True})
        r.raise_for_status()
    return {"id": "", "threadId": ""}   # Graph sendMail không trả id thư


def create_draft(access_token: str, to, subject: str, body: str,
                 cc=None, bcc=None, **_ignore) -> dict:
    """Lưu bản nháp trên Outlook: POST /me/messages (mặc định tạo message ở Drafts, chưa gửi)."""
    def _recips(s):
        return [{"emailAddress": {"address": a.strip()}} for a in
                (s if isinstance(s, list) else str(s).split(",")) if str(a).strip()]
    msg = {"subject": subject, "body": {"contentType": "Text", "content": body},
           "toRecipients": _recips(to)}
    if cc:
        msg["ccRecipients"] = _recips(cc)
    if bcc:
        msg["bccRecipients"] = _recips(bcc)
    with httpx.Client(timeout=15) as c:
        r = c.post(f"{GRAPH}/me/messages", headers=_hdr(access_token), json=msg)
        r.raise_for_status()
        d = r.json()
    return {"id": d.get("id", ""), "message": {"id": d.get("id", ""), "threadId": d.get("conversationId")}}


def reply_email(access_token: str, msg_id: str, body: str, **_ignore) -> dict:
    with httpx.Client(timeout=15) as c:
        r = c.post(f"{GRAPH}/me/messages/{msg_id}/reply",
                   headers=_hdr(access_token), json={"comment": body})
        r.raise_for_status()
    return {"id": "", "threadId": ""}


def set_read(access_token: str, ids: list[str], read: bool) -> int:
    n = 0
    with httpx.Client(timeout=15) as c:
        for i in ids:
            r = c.patch(f"{GRAPH}/me/messages/{i}", headers=_hdr(access_token), json={"isRead": read})
            if r.status_code < 300:
                n += 1
    return n


def set_flag(access_token: str, ids: list[str], flagged: bool) -> int:
    n = 0
    status = "flagged" if flagged else "notFlagged"
    with httpx.Client(timeout=15) as c:
        for i in ids:
            r = c.patch(f"{GRAPH}/me/messages/{i}", headers=_hdr(access_token),
                        json={"flag": {"flagStatus": status}})
            if r.status_code < 300:
                n += 1
    return n


def _move(access_token: str, ids: list[str], dest: str) -> int:
    n = 0
    with httpx.Client(timeout=15) as c:
        for i in ids:
            r = c.post(f"{GRAPH}/me/messages/{i}/move", headers=_hdr(access_token),
                       json={"destinationId": dest})
            if r.status_code < 300:
                n += 1
    return n


def trash(access_token: str, ids: list[str]) -> int:
    return _move(access_token, ids, "deleteditems")


def archive(access_token: str, ids: list[str]) -> int:
    return _move(access_token, ids, "archive")


def set_categories(access_token: str, ids: list[str], cats: list[str]) -> int:
    """Đặt danh sách 'categories' cho thư (rỗng = bỏ category). Outlook không có label như Gmail."""
    n = 0
    with httpx.Client(timeout=15) as c:
        for i in ids:
            r = c.patch(f"{GRAPH}/me/messages/{i}", headers=_hdr(access_token),
                        json={"categories": cats})
            if r.status_code < 300:
                n += 1
    return n


def apply_category(access_token: str, ids: list[str], label: str) -> int:
    """Gán 1 category tên `label` (tương đương 'gắn nhãn' bên Gmail)."""
    return set_categories(access_token, ids, [label])
