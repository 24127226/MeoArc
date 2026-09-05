# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/mcp/xac_thuc.py — CỬA XÁC THỰC cho MCP qua HTTP                ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Cắm vào FastMCP bằng `TokenVerifier`. Mọi yêu cầu HTTP tới MCP đi  ║
# ║ qua đây TRƯỚC khi chạm tới bất kỳ tool nào — không có đường vòng.  ║
# ║                                                                    ║
# ║ Trả về `AccessToken.subject = str(user_id)`. Đó là mắt xích quan   ║
# ║ trọng nhất của cả tính năng: từ đây `_resolve_ctx` biết mình đang  ║
# ║ phục vụ AI, thay cho phép "lấy phiên đăng nhập mới nhất" của bản   ║
# ║ stdio. Phép đó đúng khi agent chạy cùng máy, và biến thành lỗ hổng ║
# ║ ngay khi cùng một tiến trình phục vụ nhiều người qua mạng.         ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import logging

from fastmcp.server.auth import AccessToken, TokenVerifier

from app.core.db import SessionLocal
from app.repo import mcp_token_repo

logger = logging.getLogger("app.mcp.xac_thuc")


class XacThucBangThe(TokenVerifier):
    """Xác thực Bearer token bằng bảng `mcp_tokens`."""

    async def verify_token(self, token: str) -> AccessToken | None:
        # Mở kết nối NẰM TRONG try: chính lúc mở là lúc dễ hỏng nhất (hết pool, mất
        # mạng tới CSDL). Để ngoài thì lỗi thoát khỏi cửa xác thực và đi tiếp lên tầng
        # trên — mà một ngoại lệ không ai bắt ở đúng chỗ xác thực là nơi các lỗi
        # "mở khi có sự cố" sinh ra.
        db = None
        try:
            db = SessionLocal()
            row = mcp_token_repo.xac_thuc(db, token)
            if row is None:
                # KHÔNG log thẻ, kể cả một phần, kể cả khi nó sai. Thẻ sai hôm nay có
                # thể là thẻ đúng gõ nhầm một ký tự — log lại là tự chép bí mật vào
                # một nơi có ít lớp bảo vệ hơn hẳn CSDL.
                logger.info("MCP-HTTP: thẻ không hợp lệ hoặc đã hết hạn/thu hồi")
                return None
            mcp_token_repo.danh_dau_da_dung(db, row)
            return AccessToken(
                token=token,
                client_id=f"mcp-token-{row.id}",
                scopes=["mailbox"],
                # `subject` là thứ DUY NHẤT nối yêu cầu HTTP này với một người dùng.
                subject=str(row.user_id),
                expires_at=int(row.expires_at.timestamp()) if row.expires_at else None,
            )
        except Exception:
            # Hỏng CSDL thì TỪ CHỐI, không mở cửa. Một cửa xác thực "mở khi có sự cố"
            # là cửa không khoá — và sự cố là thứ kẻ tấn công tạo ra được.
            logger.warning("MCP-HTTP: lỗi khi xác thực thẻ — từ chối", exc_info=True)
            return None
        finally:
            if db is not None:
                db.close()
