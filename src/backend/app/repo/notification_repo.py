# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/notification_repo.py — tạo/đọc/đánh dấu thông báo         ║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy.orm import Session
from app.models.notification import Notification


def create(db: Session, *, user_id: int, message: str, type: str = "info") -> Notification:
    n = Notification(user_id=user_id, message=message, type=type)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def list_for_user(db: Session, user_id: int, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .count()
    )


def mark_read(db: Session, user_id: int, notif_id: int) -> Notification | None:
    n = (
        db.query(Notification)
        .filter(Notification.id == notif_id, Notification.user_id == user_id)
        .first()
    )
    if n and not n.read:
        n.read = True
        db.commit()
        db.refresh(n)
    return n


def mark_all_read(db: Session, user_id: int) -> int:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .update({Notification.read: True})
    )
    db.commit()
    return count
