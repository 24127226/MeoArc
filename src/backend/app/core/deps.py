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
from app.repo import session_repo, connected_account_repo
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
    acc = connected_account_repo.primary_for(db, session.user_id)

    # Giai đoạn chuyển tiếp: bản ghi kết nối là NGUỒN CHÍNH, phiên chỉ là đường lùi cho
    # phiên cũ chưa kịp chuyển. Đọc một nơi, ghi một nơi — nếu đọc chỗ này mà làm mới
    # chỗ kia thì hai bản token lệch nhau và lỗi chỉ hiện ra sau vài giờ.
    if acc is not None:
        token = acc.access_token
        han = acc.token_expiry
        refresh = acc.refresh_token
        provider = acc.provider
    else:
        token = session.google_access_token
        han = session.google_token_expiry
        refresh = session.google_refresh_token
        provider = session_repo.get_provider(db, session.token)

    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa cấp quyền Gmail — hãy đăng nhập.")

    # Còn hạn (chừa 60s an toàn) → dùng luôn, khỏi gọi mạng.
    if han and han > _utcnow() + timedelta(seconds=60):
        return token

    # Hết/sắp hết hạn + có refresh_token → xin token mới rồi lưu lại.
    # ĐA PROVIDER: hộp thư Microsoft làm mới qua endpoint Microsoft; Google giữ NGUYÊN.
    if refresh:
        try:
            if provider == "microsoft":
                from app.services import auth_service_ms
                new_token, expires_in = auth_service_ms.refresh_access_token(refresh)
            else:
                new_token, expires_in = auth_service.refresh_access_token(refresh)
            if acc is not None:
                connected_account_repo.update_access_token(
                    db, acc, new_token, _utcnow() + timedelta(seconds=int(expires_in or 3600)))
            else:
                session_repo.update_access_token(db, session, new_token, expires_in)
            return new_token
        except Exception:
            # Làm mới lỗi (refresh_token bị thu hồi...) → trả token cũ; Gmail có thể 403 →
            # FE sẽ thấy lỗi và bảo người dùng đăng nhập lại. Không làm sập request ở đây.
            return token

    return token  # không có refresh_token → đành dùng token hiện có (có thể đã hết hạn)


def get_provider(
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> str:
    """Nhà cung cấp của hộp thư đang dùng: 'google' | 'microsoft'. Endpoint dùng để
    định tuyến gọi Gmail hay Outlook (qua app.services.mail).

    Lấy theo KẾT NỐI chứ không theo phiên: một người có thể nối cả hai hộp thư, lúc đó
    "nhà cung cấp của phiên đăng nhập" không còn là câu hỏi có nghĩa."""
    acc = connected_account_repo.primary_for(db, session.user_id)
    if acc is not None:
        return acc.provider
    return session_repo.get_provider(db, session.token)
