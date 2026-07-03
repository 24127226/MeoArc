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
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"           # thu hồi quyền (UC002)


def build_google_auth_url() -> str:
    """Bước 1–2: dựng URL để đẩy người dùng sang Google đăng nhập."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,  # Google sẽ gọi lại địa chỉ này
        "response_type": "code",        # xin về 1 "code" (mã đổi token)
        # đăng nhập (email+hồ sơ) + QUẢN LÝ GMAIL (Nấc 6a).
        # Vì sao đổi gmail.readonly → gmail.modify: muốn GHI (đánh dấu đọc, gắn sao,
        # lưu trữ, xoá) thì quyền "chỉ đọc" không đủ. gmail.modify cho phép đọc + ghi
        # nhãn + chuyển thùng rác (KHÔNG xoá vĩnh viễn) → nó BAO LUÔN quyền đọc nên
        # thay thẳng cho readonly. Đây là scope "nhạy cảm" → Google vẫn hiện cảnh báo
        # "app chưa xác minh"; test user bấm Tiếp tục là được.
        # ⚠️ Đổi scope = phiên đăng nhập CŨ (chỉ có quyền đọc) sẽ bị 403 khi ghi
        #    → người dùng phải ĐĂNG NHẬP LẠI để cấp quyền mới.
        # Nấc 6b thêm gmail.send: GỬI thư là quyền RIÊNG, gmail.modify KHÔNG bao gồm.
        # Gộp cả 2 scope ngay từ đầu → người dùng chỉ phải đăng nhập lại MỘT lần
        # là dùng được cả hành động nhãn (6a) lẫn gửi thư (6b).
        "scope": (
            "openid email profile"
            " https://www.googleapis.com/auth/gmail.modify"
            " https://www.googleapis.com/auth/gmail.send"
        ),
        "access_type": "offline",       # xin kèm refresh_token (token làm mới sống lâu)
        # "consent" = LUÔN hiện màn đồng ý → Google MỚI trả refresh_token mỗi lần đăng nhập.
        # (Chỉ "select_account" thì lần sau Google thường KHÔNG trả refresh_token nữa.)
        "prompt": "consent select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _exchange_and_fetch(code: str) -> tuple[str, str | None, int, dict]:
    """Bước 5–6: đổi code lấy token (server↔server), rồi dùng access_token lấy hồ sơ user.
    Trả về (access_token, refresh_token, expires_in, hồ_sơ):
      • access_token  — gọi Gmail, sống ~1h.
      • refresh_token — làm mới access_token sau này (có thể None nếu Google không trả).
      • expires_in    — access_token sống bao nhiêu giây (thường 3600)."""
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
        tok = token_res.json()
        access_token = tok["access_token"]
        refresh_token = tok.get("refresh_token")     # có khi vắng (nếu user đã đồng ý trước đó)
        expires_in = tok.get("expires_in", 3600)

        info_res = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info_res.raise_for_status()
        return access_token, refresh_token, expires_in, info_res.json()


def refresh_access_token(refresh_token: str) -> tuple[str, int]:
    """Nấc 9 — dùng refresh_token xin access_token MỚI (KHÔNG cần người dùng đăng nhập lại).
    Trả (access_token mới, số giây sống). Đây là điểm mấu chốt để khỏi 'cứ 1h lại phải login'."""
    with httpx.Client(timeout=10) as client:
        r = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",       # khác login: đây là "gia hạn"
            },
        )
        r.raise_for_status()
        d = r.json()
        return d["access_token"], d.get("expires_in", 3600)


def revoke_google_token(access_token: str) -> None:
    """Gọi Google THU HỒI quyền (UC002): token hết tác dụng NGAY, lần sau muốn dùng phải
    đăng nhập + đồng ý lại từ đầu. Khác logout (chỉ xoá phiên phía mình, quyền vẫn còn).
    Bỏ qua lỗi (vd token đã hết hạn) — mục tiêu là 'chắc chắn không còn quyền'."""
    try:
        with httpx.Client(timeout=10) as client:
            client.post(GOOGLE_REVOKE_URL, params={"token": access_token})
    except Exception:
        pass


def login_with_code(db: Session, code: str):
    """Bước 5–7: code → (token, user) → tạo phiên KÈM access_token + refresh_token + hạn."""
    access_token, refresh_token, expires_in, info = _exchange_and_fetch(code)
    email = info["email"]
    name = info.get("name") or email
    user = user_repo.get_or_create_user(db, email=email, name=name, initial=name[:1].upper())
    session = session_repo.create_session(
        db, user_id=user.id, ttl_hours=settings.session_ttl_hours,
        google_access_token=access_token,
        google_refresh_token=refresh_token,
        access_expires_in=expires_in,
    )
    return user, session.token
