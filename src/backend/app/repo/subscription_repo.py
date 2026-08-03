# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/subscription_repo.py — gói + hạn mức token per user      ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import date
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.core.plans import tier_limits, is_valid_tier, DEFAULT_TIER


def get_or_create(db: Session, user_id: int) -> Subscription:
    s = db.get(Subscription, user_id)
    if s is None:
        s = Subscription(user_id=user_id, tier=DEFAULT_TIER)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _roll_period(db: Session, s: Subscription) -> None:
    """Sang NGÀY/THÁNG mới → reset bộ đếm tương ứng về 0 (lazy, khi có truy cập)."""
    today = date.today().isoformat()
    month = today[:7]
    changed = False
    if s.day_key != today:
        s.day_key, s.tokens_today, changed = today, 0, True
    if s.month_key != month:
        s.month_key, s.tokens_month, changed = month, 0, True
    if changed:
        db.commit()


def status(db: Session, s: Subscription) -> dict:
    """Trạng thái để FE hiển thị: tier + đã dùng/trần + còn lại (ngày & tháng)."""
    _roll_period(db, s)
    lim = tier_limits(s.tier)
    return {
        "tier": s.tier,
        "tierLabel": lim["label"],
        "isActive": s.is_active,
        "daily": {"used": s.tokens_today, "limit": lim["daily_tokens"],
                  "remaining": max(0, lim["daily_tokens"] - s.tokens_today)},
        "monthly": {"used": s.tokens_month, "limit": lim["monthly_tokens"],
                    "remaining": max(0, lim["monthly_tokens"] - s.tokens_month)},
    }


def is_over_quota(db: Session, s: Subscription) -> bool:
    """True nếu đã CHẠM/vượt trần token ngày HOẶC tháng của tier."""
    _roll_period(db, s)
    lim = tier_limits(s.tier)
    return s.tokens_today >= lim["daily_tokens"] or s.tokens_month >= lim["monthly_tokens"]


def add_usage(db: Session, s: Subscription, tokens: int) -> None:
    """Cộng token đã tiêu sau 1 lượt agent. Âm/0 thì bỏ qua."""
    if tokens <= 0:
        return
    _roll_period(db, s)
    s.tokens_today += tokens
    s.tokens_month += tokens
    db.commit()


def set_tier(db: Session, user_id: int, tier: str) -> Subscription:
    """Đổi gói (dùng khi nâng cấp/hạ cấp — hoặc admin/seed cho demo)."""
    s = get_or_create(db, user_id)
    s.tier = tier if is_valid_tier(tier) else DEFAULT_TIER
    db.commit()
    db.refresh(s)
    return s
