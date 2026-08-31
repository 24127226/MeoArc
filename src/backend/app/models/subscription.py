# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/subscription.py — BẢNG 'subscriptions' (gói + hạn mức)  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mỗi user 1 dòng (PK = user_id). Giữ tier + BỘ ĐẾM token đã dùng     ║
# ║ theo NGÀY và THÁNG (kèm khoá ngày/tháng để tự reset khi sang kỳ     ║
# ║ mới). Khớp lớp Subscription (Class Diagram) — nhưng thay              ║
# ║ 'mailboxScopeDays' bằng hạn mức TOKEN (đúng mô hình freemium AI).   ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    tier: Mapped[str] = mapped_column(String, default="free")     # 'free' | 'pro'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # NFR-SCO-01 — cửa sổ quét CHỐT theo từng người, không đọc lại từ file cấu hình.
    # Đọc lại từ cấu hình thì sửa bảng giá một cái là phạm vi của mọi người dùng hiện
    # hữu đổi theo, kể cả người đã trả tiền cho mức cũ. Khớp cột `mailboxScopeDays`
    # mà PA2 §1.5.5 đã mô tả.
    mailbox_scope_days: Mapped[int] = mapped_column(Integer, default=90)

    day_key: Mapped[str] = mapped_column(String, default="")       # 'YYYY-MM-DD' — kỳ ngày hiện tại
    tokens_today: Mapped[int] = mapped_column(Integer, default=0)
    month_key: Mapped[str] = mapped_column(String, default="")     # 'YYYY-MM'
    tokens_month: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
