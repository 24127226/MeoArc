# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/mcp_token.py — THẺ RA VÀO cho MCP qua HTTP              ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ VÌ SAO PHẢI CÓ BẢNG NÀY                                            ║
# ║ MCP qua stdio không cần xác thực: agent chạy CÙNG MÁY với backend, ║
# ║ ai chạy được tiến trình thì vốn đã có quyền trên máy đó. Mở HTTP   ║
# ║ thì tiền đề ấy mất sạch — địa chỉ nằm trên Internet, và            ║
# ║ `_resolve_ctx` bản stdio lấy PHIÊN ĐĂNG NHẬP MỚI NHẤT trong DB.    ║
# ║ Phơi nguyên xi ra HTTP nghĩa là ai gõ trúng địa chỉ cũng thao tác  ║
# ║ hộ thư của người vừa đăng nhập. Nên mỗi kết nối HTTP phải mang một ║
# ║ thẻ, và thẻ đó buộc chặt vào ĐÚNG MỘT người dùng.                  ║
# ║                                                                    ║
# ║ LƯU BĂM, KHÔNG LƯU THẺ GỐC                                         ║
# ║ CSDL bị lộ là chuyện xảy ra. Lưu thẻ gốc thì kẻ đọc được bảng này  ║
# ║ đọc luôn được hộp thư của mọi người dùng. Lưu SHA-256 thì bảng chỉ ║
# ║ chứng minh được thẻ nào hợp lệ, không tái tạo lại được thẻ. Đổi    ║
# ║ lại: thẻ gốc chỉ hiện ĐÚNG MỘT LẦN lúc tạo, mất thì tạo cái khác.  ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class McpToken(Base):
    """1 thẻ ra vào MCP-HTTP, thuộc về đúng 1 người dùng."""

    __tablename__ = "mcp_tokens"
    __table_args__ = (
        # Tra cứu lúc xác thực LUÔN đi bằng băm — đánh index để mỗi lượt gọi tool
        # không phải quét bảng. Agent ngoài gọi 3-10 tool liên tiếp là chuyện thường.
        Index("ix_mcp_token_hash", "token_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # SHA-256 hex của thẻ gốc. KHÔNG BAO GIỜ chứa thẻ gốc.
    token_hash: Mapped[str] = mapped_column(String(64))
    # 8 ký tự đầu của thẻ, chỉ để người dùng NHẬN RA thẻ nào trong danh sách mà thu
    # hồi cho đúng. Ngắn tới mức không đoán ngược được phần còn lại (còn 32 byte ngẫu nhiên).
    tien_to: Mapped[str] = mapped_column(String(16), default="")
    ten: Mapped[str] = mapped_column(String(80), default="")   # "Claude Desktop máy nhà"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # CÓ HẠN, không phải tuỳ chọn. Thẻ sống mãi thì một lần rò rỉ là rò rỉ vĩnh viễn,
    # và không ai nhớ nổi mình đã phát bao nhiêu thẻ từ năm ngoái.
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    # Để người dùng thấy thẻ nào đang thực sự được dùng — thẻ im lặng ba tháng thì
    # thu hồi không mất gì, còn để đó thì chỉ là bề mặt tấn công thừa.
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
