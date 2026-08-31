# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_maintenance.py — DỌN DỮ LIỆU CŨ (retention)            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Ba bảng sessions/audit_logs/notifications chỉ THÊM mà không bớt.   ║
# ║ Test ở đây chứng minh việc dọn xoá ĐÚNG cái cần xoá và GIỮ LẠI     ║
# ║ cái còn giá trị — quan trọng nhất là KHÔNG đụng thông báo chưa đọc.║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.core import maintenance


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture()
def db():
    """DB SQLite trong RAM — mỗi test một cái sạch, không đụng dữ liệu thật."""
    import app.models.audit  # noqa: F401 — nạp để Base biết các bảng
    import app.models.notification  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.session_provider  # noqa: F401
    import app.models.user  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    try:
        yield s
    finally:
        s.close()


def _make_user(db):
    from app.models.user import User
    u = User(email="ai@meoarc.test", name="Ai Đó", initial="A")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_xoa_phien_het_han_giu_phien_con_han(db):
    """Phiên hết hạn không dùng được nữa nhưng vẫn chiếm chỗ → phải dọn.
    Phiên còn hạn thì tuyệt đối không được đụng (đang có người dùng)."""
    from app.models.session import AuthSession
    u = _make_user(db)
    db.add(AuthSession(token="het-han", user_id=u.id, expires_at=_now() - timedelta(hours=1)))
    db.add(AuthSession(token="con-han", user_id=u.id, expires_at=_now() + timedelta(hours=5)))
    db.commit()

    n = maintenance.purge_expired_sessions(db)

    assert n == 1
    con_lai = [s.token for s in db.query(AuthSession).all()]
    assert con_lai == ["con-han"], "Phiên còn hạn bị xoá nhầm là đá người dùng ra khỏi hệ thống"


def test_xoa_nhat_ky_qua_cu_giu_nhat_ky_gan_day(db):
    """Nhật ký là bằng chứng human-in-the-loop → chỉ cắt phần quá cũ."""
    from app.models.audit import AuditLog
    u = _make_user(db)
    db.add(AuditLog(user_id=u.id, action="cu", created_at=_now() - timedelta(days=400)))
    db.add(AuditLog(user_id=u.id, action="moi", created_at=_now() - timedelta(days=3)))
    db.commit()

    n = maintenance.purge_old_audit(db, days=180)

    assert n == 1
    assert [a.action for a in db.query(AuditLog).all()] == ["moi"]


def test_khong_xoa_thong_bao_chua_doc_du_rat_cu(db):
    """Điểm dễ sai nhất: thông báo CHƯA ĐỌC dù cũ tới đâu cũng phải giữ —
    người dùng chưa xem thì hệ thống không được tự ý bỏ đi."""
    from app.models.notification import Notification
    u = _make_user(db)
    old = _now() - timedelta(days=365)
    db.add(Notification(user_id=u.id, message="da doc, rat cu", read=True, created_at=old))
    db.add(Notification(user_id=u.id, message="CHUA doc, rat cu", read=False, created_at=old))
    db.add(Notification(user_id=u.id, message="da doc, moi", read=True,
                        created_at=_now() - timedelta(days=2)))
    db.commit()

    n = maintenance.purge_read_notifications(db, days=30)

    assert n == 1
    con_lai = sorted(x.message for x in db.query(Notification).all())
    assert con_lai == ["CHUA doc, rat cu", "da doc, moi"]


def test_chay_tron_mot_luot_tra_ve_so_dong_da_xoa(db):
    from app.models.audit import AuditLog
    from app.models.session import AuthSession
    u = _make_user(db)
    db.add(AuthSession(token="qua-han", user_id=u.id, expires_at=_now() - timedelta(days=2)))
    db.add(AuditLog(user_id=u.id, action="cu", created_at=_now() - timedelta(days=999)))
    db.commit()

    ket_qua = maintenance.run_maintenance(db)

    assert ket_qua["sessions"] == 1
    assert ket_qua["audit_logs"] == 1
    assert set(ket_qua) == {"sessions", "audit_logs", "notifications"}


def test_khoa_chong_trung_chi_mot_worker_duoc_chay():
    """Chạy nhiều worker thì cả bốn tiến trình đều muốn dọn cùng lúc.
    Khoá phải cho đúng MỘT người thắng trong mỗi chu kỳ."""
    ket = [maintenance.try_acquire_lock("test-lock-unique", ttl_s=60) for _ in range(4)]
    assert sum(ket) == 1, f"Phải đúng 1 worker được chạy, thực tế {sum(ket)}"
    assert ket[0] is True


def test_dem_so_dong_cac_bang_tich_luy(db):
    from app.models.audit import AuditLog
    u = _make_user(db)
    db.add(AuditLog(user_id=u.id, action="x", created_at=_now()))
    db.commit()

    sizes = maintenance.table_sizes(db)

    assert sizes["audit_logs"] == 1
    assert set(sizes) == {"sessions", "audit_logs", "notifications"}
