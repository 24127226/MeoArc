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
    #   token Google để GỌI GMAIL (Nấc 5). Lưu theo phiên; hết hạn ~1h → đăng nhập lại.
