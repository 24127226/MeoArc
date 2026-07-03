# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/conversation_repo.py — TRUY VẤN bảng conversations (UC011)║
# ╚══════════════════════════════════════════════════════════════════╝

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.conversation import Conversation


def _utcnow() -> datetime:
    """Giờ UTC 'naive' — đồng nhất với cách so sánh thời gian ở session_repo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_id() -> str:
    return uuid.uuid4().hex


def list_for_user(db: Session, user_id: int) -> list[Conversation]:
    """Danh sách phiên của user: ghim lên đầu, rồi mới-nhất-trước."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.pinned.desc(), Conversation.updated_at.desc())
        .all()
    )


def get_owned(db: Session, conv_id: str, user_id: int) -> Conversation | None:
    """Lấy 1 phiên NHƯNG chỉ khi đúng chủ — chặn user A đọc phiên user B."""
    c = db.get(Conversation, conv_id)
    if c is None or c.user_id != user_id:
        return None
    return c


def get_or_create(db: Session, conv_id: str | None, user_id: int) -> Conversation:
    """Lấy phiên đang có (đúng chủ) hoặc TẠO mới. conv_id None/lạ → tạo mới với id sinh ra.
    Trả về phiên CHƯA commit phần nội dung — gọi save_turn để ghi sau khi chạy agent."""
    if conv_id:
        c = db.get(Conversation, conv_id)
        if c is not None and c.user_id == user_id:
            return c
    now = _utcnow()
    c = Conversation(
        id=conv_id or new_id(),
        user_id=user_id,
        title="Cuộc trò chuyện mới",
        pinned=False,
        created_at=now,
        updated_at=now,
        agent_messages=[],
        display_messages=[],
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _auto_title(text: str) -> str:
    """Đặt tiêu đề từ câu hỏi đầu: gọn 1 dòng, tối đa ~48 ký tự."""
    t = " ".join((text or "").split())
    return (t[:48] + "…") if len(t) > 48 else (t or "Cuộc trò chuyện mới")


def save_turn(
    db: Session,
    conv: Conversation,
    agent_messages: list,
    display_messages: list,
    first_user_text: str | None = None,
) -> Conversation:
    """Ghi lại sau MỘT lượt chat: cập nhật 2 khuôn dữ liệu + dời updated_at.
    Nếu phiên còn tiêu đề mặc định và có câu user đầu → tự đặt tiêu đề cho dễ tìm."""
    conv.agent_messages = agent_messages
    conv.display_messages = display_messages
    conv.updated_at = _utcnow()
    if first_user_text and conv.title == "Cuộc trò chuyện mới":
        conv.title = _auto_title(first_user_text)
    db.commit()
    db.refresh(conv)
    return conv


def rename(db: Session, conv: Conversation, title: str) -> Conversation:
    conv.title = (title or "").strip()[:60] or "Cuộc trò chuyện mới"
    db.commit()
    db.refresh(conv)
    return conv


def set_pinned(db: Session, conv: Conversation, pinned: bool) -> Conversation:
    conv.pinned = pinned
    db.commit()
    db.refresh(conv)
    return conv


def delete(db: Session, conv: Conversation) -> None:
    db.delete(conv)
    db.commit()
