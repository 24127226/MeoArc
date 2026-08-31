# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/audit_repo.py — ghi/đọc nhật ký hành động (AuditLog)      ║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log(
    db: Session,
    *,
    user_id: int,
    action: str,
    tool_name: str = "",
    actor_type: str = "user",
    affected_email_ids: list[str] | None = None,
    status: str = "success",
    details: dict | None = None,
    conversation_id: str | None = None,
) -> AuditLog:
    """Ghi 1 dòng audit. Nuốt lỗi ở nơi GỌI (audit hỏng không được làm sập hành động chính)."""
    row = AuditLog(
        user_id=user_id,
        action=action,
        tool_name=tool_name,
        actor_type=actor_type,
        affected_email_ids=list(affected_email_ids or []),
        status=status,
        details=details or {},
        conversation_id=conversation_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_recent(db: Session, user_id: int, limit: int = 50) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
