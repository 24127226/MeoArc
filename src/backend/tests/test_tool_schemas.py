"""test_tool_schemas.py — Hợp đồng ĐẦU VÀO tool (§3 đặc tả QA) phải THẬT SỰ được cưỡng chế.

TÍNH KHÁCH QUAN: chuẩn ở đây là những ràng buộc ĐÃ CÔNG BỐ trong đặc tả §3
(SearchEmailsInput / SendEmailInput / ReplyEmailInput) + cơ chế human-in-the-loop của SRS
(UC010: hành động không hoàn tác phải được duyệt). Test kiểm rằng vi phạm ràng buộc BỊ TỪ CHỐI
— nếu schema khai một đằng chạy một nẻo (khai ge=1 mà nhận limit=0) là FAIL.

Chạy: uv run pytest tests/test_tool_schemas.py -v   (KHÔNG cần server/Gmail/LLM)
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.tools.schemas import ReplyEmailInput, SearchEmailsInput, SendEmailInput


# ── §3.1 SearchEmailsInput: limit ∈ [1,50]; date_from ≤ date_to ─────────────
def test_search_limit_bien_hop_le():
    assert SearchEmailsInput(limit=1).limit == 1
    assert SearchEmailsInput(limit=50).limit == 50
    assert SearchEmailsInput().limit == 10, "default limit công bố là 10"


@pytest.mark.parametrize("bad", [0, -3, 51, 1000])
def test_search_limit_ngoai_bien_phai_bi_tu_choi(bad):
    with pytest.raises(ValidationError):
        SearchEmailsInput(limit=bad)


def test_search_date_from_sau_date_to_phai_bi_tu_choi():
    with pytest.raises((ValidationError, ValueError)):
        SearchEmailsInput(date_from=datetime(2026, 7, 2), date_to=datetime(2026, 7, 1))


def test_search_date_hop_le_duoc_nhan():
    inp = SearchEmailsInput(date_from=datetime(2026, 7, 1), date_to=datetime(2026, 7, 2))
    assert inp.date_from < inp.date_to


# ── §3.2 SendEmailInput: to ≥ 1 địa chỉ; subject/body không rỗng; str → list ──
def test_send_thieu_nguoi_nhan_phai_bi_tu_choi():
    with pytest.raises(ValidationError):
        SendEmailInput(to=[], subject="S", body="B")


@pytest.mark.parametrize("field,value", [("subject", ""), ("body", "")])
def test_send_subject_body_rong_phai_bi_tu_choi(field, value):
    kw = {"to": ["a@b.c"], "subject": "S", "body": "B"}
    kw[field] = value
    with pytest.raises(ValidationError):
        SendEmailInput(**kw)


def test_send_chuoi_don_duoc_chuan_hoa_thanh_list():
    """Đặc tả §3: normalize_addresses — LLM đưa 'a@b.c' (chuỗi) phải thành ['a@b.c']."""
    inp = SendEmailInput(to="a@b.c", subject="S", body="B", cc="c@d.e")
    assert inp.to == ["a@b.c"]
    assert inp.cc == ["c@d.e"]


# ── §3.3 ReplyEmailInput: mặc định công bố tone='formal', reply_all=False ────
def test_reply_default_dung_cong_bo():
    inp = ReplyEmailInput(email_id="abc123", instructions="cảm ơn và hẹn gặp")
    assert inp.tone == "formal"
    assert inp.reply_all is False


def test_reply_thieu_email_id_phai_bi_tu_choi():
    with pytest.raises(ValidationError):
        ReplyEmailInput(instructions="x")  # type: ignore[call-arg]


# ── Registry: cổng gọi tool DUY NHẤT phải validate TRƯỚC khi chạy handler ────
def test_registry_chan_input_sai_truoc_khi_cham_handler():
    """Input sai schema → ToolInputError và handler KHÔNG được thực thi (không gọi mạng bậy)."""
    from app.tools.registry import (RequestContext, ToolCategory, ToolInputError,
                                    ToolNotFoundError, ToolRegistry)
    reg = ToolRegistry()  # registry riêng cho test — không đụng singleton toàn cục
    calls = []

    @reg.register(category=ToolCategory.READ, input_schema=SearchEmailsInput)
    async def spy_search(inp: SearchEmailsInput, ctx: RequestContext):
        """Tool gián điệp: ghi vết mỗi lần được gọi."""
        calls.append(inp.limit)
        return {"ok": True}

    ctx = RequestContext(user_id="u1", access_token="tok")

    with pytest.raises(ToolInputError):
        asyncio.run(reg.call("spy_search", {"limit": 0}, ctx))
    assert calls == [], "Input sai schema mà handler VẪN chạy — cổng validate bị hổng!"

    asyncio.run(reg.call("spy_search", {"limit": 5}, ctx))
    assert calls == [5], "Input hợp lệ phải được chạy đúng 1 lần"

    with pytest.raises(ToolNotFoundError):
        asyncio.run(reg.call("khong_ton_tai", {}, ctx))


# ── SRS UC010 (human-in-the-loop): tool KHÔNG HOÀN TÁC phải gắn cờ cần duyệt ──
def test_tool_khong_hoan_tac_phai_yeu_cau_xac_nhan():
    import app.tools.email_tools  # noqa: F401 — nạp 7 tool thật vào registry
    from app.tools.registry import tool_registry

    for name in ("send_email", "reply_email", "bulk_action"):
        spec = tool_registry.get_spec(name)
        assert spec.requires_confirmation is True, (
            f"'{name}' là hành động KHÔNG HOÀN TÁC nhưng không gắn cờ cần duyệt — vi phạm UC010."
        )
    # Đối chứng: tool chỉ-đọc không được đòi duyệt (tránh phiền người dùng vô lý)
    assert tool_registry.get_spec("search_emails").requires_confirmation is False
