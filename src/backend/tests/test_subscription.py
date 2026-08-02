"""test_subscription.py — Gói + hạn mức token (freemium) chạy OFFLINE.

Kiểm: mặc định gói free; cộng token vào ngày/tháng; CHẠM trần → over_quota;
sang kỳ mới tự reset; _turn_tokens đo đúng theo usage_metadata (và fallback).

Chạy: uv run pytest tests/test_subscription.py -v
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _mem_db():
    from app.core.db import Base
    import app.models.user  # noqa: F401
    import app.models.subscription  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def test_mac_dinh_free_va_cong_token():
    from app.repo import subscription_repo
    from app.core.plans import tier_limits

    db = _mem_db()
    sub = subscription_repo.get_or_create(db, 1)
    assert sub.tier == "free"
    assert subscription_repo.is_over_quota(db, sub) is False

    subscription_repo.add_usage(db, sub, 3000)
    st = subscription_repo.status(db, sub)
    assert st["daily"]["used"] == 3000 and st["monthly"]["used"] == 3000
    assert st["daily"]["remaining"] == tier_limits("free")["daily_tokens"] - 3000


def test_cham_tran_ngay_thi_over_quota():
    from app.repo import subscription_repo
    from app.core.plans import tier_limits

    db = _mem_db()
    sub = subscription_repo.get_or_create(db, 2)
    subscription_repo.add_usage(db, sub, tier_limits("free")["daily_tokens"])  # dùng đúng trần ngày
    assert subscription_repo.is_over_quota(db, sub) is True


def test_sang_ngay_moi_tu_reset():
    from app.repo import subscription_repo

    db = _mem_db()
    sub = subscription_repo.get_or_create(db, 3)
    # Giả lập "hôm qua đã tiêu kịch trần"
    sub.day_key, sub.tokens_today = "2000-01-01", 10_000_000
    db.commit()
    # Truy cập hôm nay → _roll_period reset bộ đếm ngày về 0
    assert subscription_repo.is_over_quota(db, sub) is False
    assert subscription_repo.status(db, sub)["daily"]["used"] == 0


def test_pro_tran_cao_hon_free():
    from app.core.plans import tier_limits
    assert tier_limits("pro")["daily_tokens"] > tier_limits("free")["daily_tokens"]


def test_turn_tokens_theo_usage_metadata():
    from app.api.app import _turn_tokens
    from langchain_core.messages import HumanMessage, AIMessage

    msgs = [
        AIMessage(content="cũ", usage_metadata={"input_tokens": 9, "output_tokens": 9, "total_tokens": 999}),
        HumanMessage(content="liệt kê thư"),  # ← mốc lượt hiện tại
        AIMessage(content="ok", usage_metadata={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}),
    ]
    # Chỉ tính từ HumanMessage cuối → 150, KHÔNG cộng 999 của lượt cũ.
    assert _turn_tokens(msgs) == 150


def test_turn_tokens_fallback_khong_metadata():
    from app.api.app import _turn_tokens
    from langchain_core.messages import HumanMessage, AIMessage

    msgs = [HumanMessage(content="x" * 40), AIMessage(content="y" * 40)]  # 80 ký tự
    assert _turn_tokens(msgs) == 20  # ~4 ký tự/token
