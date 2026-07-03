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
from app.models.user import User  # noqa: F401 — phải import để create_all "thấy" bảng users
from app.models.session import AuthSession  # noqa: F401 — để create_all tạo cả bảng sessions
from app.models.conversation import Conversation  # noqa: F401 — UC011: tạo bảng conversations
from app.repo import user_repo, conversation_repo
from app.schemas.user import UserCreate, UserOut
from app.schemas.conversation import ConversationSummary, ConversationDetail, UpdateConversationReq

# --- Nấc 4b: đăng nhập ---
from app.core.deps import get_current_user, get_current_session, get_gmail_token
from app.services import gmail_service
from app.api import auth as auth_routes

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
):
    items, next_cursor = gmail_service.list_messages(
        token, folder=folder, q=q, unread=unread, starred=starred,
        attachment=attachment, page_token=cursor, max_results=limit, bypass_cache=fresh,
    )
    return {"items": items, "nextCursor": next_cursor, "criteria": []}


# ── Nấc 5b: xem CHI TIẾT 1 thư (UC004) — thân thư đầy đủ + đính kèm ──
@app.get("/emails/{email_id}")
def get_email(email_id: str, token: str = Depends(get_gmail_token)):
    return gmail_service.get_message(token, email_id)


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


@app.post("/emails/actions/read", response_model=ActionResult)
def action_read(req: ReadReq, token: str = Depends(get_gmail_token)):
    """Đánh dấu đã/chưa đọc. Đã đọc = BỚT nhãn UNREAD; chưa đọc = THÊM UNREAD."""
    if req.read:
        return _write(lambda: gmail_actions.modify_labels(token, req.ids, remove=["UNREAD"]))
    return _write(lambda: gmail_actions.modify_labels(token, req.ids, add=["UNREAD"]))


@app.post("/emails/actions/important", response_model=ActionResult)
def action_important(req: ImportantReq, token: str = Depends(get_gmail_token)):
    """Gắn/bỏ sao. value=True → THÊM nhãn STARRED; value=False → BỚT STARRED."""
    if req.value:
        return _write(lambda: gmail_actions.modify_labels(token, req.ids, add=["STARRED"]))
    return _write(lambda: gmail_actions.modify_labels(token, req.ids, remove=["STARRED"]))


@app.post("/emails/actions/archive", response_model=ActionResult)
def action_archive(req: IdsReq, token: str = Depends(get_gmail_token)):
    """Lưu trữ = BỚT nhãn INBOX → thư rời 'Hộp thư đến' nhưng vẫn còn trong 'Tất cả thư'."""
    return _write(lambda: gmail_actions.modify_labels(token, req.ids, remove=["INBOX"]))


@app.post("/emails/actions/delete", response_model=ActionResult)
def action_delete(req: IdsReq, token: str = Depends(get_gmail_token)):
    """Xoá = chuyển vào THÙNG RÁC (xoá mềm, khôi phục được). Không xoá vĩnh viễn (an toàn)."""
    return _write(lambda: gmail_actions.trash(token, req.ids))


@app.post("/emails/actions/label", response_model=ActionResult)
def action_label(req: LabelReq, token: str = Depends(get_gmail_token)):
    """Gắn NHÃN cho thư (UC006). BE tự tạo nhãn Gmail nếu chưa có rồi gắn vào từng thư."""
    return _write(lambda: gmail_actions.apply_label(token, req.ids, req.label))


@app.post("/emails/{email_id}/read", response_model=ActionResult)
def mark_read_one(email_id: str, req: ReadOneReq, token: str = Depends(get_gmail_token)):
    """Đánh dấu MỘT thư đã/chưa đọc — FE gọi khi MỞ thư (UC004)."""
    if req.read:
        return _write(lambda: gmail_actions.modify_labels(token, [email_id], remove=["UNREAD"]))
    return _write(lambda: gmail_actions.modify_labels(token, [email_id], add=["UNREAD"]))


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
def send_email_route(req: SendReq, token: str = Depends(get_gmail_token)):
    """Soạn & gửi thư mới (kèm tệp). Body khớp `SendEmailInput` của FE + attachmentIds."""
    # Đổi danh sách id tệp → nội dung thật (bytes) đã cất ở /uploads. Id không tồn tại → bỏ qua.
    attachments = [
        {"name": f["name"], "content": f["content"], "mime": f["mime"]}
        for fid in (req.attachmentIds or [])
        if (f := upload_store.get(fid))
    ]
    res = _guard(lambda: gmail_send.send_email(
        token, req.to, req.subject, req.body, cc=req.cc, bcc=req.bcc, attachments=attachments,
    ))
    return SendResult(id=res.get("id", ""), threadId=res.get("threadId"))


@app.post("/emails/{email_id}/reply", response_model=SendResult)
def reply_email_route(email_id: str, req: ReplyReq, token: str = Depends(get_gmail_token)):
    """Trả lời thư email_id: BE tự suy người nhận/tiêu đề/luồng từ thư gốc, chỉ cần `body`."""
    res = _guard(lambda: gmail_send.reply_email(token, email_id, req.body))
    return SendResult(id=res.get("id", ""), threadId=res.get("threadId"))


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
    session: AuthSession = Depends(get_current_session),  # phải đăng nhập (agent đụng hộp thư thật)
    token: str = Depends(get_gmail_token),                # token Gmail còn hạn (tự refresh)
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
            email_provider="gmail",
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
