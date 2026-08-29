"""them bang don_dat_cho (Giai doan 3 — cong tien)

Moi lan dinh dat ve/phong la MOT dong o day, ghi TRUOC khi goi ra nha cung cap.

Cot quan trong nhat la `khoa_chong_trung` voi rang buoc UNIQUE. Do la thu khien bam
hai lan, mang dut giua chung, hai tab cung mo, hay thu lai — van chi ra MOT don.

VI SAO RANG BUOC O TANG CSDL, KHONG PHAI O TANG MA: kiem "da co don nay chua" bang
mot cau SELECT roi moi INSERT la kinh dien cua loi dua — hai yeu cau vao cung luc thi
ca hai deu thay "chua co". Chi rang buoc UNIQUE cua CSDL moi cat duoc, vi no la diem
tuan tu hoa duy nhat.

Khong backfill: bang moi hoan toan, chua co du lieu cu.

Revision ID: c7d1e39ab204
Revises: a1f4c9d2e7b8
Create Date: 2026-08-29
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "c7d1e39ab204"
down_revision: str | None = "a1f4c9d2e7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "don_dat_cho",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        # 64 ky tu du cho sha256 rut gon (48) va con cho neu sau nay doi cach sinh khoa.
        sa.Column("khoa_chong_trung", sa.String(length=64), nullable=False),
        sa.Column("loai", sa.String(length=16), nullable=False),
        sa.Column("mo_ta", sa.String(), nullable=False),
        sa.Column("so_tien_vnd", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trang_thai", sa.String(length=16), nullable=False,
                  server_default="dang_xu_ly"),
        sa.Column("chi_tiet", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ket_qua", sa.JSON(), nullable=True),
        sa.Column("nguoi_duyet", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        # ondelete CASCADE: xoa nguoi dung thi don di theo — de lai la rac tro toi mot
        # hang khong con ton tai.
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # UNIQUE la ly do ca bang nay ton tai. Dat ro rang thay vi dua vao `unique=True`
    # cua model, de doc ban di tru cung thay duoc rang buoc.
    op.create_index(
        "ix_don_dat_cho_khoa_chong_trung", "don_dat_cho",
        ["khoa_chong_trung"], unique=True,
    )
    op.create_index("ix_don_dat_cho_user_id", "don_dat_cho", ["user_id"])
    op.create_index("ix_don_dat_cho_trang_thai", "don_dat_cho", ["trang_thai"])
    # Tran chi tieu theo NGAY truy van "don thanh cong cua nguoi nay trong 24h qua".
    # Hai chi muc roi khong phuc vu duoc cau do bang mot chi muc gop.
    op.create_index(
        "ix_don_dat_cho_user_recent", "don_dat_cho", ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_don_dat_cho_user_recent", table_name="don_dat_cho")
    op.drop_index("ix_don_dat_cho_trang_thai", table_name="don_dat_cho")
    op.drop_index("ix_don_dat_cho_user_id", table_name="don_dat_cho")
    op.drop_index("ix_don_dat_cho_khoa_chong_trung", table_name="don_dat_cho")
    op.drop_table("don_dat_cho")
