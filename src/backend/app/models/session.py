# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/session.py — BẢNG 'sessions' (tầng models/)            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mỗi lần đăng nhập thành công → tạo 1 dòng ở đây: token ↔ user nào, ║
# ║ hết hạn khi nào. Đăng xuất = xoá dòng. (Tên class AuthSession để    ║
# ║ KHÔNG trùng với Session của SQLAlchemy.)                          ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class AuthSession(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    #   token chính là khoá chính — tra phiên bằng token rất nhanh.

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    #   ForeignKey = "khoá ngoại": liên kết phiên này thuộc về user nào trong bảng users.

    expires_at: Mapped[datetime] = mapped_column(DateTime)
    #   thời điểm hết hạn — quá hạn thì phiên không còn dùng được.

    google_access_token: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    #   token Google để GỌI GMAIL (Nấc 5). Sống ngắn (~1h) → sẽ tự làm mới (Nấc 9).

    google_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    #   token "làm mới" (Nấc 9): SỐNG LÂU, dùng để xin access_token mới khi cái cũ hết hạn
    #   mà KHÔNG bắt người dùng đăng nhập lại. Google chỉ trả nó khi xin "offline + consent".

    google_token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    #   thời điểm access_token hết hạn → biết KHI NÀO cần làm mới (trước khi gọi Gmail).
