"""test_audit_notify.py — AuditLog + Notification (accountability) chạy OFFLINE.

Không đụng Gmail: test thẳng helper `_record` + 2 repo trên DB sqlite in-memory.
Kiểm: audit ghi đúng affected_email_ids (quan hệ ToolCall–Email); notification chỉ
sinh khi có `notify`; đọc/đếm/đánh dấu-đã-đọc đúng; KHÔNG đọc chéo user.

Chạy: uv run pytest tests/test_audit_notify.py -v
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _mem_db():
    """1 DB sqlite in-memory dùng chung 1 kết nối (StaticPool) → mọi thao tác cùng 1 DB."""
    from app.core.db import Base
    import app.models.user  # noqa: F401 — đăng ký bảng users (FK target)
    import app.models.audit  # noqa: F401
    import app.models.notification  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def test_record_ghi_audit_va_sinh_notification():
    from app.api.app import _record
    from app.repo import audit_repo, notification_repo

    db = _mem_db()
    _record(db, 1, action="send_email", tool_name="send_email", ids=["m1", "m2"],
            notify="Đã gửi email tới a@b.c.", notify_type="success")
    _record(db, 1, action="mark_read", ids=["m3"])  # audit-only — KHÔNG notify

    audits = audit_repo.list_recent(db, 1)
    assert len(audits) == 2
    assert audits[0].action == "mark_read"  # mới nhất trước
    send = next(a for a in audits if a.action == "send_email")
    assert send.affected_email_ids == ["m1", "m2"]  # ← quan hệ ToolCall–Email (thay Toolcall_Email)

    notifs = notification_repo.list_for_user(db, 1)
    assert len(notifs) == 1, "chỉ send mới sinh notification, mark_read thì không"
    assert notifs[0].message.startswith("Đã gửi")
    assert notification_repo.unread_count(db, 1) == 1


def test_notification_mark_read_va_khong_doc_cheo():
    from app.repo import notification_repo

    db = _mem_db()
    n = notification_repo.create(db, user_id=7, message="X")
    assert notification_repo.unread_count(db, 7) == 1
    notification_repo.mark_read(db, 7, n.id)
    assert notification_repo.unread_count(db, 7) == 0

    # user KHÁC không đánh dấu-đọc được thông báo của user 7
    n2 = notification_repo.create(db, user_id=7, message="Y")
    assert notification_repo.mark_read(db, 999, n2.id) is None
    assert notification_repo.unread_count(db, 7) == 1


def test_audit_chi_thay_cua_minh():
    from app.repo import audit_repo

    db = _mem_db()
    audit_repo.log(db, user_id=1, action="delete", affected_email_ids=["a"])
    audit_repo.log(db, user_id=2, action="delete", affected_email_ids=["b"])
    rows1 = audit_repo.list_recent(db, 1)
    assert len(rows1) == 1 and rows1[0].affected_email_ids == ["a"]
