# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/deps.py — "BẢO VỆ CỬA": ai đang gọi API? (tầng core/)    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ get_current_user là một DEPENDENCY: gắn vào endpoint nào thì endpoint║
# ║ đó yêu cầu ĐÃ ĐĂNG NHẬP. Nó đọc token (từ cookie hoặc header), kiểm  ║
# ║ tra phiên, trả về User — hoặc ném 401 nếu chưa/đã hết hạn.         ║
# ╚══════════════════════════════════════════════════════════════════╝

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.session import AuthSession
from app.repo import session_repo

COOKIE_NAME = "meoarc_session"  # tên cookie giữ token phiên


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
