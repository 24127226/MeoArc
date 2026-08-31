# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/conversation.py — BẢNG 'conversations' (UC011)         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Lưu BỀN các phiên chat với agent → xem lại / TIẾP TỤC sau (kể cả   ║
# ║ khi restart server). Thay cho bộ nhớ tạm trong RAM trước đây.      ║
# ║ Mỗi phiên giữ HAI khuôn dữ liệu cho hai mục đích khác nhau:        ║
# ║  • agent_messages   = tin nhắn LangChain (messages_to_dict) → để   ║
# ║    AGENT nạp lại NGỮ CẢNH đầy đủ mà nghĩ tiếp (gồm cả tool calls).  ║
# ║  • display_messages = khuôn FE (user text + AgentReply card) → để  ║
# ║    GIAO DIỆN vẽ lại đúng lịch sử (thẻ result/digest/triage…).      ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    #   id chuỗi (uuid) do FE/BE sinh — 1 phiên hội thoại.

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    #   thuộc về user nào (index để liệt kê theo user nhanh).

    title: Mapped[str] = mapped_column(String, default="Cuộc trò chuyện mới")
    #   tiêu đề hiển thị ở drawer; tự đặt theo câu hỏi đầu nếu user chưa đổi.

    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    #   ghim lên đầu danh sách (UC011).

    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    #   updated_at: mốc lượt chat gần nhất → sắp xếp "mới nhất trước".

    agent_messages: Mapped[list] = mapped_column(JSON, default=list)
    #   ngữ cảnh LangChain (Human/AI/Tool) đã serialize → agent NHỚ để nghĩ tiếp.

    display_messages: Mapped[list] = mapped_column(JSON, default=list)
    #   lịch sử để FE vẽ lại: [{role:'user',text}, {role:'agent',reply:<AgentReply>}, ...].
