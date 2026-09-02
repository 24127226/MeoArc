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
from app.models.user import User

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


# ── NHIỀU TÀI KHOẢN CÙNG LÚC ─────────────────────────────────────────────────
# Cookie cũ (`meoarc_session`) giữ phiên ĐANG HOẠT ĐỘNG — giữ nguyên tên và ý nghĩa
# để mọi endpoint sẵn có không phải sửa gì.
# Cookie mới giữ DANH SÁCH phiên trình duyệt này đang có. Đăng nhập thêm một tài khoản
# thì nối vào danh sách chứ không ghi đè, nên đổi qua lại không phải đăng xuất — đúng
# cách Google làm, và là thứ người dùng đã quen tới mức không nghĩ nó là tính năng.
COOKIE_DS = "meoarc_sessions"

# Trần 5 tài khoản: cookie có giới hạn ~4KB, mà mỗi token là một chuỗi dài. Vượt trần
# thì trình duyệt lặng lẽ bỏ cookie — hỏng theo cách không có thông báo nào.
_TRAN_TAI_KHOAN = 5


def _doc_ds(request: Request) -> list[str]:
    """Danh sách token trong cookie, đã lọc trùng và giữ nguyên thứ tự."""
    raw = request.cookies.get(COOKIE_DS) or ""
    ra: list[str] = []
    for t in raw.split(","):
        t = t.strip()
        if t and t not in ra:
            ra.append(t)
    return ra[:_TRAN_TAI_KHOAN]


def _gan_cookie(resp, token: str, ds: list[str]):
    """Gắn CẢ HAI cookie. Luôn đi cùng nhau: lệch nhau thì phiên đang hoạt động không
    nằm trong danh sách, và trình đổi tài khoản sẽ không thấy chính tài khoản đang mở."""
    kw = dict(httponly=True, max_age=settings.session_ttl_hours * 3600, **settings.cookie_kw)
    resp.set_cookie(COOKIE_NAME, token, **kw)
    resp.set_cookie(COOKIE_DS, ",".join(ds[:_TRAN_TAI_KHOAN]), **kw)
    return resp


def _set_session_cookie(token: str, request: Request | None = None):
    """Đăng nhập xong (Google/Microsoft) → vào /app + gắn cookie httponly (dùng chung).

    NỐI vào danh sách sẵn có thay vì thay thế: đây là chỗ biến "đăng nhập" thành "thêm
    một tài khoản". Token mới lên ĐẦU danh sách vì nó vừa được chọn."""
    ds = _doc_ds(request) if request is not None else []
    ds = [token] + [t for t in ds if t != token]
    return _gan_cookie(RedirectResponse(_app_url(), status_code=302), token, ds)


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
def outlook_callback(request: Request, code: str | None = None, error: str | None = None,
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
    return _set_session_cookie(token, request)


@router.get("/google/start")
def google_start():
    # Bước 1–2: đẩy trình duyệt sang trang đăng nhập Google.
    return RedirectResponse(auth_service.build_google_auth_url())


@router.get("/google/callback")
def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    # Bước 4–7: Google gọi lại kèm ?code → đổi lấy user + tạo phiên.
    _user, token = auth_service.login_with_code(db, code)
    # Dùng CHUNG một đường gắn cookie với Outlook. Trước đây nhánh này tự gắn cookie
    # riêng, nên mọi thay đổi về phiên phải nhớ sửa hai chỗ — và quên một chỗ thì chỉ
    # một nhà cung cấp hỏng, kiểu lệch rất khó thấy vì phải đăng nhập đúng loại tài
    # khoản đó mới gặp.
    return _set_session_cookie(token, request)


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """Đăng xuất TÀI KHOẢN ĐANG MỞ, không phải mọi tài khoản.

    Còn tài khoản khác trong trình duyệt thì CHUYỂN SANG nó thay vì đá về trang đăng
    nhập — đăng xuất một tài khoản mà mất luôn các tài khoản còn lại là hành vi người
    dùng không hề yêu cầu, và họ phải đăng nhập lại từng cái."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        session_repo.delete_session(db, token)  # xoá phiên trong DB
    con_lai = [t for t in _doc_ds(request) if t != token]
    # Chỉ giữ token còn hiệu lực: phiên hết hạn nằm lại trong danh sách sẽ hiện ra
    # thành một tài khoản bấm vào thì văng 401.
    con_lai = [t for t in con_lai if session_repo.get_valid_session(db, t)]
    if con_lai:
        return _gan_cookie(JSONResponse({"message": "Đã đăng xuất", "con_lai": len(con_lai)}),
                           con_lai[0], con_lai)
    resp = JSONResponse({"message": "Đã đăng xuất"})
    resp.delete_cookie(COOKIE_NAME)              # xoá cookie ở trình duyệt
    resp.delete_cookie(COOKIE_DS)
    return resp


@router.get("/accounts")
def danh_sach_tai_khoan(request: Request, db: Session = Depends(get_db)):
    """Các tài khoản trình duyệt này đang đăng nhập, để giao diện dựng trình đổi.

    KHÔNG trả về token. Giao diện chỉ cần biết có những ai và ai đang hoạt động; đưa
    token ra là biến một cookie httponly (JS không đọc được) thành một chuỗi nằm trong
    bộ nhớ trang — mất sạch lớp bảo vệ trước XSS. Đổi tài khoản đi bằng `user_id`."""
    dang = request.cookies.get(COOKIE_NAME)
    ra = []
    for t in _doc_ds(request):
        s_ = session_repo.get_valid_session(db, t)
        if not s_:
            continue
        u = db.get(User, s_.user_id)
        if not u:
            continue
        ra.append({"user_id": u.id, "email": u.email, "name": getattr(u, "name", "") or u.email,
                   "provider": getattr(s_, "provider", "gmail") or "gmail",
                   "dang_dung": t == dang})
    return {"ket_qua": ra}


@router.post("/switch/{user_id}")
def doi_tai_khoan(user_id: int, request: Request, db: Session = Depends(get_db)):
    """Đổi sang một tài khoản ĐÃ đăng nhập trong chính trình duyệt này.

    ── CHỖ PHẢI CANH ──
    Chỉ chấp nhận token CÓ SẴN trong cookie của trình duyệt. Nếu nhận `user_id` rồi tự
    đi tìm phiên trong CSDL thì bất kỳ ai gọi endpoint này cũng nhảy được vào hộp thư
    của người khác — biến trình đổi tài khoản thành một cửa sau."""
    dang_co = _doc_ds(request)
    for t in dang_co:
        s_ = session_repo.get_valid_session(db, t)
        if s_ and s_.user_id == user_id:
            ds = [t] + [x for x in dang_co if x != t]
            return _gan_cookie(JSONResponse({"message": "Đã đổi tài khoản"}), t, ds)
    raise HTTPException(status.HTTP_404_NOT_FOUND,
                        "Tài khoản này chưa đăng nhập trên trình duyệt hiện tại.")


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
