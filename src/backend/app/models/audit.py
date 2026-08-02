# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/audit.py — BẢNG 'audit_logs' (accountability agent)     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Ghi lại MỌI hành động KHÔNG HOÀN TÁC lên hộp thư (gửi/trả lời/xoá/  ║
# ║ lưu trữ/gắn nhãn) — do người dùng bấm hoặc agent đề xuất-rồi-duyệt. ║
# ║ Đây là hiện thực THẬT của ý 'Toolcall_Email' trong Design: quan hệ  ║
# ║ "hành động ↔ email nào" nằm ở cột `affected_email_ids` (list Gmail  ║
# ║ message id — CHUỖI tham chiếu, KHÔNG lưu nội dung email → giữ privacy).║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    #   ai là chủ hành động (index để liệt kê theo user nhanh).

    conversation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    #   phiên chat nào (nếu hành động đến từ luồng agent) — chuỗi, không FK cứng.

    action: Mapped[str] = mapped_column(String)
    #   'send_email' | 'reply_email' | 'delete' | 'archive' | 'apply_label' | 'mark_read' ...

    tool_name: Mapped[str] = mapped_column(String, default="")
    #   tên tool nếu do agent (send_email/bulk_action...), rỗng nếu user bấm nút trực tiếp.

    actor_type: Mapped[str] = mapped_column(String, default="user")
    #   'user' (bấm nút) | 'agent' (agent duyệt) | 'mcp' (client ngoài).

    affected_email_ids: Mapped[list] = mapped_column(JSON, default=list)
    #   ← QUAN HỆ ToolCall–Email: danh sách Gmail message id bị hành động này tác động.

    status: Mapped[str] = mapped_column(String, default="success")   # 'success' | 'failed'
    details: Mapped[dict] = mapped_column(JSON, default=dict)        # thêm ngữ cảnh (lỗi, label...).
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
