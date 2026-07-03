# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/user.py — BẢNG 'users' trong database (tầng models/)    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: mô tả "một dòng user trong DB gồm cột nào". Đây là cấu    ║
# ║ trúc BÊN TRONG kho — KHÁC với schema Email/User ở schemas/ (là      ║
# ║ hình dạng dữ liệu trao đổi với bên ngoài qua API).                 ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class User(Base):
    __tablename__ = "users"  # tên bảng thật trong database

    # mapped_column = MỘT CỘT của bảng. Mapped[kiểu] = kiểu dữ liệu Python tương ứng.
    id: Mapped[int] = mapped_column(primary_key=True)
    #   primary_key=True → khoá chính, mỗi dòng một id duy nhất, tự tăng.

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    #   unique=True → KHÔNG cho 2 user trùng email (DB tự chặn).
    #   index=True  → đánh chỉ mục để tìm theo email NHANH (hay dùng khi đăng nhập).

    name: Mapped[str] = mapped_column(String)
    initial: Mapped[str] = mapped_column(String(1))  # 1 ký tự cho avatar

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # tự ghi thời điểm tạo — dấu vết hữu ích, không cần truyền vào
