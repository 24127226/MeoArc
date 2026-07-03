# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/deps.py — "BẢO VỆ CỬA": ai đang gọi API? (tầng core/)    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ get_current_user là một DEPENDENCY: gắn vào endpoint nào thì endpoint║
# ║ đó yêu cầu ĐÃ ĐĂNG NHẬP. Nó đọc token (từ cookie hoặc header), kiểm  ║
# ║ tra phiên, trả về User — hoặc ném 401 nếu chưa/đã hết hạn.         ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.session import AuthSession
from app.repo import session_repo
from app.services import auth_service

COOKIE_NAME = "meoarc_session"  # tên cookie giữ token phiên


def _utcnow() -> datetime:
    # Giờ UTC "naive" — khớp cách lưu mốc hết hạn trong session_repo (so sánh nhất quán).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _read_token(request: Request) -> str | None:
    # Ưu tiên cookie (trình duyệt tự gửi); nếu không có thì thử header
    # "Authorization: Bearer <token>" (dành cho API client gọi bằng fetch).
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
    return token


def get_current_session(request: Request, db: Session = Depends(get_db)) -> AuthSession:
    """Trả PHIÊN hiện tại (bên trong có google_access_token để gọi Gmail)."""
    token = _read_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập")
    session = session_repo.get_valid_session(db, token)
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên không hợp lệ hoặc đã hết hạn")
    return session


def get_current_user(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> User:
    # Tái dùng get_current_session ở trên → khỏi lặp code đọc token.
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại")
    return user


def get_gmail_token(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> str:
    """Nấc 9 — trả về access_token Gmail CÒN HẠN, TỰ làm mới nếu sắp/đã hết hạn.
    Mọi endpoint gọi Gmail dùng `Depends(get_gmail_token)` thay vì tự đọc session
    → không còn cảnh '1 tiếng phải đăng nhập lại'.
    """
    token = session.google_access_token
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa cấp quyền Gmail — hãy đăng nhập.")

    # Còn hạn (chừa 60s an toàn) → dùng luôn, khỏi gọi mạng.
    if session.google_token_expiry and session.google_token_expiry > _utcnow() + timedelta(seconds=60):
        return token

    # Hết/sắp hết hạn + có refresh_token → xin token mới rồi lưu lại.
    if session.google_refresh_token:
        try:
            new_token, expires_in = auth_service.refresh_access_token(session.google_refresh_token)
            session_repo.update_access_token(db, session, new_token, expires_in)
            return new_token
        except Exception:
            # Làm mới lỗi (refresh_token bị thu hồi...) → trả token cũ; Gmail có thể 403 →
            # FE sẽ thấy lỗi và bảo người dùng đăng nhập lại. Không làm sập request ở đây.
            return token

    return token  # không có refresh_token → đành dùng token hiện có (có thể đã hết hạn)
