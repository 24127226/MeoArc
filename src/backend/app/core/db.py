# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/db.py — KẾT NỐI DATABASE (tầng core/, hạ tầng dùng chung) ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: mở "đường ống" tới database để các tầng repo/ dùng.       ║
# ║ Ở đây dùng SQLAlchemy (ORM) + SQLite.                              ║
# ║  • ORM = "người phiên dịch": ta viết object Python, nó dịch ra SQL. ║
# ║  • SQLite = database nằm trong MỘT FILE (meoarc.db) — không cần     ║
# ║    cài server DB; rất hợp để học. Lên thật chỉ cần đổi URL.         ║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Địa chỉ database. "sqlite:///./meoarc.db" = file meoarc.db ngay thư mục dự án.
# Đổi sang Postgres/Supabase sau này: chỉ thay dòng URL này, phần còn lại giữ nguyên.
DATABASE_URL = "sqlite:///./meoarc.db"

# engine = đường ống tới DB. (check_same_thread=False: cần cho SQLite khi web đa luồng.)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

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
