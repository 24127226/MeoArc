# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/app.py — TRÁI TIM của server (Nấc 0)                        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: tạo ra "ứng dụng web" và khai báo vài ROUTE đầu tiên.     ║
# ║ AI GỌI: Frontend (hoặc trình duyệt) gửi request HTTP tới đây.       ║
# ║ Ở nấc này chưa có Gmail/đăng nhập — chỉ để bạn THẤY server chạy.    ║
# ╚══════════════════════════════════════════════════════════════════╝

# Nhập lớp FastAPI từ thư viện fastapi. Đây là "bộ khung" lo hết phần
# khó của web (nhận request, parse, trả JSON, sinh tài liệu...).
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # cho phép FE gọi sang (xem CORS bên dưới)
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.email_service import list_emails  # logic lấy email (tầng service)

# --- Nấc 3: database (ORM) ---
from fastapi import Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.db import Base, engine, get_db
from app.core.config import settings  # cờ tính năng (vd mailbox_store_enabled) dùng ở nhiều route
from app.models.user import User  # noqa: F401 — phải import để create_all "thấy" bảng users
from app.models.session import AuthSession  # noqa: F401 — để create_all tạo cả bảng sessions
from app.models.conversation import Conversation  # noqa: F401 — UC011: tạo bảng conversations
from app.models.audit import AuditLog  # noqa: F401 — tạo bảng audit_logs (accountability)
from app.models.notification import Notification  # noqa: F401 — tạo bảng notifications
from app.models.subscription import Subscription  # noqa: F401 — tạo bảng subscriptions (quota token)
from app.models.session_provider import SessionProvider  # noqa: F401 — tạo bảng session_providers (Gmail/Outlook)
from app.models.email_store import StoredEmail, MailboxSync  # noqa: F401 — tạo bảng emails + mailbox_sync (store-of-record)
from app.repo import user_repo, conversation_repo, audit_repo, notification_repo, subscription_repo, email_store_repo
from app.core import plans  # danh mục gói + hạn mức token (một nguồn duy nhất)
from app.schemas.user import UserCreate, UserOut
from app.schemas.conversation import ConversationSummary, ConversationDetail, UpdateConversationReq

# --- Nấc 4b: đăng nhập ---
from app.core.deps import get_current_user, get_current_session, get_gmail_token, get_provider
from app.services import gmail_service, mail, sync_service
from app.api import auth as auth_routes
from fastapi import BackgroundTasks  # hàng đợi nhẹ (in-process) cho webhook/sync chạy nền

# --- Nấc 6a: hành động Gmail (ghi) ---
from fastapi import Response
from app.services import gmail_actions
from app.schemas.actions import ReadReq, ImportantReq, IdsReq, ActionResult, LabelReq, ReadOneReq

# --- Nấc 6b: gửi & trả lời thư ---
from app.services import gmail_send
from app.schemas.send import SendReq, ReplyReq, SendResult

# --- Nấc 8: kho tệp đính kèm (giữ bytes để gắn vào mail) ---
from app.services import upload_store

# --- Nấc 10: thực thi sau duyệt (cầu nối agent ↔ service, KHÔNG phải LLM) ---
from app.schemas.agent import ExecutePlanReq, ExecuteResult, AutopilotApplyReq, OkResult

# Tạo bảng trong DB nếu chưa có. (Cách này hợp để HỌC; dự án thật dùng Alembic —
# công cụ "migration" quản lý thay đổi cấu trúc bảng theo thời gian.)
Base.metadata.create_all(bind=engine)

# ── NFR-Observability: BẬT hệ thống log có request-id + xoay file (logs/app.log) ──
# Hạ tầng này develop đã viết sẵn ở core/logging.py nhưng CHƯA từng được gọi → giờ nối vào.
# Mỗi request được gắn rid riêng (middleware bên dưới) → mọi dòng log của cùng 1 request
# mang cùng rid, tra lỗi production dễ hơn hẳn.
from app.core.logging import setup_logging, set_request_id
setup_logging()

import time as _time
_STARTED_AT = _time.time()  # mốc khởi động — /health báo uptime

# Tạo đối tượng ứng dụng. title/description/version sẽ HIỆN trên trang
# tài liệu tự sinh tại /docs — nên đặt cho rõ để dễ đọc khi demo.
app = FastAPI(
    title="MeoArc Backend (sandbox)",
    description="Server học việc — nấc 0: làm cho FastAPI chạy được.",
    version="0.1.0",
)

# ── NFR-Speed: nén GZip cho response lớn (danh sách email JSON rất "nặng chữ") ──
# minimum_size=1024: gói nhỏ khỏi nén (nén còn tốn CPU hơn tiết kiệm).
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1024)


# ── NFR-Observability + Security: middleware gắn request-id, đo thời gian, header an toàn ──
@app.middleware("http")
async def observability_and_security(request: Request, call_next):
    rid = set_request_id()                      # log của request này đều mang rid
    t0 = _time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (_time.perf_counter() - t0) * 1000
    # Đo được mới nói chuyện "tốc độ": FE/DevTools đọc 2 header này để soi độ trễ từng call.
    response.headers["X-Request-ID"] = rid
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.0f}"
    # Header bảo mật cơ bản (OWASP): chặn đoán MIME, chặn nhúng iframe (clickjacking),
    # hạn chế rò URL qua referrer. (HSTS chỉ bật khi chạy HTTPS thật — dev là HTTP.)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Request chậm bất thường → cảnh báo kèm rid để lần ra (agent >10s là đáng nhìn).
    if elapsed_ms > 10_000:
        import logging
        logging.getLogger("app.perf").warning(
            "SLOW %s %s took %.0fms", request.method, request.url.path, elapsed_ms)
    return response

# ── CORS — vì sao bắt buộc khi nối Frontend ──────────────────────────
# Trình duyệt có quy tắc "same-origin": một trang ở origin A
# (vd http://localhost:5173 của FE) MẶC ĐỊNH bị chặn gọi sang origin B
# (vd http://localhost:8000 của BE). Server phải KHAI BÁO origin được
# phép thì trình duyệt mới cho. Thiếu đoạn này → FE gọi sẽ lỗi CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite khi chạy `npm run dev`
        "http://localhost:5180",  # cổng preview (nếu dùng)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── NFR-Reliability: /health — điểm bắt mạch cho monitor/uptime check ────────
# Chuẩn production: hệ thống giám sát (hoặc giám khảo 😄) gọi GET /health là biết ngay
# app sống không + DB nối được không, khỏi bấm mò từng tính năng. DB đứt → 503 "degraded".
@app.get("/health")
def health(db: Session = Depends(get_db)):
    from sqlalchemy import text as _sqltext
    try:
        db.execute(_sqltext("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    body = {
        "status": "ok" if db_ok else "degraded",
        "db": "up" if db_ok else "down",
        "uptime_s": int(_time.time() - _STARTED_AT),
        "version": app.version,
    }
    return body if db_ok else JSONResponse(status_code=503, content=body)


# ── Nấc 9 (#2): CHUẨN HOÁ định dạng lỗi ──────────────────────────────
# Hợp đồng (docs/02-API-CONTRACT) quy ước MỌI lỗi trả về dạng:
#   { "error": { "code": "...", "message": "...", "details": {} } }
# FastAPI mặc định trả { "detail": ... } → FE đọc `error.message` không thấy. Hai handler
# dưới đổi mọi lỗi sang đúng khuôn để FE hiển thị thông báo thật (vd "Token thiếu quyền…").

# Mã chữ theo HTTP status (để FE/log phân loại dễ hơn số trần).
_ERR_CODE = {
    400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND",
    409: "CONFLICT", 422: "VALIDATION_ERROR", 500: "INTERNAL_ERROR",
}


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Mọi HTTPException (401/403/404...) → khuôn { error: { code, message, details } }."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {
            "code": _ERR_CODE.get(exc.status_code, "ERROR"),
            "message": exc.detail,
            "details": {},
        }},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Lỗi dữ liệu vào sai/thiếu (422) → cùng khuôn, kèm chi tiết field nào sai."""
    return JSONResponse(
        status_code=422,
        content={"error": {
            "code": "VALIDATION_ERROR",
            "message": "Dữ liệu gửi lên không hợp lệ.",
            "details": {"errors": jsonable_encoder(exc.errors())},
        }},
    )


# @app.get("/") là một DECORATOR. Đọc là:
#   "Khi có request GET tới đường dẫn '/', hãy chạy hàm ngay bên dưới."
# GET = 'lấy/đọc dữ liệu' (một trong các 'động từ' HTTP: GET/POST/PUT/DELETE).
@app.get("/")
async def root():
    # `async def` = hàm BẤT ĐỒNG BỘ. Nhờ vậy server có thể phục vụ
    # nhiều người cùng lúc mà không bị "kẹt" chờ từng việc xong.
    #
    # Trả về một dict Python bình thường. FastAPI TỰ ĐỘNG đổi nó thành
    # JSON cho trình duyệt — bạn không phải tự viết code chuyển đổi.
    return {"message": "MeoArc backend đang chạy 🎉"}


# (Route /health cũ đã GỘP vào bản NFR phía trên — thêm kiểm tra DB + uptime/version.)


# ── /emails — list theo thư mục + LỌC + TÌM + PHÂN TRANG (UC003/005) ──
# `token = Depends(get_gmail_token)` → tự lấy access_token CÒN HẠN (làm mới nếu cần, Nấc 9).
@app.get("/emails")
def get_emails(
    folder: str = "inbox",
    q: str | None = None,            # UC005: từ khoá tìm kiếm
    unread: bool | None = None,      # bộ lọc nhanh: chỉ thư chưa đọc
    starred: bool | None = None,     # chỉ thư gắn sao
    attachment: bool | None = None,  # chỉ thư có đính kèm
    category: str | None = None,     # màu chip của FE — Gmail KHÔNG có khái niệm này → bỏ qua ở server
    cursor: str | None = None,       # Nấc 9 (#3): token trang KẾ để lấy thêm thư (>30)
    limit: int = 30,
    fresh: bool = False,             # nút "Làm mới": bỏ qua cache 60s, ép lấy bản mới nhất
    token: str = Depends(get_gmail_token),
    provider: str = Depends(get_provider),  # 'google' | 'microsoft' → định tuyến Gmail/Outlook
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    # STORE-OF-RECORD: bật cờ + DB đã có thư của user ⇒ phục vụ TỪ DB, KHÔNG gọi Gmail
    # (chống rate-limit — yêu cầu nhóm). DB còn "lạnh" (chưa sync) ⇒ lùi về live như cũ.
    if settings.mailbox_store_enabled and email_store_repo.has_any(db, session.user_id, provider):
        items, next_cursor = email_store_repo.get_page(
            db, session.user_id, provider, folder=folder, q=q, unread=unread,
            starred=starred, attachment=attachment, limit=limit, cursor=cursor,
        )
        return {"items": items, "nextCursor": next_cursor, "criteria": [], "source": "db"}

    items, next_cursor = mail.list_messages(
        provider, token, folder=folder, q=q, unread=unread, starred=starred,
        attachment=attachment, page_token=cursor, max_results=limit, bypass_cache=fresh,
    )
    return {"items": items, "nextCursor": next_cursor, "criteria": []}


# ── Nấc 5b: xem CHI TIẾT 1 thư (UC004) — thân thư đầy đủ + đính kèm ──
@app.get("/emails/{email_id}")
def get_email(email_id: str, token: str = Depends(get_gmail_token),
              provider: str = Depends(get_provider),
              session: AuthSession = Depends(get_current_session),
              db: Session = Depends(get_db)):
    # Chi tiết LUÔN lấy LIVE (có HTML gốc + mới nhất; 1 call/thư, cache 60s). Store phục vụ LIST.
    # Lỗi live (offline / thư đã xoá) → lùi về bản DB nếu có.
    try:
        live = mail.get_message(provider, token, email_id)
        if settings.mailbox_store_enabled:
            try:
                email_store_repo.upsert(db, session.user_id, provider, live,
                                        folder=live.folder or "inbox", full=True)
            except Exception:
                db.rollback()
        return live
    except Exception:
        if settings.mailbox_store_enabled:
            cached = email_store_repo.get_one(db, session.user_id, provider, email_id)
            if cached is not None:
                return cached
        raise


@app.post("/emails/{email_id}/summarize")
def summarize_email(email_id: str, token: str = Depends(get_gmail_token),
                    provider: str = Depends(get_provider)):
    """UC008 — Tóm tắt 1 email bằng LLM → trả list gạch đầu dòng cho thẻ 'Tóm tắt · AI' ở
    màn chi tiết. LLM chưa cấu hình / thư rỗng / lỗi → lùi về TRÍCH đoạn đầu (fallback an toàn)."""
    import re as _re
    email = mail.get_message(provider, token, email_id)
    body = "\n".join(email.body or []).strip() or email.preview

    def _extract() -> list[str]:
        pts = [p.strip() for p in (email.body or []) if len(p.strip()) > 20][:3]
        return pts or [email.preview or "(thư rỗng)"]

    if not settings.agent_enabled or not body:
        return {"points": _extract(), "source": "extract"}
    try:
        from app.core.llm import create_llm
        from app.agent.nodes.agent_node import coerce_text
        prompt = (
            "Tóm tắt email dưới đây thành 2–4 gạch đầu dòng NGẮN GỌN bằng tiếng Việt, "
            "mỗi dòng 1 ý chính. CHỈ trả các gạch đầu dòng, không mở đầu/kết luận.\n\n"
            f"Tiêu đề: {email.subject}\nNội dung:\n{body[:4000]}"
        )
        text = coerce_text(getattr(create_llm().invoke(prompt), "content", "")) or ""
        pts = [_re.sub(r"^[\-\*•\d\.\)\s]+", "", ln).strip() for ln in text.splitlines()]
        pts = [p for p in pts if p][:5]
        return {"points": pts or _extract(), "source": "llm"}
    except Exception:
        return {"points": _extract(), "source": "extract"}


# ── Nấc 6a: HÀNH ĐỘNG Gmail (UC006) — đánh dấu đọc · sao · lưu trữ · xoá ──
# Hàm phụ dùng chung cho các endpoint ghi (viết 1 lần, tránh lặp code):

def _guard(action):
    """Chạy 1 lệnh gọi Gmail và DỊCH lỗi thiếu quyền (403) thành thông báo dễ hiểu.
    VÌ SAO: token cũ có thể thiếu quyền ghi/gửi → service ném GmailPermissionError;
    ở đây đổi thành 403 kèm hướng dẫn 'đăng nhập lại' thay vì lỗi 500 khó hiểu.
    Trả NGUYÊN giá trị của action (số thư, hay dict thư đã gửi) để nơi gọi tự xử."""
    try:
        return action()
    except gmail_actions.GmailPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Token thiếu quyền. Hãy ĐĂNG NHẬP LẠI để cấp quyền quản lý & gửi Gmail.",
        )


def _write(action) -> ActionResult:
    """Riêng cho 4 hành động nhãn: chạy qua _guard rồi gói số thư vào ActionResult."""
    return ActionResult(affected=_guard(action))


def _record(
    db: Session,
    user_id: int,
    *,
    action: str,
    ids: list[str] | None = None,
    tool_name: str = "",
    actor_type: str = "user",
    status: str = "success",
    details: dict | None = None,
    conversation_id: str | None = None,
    notify: str | None = None,
    notify_type: str = "info",
) -> None:
    """Ghi 1 dòng AuditLog (LUÔN) + sinh 1 Notification (nếu có `notify`). Gọi SAU khi
    hành động Gmail đã thành công. Nuốt mọi lỗi phụ trợ: audit/notify hỏng KHÔNG được
    làm sập response của hành động chính (accountability là 'thêm', không phải 'chặn')."""
    try:
        audit_repo.log(
            db, user_id=user_id, action=action, tool_name=tool_name, actor_type=actor_type,
            affected_email_ids=ids or [], status=status, details=details or {},
            conversation_id=conversation_id,
        )
        if notify:
            notification_repo.create(db, user_id=user_id, message=notify, type=notify_type)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def _turn_tokens(messages: list) -> int:
    """Ước lượng token đã tiêu của LƯỢT hiện tại (từ HumanMessage cuối → tránh cộng dồn lượt cũ).
    Ưu tiên usage_metadata model báo (Gemini/Groq đều có); thiếu thì ước ~4 ký tự/token."""
    last_human = max((i for i, m in enumerate(messages)
                      if getattr(m, "type", None) == "human"), default=0)
    turn = messages[last_human:]
    total, have_meta = 0, False
    for m in turn:
        if getattr(m, "type", None) != "ai":
            continue
        um = getattr(m, "usage_metadata", None)
        if isinstance(um, dict) and um.get("total_tokens"):
            total += int(um["total_tokens"])
            have_meta = True
    if have_meta:
        return total
    from app.agent.nodes.agent_node import coerce_text
    chars = sum(len(coerce_text(getattr(m, "content", "")) or "") for m in turn)
    return max(1, chars // 4)


def _wt(fn) -> None:
    """WRITE-THROUGH: cập nhật store `emails` sau khi hành động đã chạy thật trên Gmail/Graph.
    Chỉ khi bật cờ store; nuốt lỗi để KHÔNG bao giờ phá hành động chính (best-effort)."""
    if not settings.mailbox_store_enabled:
        return
    try:
        fn()
    except Exception:
        pass


@app.post("/emails/actions/read", response_model=ActionResult)
def action_read(req: ReadReq, token: str = Depends(get_gmail_token),
                provider: str = Depends(get_provider),
                session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Đánh dấu đã/chưa đọc (Gmail: nhãn UNREAD · Outlook: isRead)."""
    result = _write(lambda: mail.set_read(provider, token, req.ids, req.read))
    _wt(lambda: email_store_repo.mark_read(db, session.user_id, provider, req.ids, req.read))
    # Hành động NHẸ, đảo được → chỉ audit, KHÔNG làm phiền bằng notification.
    _record(db, session.user_id, action="mark_read" if req.read else "mark_unread",
            ids=req.ids, tool_name="bulk_action")
    return result


@app.post("/emails/actions/important", response_model=ActionResult)
def action_important(req: ImportantReq, token: str = Depends(get_gmail_token),
                     provider: str = Depends(get_provider),
                     session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Gắn/bỏ sao (Gmail: STARRED · Outlook: flag)."""
    result = _write(lambda: mail.set_flag(provider, token, req.ids, req.value))
    _wt(lambda: email_store_repo.set_starred(db, session.user_id, provider, req.ids, req.value))
    _record(db, session.user_id, action="star" if req.value else "unstar",
            ids=req.ids, tool_name="bulk_action")
    return result


@app.post("/emails/actions/archive", response_model=ActionResult)
def action_archive(req: IdsReq, token: str = Depends(get_gmail_token),
                   provider: str = Depends(get_provider),
                   session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Lưu trữ (Gmail: bỏ nhãn INBOX · Outlook: chuyển thư mục Archive)."""
    result = _write(lambda: mail.archive(provider, token, req.ids))
    _wt(lambda: email_store_repo.move_folder(db, session.user_id, provider, req.ids, "archive"))
    _record(db, session.user_id, action="archive", ids=req.ids, tool_name="bulk_action",
            notify=f"Đã lưu trữ {len(req.ids)} thư.", notify_type="info")
    return result


@app.post("/emails/actions/delete", response_model=ActionResult)
def action_delete(req: IdsReq, token: str = Depends(get_gmail_token),
                  provider: str = Depends(get_provider),
                  session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Xoá = vào THÙNG RÁC (Gmail: trash · Outlook: chuyển Deleted Items) — khôi phục được."""
    result = _write(lambda: mail.trash(provider, token, req.ids))
    _wt(lambda: email_store_repo.move_folder(db, session.user_id, provider, req.ids, "trash"))
    _record(db, session.user_id, action="delete", ids=req.ids, tool_name="bulk_action",
            notify=f"Đã chuyển {len(req.ids)} thư vào thùng rác.", notify_type="warning")
    return result


@app.post("/emails/actions/label", response_model=ActionResult)
def action_label(req: LabelReq, token: str = Depends(get_gmail_token),
                 provider: str = Depends(get_provider),
                 session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Gắn NHÃN (Gmail: label tự tạo · Outlook: categories) cho thư (UC006)."""
    result = _write(lambda: mail.apply_label(provider, token, req.ids, req.label))
    _wt(lambda: email_store_repo.set_label(db, session.user_id, provider, req.ids, req.label))
    _record(db, session.user_id, action="apply_label", ids=req.ids, tool_name="apply_labels",
            details={"label": req.label},
            notify=f"Đã gắn nhãn “{req.label}” cho {len(req.ids)} thư.", notify_type="success")
    return result


@app.post("/emails/{email_id}/read", response_model=ActionResult)
def mark_read_one(email_id: str, req: ReadOneReq, token: str = Depends(get_gmail_token),
                  provider: str = Depends(get_provider)):
    """Đánh dấu MỘT thư đã/chưa đọc — FE gọi khi MỞ thư (UC004). Không audit (quá thường)."""
    return _write(lambda: mail.set_read(provider, token, [email_id], req.read))


@app.get("/emails/{email_id}/attachments/{name}")
def download_attachment(email_id: str, name: str, token: str = Depends(get_gmail_token)):
    """Tải 1 tệp đính kèm (UC004 — nút Download). Trả bytes kèm tên + kiểu để trình duyệt lưu."""
    data, mime, fname = gmail_service.get_attachment(token, email_id, name)
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tệp đính kèm")
    # Content-Disposition: attachment → trình duyệt TẢI XUỐNG (thay vì mở trong tab).
    return Response(
        content=data,
        media_type=mime or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


# ── Nấc 6b: GỬI & TRẢ LỜI thư thật (UC010) ───────────────────────────
@app.post("/emails/send", response_model=SendResult)
def send_email_route(req: SendReq, bg: BackgroundTasks, token: str = Depends(get_gmail_token),
                     provider: str = Depends(get_provider),
                     session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Soạn & gửi thư mới (kèm tệp — Gmail). Body khớp `SendEmailInput` + attachmentIds."""
    # Đổi danh sách id tệp → nội dung thật (bytes) đã cất ở /uploads. Id không tồn tại → bỏ qua.
    attachments = [
        {"name": f["name"], "content": f["content"], "mime": f["mime"]}
        for fid in (req.attachmentIds or [])
        if (f := upload_store.get(fid))
    ]
    res = _guard(lambda: mail.send_email(
        provider, token, req.to, req.subject, req.body, cc=req.cc, bcc=req.bcc, attachments=attachments,
    ))
    new_id = res.get("id", "")
    _record(db, session.user_id, action="send_email", tool_name="send_email",
            ids=[new_id] if new_id else [], details={"to": req.to, "subject": req.subject},
            notify=f"Đã gửi email tới {req.to}.", notify_type="success")
    if settings.mailbox_store_enabled:
        bg.add_task(_bg_sync, session.user_id, provider, token)  # Sent hiện ngay
    return SendResult(id=new_id, threadId=res.get("threadId"))


@app.post("/emails/{email_id}/reply", response_model=SendResult)
def reply_email_route(email_id: str, req: ReplyReq, bg: BackgroundTasks,
                      token: str = Depends(get_gmail_token),
                      provider: str = Depends(get_provider),
                      session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Trả lời thư email_id: BE tự suy người nhận/tiêu đề/luồng từ thư gốc, chỉ cần `body`."""
    res = _guard(lambda: mail.reply_email(provider, token, email_id, req.body))
    new_id = res.get("id", "")
    _record(db, session.user_id, action="reply_email", tool_name="reply_email",
            ids=[i for i in (email_id, new_id) if i], details={"reply_to": email_id},
            notify="Đã gửi trả lời trong đúng luồng thư.", notify_type="success")
    if settings.mailbox_store_enabled:
        bg.add_task(_bg_sync, session.user_id, provider, token)  # Sent hiện ngay
    return SendResult(id=new_id, threadId=res.get("threadId"))


# ── UC010: LƯU NHÁP · GỢI Ý AI · AUTOCOMPLETE NGƯỜI NHẬN ────────────────────
@app.post("/emails/draft")
def save_draft(req: SendReq, token: str = Depends(get_gmail_token),
               provider: str = Depends(get_provider),
               session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Lưu BẢN NHÁP (không gửi) — tạo nháp trên Gmail/Outlook + upsert vào store (folder='drafts')
    để hiện NGAY ở tab Nháp dù chưa sync lại."""
    attachments = [
        {"name": f["name"], "content": f["content"], "mime": f["mime"]}
        for fid in (req.attachmentIds or []) if (f := upload_store.get(fid))
    ]
    res = _guard(lambda: mail.create_draft(provider, token, req.to, req.subject, req.body,
                                           cc=req.cc, bcc=req.bcc, attachments=attachments))
    gid = (res.get("message") or {}).get("id") or res.get("id") or ""
    try:
        if settings.mailbox_store_enabled and gid:
            from app.schemas.email import Email
            recipient = (req.to or "").strip() or "(chưa có người nhận)"
            em = Email(id=gid, sender=recipient, senderEmail=(req.to or "").strip(),
                       senderInitial=(recipient.lstrip("(")[:1].upper() or "?"), to=(req.to or ""),
                       subject=req.subject or "(không tiêu đề)", preview=(req.body or "")[:120],
                       body=[req.body or ""], time="", date="", unread=False, starred=False,
                       category="sky", label="Nháp", folder="drafts",
                       threadId=(res.get("message") or {}).get("threadId"))
            email_store_repo.upsert(db, session.user_id, provider, em, folder="drafts", full=True)
    except Exception:
        db.rollback()
    return {"id": gid}


@app.post("/emails/compose/suggest")
def compose_suggest(payload: dict):
    """Smart Compose — gợi ý ĐOẠN TIẾP THEO khi soạn thư, dựa trên tiêu đề + phần đang gõ.
    LLM chưa cấu hình / lỗi → trả rỗng (FE tự ẩn gợi ý)."""
    subject = (payload or {}).get("subject", "")
    body = (payload or {}).get("body", "")
    if not settings.agent_enabled:
        return {"suggestion": ""}
    try:
        from app.core.llm import create_llm
        from app.agent.nodes.agent_node import coerce_text
        prompt = (
            "Bạn là trợ lý viết email tiếng Việt. Dựa trên TIÊU ĐỀ và phần người dùng ĐANG viết, "
            "gợi ý PHẦN TIẾP THEO (nối liền mạch, tự nhiên, tối đa 1–2 câu). CHỈ trả phần nối tiếp, "
            "KHÔNG lặp lại phần đã viết, KHÔNG giải thích.\n\n"
            f"Tiêu đề: {subject}\nĐang viết:\n{body}\n\nGợi ý tiếp theo:"
        )
        text = coerce_text(getattr(create_llm().invoke(prompt), "content", "")) or ""
        return {"suggestion": text.strip()[:300]}
    except Exception:
        return {"suggestion": ""}


@app.get("/contacts")
def contacts(q: str = "", limit: int = 8, provider: str = Depends(get_provider),
             session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Autocomplete người nhận (như Gmail) — suy từ sender/recipient các thư đã đồng bộ trong store."""
    return {"items": email_store_repo.contacts(db, session.user_id, provider, q, min(max(limit, 1), 20))}


# ── ĐỒNG BỘ HỘP THƯ → DB store (chống rate-limit) ───────────────────────────
# Chiến lược: Gmail Push (Pub/Sub) đẩy thông báo khi hộp thư đổi → webhook này nhận →
# đồng bộ LŨY TIẾN (chỉ phần thay đổi) vào DB. User đọc web = đọc DB, KHÔNG gọi Gmail.

def _bg_sync(user_id: int, provider: str, token: str) -> None:
    """Đồng bộ lũy tiến ở NỀN sau hành động GHI (gửi/trả lời/agent) → Sent/Inbox trong web cập nhật
    NGAY mà không cần Pub/Sub. Mở phiên DB riêng; nuốt lỗi (không phá response chính)."""
    from app.core.db import SessionLocal
    d = SessionLocal()
    try:
        sync_service.incremental_sync(d, user_id, provider, token)
    except Exception:
        pass
    finally:
        d.close()


def _bg_pubsub(email_address: str) -> None:
    """Chạy NỀN sau khi webhook đã trả 2xx (Pub/Sub yêu cầu phản hồi nhanh). Mở phiên DB riêng."""
    from app.core.db import SessionLocal
    db = SessionLocal()
    try:
        n = sync_service.handle_pubsub(db, email_address)
        import logging
        logging.getLogger("app.sync").info("Pub/Sub sync %s: %d thư", email_address, n)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


@app.post("/gmail/push", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_push(request: Request, bg: BackgroundTasks, token: str | None = None):
    """WEBHOOK Gmail Push (Pub/Sub push subscription trỏ vào đây). Giải mã thông báo lấy
    emailAddress rồi ĐẨY việc đồng bộ sang nền, trả 204 NGAY (Pub/Sub retry nếu chậm/lỗi).
    Bảo vệ tối thiểu bằng ?token= khớp PUBSUB_VERIFY_TOKEN (nếu có cấu hình)."""
    import base64 as _b64, json as _json, logging as _log
    if settings.pubsub_verify_token and token != settings.pubsub_verify_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "token webhook không hợp lệ")
    try:
        envelope = await request.json()
        data_b64 = (envelope.get("message") or {}).get("data") or ""
        payload = _json.loads(_b64.b64decode(data_b64).decode("utf-8")) if data_b64 else {}
        email_address = payload.get("emailAddress")
    except Exception as exc:
        _log.getLogger("app.sync").warning("Pub/Sub payload lỗi: %s", exc)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if email_address:
        bg.add_task(_bg_pubsub, email_address)   # HÀNG ĐỢI nhẹ: tách việc nặng khỏi phản hồi
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/sync/run")
def sync_run(bg: BackgroundTasks, background: bool = False,
             token: str = Depends(get_gmail_token), provider: str = Depends(get_provider),
             session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Đồng bộ hộp thư của PHIÊN đang đăng nhập vào DB (nút 'Đồng bộ ngay' / gọi định kỳ).
    background=true → chạy nền, trả ngay. Mặc định chạy đồng bộ và trả số thư đã cập nhật."""
    if background:
        uid, prov, tok = session.user_id, provider, token
        def _job():
            from app.core.db import SessionLocal
            d = SessionLocal()
            try:
                sync_service.incremental_sync(d, uid, prov, tok)
            finally:
                d.close()
        bg.add_task(_job)
        return {"queued": True}
    n = sync_service.incremental_sync(db, session.user_id, provider, token)
    return {"synced": n, "provider": provider}


@app.post("/gmail/watch")
def gmail_watch(token: str = Depends(get_gmail_token), provider: str = Depends(get_provider),
                session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """BẬT Gmail Push cho hộp thư này (cần GMAIL_PUBSUB_TOPIC). Lưu hạn watch để gia hạn sau.
    Chỉ Gmail — Outlook dùng Graph subscriptions (hướng nâng cấp)."""
    if provider != "google":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "watch chỉ hỗ trợ Gmail (google).")
    if not settings.gmail_pubsub_topic:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Chưa cấu hình GMAIL_PUBSUB_TOPIC trong .env.")
    res = _guard(lambda: gmail_service.watch(token, settings.gmail_pubsub_topic))
    state = sync_service._get_state(db, session.user_id, "google")
    exp = res.get("expiration")
    if exp:
        from datetime import datetime as _dt, timezone as _tz
        state.watch_expiration = _dt.fromtimestamp(int(exp) / 1000, tz=_tz.utc).replace(tzinfo=None)
    if res.get("historyId"):
        state.history_id = str(res["historyId"])
    db.commit()
    return {"watching": True, "expiration": res.get("expiration"),
            "historyId": res.get("historyId")}


# ── ACCOUNTABILITY: AuditLog + Notification ─────────────────────────────────
# AuditLog = nhật ký KỸ THUẬT "agent/user đã làm gì lên email nào" (hiện thực ý
# Toolcall_Email trong Design bằng affected_email_ids). Notification = thông báo
# hướng NGƯỜI DÙNG, sinh kèm các hành động đáng chú ý. Chỉ đọc phiên của CHÍNH user.
@app.get("/audit")
def get_audit(limit: int = 50,
              session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """N hành động gần nhất của user — để soi 'agent đã đụng gì' (accountability)."""
    rows = audit_repo.list_recent(db, session.user_id, limit=min(max(limit, 1), 200))
    return {"items": [{
        "id": r.id, "action": r.action, "toolName": r.tool_name, "actorType": r.actor_type,
        "affectedEmailIds": r.affected_email_ids, "status": r.status, "details": r.details,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]}


def _notif_dto(n) -> dict:
    return {"id": n.id, "type": n.type, "message": n.message, "read": n.read,
            "createdAt": n.created_at.isoformat() if n.created_at else None}


@app.get("/notifications")
def get_notifications(limit: int = 50,
                      session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    rows = notification_repo.list_for_user(db, session.user_id, limit=min(max(limit, 1), 200))
    return {"items": [_notif_dto(n) for n in rows],
            "unread": notification_repo.unread_count(db, session.user_id)}


@app.get("/notifications/unread-count")
def get_unread_count(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    return {"unread": notification_repo.unread_count(db, session.user_id)}


@app.post("/notifications/read-all")
def read_all_notifications(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    return {"marked": notification_repo.mark_all_read(db, session.user_id)}


@app.post("/notifications/{notif_id}/read")
def read_notification(notif_id: int,
                      session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    n = notification_repo.mark_read(db, session.user_id, notif_id)
    if not n:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thông báo")
    return _notif_dto(n)


# ── SUBSCRIPTION: gói + hạn mức token (freemium kiểu sản phẩm AI) ────────────
@app.get("/subscription")
def get_subscription(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Gói hiện tại + token đã dùng/còn lại (ngày & tháng) — FE hiện thanh usage."""
    sub = subscription_repo.get_or_create(db, session.user_id)
    return subscription_repo.status(db, sub)


@app.get("/subscription/plans")
def list_plans():
    """Danh mục 3 gói (Miễn phí / Pro / Pro Max) kèm hạn mức + giá hiển thị.
    FE dựng trang nâng cấp từ đây → số liệu chỉ nằm MỘT chỗ (app/core/plans.py)."""
    return {"plans": plans.public_catalog()}


@app.post("/subscription/tier")
def set_subscription_tier(payload: dict,
                          session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """Đổi gói (free/pro/max). ĐỒ ÁN: stub nâng cấp — sản phẩm thật sẽ qua cổng THANH TOÁN
    rồi mới set tier (không cho client tự nâng gói)."""
    tier = (payload or {}).get("tier", "free")
    if not plans.is_valid_tier(tier):
        raise HTTPException(status_code=400, detail=f"Gói không hợp lệ: {tier}")
    sub = subscription_repo.set_tier(db, session.user_id, tier)
    audit_repo.log(db, user_id=session.user_id, action="subscription.change_tier",
                   status="success", details={"tier": tier})
    return subscription_repo.status(db, sub)


# ── Pha 3 (tích hợp): AGENT THẬT — LangGraph + Gemini + tool Gmail ───
# FE gọi POST /agent/chat (qua api.sendAgentMessage). Giờ KHÔNG còn trả mẫu nữa:
# chạy graph agent → LLM hiểu lệnh → tự gọi tool (email_tools → service của quan).
# Vẫn trả đúng khuôn AgentReply kind "text" để FE hiện được như cũ.
_AGENT_GRAPH = None  # graph đã compile, dựng 1 lần ở request đầu rồi tái dùng (lazy singleton)

# ── NFR-Reliability: RATE LIMIT /agent/chat theo NGƯỜI (cửa sổ 60s) ──────────
# Vì sao cần: mỗi lượt chat đốt 2-3 lần gọi Gemini; quota free rất mỏng. Một người bấm
# liên tục (hoặc script lỗi lặp vô hạn) sẽ cạn quota của CẢ nhóm → chặn từ cửa, trả lời
# nhẹ nhàng TRƯỚC khi chạm LLM. Chạy trên kho KV cắm-rút: có REDIS_URL thì đếm trên
# Redis (đúng khi scale nhiều worker), không có thì in-memory như cũ.
from app.core.kv import kv as _kv


def _rate_limited(user_id: int) -> bool:
    from app.core.config import settings
    n = _kv.incr_window(f"rate:agent:{user_id}", window=60)
    return n > settings.agent_rate_limit_per_min

# ── BỘ NHỚ HỘI THOẠI (UC011 — LƯU BỀN xuống DB) ─────────────────────
# Vì sao CẦN: mỗi POST /agent/chat trước đây chạy 1 lượt RỖNG (chỉ tin nhắn mới) → agent KHÔNG
# nhớ gì. Luồng nhiều bước (vd "gửi mail cho A" → agent hỏi "xác nhận?" → user "ừ") bị ĐỨT.
# Giờ lưu lịch sử xuống bảng `conversations` theo sessionId → agent NHỚ + người dùng xem/tiếp tục
# lại phiên cũ (kể cả sau khi restart server). Xem app/models/conversation.py.
_MAX_HISTORY = 30  # giữ tối đa N tin LangChain gần nhất mỗi phiên (chặn phình token)


def _trim_history(msgs: list) -> list:
    """Cắt ngữ cảnh agent an toàn cho lượt sau:
    • Bỏ AIMessage 'mồ côi' ở cuối (có tool_calls nhưng CHƯA có ToolMessage — xảy ra khi chạm
      trần vòng lặp) để Gemini không báo lỗi 'tool_call thiếu kết quả'.
    • Giữ N tin cuối, rồi bỏ phần đầu cho tới HumanMessage đầu tiên (không mở màn bằng tool/ai mồ côi).
    """
    msgs = list(msgs)
    while msgs and getattr(msgs[-1], "type", None) == "ai" and getattr(msgs[-1], "tool_calls", None):
        msgs.pop()
    trimmed = msgs[-_MAX_HISTORY:]
    for i, m in enumerate(trimmed):
        if getattr(m, "type", None) == "human":
            return trimmed[i:]
    return trimmed


def _compact_tools(msgs: list, cap: int = 600) -> list:
    """NFR-Memory: rút gọn nội dung ToolMessage (JSON email thô — thường vài KB) khi CẤT KHO lịch sử.
    Lượt HIỆN TẠI đã dùng bản đầy đủ để trả lời + responder đã tóm tắt thành thẻ; nên bản lưu cho các
    lượt SAU chỉ cần giữ 'gợi ý' → đỡ phình token/RAM mỗi lần nạp lại phiên. Giữ nguyên tool_call_id để
    cặp AIMessage(tool_calls)↔ToolMessage không bị đứt."""
    from langchain_core.messages import ToolMessage
    out = []
    for m in msgs:
        c = getattr(m, "content", None)
        if getattr(m, "type", None) == "tool" and isinstance(c, str) and len(c) > cap:
            out.append(ToolMessage(
                content=c[:cap] + " …(đã rút gọn để tiết kiệm bộ nhớ)",
                tool_call_id=getattr(m, "tool_call_id", ""), name=getattr(m, "name", ""),
            ))
        else:
            out.append(m)
    return out


def _emails_from_search(messages: list, cap: int = 15) -> list:
    """UI/UX: rút danh sách email THẬT (id + người gửi + tiêu đề + snippet) từ kết quả search_emails
    của LƯỢT HIỆN TẠI → đính vào reply để FE vẽ thẻ BẤM ĐƯỢC (mở thẳng thư). Lấy id trực tiếp từ
    dữ liệu tool (KHÔNG nhờ LLM) nên id luôn chính xác — bấm là mở đúng thư.
    ⚠️ CHỈ xét từ HumanMessage CUỐI trở đi: vì có conversation memory, messages chứa cả lượt CŨ —
    không cắt sẽ đính nhầm danh sách thư của lượt trước vào câu trả lời mới (vd user nói 'cảm ơn'
    mà reply lại kèm chục thư cũ)."""
    import json
    last_human = max((i for i, m in enumerate(messages)
                      if getattr(m, "type", None) == "human"), default=0)
    for m in reversed(messages[last_human:]):
        # semantic_search trả CÙNG khuôn dữ liệu → thẻ bấm-được dùng chung
        if getattr(m, "type", None) == "tool" and getattr(m, "name", None) in ("search_emails", "semantic_search"):
            try:
                data = json.loads(m.content)
            except Exception:
                return []
            out = []
            for e in (data.get("data") or [])[:cap]:
                if not isinstance(e, dict) or not e.get("id"):
                    continue
                sender = (e.get("sender") or "").strip()
                out.append({
                    "id": str(e["id"]),
                    "sender": sender or "(không rõ)",
                    "initial": (sender[:1].upper() if sender else "•"),
                    "subject": e.get("subject") or "(không tiêu đề)",
                    "snippet": e.get("snippet") or "",
                    "unread": not e.get("is_read", True),
                })
            return out
    return []


def _categorize_card(messages: list) -> dict | None:
    """UC009: dựng thẻ 'categorize' cho FE từ kết quả categorize_emails CỦA LƯỢT NÀY.
    Tất định (id + nhãn lấy thẳng từ tool) → không nhờ LLM nên không sai nhãn/ id.
    Trả None nếu lượt này không phân loại."""
    import json
    last_human = max((i for i, m in enumerate(messages)
                      if getattr(m, "type", None) == "human"), default=0)
    for m in reversed(messages[last_human:]):
        if getattr(m, "type", None) == "tool" and getattr(m, "name", None) == "categorize_emails":
            try:
                data = json.loads(m.content)
            except Exception:
                return None
            raw = data.get("data") or []
            items = [{
                "id": str(it["id"]), "sender": it.get("sender", ""),
                "subject": it.get("subject", "(không tiêu đề)"),
                "category": it.get("category", "cherry"),   # màu chip FE
                "label": it.get("label", "Cá nhân"),
            } for it in raw if isinstance(it, dict) and it.get("id")]
            if not items:
                return None
            summary = data.get("summary") or {}
            gist = " · ".join(f"{v} {k}" for k, v in summary.items())
            return {
                "kind": "categorize",
                "intro": "Mình đã tự phân loại giúp bạn — xem lại/sửa nhãn từng thư rồi bấm Áp dụng nhé:",
                "title": f"Đề xuất nhãn cho {len(items)} thư" + (f" ({gist})" if gist else ""),
                "items": items,
            }
    return None


def _confirm_card(messages: list) -> dict | None:
    """Human-in-the-loop (UC007/UC010): tool KHÔNG HOÀN TÁC bị tool_node CHẶN (payload
    needs_confirmation) → dựng thẻ CÓ NÚT DUYỆT cho FE: 'draft' (gửi/trả lời — nút
    Niêm phong & Gửi) hoặc 'plan' (hàng loạt — nút Duyệt/Từ chối). Dựng TẤT ĐỊNH từ
    args tool (không nhờ LLM) → nội dung thẻ chính là thứ sẽ thực thi, không sai lệch.
    Trả None nếu lượt này không có tool nào bị chặn."""
    import json
    last_human = max((i for i, m in enumerate(messages)
                      if getattr(m, "type", None) == "human"), default=0)
    for m in reversed(messages[last_human:]):
        if getattr(m, "type", None) != "tool":
            continue
        try:
            data = json.loads(m.content)
        except Exception:
            continue
        if not (isinstance(data, dict) and data.get("needs_confirmation")):
            continue
        args = data.get("args") or {}
        name = getattr(m, "name", "")

        if name == "send_email":
            to = args.get("to") or []
            return {
                "kind": "draft",
                "intro": "Mình đã soạn xong — bạn xem lại rồi bấm gửi nhé:",
                "to": ", ".join(to) if isinstance(to, list) else str(to),
                "subject": args.get("subject") or "(không tiêu đề)",
                "body": args.get("body") or "",
            }
        if name == "reply_email":
            return {
                "kind": "draft",
                "intro": "Bản nháp trả lời đã sẵn sàng — bạn duyệt là mình gửi trong đúng luồng thư:",
                "to": "(người gửi thư gốc — trả lời trong luồng)",
                "subject": "Re: (thư gốc)",
                "body": args.get("instructions") or "",
                "replyToId": args.get("email_id") or "",
            }
        if name == "bulk_action":
            ids = [str(x) for x in (args.get("email_ids") or [])]
            act = str(args.get("action") or "").lower()
            op = None
            if "delete" in act:
                op = {"type": "delete", "ids": ids}
            elif "unread" in act:
                op = {"type": "markRead", "ids": ids, "read": False}
            elif "read" in act:
                op = {"type": "markRead", "ids": ids, "read": True}
            if op:
                verb = {"delete": "Xoá", "markRead": "Đánh dấu"}[op["type"]]
                card = {
                    "kind": "plan",
                    "intro": "Mình đã lên kế hoạch — bạn duyệt là chạy ngay:",
                    "steps": [f"Chọn {len(ids)} thư theo yêu cầu", f"{verb} {len(ids)} thư"],
                    "confirmLabel": f"{verb} {len(ids)} thư",
                    "op": op,
                }
                if op["type"] == "delete":
                    card["warn"] = "Xoá hàng loạt không hoàn tác được — kiểm tra kỹ trước khi duyệt."
                return card
        return None  # tool destructive khác: chưa có thẻ riêng → giữ câu trả lời của agent
    return None


def _preview_of(display_messages: list) -> str:
    """Vài chữ của TIN GẦN NHẤT (cho drawer xem lướt). Tin agent là thẻ → rút text/intro."""
    for m in reversed(display_messages or []):
        if m.get("role") == "user":
            return " ".join((m.get("text") or "").split())[:80]
        if m.get("role") == "agent":
            r = m.get("reply") or {}
            txt = r.get("text") or r.get("intro") or r.get("title") or ""
            if txt:
                return " ".join(txt.split())[:80]
    return ""


@app.post("/agent/chat")
async def agent_chat(
    payload: dict,
    bg: BackgroundTasks,                                  # sync nền sau lượt (Sent/Inbox cập nhật ngay)
    session: AuthSession = Depends(get_current_session),  # phải đăng nhập (agent đụng hộp thư thật)
    token: str = Depends(get_gmail_token),                # token còn hạn (tự refresh, đa provider)
    provider: str = Depends(get_provider),                # 'google'|'microsoft' → tool route Gmail/Outlook
    db: Session = Depends(get_db),                        # UC011: lưu/đọc lịch sử phiên
):
    from app.core.config import settings
    message = (payload or {}).get("message", "")
    incoming_id = (payload or {}).get("sessionId")  # id phiên FE gửi (None = phiên mới)

    # NFR-Reliability: chặn spam TRƯỚC MỌI THỨ (không tốn LLM/DB) — bảo vệ quota chung.
    if _rate_limited(session.user_id):
        return {"kind": "text", "conversationId": incoming_id,
                "text": ("🐢 Bạn đang gửi hơi nhanh — mình xin nghỉ vài giây để tiết kiệm "
                         "lượt gọi AI. Chờ chút rồi gửi lại giúp mình nhé.")}

    # NFR-Security: chặn prompt-injection NGAY (regex, không tốn LLM) trước khi vào graph.
    from app.agent.guardrails.input_guardrail import check_input
    blocked = check_input(message)
    if blocked:
        return {"kind": "text", "text": blocked, "conversationId": incoming_id}

    # FALLBACK: chưa cấu hình khoá LLM → trả lời lịch sự, KHÔNG làm sập gì.
    # Nhờ vậy app vẫn chạy đầy đủ kể cả khi chưa cắm Gemini (mọi nút bấm khác vô tư).
    if not settings.agent_enabled:
        return {
            "kind": "text",
            "text": (
                "🔑 Agent chưa được cấp khoá Gemini nên mình chưa “suy nghĩ” được.\n"
                "Thêm AI_API_KEY vào .env (lấy free ở aistudio.google.com) rồi khởi động lại "
                "là mình chạy thật ngay. Các tính năng bấm-nút khác vẫn dùng bình thường nhé."
            ),
        }

    # SUBSCRIPTION: chặn khi CHẠM trần token của gói (free/pro) — theo ngày HOẶC tháng.
    # Kiểm TRƯỚC khi gọi LLM (không đốt thêm token khi đã hết hạn mức). Chặn MỀM: báo lịch sự,
    # gợi ý nâng cấp; các nút bấm khác vẫn dùng bình thường.
    sub = subscription_repo.get_or_create(db, session.user_id)
    if subscription_repo.is_over_quota(db, sub):
        st = subscription_repo.status(db, sub)
        return {"kind": "text", "conversationId": incoming_id,
                "text": (f"🎟️ Bạn đã dùng hết hạn mức token gói “{sub.tier}” "
                         f"(ngày: {st['daily']['used']:,}/{st['daily']['limit']:,}). "
                         "Chờ sang kỳ mới hoặc nâng cấp gói để tiếp tục dùng trợ lý AI. "
                         "Các thao tác bấm-nút (đọc/gắn nhãn/gửi qua nút) vẫn dùng bình thường.")}

    # CHẠY AGENT — lazy-import bên trong + bọc try/except để lỗi LLM/tool KHÔNG thành 500,
    # mà báo nhẹ nhàng (giữ trải nghiệm mượt + an toàn).
    conv = None  # bind trước try: except cần biết phiên đã tạo chưa (trả đúng conversationId)
    try:
        from langchain_core.messages import HumanMessage, messages_to_dict, messages_from_dict
        from app.agent.graph import build_graph
        from app.agent.skills.skill_loader import load_skills
        from app.tools.registry import RequestContext

        global _AGENT_GRAPH
        if _AGENT_GRAPH is None:
            _AGENT_GRAPH = build_graph()  # dựng + compile graph 1 lần duy nhất

        # UC011: lấy/tạo phiên trong DB rồi NẠP LẠI ngữ cảnh LangChain đã lưu (agent NHỚ).
        conv = conversation_repo.get_or_create(db, incoming_id, session.user_id)
        history = messages_from_dict(conv.agent_messages) if conv.agent_messages else []

        # RequestContext = "thẻ ra vào" bơm xuống mọi tool: ai gọi + token nào để đụng Gmail.
        ctx = RequestContext(
            user_id=str(session.user_id),
            access_token=token,
            email_provider=provider,   # tool trong graph route đúng Gmail/Outlook theo phiên
            conversation_id=conv.id,
        )
        # State khởi đầu: lịch sử cũ + tin mới → agent thấy CẢ hội thoại (luồng hỏi-xác-nhận → gửi…).
        init_state = {
            "messages": [*history, HumanMessage(content=message)],
            "request_ctx": ctx,
            "skill_context": load_skills(message),  # nạp kỹ năng khớp ngữ cảnh
            "pending_confirmation": None,
            "iteration_count": 0,
            "final_output": None,
        }
        # Graph lo TỪ A-Z: agent (nghĩ) ↔ tools (chạy) → responder (ép thẻ) hoặc dừng (thuần text).
        result = await _AGENT_GRAPH.ainvoke(init_state)

        # SUBSCRIPTION: cộng token đã tiêu của lượt này vào hạn mức ngày/tháng.
        try:
            subscription_repo.add_usage(db, sub, _turn_tokens(result.get("messages") or []))
        except Exception:
            pass  # đo/ghi token hỏng KHÔNG được làm sập câu trả lời

        # Agent có thể vừa gửi/xoá/gắn nhãn → sync nền để Hộp thư/Đã gửi trong web cập nhật NGAY
        # (không chờ Pub/Sub). incremental_sync nhẹ (history.list + fetch phần đổi).
        if settings.mailbox_store_enabled:
            bg.add_task(_bg_sync, session.user_id, provider, token)

        # responder_node (khi có dữ liệu tool) đóng gói sẵn AgentReply vào final_output (thẻ FE).
        out = result.get("final_output")
        if not out:
            # Lượt thuần văn bản (graph đi thẳng END, bỏ responder để tiết kiệm) → lấy câu trả lời
            # cuối của agent làm thẻ 'text'. Chào hỏi/hỏi-xác-nhận vẫn hiện đúng, KHÔNG tốn LLM lần 2.
            from app.agent.nodes.agent_node import coerce_text
            last_ai = next((m for m in reversed(result["messages"])
                            if getattr(m, "type", None) == "ai" and getattr(m, "content", None)), None)
            # coerce_text: content có thể là LIST part (tuỳ model Gemini) → ép về chuỗi chuẩn cho FE.
            last_text = coerce_text(last_ai.content).strip() if last_ai else ""
            out = {"kind": "text", "text": last_text or "Mình đã xử lý xong."}

        # UC009: nếu lượt này có gọi categorize_emails → ÉP thành thẻ 'categorize' (widget FE cho
        # sửa nhãn từng thư rồi Áp dụng). Xây TẤT ĐỊNH từ dữ liệu tool (id + nhãn), KHÔNG nhờ LLM
        # → nhãn/ id luôn chuẩn. Đặt TRƯỚC phần đính emails để không lẫn 2 loại thẻ.
        cat_card = _categorize_card(result["messages"])
        if cat_card:
            out = cat_card

        # HUMAN-IN-THE-LOOP: lượt này có tool không-hoàn-tác bị CHẶN chờ duyệt →
        # thẻ draft/plan CÓ NÚT thắng mọi thẻ khác (người dùng phải thấy nút duyệt,
        # không phải câu chữ của LLM).
        confirm_card = _confirm_card(result["messages"])
        if confirm_card:
            out = confirm_card

        # UI/UX: đính danh sách thư THẬT (bấm mở được) từ search_emails CỦA LƯỢT NÀY → FE render
        # thẻ clickable. Lưu luôn vào display_messages nên phiên cũ mở lại vẫn bấm được.
        # Chỉ đính cho kind 'text'/'result' — 2 kind FE có render danh sách này (digest/triage
        # có widget riêng, đính thêm chỉ phình payload + DB vô ích).
        ref_emails = _emails_from_search(result["messages"]) if out.get("kind") in ("text", "result") else []
        if ref_emails:
            # KHỚP số thẻ với số mục LLM ĐÃ trình bày: user xin "5 thư" → responder liệt kê 5 dòng →
            # chỉ hiện 5 thẻ (đừng đổ hết kết quả tool ra, kẻo "liệt kê 5" lại hiện 10-15).
            if out.get("kind") == "result" and out.get("lines"):
                ref_emails = ref_emails[: len(out["lines"])]
            else:
                ref_emails = ref_emails[:8]
            out = {**out, "emails": ref_emails}

        # UC011: LƯU lượt này — ngữ cảnh agent (để nghĩ tiếp) + lịch sử FE (để vẽ lại thẻ).
        # _compact_tools: cắt bớt JSON email thô trước khi cất → NFR-Memory (đỡ phình token lượt sau).
        agent_dump = messages_to_dict(_compact_tools(_trim_history(result["messages"])))
        display = list(conv.display_messages or [])
        display.append({"role": "user", "text": message})
        display.append({"role": "agent", "reply": out})
        conversation_repo.save_turn(db, conv, agent_dump, display, first_user_text=message)

        # Trả AgentReply kèm conversationId để FE biết phiên nào (nhất là khi phiên VỪA tạo).
        return {**out, "conversationId": conv.id}
    except Exception as exc:
        # Lỗi bất ngờ (mạng/LLM/tool) → vẫn trả AgentReply hợp lệ, không vỡ FE.
        # PHÂN LOẠI để báo đúng bệnh thay vì ném stack-trace khó hiểu cho người dùng:
        text = str(exc)
        low = text.lower()
        if "resource_exhausted" in low or "429" in text or "quota" in low:
            # Quota Gemini free hết (theo phút hoặc theo ngày). max_retries=6 đã tự thử lại các
            # lỗi chớp nhoáng; tới đây là hết lượt thật → khuyên người dùng cách xử lý.
            msg = ("🚦 Gemini đã hết lượt miễn phí (quota) lúc này. Chờ ít phút rồi thử lại, "
                   "hoặc đổi sang model nhẹ hơn (gemini-2.5-flash-lite) / cấp khoá có quota cao hơn. "
                   "Các thao tác bấm-nút (đọc/gắn nhãn/gửi qua nút) vẫn dùng bình thường nhé.")
        elif "503" in text or "unavailable" in low or "overloaded" in low or "high demand" in low:
            # Google báo model quá tải NHẤT THỜI (503). max_retries đã thử lại vài lần vẫn kẹt →
            # khuyên chờ chút. Khác quota: đây là phía Google đông, không phải mình hết lượt.
            msg = ("⏳ Mô hình AI của Google đang quá tải nhất thời (lỗi 503). Đây thường chỉ thoáng qua — "
                   "bạn thử lại sau vài giây nhé. Nếu lặp lại nhiều, đổi model (gemini-2.5-flash) cũng đỡ. "
                   "Các thao tác bấm-nút vẫn dùng bình thường.")
        elif "permission" in low or "403" in text or "invalid_grant" in low or "unauthorized" in low:
            msg = ("🔑 Phiên Gmail có thể đã hết hạn hoặc thiếu quyền. Bạn đăng xuất rồi đăng nhập "
                   "lại bằng Google để cấp quyền mới giúp mình nhé.")
        elif "tool_use_failed" in low or "failed to call a function" in low or "failed_generation" in low:
            # Model (thường Llama-trên-Groq) sinh cú gọi tool SAI cú pháp → nhà cung cấp
            # từ chối. Là lỗi CHẤT LƯỢNG MODEL, không phải hộp thư. Thử lại thường qua
            # (do lấy mẫu ngẫu nhiên); dai dẳng thì đổi model tool tốt hơn / hạ nhiệt độ.
            msg = ("🤖 Model AI vừa tạo lệnh gọi công cụ chưa đúng chuẩn (hay gặp với Llama trên "
                   "Groq). Bạn thử gửi lại — thường lần sau là được. Nếu lặp nhiều, đổi sang "
                   "model gọi-tool ổn hơn (vd llama-3.3-70b-versatile) hoặc đặt AGENT_TEMPERATURE=0.")
        else:
            msg = f"Xin lỗi, agent đang gặp trục trặc: {exc}"

        # UC011: phiên đã được tạo TRƯỚC khi graph chạy → phải trả ĐÚNG id + LƯU lượt lỗi vào
        # lịch sử. Nếu trả None như trước: FE không bám phiên → mỗi lần lỗi đẻ thêm 1 dòng
        # "Cuộc trò chuyện mới" RỖNG trong drawer, còn tin nhắn của user thì bốc hơi.
        err_reply = {"kind": "text", "text": msg}
        if conv is not None:
            try:
                display = list(conv.display_messages or [])
                display.append({"role": "user", "text": message})
                display.append({"role": "agent", "reply": err_reply})
                conversation_repo.save_turn(db, conv, list(conv.agent_messages or []),
                                            display, first_user_text=message)
            except Exception:
                pass  # lưu lỗi thất bại thì thôi — ưu tiên vẫn trả reply hợp lệ cho FE
        return {**err_reply, "conversationId": conv.id if conv is not None else incoming_id}


# ── UC011: QUẢN LÝ LỊCH SỬ HỘI THOẠI ────────────────────────────────
# Drawer lịch sử của FE đọc/sửa qua 4 endpoint dưới. Tất cả CHỈ đụng phiên của CHÍNH user
# (get_owned chặn xem chéo). Phiên được tạo ngầm khi chat (/agent/chat), nên ở đây không có POST tạo.

def _summary_of(c: Conversation) -> ConversationSummary:
    return ConversationSummary(
        id=c.id, title=c.title, pinned=c.pinned, updatedAt=c.updated_at,
        messageCount=len(c.display_messages or []),
        preview=_preview_of(c.display_messages or []),
    )


@app.get("/agent/conversations", response_model=list[ConversationSummary])
def list_conversations(
    session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)
):
    """Liệt kê phiên chat của user (ghim trước, mới-nhất-trước) cho drawer lịch sử."""
    return [_summary_of(c) for c in conversation_repo.list_for_user(db, session.user_id)]


@app.get("/agent/conversations/{conv_id}", response_model=ConversationDetail)
def get_conversation(
    conv_id: str,
    session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db),
):
    """Mở 1 phiên: trả display_messages để FE vẽ lại lịch sử (Xem / Tiếp tục)."""
    c = conversation_repo.get_owned(db, conv_id, session.user_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại.")
    return ConversationDetail(
        id=c.id, title=c.title, pinned=c.pinned,
        createdAt=c.created_at, updatedAt=c.updated_at,
        messages=c.display_messages or [],
    )


@app.patch("/agent/conversations/{conv_id}", response_model=ConversationSummary)
def update_conversation(
    conv_id: str, req: UpdateConversationReq,
    session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db),
):
    """Đổi tên và/hoặc ghim một phiên (chỉ gửi field cần đổi)."""
    c = conversation_repo.get_owned(db, conv_id, session.user_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại.")
    if req.title is not None:
        conversation_repo.rename(db, c, req.title)
    if req.pinned is not None:
        conversation_repo.set_pinned(db, c, req.pinned)
    return _summary_of(c)


@app.delete("/agent/conversations/{conv_id}", status_code=204)
def delete_conversation(
    conv_id: str,
    session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db),
):
    """Xoá một phiên (drawer có xác nhận trước khi gọi)."""
    c = conversation_repo.get_owned(db, conv_id, session.user_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hội thoại.")
    conversation_repo.delete(db, c)
    return Response(status_code=204)


# ── Nấc 10: THỰC THI SAU DUYỆT (cầu nối agent ↔ service) ──────────────
# Khép kín human-in-the-loop: agent trả 'plan'/'autopilot' → user Approve →
# FE gọi 2 endpoint dưới để CHẠY THẬT qua cùng lớp gmail_actions.
# KHÔNG có LLM ở đây — chỉ nhận hành động ĐÃ DUYỆT rồi thực thi (phần của BE).

@app.post("/agent/plan/execute", response_model=ExecuteResult)
def execute_plan(req: ExecutePlanReq, token: str = Depends(get_gmail_token)):
    """Chạy 1 PlanOp đã được user Approve, trả câu tóm tắt 'done' cho FE hiển thị."""
    op = req.op
    if op.type == "archive":
        n = _guard(lambda: gmail_actions.modify_labels(token, op.ids, remove=["INBOX"]))
        done = f"Đã lưu trữ {n} thư."
    elif op.type == "delete":
        n = _guard(lambda: gmail_actions.trash(token, op.ids))
        done = f"Đã chuyển {n} thư vào thùng rác."
    elif op.type == "markRead":
        if op.read:
            n = _guard(lambda: gmail_actions.modify_labels(token, op.ids, remove=["UNREAD"]))
            done = f"Đã đánh dấu {n} thư là đã đọc."
        else:
            n = _guard(lambda: gmail_actions.modify_labels(token, op.ids, add=["UNREAD"]))
            done = f"Đã đánh dấu {n} thư là chưa đọc."
    elif op.type == "label":
        n = _guard(lambda: gmail_actions.apply_label(token, op.ids, op.label))
        done = f"Đã gắn nhãn “{op.label}” cho {n} thư."
    else:  # autoLabel — mỗi thư một nhãn riêng (gán `it=it` để lambda khỏi dính biến vòng lặp)
        total = 0
        for it in op.items:
            total += _guard(lambda it=it: gmail_actions.apply_label(token, [it.id], it.label))
        done = f"Đã gắn nhãn cho {total} thư."
    return ExecuteResult(done=done)


@app.post("/agent/autopilot/apply", response_model=OkResult)
def autopilot_apply(req: AutopilotApplyReq, token: str = Depends(get_gmail_token)):
    """Áp dụng lô hành động tự-lái đã duyệt (UC017): lưu trữ + đánh dấu đọc + gắn sao."""
    if req.archive:
        _guard(lambda: gmail_actions.modify_labels(token, req.archive, remove=["INBOX"]))
    if req.markRead:
        _guard(lambda: gmail_actions.modify_labels(token, req.markRead, remove=["UNREAD"]))
    if req.flag:
        _guard(lambda: gmail_actions.modify_labels(token, req.flag, add=["STARRED"]))
    return OkResult()


# ── Nấc 3: chạm database lần đầu (DEV — để THẤY DB chạy) ──────────────
# Đây là endpoint TẠM cho việc học (chưa phải đăng nhập thật). Mục đích:
# tạo & xem User trong DB, hiểu vòng route → repo → database.
# `db: Session = Depends(get_db)` → FastAPI tự mở 1 phiên DB, đưa vào, đóng sau.
@app.post("/dev/users", response_model=UserOut)
def dev_create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # get_or_create: có email rồi thì lấy lại, chưa có thì tạo (mẫu khi đăng nhập).
    return user_repo.get_or_create_user(db, payload.email, payload.name, payload.initial)


@app.get("/dev/users", response_model=list[UserOut])
def dev_list_users(db: Session = Depends(get_db)):
    return user_repo.list_users(db)


# ── Nấc 4b: gắn router đăng nhập + endpoint /me ──────────────────────
app.include_router(auth_routes.router)  # thêm /auth/google/start, /callback, /auth/logout


@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Trả thông tin user của phiên hiện tại.
    `Depends(get_current_user)` = "cửa có bảo vệ": chưa đăng nhập → tự động 401."""
    return current_user


# ── Gửi tệp đính kèm: nhận FILE upload từ frontend (multipart/form-data) ──
# `file: UploadFile = File(...)` → FastAPI đọc tệp từ form-data (cần python-multipart).
# Nấc 8: GIỮ CẢ BYTES trong upload_store → khi bấm Gửi sẽ lấy ra đính vào email.
@app.post("/uploads")
async def upload_file(
    file: UploadFile = File(...),
    session: AuthSession = Depends(get_current_session),  # cần đăng nhập mới được upload
):
    content = await file.read()  # đọc toàn bộ nội dung tệp (dạng bytes)
    # NFR-Memory/Security: chặn tệp quá trần — không giới hạn thì 1 tệp 2GB = 2GB RAM (DoS).
    from app.core.config import settings
    if len(content) > settings.upload_max_mb * 1024 * 1024:
        raise HTTPException(status_code=413,
                            detail=f"Tệp vượt quá {settings.upload_max_mb}MB cho phép.")
    # Cất vào kho tạm; trả {id, name, size} để FE GIỮ `id` rồi gửi kèm khi soạn xong.
    return upload_store.save(file.filename or "tep", content, file.content_type)
