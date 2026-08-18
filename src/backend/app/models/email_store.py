# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/email_store.py — EMAIL LÀM STORE-OF-RECORD + con trỏ sync║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là bảng `emails` mà Design (mục 4.1.5.3) mô tả: LƯU metadata +  ║
# ║ nội dung email trong DB của MÌNH để PHỤC VỤ ĐỌC TỪ DB, KHÔNG gọi    ║
# ║ Gmail/Graph mỗi lần user mở web → tránh rate-limit (yêu cầu nhóm).  ║
# ║                                                                    ║
# ║ CHIẾN LƯỢC ĐỒNG BỘ (template không quy định → tự chọn tối ưu):      ║
# ║  • Ingest bằng Gmail Push (Pub/Sub) → webhook → incremental sync    ║
# ║    (history.list) — KHÔNG polling liên tục.                         ║
# ║  • Đọc: LUÔN lấy từ bảng này (services/sync_service làm store).     ║
# ║  • Ghi: write-through — gọi Gmail rồi cập nhật bản ghi ở đây.       ║
# ║                                                                    ║
# ║ PRIVACY: `body_enc` (thân thư) được MÃ HOÁ khi lưu (Fernet, chung   ║
# ║ khoá token) — DB rò rỉ cũng không lộ nội dung thư. Bật/tắt cả tính  ║
# ║ năng qua cờ settings.mailbox_store_enabled.                         ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Boolean, DateTime, ForeignKey, JSON, Integer, UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StoredEmail(Base):
    """1 email đã đồng bộ về DB. Khoá tự nhiên = (user_id, provider, g_id)."""
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", "g_id", name="uq_email_user_provider_gid"),
        # Liệt kê theo thư mục + mới nhất trước = truy vấn nóng nhất (UC003).
        Index("ix_email_list", "user_id", "provider", "folder", "received_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String, default="google")   # 'google' | 'microsoft'

    g_id: Mapped[str] = mapped_column(String, index=True)   # message id gốc từ Gmail/Graph (Design: gID)
    thread_id: Mapped[str | None] = mapped_column(String, nullable=True)
    folder: Mapped[str] = mapped_column(String, default="inbox", index=True)  # inbox/sent/drafts/archive/trash

    # Hiển thị (đã tính sẵn khi ingest → đọc khỏi tính lại).
    sender: Mapped[str] = mapped_column(String, default="")
    sender_email: Mapped[str] = mapped_column(String, default="")
    sender_initial: Mapped[str] = mapped_column(String, default="?")
    to_addr: Mapped[str] = mapped_column(String, default="")
    subject: Mapped[str] = mapped_column(String, default="")
    preview: Mapped[str] = mapped_column(Text, default="")           # bodySnippet

    body_enc: Mapped[str | None] = mapped_column(Text, nullable=True)  # bodyText — MÃ HOÁ (JSON list đoạn)
    has_full: Mapped[bool] = mapped_column(Boolean, default=False)     # đã có thân thư đầy đủ chưa
    has_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    attachments_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{name,size}]

    gmail_labels: Mapped[list] = mapped_column(JSON, default=list)   # nhãn GỐC provider (khác nhãn AI)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    starred: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Nhãn AI: BA TRỤC theo PA1 §4.2.9 ─────────────────────────────────────
    # Category LUÔN có; Priority và Status CHỈ có với thư mang tính công việc.
    ai_category: Mapped[str] = mapped_column(String, default="sky")   # 1 trong 7 màu chip
    ai_label: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_priority: Mapped[str | None] = mapped_column(String, nullable=True)   # High | Medium | Low
    ai_status: Mapped[str | None] = mapped_column(String, nullable=True)     # Todo | Waiting | Done
    ai_tldr: Mapped[str | None] = mapped_column(Text, nullable=True)

    time_s: Mapped[str] = mapped_column(String, default="")   # nhãn giờ ngắn
    date_s: Mapped[str] = mapped_column(String, default="")   # nhãn ngày đầy đủ
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)   # "System sync timestamp"
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # ── PA2 §1.3.9: applyAILabels(category, priority, status) ────────────────
    def apply_ai_labels(self, category: str, priority: str | None,
                        status: str | None, *, label: str | None = None) -> None:
        """Gắn CẢ BA nhãn AI trong MỘT thao tác (PA2 §1.3.9: "All three parameters
        must be set simultaneously").

        Vì sao phải đi cùng nhau: ba nhãn là kết quả của MỘT lượt phân tích. Cho phép
        gán lẻ thì sớm muộn cũng có thư mang Priority của lượt phân tích này và Status
        của lượt trước — người dùng thấy "High / Done" và không hiểu chuyện gì.

        Thư không mang tính công việc thì priority và status phải là **None**, không
        phải "Low"/"Done": None nghĩa là ĐÂY KHÔNG PHẢI VIỆC, còn Low nghĩa là đã xét
        và kết luận việc nhẹ. Nhầm hai thứ đó là đổ cả hộp thư quảng cáo vào danh sách
        việc cần làm.
        """
        self.ai_category = category
        # Ép cặp đôi: thiếu một trong hai thì bỏ cả hai, không giữ trạng thái nửa vời.
        if priority is None or status is None:
            self.ai_priority = None
            self.ai_status = None
        else:
            self.ai_priority = priority
            self.ai_status = status
        if label is not None:
            self.ai_label = label


class MailboxSync(Base):
    """Con trỏ đồng bộ mỗi (user, provider): tới đâu rồi + hạn của Gmail watch."""
    __tablename__ = "mailbox_sync"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_mailbox_sync_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String, default="google")

    history_id: Mapped[str | None] = mapped_column(String, nullable=True)   # con trỏ Gmail history.list
    delta_link: Mapped[str | None] = mapped_column(Text, nullable=True)     # con trỏ Graph delta (Outlook)
    watch_expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # hạn Gmail watch (~7 ngày)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
