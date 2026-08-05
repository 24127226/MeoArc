# ╔══════════════════════════════════════════════════════════════════╗
# ║ alembic/env.py — CẦU NỐI ALEMBIC ↔ CẤU HÌNH CỦA APP               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Vì sao cần Alembic: `Base.metadata.create_all` chỉ TẠO BẢNG MỚI,   ║
# ║ KHÔNG sửa bảng đã có. Thêm một cột vào bảng đang chạy là nó im      ║
# ║ lặng bỏ qua — đúng vấn đề nhóm từng gặp và phải né bằng cách tạo    ║
# ║ bảng riêng `session_providers`. Trên sản phẩm thật, đổi schema mà   ║
# ║ không có công cụ di trú thì hoặc mất dữ liệu, hoặc phải sửa tay     ║
# ║ trên máy chủ thật lúc nửa đêm.                                     ║
# ║                                                                    ║
# ║ File này KHÔNG chép cứng chuỗi kết nối: nó đọc đúng `DATABASE_URL`  ║
# ║ mà app đang dùng, nên di trú luôn chạy trên cùng database với app.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Cho phép import `app.*` khi chạy lệnh alembic từ thư mục src/backend
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.db import Base  # noqa: E402

# Nạp TẤT CẢ model để Base.metadata biết đủ bảng.
# ⚠️ Thiếu một dòng import ở đây thì autogenerate tưởng bảng đó "thừa" và sinh
# lệnh XOÁ BẢNG — mất sạch dữ liệu. Thêm model mới thì nhớ thêm vào danh sách này.
import app.models.audit  # noqa: E402,F401
import app.models.conversation  # noqa: E402,F401
import app.models.email_store  # noqa: E402,F401
import app.models.notification  # noqa: E402,F401
import app.models.session  # noqa: E402,F401
import app.models.session_provider  # noqa: E402,F401
import app.models.subscription  # noqa: E402,F401
import app.models.user  # noqa: E402,F401

config = context.config

# Chuỗi kết nối: ưu tiên cái người gọi đã chỉ định, chỉ tự điền khi chưa có.
#
# ⚠️ Trước đây dòng này ghi đè VÔ ĐIỀU KIỆN bằng DATABASE_URL của app. Hậu quả:
# ai chạy di trú với một database khác (test tự động, kiểm thử trên bản sao,
# dựng môi trường mới) đều bị kéo ngược về DATABASE_URL thật — tức là có thể
# LỠ TAY CHẠY DI TRÚ LÊN DATABASE ĐANG PHỤC VỤ NGƯỜI DÙNG.
# Giờ chỉ điền khi alembic.ini còn để giá trị mẫu 'driver://...'.
_url = config.get_main_option("sqlalchemy.url", "") or ""
if not _url or _url.startswith("driver://"):
    # Escape '%' vì ConfigParser hiểu '%' là ký tự đặc biệt (mật khẩu hay có).
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Sinh câu lệnh SQL ra màn hình mà KHÔNG nối database.

    Dùng khi muốn ĐỌC TRƯỚC những gì sắp chạy trên máy chủ thật:
        alembic upgrade head --sql
    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy di trú thật trên database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # compare_type: bắt cả khi KIỂU cột đổi (mặc định Alembic bỏ qua)
            compare_type=True,
            # compare_server_default: bắt khi giá trị mặc định đổi
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
