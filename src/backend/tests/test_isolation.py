# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_isolation.py — CÔ LẬP DỮ LIỆU GIỮA NGƯỜI DÙNG          ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là lỗi TỆ NHẤT mà một ứng dụng email có thể mắc: người này đọc ║
# ║ được thư của người kia. Nó không làm app sập, không hiện trong log, ║
# ║ và có thể sống nhiều tháng trước khi bị phát hiện — lúc đó thì đã   ║
# ║ là sự cố lộ dữ liệu phải đi báo cáo.                               ║
# ║                                                                    ║
# ║ Hiện mọi truy vấn lọc `user_id` BẰNG TAY. Chỉ cần MỘT chỗ quên là   ║
# ║ thủng. Bộ test này canh đúng chỗ đó, ở hai tầng:                    ║
# ║   1. Tầng truy vấn: repo có thật sự lọc theo người không.           ║
# ║   2. Tầng mã nguồn: có hàm nào đọc dữ liệu mà quên điều kiện user.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def db():
    import app.models.audit  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.email_store  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.subscription  # noqa: F401
    import app.models.user  # noqa: F401
    from app.core.db import Base

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    try:
        yield s
    finally:
        s.close()


def _hai_nguoi(db):
    from app.models.user import User
    a = User(email="an@meoarc.test", name="An", initial="A")
    b = User(email="binh@meoarc.test", name="Binh", initial="B")
    db.add_all([a, b])
    db.commit()
    db.refresh(a)
    db.refresh(b)
    return a, b


def test_khong_doc_duoc_thu_cua_nguoi_khac(db):
    """Kịch bản lộ dữ liệu kinh điển: An mở hộp thư và thấy thư của Bình."""
    from app.models.email_store import StoredEmail
    from app.repo import email_store_repo

    an, binh = _hai_nguoi(db)
    db.add(StoredEmail(user_id=an.id, provider="google", g_id="thu-cua-an", folder="inbox"))
    db.add(StoredEmail(user_id=binh.id, provider="google", g_id="thu-MAT-cua-binh", folder="inbox"))
    db.commit()

    items, _ = email_store_repo.get_page(db, an.id, "google", folder="inbox", limit=50)
    ids = [e.id for e in items]

    assert "thu-cua-an" in ids
    assert "thu-MAT-cua-binh" not in ids, "LỘ DỮ LIỆU: An đọc được thư của Bình"


def test_khong_doc_duoc_thong_bao_cua_nguoi_khac(db):
    from app.models.notification import Notification
    from app.repo import notification_repo

    an, binh = _hai_nguoi(db)
    db.add(Notification(user_id=an.id, message="cua An"))
    db.add(Notification(user_id=binh.id, message="RIENG TU cua Binh"))
    db.commit()

    ket_qua = notification_repo.list_for_user(db, an.id)
    noi_dung = [n.message for n in (ket_qua.get("items") if isinstance(ket_qua, dict) else ket_qua)]

    assert "cua An" in noi_dung
    assert "RIENG TU cua Binh" not in noi_dung


def test_khong_doc_duoc_hoi_thoai_cua_nguoi_khac(db):
    from app.repo import conversation_repo

    an, binh = _hai_nguoi(db)
    c_an = conversation_repo.get_or_create(db, None, an.id)
    conversation_repo.get_or_create(db, None, binh.id)

    cua_an = conversation_repo.list_for_user(db, an.id)
    ids = [c.id for c in cua_an]

    assert c_an.id in ids
    assert len(ids) == 1, "Danh sách hội thoại phải chỉ chứa phiên của chính người đó"


def test_moi_ham_doc_du_lieu_deu_nhan_user_id():
    """Chốt chặn ở tầng MÃ NGUỒN.

    Mọi hàm đọc dữ liệu trong các repo có gắn với người dùng đều phải nhận
    `user_id`. Hàm nào quên tham số này gần như chắc chắn đang trả về dữ liệu
    của TẤT CẢ mọi người — đúng kiểu lỗi âm thầm mà test dữ liệu ở trên có thể
    bỏ sót nếu chưa ai gọi tới hàm đó.
    """
    repo_theo_nguoi = [
        "email_store_repo.py", "notification_repo.py",
        "conversation_repo.py", "audit_repo.py",
    ]
    # Các hàm dùng chung/nội bộ không gắn với một người cụ thể
    mien_tru = {"upsert", "delete_all", "purge", "log", "create", "get_or_create", "mark_read"}

    vi_pham = []
    for ten_file in repo_theo_nguoi:
        p = BACKEND_DIR / "app" / "repo" / ten_file
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r"^def (\w+)\(([^)]*)\)", src, re.M):
            ten, tham_so = m.group(1), m.group(2)
            if ten.startswith("_") or ten in mien_tru:
                continue
            if not ten.startswith(("list", "get", "search", "count", "has", "find")):
                continue
            if "user_id" not in tham_so:
                vi_pham.append(f"{ten_file}::{ten}")

    assert not vi_pham, (
        "Các hàm đọc dữ liệu sau KHÔNG nhận user_id — nhiều khả năng đang trả về "
        f"dữ liệu của mọi người dùng: {vi_pham}"
    )
