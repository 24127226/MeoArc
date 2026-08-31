# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/session_provider.py — BẢNG 'session_providers'         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Ghi mỗi phiên (token) dùng nhà cung cấp email NÀO: 'google' |      ║
# ║ 'microsoft'. Tách bảng RIÊNG (thay vì thêm cột vào 'sessions') để   ║
# ║ KHÔNG phải migrate DB cũ — create_all tự tạo bảng mới này. Phiên    ║
# ║ không có dòng ở đây ⇒ mặc định 'google' (giữ luồng Gmail y nguyên). ║
# ║ Token access/refresh vẫn nằm ở cột google_* của 'sessions' (dùng    ║
# ║ chung — chỉ là chuỗi mã hoá, provider quyết định gọi Gmail hay Graph).║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class SessionProvider(Base):
    __tablename__ = "session_providers"

    token: Mapped[str] = mapped_column(ForeignKey("sessions.token"), primary_key=True)
    provider: Mapped[str] = mapped_column(String, default="google")  # 'google' | 'microsoft'
