# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/auth.py — ROUTER nhóm đăng nhập (tầng api/)               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ QUY CHUẨN: gom các route cùng nhóm vào 1 APIRouter, rồi app.py     ║
# ║ include vào. prefix="/auth" → mọi route ở đây tự có tiền tố /auth. ║
# ║ Route vẫn MỎNG: chỉ điều phối, logic nằm ở auth_service.          ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import settings
from app.core.deps import COOKIE_NAME
from app.services import auth_service, auth_service_ms
from app.repo import session_repo

logger = logging.getLogger("app.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


def _app_url() -> str:
    """Đăng nhập xong phải vào THẲNG hộp thư (/app), không rơi lại trang giới thiệu."""
    return settings.frontend_url.rstrip("/") + "/app"


def _login_error(step: str, detail: str):
    """Đăng nhập hỏng → quay về trang đăng nhập kèm lý do, thay vì trả 500 trống."""
    base = settings.frontend_url.rstrip("/")
    return RedirectResponse(
        f"{base}/login?loi={quote(step)}&chi_tiet={quote(detail[:300])}",
        status_code=302,
    )


def _set_session_cookie(token: str):
    """Đăng nhập xong (Google/Microsoft) → vào /app + gắn cookie httponly (dùng chung)."""
    resp = RedirectResponse(_app_url(), status_code=302)
    resp.set_cookie(COOKIE_NAME, token, httponly=True,
                    max_age=settings.session_ttl_hours * 3600,
                    **settings.cookie_kw)
    return resp


@router.get("/outlook/start")
def outlook_start():
    """Đẩy sang trang đăng nhập Microsoft (Outlook). Chỉ chạy khi đã đặt MS_CLIENT_ID.

    ── VÌ SAO PHẢI CHẶN Ở ĐÂY ──
    Chú thích cũ đã nói "chỉ hoạt động khi đã đặt MS_CLIENT_ID" nhưng KHÔNG ai kiểm.
    Thiếu khoá thì app vẫn đẩy người dùng sang Microsoft với `client_id=` rỗng, và họ
    nhận về một trang lỗi của Microsoft:

        AADSTS900144: The request body must contain the following parameter: 'client_id'

    Người dùng đọc câu đó sẽ tưởng TÀI KHOẢN MICROSOFT của mình có vấn đề, và đi sửa
    ở đúng chỗ không có lỗi gì. Sự thật là MeoArc chưa được cấu hình — một câu mà chỉ
    máy chủ này biết, nên nó phải là nơi nói ra.

    Chặn ở đây, không phải chỉ ẩn nút ở giao diện: ai gõ thẳng URL vẫn phải nhận được
    câu trả lời đúng."""
    if not settings.ms_client_id:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Đăng nhập Outlook chưa được bật trên máy chủ này (thiếu MS_CLIENT_ID). "
            "Bạn đăng nhập bằng Google nhé.",
        )
    return RedirectResponse(auth_service_ms.build_ms_auth_url())


@router.get("/outlook/callback")
def outlook_callback(code: str | None = None, error: str | None = None,
                     error_description: str | None = None,
                     db: Session = Depends(get_db)):
    # Microsoft có thể gọi lại kèm ?error khi người dùng bấm Huỷ hoặc app thiếu quyền.
    if error:
        logger.warning("Outlook tu choi: %s — %s", error, error_description)
        return _login_error("microsoft-tu-choi", error_description or error)
    if not code:
        return _login_error("thieu-code", "Microsoft khong gui ma uy quyen")
    try:
        _user, token = auth_service_ms.login_with_code(db, code)  # phiên + provider='microsoft'
    except auth_service_ms.OutlookLoginError as e:
        # Trước đây mọi lỗi ở đây đều thành "Internal Server Error" trống trơn,
        # không cách nào biết hỏng ở bước nào. Giờ ghi log + đưa lý do về giao diện.
        logger.error("Dang nhap Outlook hong o buoc %s: %s", e.step, e.detail)
        return _login_error(e.step, e.detail)
    except Exception as e:  # noqa: BLE001 — chặn để user thấy lý do thay vì 500 trần
        logger.exception("Dang nhap Outlook loi khong luong truoc")
        return _login_error("khong-xac-dinh", f"{type(e).__name__}: {e}")
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
        # FE và BE khác tên miền thì phải là SameSite=None; Secure, nếu không trình
        # duyệt lặng lẽ không gửi cookie và mọi lệnh gọi sau đăng nhập đều 401.
        **settings.cookie_kw,
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
