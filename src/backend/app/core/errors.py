# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/errors.py — THU THẬP LỖI (error tracking)                ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ /metrics cho biết hệ thống CÓ ĐANG NGHẼN KHÔNG. Nó không cho biết  ║
# ║ AI GẶP LỖI GÌ. Khi người dùng báo "web lỗi rồi", không có thứ này  ║
# ║ thì chỉ còn cách mò trong log — mà log nhiều worker thì mỗi tiến    ║
# ║ trình một file.                                                    ║
# ║                                                                    ║
# ║ Thiết kế CẮM-RÚT giống app/core/kv.py:                             ║
# ║   • Có SENTRY_DSN  → gửi lỗi kèm ngữ cảnh lên dịch vụ ngoài.       ║
# ║   • Không có       → ghi vào log kèm request-id, không phụ thuộc.  ║
# ║ Nhờ vậy đồ án chạy được ngay, còn khi bán thì chỉ cần điền DSN.     ║
# ║                                                                    ║
# ║ ⚠️ QUYỀN RIÊNG TƯ: app này xử lý nội dung email. TUYỆT ĐỐI không    ║
# ║ đính kèm thân thư, tiêu đề, địa chỉ hay token vào báo cáo lỗi.      ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging

from app.core.config import settings

logger = logging.getLogger("app.errors")

_sentry = None
backend_name = "log"

# Những khoá KHÔNG BAO GIỜ được rời khỏi máy chủ.
_CAM_GUI = (
    "authorization", "cookie", "token", "access_token", "refresh_token",
    "password", "secret", "api_key", "client_secret",
    "body", "bodyText", "snippet", "subject", "sender", "recipient", "email",
)


def _loc_du_lieu_nhay_cam(event, _hint):
    """Bộ lọc chạy TRƯỚC khi gửi: che mọi trường có thể chứa dữ liệu người dùng."""
    def _walk(obj):
        if isinstance(obj, dict):
            return {
                k: ("[da-che]" if any(c in k.lower() for c in _CAM_GUI) else _walk(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_walk(x) for x in obj]
        return obj

    try:
        return _walk(event)
    except Exception:
        return None  # lọc lỗi thì THÀ KHÔNG GỬI còn hơn gửi nhầm dữ liệu thật


def setup_error_tracking() -> str:
    """Bật thu thập lỗi nếu có cấu hình. Trả tên backend đang dùng."""
    global _sentry, backend_name

    dsn = getattr(settings, "sentry_dsn", "")
    if not dsn:
        logger.info("Thu thập lỗi: ghi log nội bộ (chưa đặt SENTRY_DSN)")
        return backend_name

    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.0,     # chỉ lấy lỗi, không lấy vết hiệu năng (đỡ tốn)
            send_default_pii=False,     # không gửi IP, email, tên người dùng
            before_send=_loc_du_lieu_nhay_cam,
            environment=getattr(settings, "app_env", "development"),
        )
        _sentry = sentry_sdk
        backend_name = "sentry"
        logger.info("Thu thập lỗi: Sentry")
    except ImportError:
        logger.warning("Đã đặt SENTRY_DSN nhưng chưa cài sentry-sdk → ghi log nội bộ")
    except Exception as exc:  # noqa: BLE001 — hỏng phần này không được kéo sập app
        logger.warning("Không bật được Sentry (%s) → ghi log nội bộ", exc)

    return backend_name


def capture(exc: BaseException, **ngu_canh) -> None:
    """Ghi nhận một lỗi kèm ngữ cảnh KHÔNG nhạy cảm (user_id, đường dẫn, thao tác)."""
    if _sentry is not None:
        try:
            with _sentry.push_scope() as scope:
                for k, v in ngu_canh.items():
                    scope.set_tag(k, str(v)[:120])
                _sentry.capture_exception(exc)
            return
        except Exception:
            pass  # rơi xuống ghi log
    logger.exception("Lỗi chưa xử lý %s", ngu_canh or "")
