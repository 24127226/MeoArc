"""Kho thẻ ra vào MCP-HTTP: phát, xác thực, liệt kê, thu hồi.

Thẻ gốc CHỈ tồn tại trong bộ nhớ đúng một lần, ở hàm `tao()`. Từ đó trở đi mọi thứ
trong hệ thống — CSDL, log, thông báo lỗi — chỉ còn thấy bản băm.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select

from app.models.mcp_token import McpToken

# Tiền tố cố định để thẻ NHÌN LÀ BIẾT của MeoArc. Không phải trang trí: người ta hay
# dán nhầm thẻ vào chỗ công khai, và các máy quét bí mật (GitHub secret scanning...)
# bắt theo đúng loại tiền tố này.
TIEN_TO = "meoarc_mcp_"
HAN_MAC_DINH = 30      # ngày
HAN_TOI_DA = 365


def _bam(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def tao(db, user_id: int, ten: str = "", so_ngay: int = HAN_MAC_DINH) -> tuple[McpToken, str]:
    """Phát 1 thẻ mới. Trả (bản ghi, THẺ GỐC) — thẻ gốc chỉ có ở đây, hiện đúng 1 lần.

    32 byte ngẫu nhiên từ `secrets` (nguồn của hệ điều hành), không phải `random`:
    `random` sinh dãy đoán được nếu biết mầm, và một thẻ đoán được thì bằng không có thẻ.
    """
    so_ngay = max(1, min(int(so_ngay or HAN_MAC_DINH), HAN_TOI_DA))
    raw = TIEN_TO + secrets.token_urlsafe(32)
    row = McpToken(
        user_id=user_id,
        token_hash=_bam(raw),
        tien_to=raw[: len(TIEN_TO) + 6],
        ten=(ten or "").strip()[:80],
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=so_ngay),
        revoked=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, raw


def xac_thuc(db, raw: str) -> McpToken | None:
    """Thẻ gốc → bản ghi còn hiệu lực, hoặc None.

    Tra bằng BĂM chứ không duyệt bảng rồi so từng cái: tra băm là một phép tìm theo
    index, thời gian không phụ thuộc nội dung thẻ, nên không rò rỉ gì qua thời gian đáp.
    """
    if not raw or not raw.startswith(TIEN_TO):
        return None
    row = db.scalars(
        select(McpToken).where(McpToken.token_hash == _bam(raw))
    ).first()
    if row is None or row.revoked:
        return None
    if row.expires_at and row.expires_at <= datetime.utcnow():
        return None
    return row


def danh_dau_da_dung(db, row: McpToken) -> None:
    """Ghi mốc dùng gần nhất. Tách khỏi `xac_thuc` để phần xác thực thuần đọc —
    tiện gọi trong các đường không được phép ghi."""
    row.last_used_at = datetime.utcnow()
    db.commit()


def liet_ke(db, user_id: int) -> list[McpToken]:
    return list(db.scalars(
        select(McpToken)
        .where(McpToken.user_id == user_id)
        .order_by(McpToken.created_at.desc())
    ))


def thu_hoi(db, user_id: int, token_id: int) -> bool:
    """Thu hồi 1 thẻ CỦA CHÍNH MÌNH.

    `user_id` nằm trong điều kiện lọc chứ không phải kiểm sau: thiếu nó thì endpoint
    thu hồi trở thành chỗ ai cũng vô hiệu hoá được thẻ của người khác chỉ bằng cách
    đoán số id — một lỗ hổng trông rất vô hại khi đọc lướt.
    """
    row = db.scalars(
        select(McpToken).where(McpToken.id == token_id, McpToken.user_id == user_id)
    ).first()
    if row is None or row.revoked:
        return False
    row.revoked = True
    db.commit()
    return True
