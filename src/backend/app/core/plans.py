# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/plans.py — GÓI DỊCH VỤ (tier) + hạn mức token             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mô hình freemium giống các sản phẩm AI: mỗi tier có trần token/NGÀY ║
# ║ và /THÁNG. Vượt → chặn mềm ở /agent/chat (không sập, báo lịch sự).  ║
# ║ Con số để ở ĐÂY (một nguồn) — chỉnh dễ, không rải khắp code.        ║
# ╚══════════════════════════════════════════════════════════════════╝

DEFAULT_TIER = "free"

# daily/monthly = trần TOKEN. 1 lượt chat ~2k–10k token → free ~ vài chục lượt/ngày.
TIERS: dict[str, dict] = {
    "free": {"label": "Miễn phí", "daily_tokens": 100_000, "monthly_tokens": 2_000_000},
    "pro":  {"label": "Pro",      "daily_tokens": 2_000_000, "monthly_tokens": 40_000_000},
}


def tier_limits(tier: str) -> dict:
    """Trần của 1 tier (lùi về free nếu tier lạ)."""
    return TIERS.get(tier, TIERS[DEFAULT_TIER])
