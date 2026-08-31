# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/maintenance.py — DỌN DỮ LIỆU CŨ (data retention)         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Vì sao cần khi lên quy mô: ba bảng dưới đây CHỈ THÊM, không bao    ║
# ║ giờ tự bớt. Chạy vài tháng với vài nghìn người là:                 ║
# ║   • `sessions`      — mỗi lần đăng nhập một dòng, hết hạn vẫn nằm  ║
# ║   • `audit_logs`    — mỗi thao tác một dòng                       ║
# ║   • `notifications` — mỗi sự kiện một dòng                        ║
# ║ Bảng phình → index phình → truy vấn chậm dần → sao lưu nặng dần.   ║
# ║                                                                    ║
# ║ Cùng tinh thần "trần + TTL" đã ghi trong NFR.md cho kho upload và   ║
# ║ cache Gmail: mọi thứ tích luỹ đều phải có hạn.                     ║
# ║                                                                    ║
# ║ KHÔNG đổi cột nào — chỉ xoá dòng quá hạn. Mô hình dữ liệu trong     ║
# ║ tài liệu (ERD/class diagram) giữ nguyên.                           ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.kv import kv

logger = logging.getLogger("app.maintenance")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def purge_expired_sessions(db: Session) -> int:
    """Xoá phiên đã hết hạn. Phiên hết hạn KHÔNG dùng được nữa nhưng vẫn chiếm chỗ
    và làm chậm mọi truy vấn tra phiên."""
    from app.models.session import AuthSession
    from app.models.session_provider import SessionProvider

    now = _utcnow()
    dead = db.scalars(select(AuthSession.token).where(AuthSession.expires_at < now)).all()
    if not dead:
        return 0
    # Xoá bảng con trước để không vướng khoá ngoại
    db.execute(delete(SessionProvider).where(SessionProvider.token.in_(dead)))
    db.execute(delete(AuthSession).where(AuthSession.token.in_(dead)))
    db.commit()
    return len(dead)


def purge_old_audit(db: Session, days: int) -> int:
    """Xoá nhật ký thao tác cũ hơn `days` ngày.

    Nhật ký là bằng chứng cho human-in-the-loop nên KHÔNG xoá sạch — chỉ cắt phần
    quá cũ. Cần giữ lâu hơn thì tăng AUDIT_RETENTION_DAYS, hoặc xuất ra kho lạnh
    trước khi dọn.
    """
    from app.models.audit import AuditLog

    cutoff = _utcnow() - timedelta(days=days)
    n = db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff)).rowcount or 0
    db.commit()
    return n


def purge_read_notifications(db: Session, days: int) -> int:
    """Xoá thông báo ĐÃ ĐỌC và cũ hơn `days` ngày. Chưa đọc thì giữ nguyên,
    dù cũ tới đâu — người dùng chưa xem thì không được tự ý bỏ."""
    from app.models.notification import Notification

    cutoff = _utcnow() - timedelta(days=days)
    n = db.execute(
        delete(Notification).where(Notification.read.is_(True), Notification.created_at < cutoff)
    ).rowcount or 0
    db.commit()
    return n


def run_maintenance(db: Session) -> dict:
    """Chạy trọn một lượt dọn. Trả số dòng đã xoá từng loại để ghi log và cho /metrics."""
    result = {
        "sessions": purge_expired_sessions(db),
        "audit_logs": purge_old_audit(db, settings.audit_retention_days),
        "notifications": purge_read_notifications(db, settings.notification_retention_days),
    }
    if any(result.values()):
        logger.info("Dọn dữ liệu cũ: %s", result)
    return result


def table_sizes(db: Session) -> dict:
    """Đếm số dòng các bảng tích luỹ — để /metrics cho thấy dữ liệu có đang phình không."""
    from app.models.audit import AuditLog
    from app.models.notification import Notification
    from app.models.session import AuthSession

    out = {}
    for name, model in (("sessions", AuthSession), ("audit_logs", AuditLog),
                        ("notifications", Notification)):
        try:
            out[name] = db.scalar(select(func.count()).select_from(model)) or 0
        except Exception:
            out[name] = -1
    return out


def try_acquire_lock(name: str, ttl_s: int) -> bool:
    """Giành quyền chạy việc định kỳ khi có NHIỀU WORKER.

    Chạy 4 worker mà không khoá thì cả 4 cùng dọn một lúc — tốn công vô ích và có
    thể chèn nhau trên cùng những dòng. Mẹo: dùng bộ đếm cửa sổ sẵn có của KV —
    ai đếm được số 1 trong cửa sổ thì người đó được chạy, ba người còn lại bỏ qua.
    Với Redis, bộ đếm dùng chung nên khoá đúng trên toàn cụm; với in-memory
    (một tiến trình) thì bản thân nó đã là duy nhất.
    """
    return kv.incr_window(f"lock:{name}", window=ttl_s) == 1
