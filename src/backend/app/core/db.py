# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/db.py — KẾT NỐI DATABASE (tầng core/, hạ tầng dùng chung) ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: mở "đường ống" tới database để các tầng repo/ dùng.       ║
# ║ Dùng SQLAlchemy (ORM) — nhờ ORM, code KHÔNG đổi khi đổi loại DB.    ║
# ║  • Mặc định/commitment: PostgreSQL (đặt DATABASE_URL trong .env).   ║
# ║  • Chưa cấu hình → tự lùi SQLite (1 file) để máy chưa cài PG vẫn chạy.║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Lấy URL từ cấu hình (.env). Postgres: postgresql+psycopg://...  SQLite: sqlite:///./meoarc.db
DATABASE_URL = settings.database_url
_is_sqlite = DATABASE_URL.startswith("sqlite")

# connect_args chỉ cần cho SQLITE (check_same_thread=False để web đa luồng dùng được).
# Postgres là server thật, KHÔNG cần (và không hiểu) tham số này → chỉ truyền khi là SQLite.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,  # Postgres: kiểm tra kết nối còn sống trước khi dùng (tránh lỗi "connection đã đóng")
)

# SessionLocal = "một ca làm việc" với DB. Mỗi request mở 1 session, xong thì đóng.
# Vì sao không dùng 1 session chung mãi: mỗi request cần giao dịch (transaction) riêng,
# tránh dữ liệu lẫn lộn giữa các request.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base = lớp cha cho MỌI model (bảng). Model kế thừa Base thì SQLAlchemy mới "thấy" bảng đó.
Base = declarative_base()


def get_db():
    """Dependency cho FastAPI: mở 1 session, đưa vào route, ĐÓNG sau khi xong.
    `yield` (không `return`) để FastAPI chạy phần `finally` đóng session sau request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
