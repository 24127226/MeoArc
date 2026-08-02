# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/notification.py — BẢNG 'notifications'                  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Thông báo hướng NGƯỜI DÙNG (khác audit_logs hướng kỹ thuật): sinh   ║
# ║ khi có hành động đáng chú ý (đã gửi thư, đã dọn N thư...) để hiện    ║
# ║ ở Notification Center. Khớp lớp Notification trong Class Diagram     ║
# ║ (type, message, read, markAsRead()).                               ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String, default="info")   # 'info'|'success'|'action'|'warning'
    message: Mapped[str] = mapped_column(String)
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
