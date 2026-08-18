# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/confirmation_repo.py — vòng đời yêu cầu xác nhận          ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Toàn bộ luật chuyển trạng thái nằm ở ĐÂY và ở model, không rải ra  ║
# ║ các endpoint. Rải ra là kiểu gì cũng có một lối vào quên kiểm.     ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.confirmation import APPROVED, PENDING, REJECTED, ConfirmationRequest


def create(db: Session, *, user_id: int, action: str, description: str,
           args: dict | None = None, conversation_id: str | None = None) -> ConfirmationRequest:
    """Mở một yêu cầu chờ duyệt. Tham số được CHỐT ngay lúc này."""
    row = ConfirmationRequest(
        id=uuid.uuid4().hex,
        user_id=user_id,
        conversation_id=conversation_id,
        action=action,
        description=description,
        args=dict(args or {}),
        status=PENDING,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_owned(db: Session, req_id: str, user_id: int) -> ConfirmationRequest | None:
    """Lấy yêu cầu NHƯNG chỉ khi đúng chủ.

    Người khác duyệt hộ được thì cổng human-in-the-loop mất sạch ý nghĩa: kẻ tấn
    công chỉ cần đoán một id là gửi thư thay bạn.
    """
    r = db.get(ConfirmationRequest, req_id)
    if r is None or r.user_id != user_id:
        return None
    return r


def approve(db: Session, req: ConfirmationRequest) -> bool:
    """Đánh dấu đã duyệt. True = lần gọi này chuyển trạng thái thật (được phép chạy
    hành động); False = đã xử lý trước đó rồi (KHÔNG được chạy lại)."""
    doi = req.approve()
    if doi:
        db.commit()
    return doi


def reject(db: Session, req: ConfirmationRequest) -> bool:
    doi = req.reject()
    if doi:
        db.commit()
    return doi


def save_result(db: Session, req: ConfirmationRequest, result: dict) -> None:
    """Cất kết quả lần chạy đầu để lần bấm sau trả lại đúng cái đó."""
    req.result = result
    db.commit()


def list_pending(db: Session, user_id: int, limit: int = 20) -> list[ConfirmationRequest]:
    return (
        db.query(ConfirmationRequest)
        .filter(ConfirmationRequest.user_id == user_id,
                ConfirmationRequest.status == PENDING)
        .order_by(ConfirmationRequest.created_at.desc())
        .limit(limit)
        .all()
    )


def to_dict(req: ConfirmationRequest) -> dict:
    """Khuôn cho FE/MCP. KHÔNG phơi `args` ra ngoài — trong đó có nội dung thư."""
    return {
        "id": req.id,
        "action": req.action,
        "description": req.description,
        "status": req.status,
        "conversationId": req.conversation_id,
        "createdAt": req.created_at.isoformat() if req.created_at else None,
    }


__all__ = [
    "APPROVED", "PENDING", "REJECTED",
    "create", "get_owned", "approve", "reject", "save_result", "list_pending", "to_dict",
]
