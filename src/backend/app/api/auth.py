# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/auth.py — ROUTER nhóm đăng nhập (tầng api/)               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ QUY CHUẨN: gom các route cùng nhóm vào 1 APIRouter, rồi app.py     ║
# ║ include vào. prefix="/auth" → mọi route ở đây tự có tiền tố /auth. ║
# ║ Route vẫn MỎNG: chỉ điều phối, logic nằm ở auth_service.          ║
# ╚══════════════════════════════════════════════════════════════════╝

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import settings
from app.core.deps import COOKIE_NAME
from app.services import auth_service, auth_service_ms
from app.repo import session_repo

router = APIRouter(prefix="/auth", tags=["auth"])


def _app_url() -> str:
    """Đăng nhập xong phải vào THẲNG hộp thư (/app), không rơi lại trang giới thiệu."""
    return settings.frontend_url.rstrip("/") + "/app"


def _set_session_cookie(token: str):
    """Đăng nhập xong (Google/Microsoft) → vào /app + gắn cookie httponly (dùng chung)."""
    resp = RedirectResponse(_app_url(), status_code=302)
    resp.set_cookie(COOKIE_NAME, token, httponly=True,
                    max_age=settings.session_ttl_hours * 3600, samesite="lax")
    return resp


@router.get("/outlook/start")
def outlook_start():
    """Đẩy sang trang đăng nhập Microsoft (Outlook). Chỉ hoạt động khi đã đặt MS_CLIENT_ID."""
    return RedirectResponse(auth_service_ms.build_ms_auth_url())


@router.get("/outlook/callback")
def outlook_callback(code: str, db: Session = Depends(get_db)):
    _user, token = auth_service_ms.login_with_code(db, code)  # tạo phiên + provider='microsoft'
    return _set_session_cookie(token)


@router.get("/google/start")
def google_start():
    # Bước 1–2: đẩy trình duyệt sang trang đăng nhập Google.
    return RedirectResponse(auth_service.build_google_auth_url())


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    # Bước 4–7: Google gọi lại kèm ?code → đổi lấy user + tạo phiên.
    _user, token = auth_service.login_with_code(db, code)
    # Đăng nhập xong → ĐẨY TRÌNH DUYỆT VÀO THẲNG HỘP THƯ (/app).
    resp = RedirectResponse(_app_url(), status_code=302)
    # Gắn token vào COOKIE httponly (JS không đọc được → an toàn hơn trước XSS).
    resp.set_cookie(
        COOKIE_NAME, token,
        httponly=True,
        max_age=settings.session_ttl_hours * 3600,
        samesite="lax",
    )
    return resp


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        session_repo.delete_session(db, token)  # xoá phiên trong DB
    resp = JSONResponse({"message": "Đã đăng xuất"})
    resp.delete_cookie(COOKIE_NAME)              # xoá cookie ở trình duyệt
    return resp


@router.post("/revoke")
def revoke(request: Request, db: Session = Depends(get_db)):
    """UC002 — THU HỒI quyền Gmail: bảo Google bỏ quyền + xoá phiên + xoá cookie.
    Mạnh hơn logout: lần sau đăng nhập Google sẽ HỎI ĐỒNG Ý LẠI toàn bộ quyền."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        session = session_repo.get_valid_session(db, token)
        if session and session.google_access_token:
            auth_service.revoke_google_token(session.google_access_token)  # gọi Google bỏ quyền
        session_repo.delete_session(db, token)   # xoá phiên phía mình
    resp = JSONResponse({"message": "Đã thu hồi quyền"})
    resp.delete_cookie(COOKIE_NAME)
    return resp
