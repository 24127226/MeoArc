"""test_mailbox_sync.py — EMAIL STORE-OF-RECORD + SYNC ENGINE chạy OFFLINE.

Không đụng Gmail thật: monkeypatch mail.list_messages / gmail_service.* rồi kiểm:
  • initial_sync kéo thư vào DB → đọc-từ-DB (get_page/get_one) đúng, body MÃ HOÁ round-trip.
  • incremental_sync theo history.list: thư 'added' fetch full + 'deleted' dời sang trash,
    con trỏ historyId cập nhật.
  • handle_pubsub map emailAddress → user → phiên → đồng bộ.

Chạy: uv run pytest tests/test_mailbox_sync.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.schemas.email import Email


def _mem_db():
    from app.core.db import Base
    import app.models.user  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.session_provider  # noqa: F401
    import app.models.email_store  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def _email(mid: str, subject="Hi", body=None, unread=True, date="01/07/2026 09:00", folder="inbox"):
    return Email(
        id=mid, sender="An", senderEmail="an@x.com", senderInitial="A", to="me@x.com",
        subject=subject, preview="preview " + mid, body=body or ["đoạn 1 " + mid],
        time="09:00", date=date, unread=unread, starred=False, category="sky",
        label="Cá nhân", folder=folder, threadId="t-" + mid,
    )


def test_initial_sync_then_read_from_db(monkeypatch):
    from app.services import sync_service
    from app.repo import email_store_repo

    db = _mem_db()

    def fake_list(provider, token, *, folder="inbox", max_results=40, bypass_cache=False, **kw):
        if folder == "inbox":
            return [_email("m1", date="02/07/2026 10:00"),
                    _email("m2", date="01/07/2026 08:00", unread=False)], None
        return [], None

    monkeypatch.setattr(sync_service.mail, "list_messages", fake_list)
    monkeypatch.setattr(sync_service.gmail_service, "get_profile_history_id", lambda t: "1000")

    n = sync_service.initial_sync(db, user_id=1, provider="google", token="tok")
    assert n == 2

    # Đọc TỪ DB — không gọi Gmail.
    items, nxt = email_store_repo.get_page(db, 1, "google", folder="inbox", limit=30)
    assert [e.id for e in items] == ["m1", "m2"]      # mới nhất trước (received_at desc)
    assert items[1].unread is False
    assert nxt is None

    # get_one dựng lại Email + body mã hoá round-trip đúng.
    one = email_store_repo.get_one(db, 1, "google", "m1")
    assert one is not None and one.body == ["đoạn 1 m1"] and one.threadId == "t-m1"

    # lọc chưa đọc
    unread_items, _ = email_store_repo.get_page(db, 1, "google", unread=True, limit=30)
    assert [e.id for e in unread_items] == ["m1"]

    # con trỏ historyId đã ghim
    state = sync_service._get_state(db, 1, "google")
    assert state.history_id == "1000"


def test_incremental_sync_history(monkeypatch):
    from app.services import sync_service
    from app.repo import email_store_repo

    db = _mem_db()
    # Seed: đã có m1 trong inbox + con trỏ history 1000.
    email_store_repo.upsert(db, 1, "google", _email("m1"), folder="inbox", full=True)
    state = sync_service._get_state(db, 1, "google")
    state.history_id = "1000"
    db.commit()

    monkeypatch.setattr(sync_service.gmail_service, "list_history",
                        lambda t, h: {"added": ["m2"], "deleted": ["m1"], "updated": [],
                                      "history_id": "1005"})
    monkeypatch.setattr(sync_service.gmail_service, "get_message",
                        lambda t, mid: _email(mid, subject="Mới", body=["thân đầy đủ"]))

    n = sync_service.incremental_sync(db, 1, "google", "tok")
    assert n == 1                                   # 1 thư added fetch full

    # m2 thêm với body đầy đủ; m1 bị dời sang trash.
    m2 = email_store_repo.get_one(db, 1, "google", "m2")
    assert m2 is not None and m2.body == ["thân đầy đủ"] and m2.folder == "inbox"
    m1 = email_store_repo.get_one(db, 1, "google", "m1")
    assert m1 is not None and m1.folder == "trash"
    assert sync_service._get_state(db, 1, "google").history_id == "1005"


def test_incremental_falls_back_to_initial_when_cold(monkeypatch):
    from app.services import sync_service

    db = _mem_db()
    calls = {"list": 0}

    def fake_list(provider, token, *, folder="inbox", max_results=40, bypass_cache=False, **kw):
        calls["list"] += 1
        return ([_email("mX")] if folder == "inbox" else []), None

    monkeypatch.setattr(sync_service.mail, "list_messages", fake_list)
    monkeypatch.setattr(sync_service.gmail_service, "get_profile_history_id", lambda t: "1")

    # DB lạnh + chưa có history → phải chạy initial_sync (gọi list_messages cho các thư mục).
    n = sync_service.incremental_sync(db, 1, "google", "tok")
    assert n == 1 and calls["list"] >= 1


def test_handle_pubsub(monkeypatch):
    from app.services import sync_service
    from app.repo import email_store_repo
    from app.models.user import User
    from app.models.session import AuthSession
    from app.models.session_provider import SessionProvider

    db = _mem_db()
    db.add(User(id=1, email="quan@x.com", name="Quan", initial="Q"))
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    db.add(AuthSession(token="sess1", user_id=1, expires_at=future,
                       google_access_token="tok", google_refresh_token="r",
                       google_token_expiry=future))
    db.add(SessionProvider(token="sess1", provider="google"))
    email_store_repo.upsert(db, 1, "google", _email("m1"), folder="inbox", full=True)
    state = sync_service._get_state(db, 1, "google")
    state.history_id = "1000"
    db.commit()

    monkeypatch.setattr(sync_service.gmail_service, "list_history",
                        lambda t, h: {"added": ["m9"], "deleted": [], "updated": [],
                                      "history_id": "1010"})
    monkeypatch.setattr(sync_service.gmail_service, "get_message",
                        lambda t, mid: _email(mid, body=["nội dung m9"]))

    n = sync_service.handle_pubsub(db, "quan@x.com")
    assert n == 1
    assert email_store_repo.get_one(db, 1, "google", "m9") is not None

    # email không tồn tại → 0, không nổ.
    assert sync_service.handle_pubsub(db, "khong-ton-tai@x.com") == 0
