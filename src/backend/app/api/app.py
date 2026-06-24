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
from app.repo import user_repo
from app.schemas.user import UserCreate, UserOut

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

# Tạo đối tượng ứng dụng. title/description/version sẽ HIỆN trên trang
# tài liệu tự sinh tại /docs — nên đặt cho rõ để dễ đọc khi demo.
app = FastAPI(
    title="MeoArc Backend (sandbox)",
    description="Server học việc — nấc 0: làm cho FastAPI chạy được.",
    version="0.1.0",
)

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


# Route thứ hai: /health — quy ước phổ biến để kiểm tra "server còn sống không".
# Các hệ thống giám sát/deploy hay gọi route này để biết app ổn định.
@app.get("/health")
async def health():
    return {"status": "ok"}


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


# ── Nấc 2b: agent chat (BẢN MẪU) ─────────────────────────────────────
# FE gọi POST /agent/chat (qua api.sendAgentMessage). Nấc này CHỈ trả lời
# mẫu để bạn THẤY vòng FE↔BE chạy thật. Agent Gemini sẽ thay ruột sau.
# `payload: dict` → FastAPI tự parse body JSON ({ message, viaVoice }) thành dict.
@app.post("/agent/chat")
async def agent_chat(payload: dict):
    message = payload.get("message", "")
    # Trả về đúng dạng AgentReply kind "text" (xem docs/interface/01) → FE vẽ được.
    return {
        "kind": "text",
        "text": f"Backend FastAPI đã nhận: “{message}”. (Phản hồi mẫu — agent thật sẽ thay sau.)",
    }


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
    # Cất vào kho tạm; trả {id, name, size} để FE GIỮ `id` rồi gửi kèm khi soạn xong.
    return upload_store.save(file.filename or "tep", content, file.content_type)
