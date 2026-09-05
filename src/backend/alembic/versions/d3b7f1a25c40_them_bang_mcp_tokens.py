"""them bang mcp_tokens — the ra vao cho MCP qua HTTP

Bang moi hoan toan, khong backfill, khong dung toi du lieu cu.

VI SAO CO BANG NAY: MCP qua stdio khong can xac thuc vi agent chay CUNG MAY voi
backend — ai chay duoc tien trinh thi von da co quyen tren may do. Mo HTTP la nem di
tien de ay: dia chi nam tren mang. Nen moi ket noi HTTP phai mang mot the, va the buoc
chat vao DUNG MOT nguoi dung.

COT `token_hash` GIU SHA-256, KHONG GIU THE GOC. CSDL bi lo la chuyen xay ra; giu the
goc thi ke doc duoc bang nay doc luon duoc hop thu cua moi nguoi. Giu bam thi bang chi
chung minh duoc the nao hop le, khong tai tao lai duoc the.

`ix_mcp_token_hash` UNIQUE: xac thuc tra bang bam nen day la duong nong nhat (agent
ngoai goi 3-10 tool lien tiep). UNIQUE cung chan hai dong cung mot bam.

Revision ID: d3b7f1a25c40
Revises: c7d1e39ab204
Create Date: 2026-09-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "d3b7f1a25c40"
down_revision: str | None = "c7d1e39ab204"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("tien_to", sa.String(length=16), nullable=False, server_default=""),
        sa.Column("ten", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_tokens_user_id", "mcp_tokens", ["user_id"])
    op.create_index("ix_mcp_token_hash", "mcp_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_mcp_token_hash", table_name="mcp_tokens")
    op.drop_index("ix_mcp_tokens_user_id", table_name="mcp_tokens")
    op.drop_table("mcp_tokens")
