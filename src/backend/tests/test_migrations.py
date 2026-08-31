# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_migrations.py — DI TRÚ DATABASE (Alembic)              ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Hai rủi ro âm thầm nhất khi dùng Alembic, cả hai đều không lộ ra   ║
# ║ cho tới lúc triển khai thật:                                       ║
# ║                                                                    ║
# ║  1. Sửa model nhưng QUÊN sinh bản di trú. Máy dev vẫn chạy ngon vì  ║
# ║     create_all tạo bảng mới; máy chủ thật thì thiếu cột → sập.      ║
# ║  2. Bản di trú không dựng lại được schema từ database trống (thiếu  ║
# ║     import, thiếu bảng...). Chỉ phát hiện khi dựng môi trường mới.  ║
# ║                                                                    ║
# ║ Hai test dưới đây bắt đúng hai lỗi đó, chạy được trên SQLite nên    ║
# ║ không cần Postgres trong CI.                                       ║
# ╚══════════════════════════════════════════════════════════════════╝

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"


def _all_models_metadata():
    """Nạp mọi model rồi trả metadata — đúng thứ Alembic so sánh khi autogenerate."""
    import app.models.audit  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.email_store  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.session_provider  # noqa: F401
    import app.models.subscription  # noqa: F401
    import app.models.user  # noqa: F401
    from app.core.db import Base
    return Base.metadata


def test_co_it_nhat_mot_ban_di_tru():
    """Thư mục versions rỗng nghĩa là chưa ai sinh di trú — schema không được quản lý."""
    files = [p for p in VERSIONS_DIR.glob("*.py") if not p.name.startswith("__")]
    assert files, "Chưa có bản di trú nào trong alembic/versions"


def test_moi_model_deu_co_trong_env_py():
    """env.py phải import ĐỦ model.

    Thiếu một dòng import thì autogenerate tưởng bảng đó 'thừa' và sinh lệnh
    XOÁ BẢNG — mất sạch dữ liệu của bảng ấy khi chạy di trú.
    """
    env_src = (BACKEND_DIR / "alembic" / "env.py").read_text(encoding="utf-8")
    models_dir = BACKEND_DIR / "app" / "models"
    thieu = []
    for p in models_dir.glob("*.py"):
        if p.stem.startswith("__"):
            continue
        if f"app.models.{p.stem}" not in env_src:
            thieu.append(p.stem)
    assert not thieu, (
        f"alembic/env.py thiếu import model: {thieu}. "
        "Thiếu import thì autogenerate sẽ sinh lệnh xoá bảng tương ứng."
    )


def test_ban_di_tru_dung_lai_duoc_schema_tu_database_trong(tmp_path):
    """Chạy toàn bộ di trú lên một database TRỐNG rồi đối chiếu với model.

    Đây là kịch bản 'dựng môi trường mới' — nếu bản di trú thiếu bảng hoặc thiếu
    import, test này hỏng ngay tại đây thay vì hỏng lúc triển khai.
    """
    pytest.importorskip("alembic")
    from alembic import command
    from alembic.config import Config

    db_file = tmp_path / "migrate_check.db"
    url = f"sqlite:///{db_file}"

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    bang_thuc_te = set(inspect(engine).get_table_names()) - {"alembic_version"}
    bang_theo_model = set(_all_models_metadata().tables)

    thieu = bang_theo_model - bang_thuc_te
    assert not thieu, (
        f"Di trú KHÔNG tạo ra các bảng: {sorted(thieu)}. "
        "Nhiều khả năng model được sửa mà quên chạy `alembic revision --autogenerate`."
    )
