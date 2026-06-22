# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/auth_service.py — LOGIC đăng nhập Google (services/) ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là "bộ não" của vũ điệu OAuth: dựng URL Google, đổi code lấy   ║
# ║ token, lấy hồ sơ user, rồi get-or-create user + tạo phiên.        ║
# ╚══════════════════════════════════════════════════════════════════╝

from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.repo import user_repo, session_repo

# 3 địa chỉ chuẩn của Google trong luồng OAuth:
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"      # trang đăng nhập
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"             # đổi code → token
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"  # lấy hồ sơ


def build_google_auth_url() -> str:
    """Bước 1–2: dựng URL để đẩy người dùng sang Google đăng nhập."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,  # Google sẽ gọi lại địa chỉ này
        "response_type": "code",        # xin về 1 "code" (mã đổi token)
        # đăng nhập (email+hồ sơ) + ĐỌC GMAIL (Nấc 5). gmail.readonly là quyền "nhạy cảm":
        # Google sẽ hiện cảnh báo "app chưa xác minh" — test user bấm Tiếp tục là được.
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "select_account",     # luôn cho chọn tài khoản
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _exchange_and_fetch(code: str) -> tuple[str, dict]:
    """Bước 5–6: đổi code lấy access_token (server↔server), rồi dùng nó lấy hồ sơ user.
    Trả về (access_token, hồ_sơ) — access_token CÒN dùng tiếp để gọi Gmail."""
    with httpx.Client(timeout=10) as client:
        token_res = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,  # bí mật chỉ server biết
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_res.raise_for_status()
        access_token = token_res.json()["access_token"]

        info_res = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info_res.raise_for_status()
        return access_token, info_res.json()


def login_with_code(db: Session, code: str):
    """Bước 5–7: code → (access_token, user) → tạo phiên KÈM access_token để gọi Gmail."""
    access_token, info = _exchange_and_fetch(code)
    email = info["email"]
    name = info.get("name") or email
    user = user_repo.get_or_create_user(db, email=email, name=name, initial=name[:1].upper())
    session = session_repo.create_session(
        db, user_id=user.id, ttl_hours=settings.session_ttl_hours,
        google_access_token=access_token,
    )
    return user, session.token
