# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/schemas/conversation.py — KHUÔN I/O cho UC011 (lịch sử chat)   ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime
from pydantic import BaseModel


class ConversationSummary(BaseModel):
    """1 dòng ở drawer lịch sử: đủ để hiện danh sách, KHÔNG kèm toàn bộ tin nhắn (nhẹ)."""
    id: str
    title: str
    pinned: bool
    updatedAt: datetime          # FE format thành 'time' (vd 'Hôm nay 14:20')
    messageCount: int
    preview: str                 # vài chữ của tin gần nhất để xem lướt


class ConversationDetail(BaseModel):
    """Mở 1 phiên: kèm display_messages để FE vẽ lại đúng lịch sử (user text + thẻ AgentReply)."""
    id: str
    title: str
    pinned: bool
    createdAt: datetime
    updatedAt: datetime
    messages: list               # [{role:'user',text} | {role:'agent',reply:<AgentReply>}]


class UpdateConversationReq(BaseModel):
    """PATCH: đổi tên và/hoặc ghim (chỉ gửi field cần đổi)."""
    title: str | None = None
    pinned: bool | None = None
