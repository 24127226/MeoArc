# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/plans.py — GÓI DỊCH VỤ (tier) + hạn mức token             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mô hình freemium giống các sản phẩm AI: mỗi tier có trần token/NGÀY ║
# ║ và /THÁNG. Vượt → chặn mềm ở /agent/chat (không sập, báo lịch sự).  ║
# ║ Con số để ở ĐÂY (một nguồn) — chỉnh dễ, không rải khắp code.        ║
# ║                                                                    ║
# ║ GIÁ chỉ để HIỂN THỊ. Đồ án không nối cổng thanh toán: nâng cấp là   ║
# ║ đổi tier thẳng trong DB, đủ để trình bày luồng giao diện.           ║
# ╚══════════════════════════════════════════════════════════════════╝

DEFAULT_TIER = "free"

# daily/monthly = trần TOKEN. 1 lượt chat ~2k–10k token → free ~ vài chục lượt/ngày.
TIERS: dict[str, dict] = {
    "free": {
        "label": "Miễn phí",
        "tagline": "Đủ dùng cho việc học và hộp thư cá nhân",
        "price_vnd": 0,
        "daily_tokens": 100_000,
        "monthly_tokens": 2_000_000,
        "features": [
            "Khoảng 20–40 lượt hỏi trợ lý mỗi ngày",
            "Tóm tắt, phân loại 7 nhóm, soạn thư",
            "Kết nối 1 hộp thư (Gmail hoặc Outlook)",
        ],
    },
    "pro": {
        "label": "Pro",
        "tagline": "Cho người dùng thư nhiều mỗi ngày",
        "price_vnd": 99_000,
        "daily_tokens": 2_000_000,
        "monthly_tokens": 40_000_000,
        "features": [
            "Gấp 20 lần hạn mức Miễn phí",
            "Kết nối đồng thời Gmail và Outlook",
            "Kỹ năng nâng cao: Digest, Triage, Brief cuộc họp",
            "Đồng bộ hộp thư ưu tiên",
        ],
    },
    "max": {
        "label": "Pro Max",
        "tagline": "Dùng thoải mái, cho khối lượng công việc lớn",
        "price_vnd": 299_000,
        "daily_tokens": 10_000_000,
        "monthly_tokens": 200_000_000,
        "features": [
            "Gấp 100 lần hạn mức Miễn phí",
            "Không giới hạn số hộp thư kết nối",
            "Truy cập MCP cho trợ lý ngoài (Claude Desktop, Codex…)",
            "Tự động hoá theo lịch + ưu tiên xử lý",
        ],
    },
}

# Thứ tự hiển thị trên trang nâng cấp (thấp → cao)
TIER_ORDER = ["free", "pro", "max"]


def tier_limits(tier: str) -> dict:
    """Trần của 1 tier (lùi về free nếu tier lạ)."""
    return TIERS.get(tier, TIERS[DEFAULT_TIER])


def is_valid_tier(tier: str) -> bool:
    return tier in TIERS


def public_catalog() -> list[dict]:
    """Danh mục gói cho Frontend dựng trang nâng cấp — một nguồn duy nhất."""
    return [
        {
            "id": key,
            "label": TIERS[key]["label"],
            "tagline": TIERS[key]["tagline"],
            "priceVnd": TIERS[key]["price_vnd"],
            "dailyTokens": TIERS[key]["daily_tokens"],
            "monthlyTokens": TIERS[key]["monthly_tokens"],
            "features": TIERS[key]["features"],
        }
        for key in TIER_ORDER
    ]
