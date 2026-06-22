# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/app.py — TRÁI TIM của server (Nấc 0)                        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: tạo ra "ứng dụng web" và khai báo vài ROUTE đầu tiên.     ║
# ║ AI GỌI: Frontend (hoặc trình duyệt) gửi request HTTP tới đây.       ║
# ║ Ở nấc này chưa có Gmail/đăng nhập — chỉ để bạn THẤY server chạy.    ║
# ╚══════════════════════════════════════════════════════════════════╝

# Nhập lớp FastAPI từ thư viện fastapi. Đây là "bộ khung" lo hết phần
# khó của web (nhận request, parse, trả JSON, sinh tài liệu...).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # cho phép FE gọi sang (xem CORS bên dưới)

from app.services.email_service import list_emails  # logic lấy email (tầng service)

# --- Nấc 3: database (ORM) ---
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import Base, engine, get_db
from app.models.user import User  # noqa: F401 — phải import để create_all "thấy" bảng users
from app.models.session import AuthSession  # noqa: F401 — để create_all tạo cả bảng sessions
from app.repo import user_repo
from app.schemas.user import UserCreate, UserOut

# --- Nấc 4b: đăng nhập ---
from app.core.deps import get_current_user, get_current_session
from app.services import gmail_service
from app.api import auth as auth_routes

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


# ── Nấc 2a: list email (DỮ LIỆU GIẢ) ─────────────────────────────────
# Khớp hợp đồng docs/interface/02: GET /emails?folder=inbox → { items: Email[] }
# `folder: str = "inbox"` → FastAPI tự đọc query param ?folder=... (mặc định inbox).
@app.get("/emails")
def get_emails(
    folder: str = "inbox",
    q: str | None = None,  # UC005: từ khoá tìm kiếm (FE gửi qua ?q=...)
    session: AuthSession = Depends(get_current_session),
):
    # Đọc Gmail THẬT. Cần ĐÃ ĐĂNG NHẬP (lấy session → có google_access_token).
    if not session.google_access_token:
        return {"items": [], "nextCursor": None, "criteria": []}
    if q:  # có từ khoá → TÌM KIẾM trên toàn hộp thư (UC005)
        items = gmail_service.list_messages(session.google_access_token, q=q)
    else:  # nạp theo thư mục đang chọn (inbox/sent/drafts/trash/starred/archive)
        items = gmail_service.list_messages(session.google_access_token, folder=folder)
    return {"items": items, "nextCursor": None, "criteria": []}


# ── Nấc 5b: xem CHI TIẾT 1 thư (UC004) — thân thư đầy đủ + đính kèm ──
@app.get("/emails/{email_id}")
def get_email(email_id: str, session: AuthSession = Depends(get_current_session)):
    if not session.google_access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa cấp quyền Gmail")
    return gmail_service.get_message(session.google_access_token, email_id)


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
