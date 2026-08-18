# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/connected_account.py — HỘP THƯ ĐÃ KẾT NỐI (v6 §7)      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Trước đây token OAuth của hộp thư nằm ngay trên bảng `sessions`,   ║
# ║ tức là buộc vào PHIÊN ĐĂNG NHẬP. Hai hệ quả:                       ║
# ║   • Đăng xuất là mất luôn kết nối hộp thư, đăng nhập lại phải cấp  ║
# ║     quyền lại từ đầu.                                              ║
# ║   • Không thể nối hai hộp thư cùng lúc (FR-01.2) vì một phiên chỉ  ║
# ║     giữ được một bộ token.                                         ║
# ║                                                                    ║
# ║ Tách ra thành thực thể riêng: kết nối hộp thư SỐNG LÂU HƠN phiên   ║
# ║ đăng nhập, và một người nối được nhiều hộp thư.                    ║
# ║                                                                    ║
# ║ Phân loại theo `provider` (v6: disjoint, partial) — mỗi nhà cung   ║
# ║ cấp có cách theo dõi thay đổi riêng nên tách bảng con, không nhồi  ║
# ║ cả hai cột vào bảng cha rồi để một cột luôn rỗng.                  ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedStr
from app.core.db import Base

ACTIVE = "active"
REVOKED = "revoked"
ERROR = "error"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"
    __table_args__ = (
        # Một hộp thư ngoài chỉ được nối một lần. Không có ràng buộc này thì bấm
        # "kết nối" hai lần là có hai bản ghi cùng trỏ về một hộp thư, rồi đồng bộ
        # chạy hai lần và thư về gấp đôi.
        UniqueConstraint("provider", "provider_user_id", name="uq_connected_account_provider_user"),
    )

    account_id: Mapped[str] = mapped_column(String, primary_key=True)   # uuid

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String, index=True)           # 'google' | 'microsoft'
    provider_user_id: Mapped[str] = mapped_column(String)
    email_address: Mapped[str] = mapped_column(String, default="")

    status: Mapped[str] = mapped_column(String, default=ACTIVE, index=True)
    #   active | revoked | error — thu hồi quyền thì đổi status, KHÔNG xoá bản ghi,
    #   để nhật ký cũ vẫn còn chỗ trỏ về.

    access_token: Mapped[str | None] = mapped_column(EncryptedStr, nullable=True, default=None)
    refresh_token: Mapped[str | None] = mapped_column(EncryptedStr, nullable=True, default=None)
    #   Cho NULL: Google/Microsoft không phải lúc nào cũng trả refresh token ở lần cấp
    #   quyền lại. NOT NULL thì buộc phải nhét chuỗi rỗng, mất luôn khả năng phân biệt
    #   "chưa từng có" với "có mà rỗng".

    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    #   v6 không nêu cột này, nhưng thiếu nó thì không biết KHI NÀO cần làm mới token —
    #   chỉ còn cách gọi thử, ăn lỗi 401 rồi mới làm mới.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class GmailAccount(Base):
    """Bảng con cho Gmail — con trỏ thay đổi riêng của Google."""
    __tablename__ = "gmail_accounts"

    account_id: Mapped[str] = mapped_column(
        ForeignKey("connected_accounts.account_id", ondelete="CASCADE"), primary_key=True)
    history_id: Mapped[str | None] = mapped_column(String, nullable=True)
    watch_expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #   Đăng ký nhận đẩy của Gmail hết hạn sau ~7 ngày. Không lưu hạn thì một hôm nào
    #   đó thư ngừng tự về mà không ai biết vì sao.
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OutlookAccount(Base):
    """Bảng con cho Outlook — Graph dùng delta link thay vì history id."""
    __tablename__ = "outlook_accounts"

    account_id: Mapped[str] = mapped_column(
        ForeignKey("connected_accounts.account_id", ondelete="CASCADE"), primary_key=True)
    delta_link: Mapped[str | None] = mapped_column(String, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ConnectedAccountScope(Base):
    """Quyền đã được người dùng cấp cho kết nối này (v6 §7c).

    Lưu lại để trả lời được câu "agent ngoài có được làm việc này không" mà không
    phải hỏi lại nhà cung cấp — đúng yêu cầu FR-05.2.
    """
    __tablename__ = "connected_account_scopes"

    account_id: Mapped[str] = mapped_column(
        ForeignKey("connected_accounts.account_id", ondelete="CASCADE"), primary_key=True)
    scope: Mapped[str] = mapped_column(String, primary_key=True)
