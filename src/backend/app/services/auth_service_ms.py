# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/auth_service_ms.py — ĐĂNG NHẬP MICROSOFT (Outlook)    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Song song với auth_service.py (Google) — KHÔNG đụng luồng Gmail.    ║
# ║ Dựng URL đăng nhập Microsoft → đổi code lấy token → lấy hồ sơ qua   ║
# ║ Graph /me → get-or-create user + tạo phiên (đánh dấu provider=      ║
# ║ microsoft). Token MS cất chung cột google_* của bảng sessions       ║
# ║ (chỉ là chuỗi mã hoá; provider quyết định gọi Gmail hay Graph).     ║
# ╚══════════════════════════════════════════════════════════════════╝

from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.repo import user_repo, session_repo

_AUTHORITY = "https://login.microsoftonline.com"
GRAPH_ME = "https://graph.microsoft.com/v1.0/me"

# Quyền: đăng nhập + đọc/ghi + gửi thư Outlook. offline_access = xin refresh_token.
_SCOPE = (
    "openid email profile offline_access"
    " https://graph.microsoft.com/Mail.ReadWrite"
    " https://graph.microsoft.com/Mail.Send"
)


def _auth_url() -> str:
    return f"{_AUTHORITY}/{settings.ms_tenant}/oauth2/v2.0/authorize"


def _token_url() -> str:
    return f"{_AUTHORITY}/{settings.ms_tenant}/oauth2/v2.0/token"


def build_ms_auth_url() -> str:
    params = {
        "client_id": settings.ms_client_id,
        "redirect_uri": settings.ms_redirect_uri,
        "response_type": "code",
        "response_mode": "query",
        "scope": _SCOPE,
        "prompt": "select_account",
    }
    return f"{_auth_url()}?{urlencode(params)}"


def _exchange_and_fetch(code: str) -> tuple[str, str | None, int, dict]:
    """Đổi code → token, rồi Graph /me lấy hồ sơ. Trả (access, refresh, expires_in, hồ_sơ)."""
    with httpx.Client(timeout=10) as client:
        tr = client.post(_token_url(), data={
            "code": code,
            "client_id": settings.ms_client_id,
            "client_secret": settings.ms_client_secret,
            "redirect_uri": settings.ms_redirect_uri,
            "grant_type": "authorization_code",
            "scope": _SCOPE,
        })
        tr.raise_for_status()
        tok = tr.json()
        access = tok["access_token"]
        refresh = tok.get("refresh_token")
        expires_in = tok.get("expires_in", 3600)

        me = client.get(GRAPH_ME, headers={"Authorization": f"Bearer {access}"})
        me.raise_for_status()
        return access, refresh, expires_in, me.json()


def refresh_access_token(refresh_token: str) -> tuple[str, int]:
    """Gia hạn access_token MS bằng refresh_token (không bắt đăng nhập lại)."""
    with httpx.Client(timeout=10) as client:
        r = client.post(_token_url(), data={
            "refresh_token": refresh_token,
            "client_id": settings.ms_client_id,
            "client_secret": settings.ms_client_secret,
            "grant_type": "refresh_token",
            "scope": _SCOPE,
        })
        r.raise_for_status()
        d = r.json()
        return d["access_token"], d.get("expires_in", 3600)


def login_with_code(db: Session, code: str):
    """code → (user, token phiên). Đặt provider='microsoft' cho phiên vừa tạo."""
    access, refresh, expires_in, info = _exchange_and_fetch(code)
    email = info.get("mail") or info.get("userPrincipalName") or ""
    name = info.get("displayName") or email
    user = user_repo.get_or_create_user(db, email=email, name=name, initial=(name[:1].upper() or "?"))
    session = session_repo.create_session(
        db, user_id=user.id, ttl_hours=settings.session_ttl_hours,
        google_access_token=access,          # cột dùng chung — ở đây chứa token MS
        google_refresh_token=refresh,
        access_expires_in=expires_in,
    )
    session_repo.set_provider(db, session.token, "microsoft")
    return user, session.token
