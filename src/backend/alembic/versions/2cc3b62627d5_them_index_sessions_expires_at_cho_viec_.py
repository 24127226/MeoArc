"""them index sessions.expires_at cho viec don du lieu

Revision ID: 2cc3b62627d5
Revises: 5ac173f90530
Create Date: 2026-08-05 12:46:25.172164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cc3b62627d5'
down_revision: Union[str, Sequence[str], None] = '5ac173f90530'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_sessions_expires_at"


def _co_index() -> bool:
    """Index đã tồn tại chưa?"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    return INDEX_NAME in {i["name"] for i in inspect(bind).get_indexes("sessions")}


def upgrade() -> None:
    """Thêm index cho việc dọn phiên hết hạn.

    Phải KIỂM TRA TRƯỚC vì bản này gặp hai tình huống khác nhau:
      • Database ĐÃ CÓ TỪ TRƯỚC: được `alembic stamp` sang baseline nên chưa hề
        chạy lệnh tạo bảng — index thật sự còn thiếu, cần tạo.
      • Database MỚI DỰNG: baseline chạy đầy đủ và đã tạo sẵn index này rồi
        (vì baseline được sinh sau khi model có index) — tạo lại sẽ lỗi trùng tên.
    Kiểm tra trước giúp cùng một bản di trú chạy đúng ở cả hai nơi.
    """
    if not _co_index():
        op.create_index(op.f(INDEX_NAME), "sessions", ["expires_at"], unique=False)


def downgrade() -> None:
    """Bỏ index (chỉ khi nó đang tồn tại)."""
    if _co_index():
        op.drop_index(op.f(INDEX_NAME), table_name="sessions")
