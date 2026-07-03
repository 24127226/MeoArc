# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/session_repo.py — TRUY VẤN bảng sessions (tầng repo/)    ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.session import AuthSession
from app.core.security import generate_token


def _utcnow() -> datetime:
    # Giờ UTC dạng "naive" (không kèm tzinfo) để SO SÁNH nhất quán với giá trị
    # đọc ra từ SQLite. (Học thì làm vậy cho gọn; dự án lớn nên dùng cột có timezone.)
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_session(
    db: Session,
    user_id: int,
    ttl_hours: int,
    google_access_token: str | None = None,
    google_refresh_token: str | None = None,
    access_expires_in: int = 3600,
) -> AuthSession:
    s = AuthSession(
        token=generate_token(),
        user_id=user_id,
        expires_at=_utcnow() + timedelta(hours=ttl_hours),
        google_access_token=google_access_token,
        google_refresh_token=google_refresh_token,
        # Mốc hết hạn access_token = bây giờ + số giây Google báo (mặc định 3600 = 1h).
        google_token_expiry=_utcnow() + timedelta(seconds=access_expires_in),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def update_access_token(
    db: Session, session: AuthSession, access_token: str, expires_in: int
) -> AuthSession:
    """Cập nhật access_token MỚI (sau khi làm mới) + dời mốc hết hạn. Nấc 9."""
    session.google_access_token = access_token
    session.google_token_expiry = _utcnow() + timedelta(seconds=expires_in)
    db.commit()
    db.refresh(session)
    return session


def get_valid_session(db: Session, token: str) -> AuthSession | None:
    s = db.get(AuthSession, token)        # tra theo khoá chính (token)
    if s is None or s.expires_at < _utcnow():  # không có HOẶC đã hết hạn
        return None
    return s


def delete_session(db: Session, token: str) -> None:
    s = db.get(AuthSession, token)
    if s:
        db.delete(s)   # đăng xuất = xoá dòng phiên
        db.commit()
