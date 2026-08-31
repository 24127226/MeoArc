"""them bang user_preferences (PA2 muc 1.5.2)

Bang so thich ca nhan: ten xung ho, giong van, chu ky, dan do rieng. Day la thu
lam tro ly viet ra GIONG CUA NGUOI NAY thay vi giong chung chung.

Quan he 1-1 voi users: user_id vua la khoa chinh vua la khoa ngoai, nen cau truc
TU CAM mot nguoi co hai bo so thich — khong can code kiem tra. Cung thu phap voi
confirmation_request o muc 1.5.23.

Khong backfill: ban ghi duoc tao khi nguoi dung mo trang cai dat lan dau
(user_preference_repo.get_or_create). Nguoi dung cu vi the khong can script va du lieu.

Revision ID: a1f4c9d2e7b8
Revises: bc4d6abd7c92
Create Date: 2026-08-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "a1f4c9d2e7b8"
down_revision: str | None = "bc4d6abd7c92"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(), nullable=False, server_default="vi"),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("theme", sa.String(), nullable=False, server_default="system"),
        sa.Column("tone_preference", sa.String(), nullable=False, server_default="friendly"),
        sa.Column("signature_note", sa.Text(), nullable=True),
        sa.Column("custom_instruction", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        # ondelete CASCADE: xoa nguoi dung thi so thich di theo. De lai la rac tro
        # toi mot user_id khong con ton tai.
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
