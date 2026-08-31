"""test_mcp.py — Kênh MCP cho agent NGOÀI (tiêu chí 10đ của thầy) + an toàn UC010.

Chuẩn khách quan (từ Q&A của thầy + SRS, KHÔNG từ code):
  * Thầy: "MCP server phải phơi TOOL HẠT MỊN (search_emails, get_email, send_email,
    apply_label, batch_delete...) để agent ngoài TỰ SUY LUẬN — không phơi tool to kiểu
    summarize_and_process" → kiểm danh sách tool phơi ra đúng hạt mịn, không có tool "to".
  * SRS UC010 (human-in-the-loop): hành động KHÔNG HOÀN TÁC phải được người dùng duyệt
    → confirm-gate: gọi lần đầu KHÔNG được thực thi, phải trả bản xem trước.
  * Hợp đồng BulkAction đã công bố: action nhận chữ thường 'delete'… (LLM viết hoa vẫn chạy).

Chạy: uv run pytest tests/test_mcp.py -v   (KHÔNG cần server/Gmail/LLM — registry được thay bằng gián điệp)
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

import app.mcp.server as mcp_server
from app.tools.registry import RequestContext
from app.tools.schemas import BulkAction, BulkActionInput


# ── Hợp đồng BulkAction: case-insensitive, đúng bộ giá trị công bố ───────────
@pytest.mark.parametrize("raw", ["delete", "Delete", "DELETE"])
def test_bulk_action_delete_moi_kieu_viet_deu_chay(raw):
    inp = BulkActionInput(email_ids=["id1"], action=raw)
    assert inp.action is BulkAction.DELETE


def test_bulk_action_gia_tri_bay_bi_tu_choi():
    with pytest.raises(ValidationError):
        BulkActionInput(email_ids=["id1"], action="obliterate_everything")


def test_bulk_action_qua_100_thu_bi_chan():
    """Hàng rào công bố: tối đa 100 thư/lần — chặn LLM 'hứng chí' xoá cả hộp thư."""
    with pytest.raises(ValidationError):
        BulkActionInput(email_ids=[f"id{i}" for i in range(101)], action="mark_read")


# ── Gián điệp registry: soi tool THẬT có bị gọi hay không ────────────────────
class SpyRegistry:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def call(self, name, args, ctx):
        self.calls.append((name, args))
        class R:  # giả ToolResult tối thiểu
            @staticmethod
            def model_dump():
                return {"success": True, "message": "spy-ok"}
        return R()


@pytest.fixture()
def spy(monkeypatch):
    s = SpyRegistry()
    monkeypatch.setattr(mcp_server, "tool_registry", s)
    monkeypatch.setattr(mcp_server, "_resolve_ctx",
                        lambda: RequestContext(user_id="qa", access_token="tok"))
    return s


# ── UC010 confirm-gate: KHÔNG HOÀN TÁC → lần đầu chỉ trả preview, KHÔNG thực thi ──
def test_send_email_lan_dau_khong_gui(spy):
    out = asyncio.run(mcp_server.send_email(to=["a@b.c"], subject="S", body="B" * 500))
    assert out.get("needs_confirmation") is True, "Thiếu confirm-gate cho send_email (UC010)!"
    assert spy.calls == [], "CHƯA xác nhận mà email ĐÃ bị gửi — vi phạm human-in-the-loop!"
    assert "body_preview" in out["preview"] and len(out["preview"]["body_preview"]) <= 310


def test_send_email_confirm_true_moi_gui_that(spy):
    out = asyncio.run(mcp_server.send_email(to=["a@b.c"], subject="S", body="B", confirm=True))
    assert out.get("success") is True
    assert [c[0] for c in spy.calls] == ["send_email"], "confirm=true phải thực thi đúng 1 lần"


def test_reply_email_confirm_gate(spy):
    out = asyncio.run(mcp_server.reply_email(email_id="e1", reply_body="Nội dung"))
    assert out.get("needs_confirmation") is True and spy.calls == []
    out2 = asyncio.run(mcp_server.reply_email(email_id="e1", reply_body="Nội dung", confirm=True))
    assert out2.get("success") is True and [c[0] for c in spy.calls] == ["reply_email"]


def test_bulk_delete_confirm_gate_nhung_mark_read_thi_khong(spy):
    """delete (mất dữ liệu) phải qua cổng duyệt; mark_read (đảo được) đi thẳng —
    duyệt đúng chỗ, không làm phiền người dùng vô lý."""
    out = asyncio.run(mcp_server.bulk_action(email_ids=["e1", "e2"], action="Delete"))
    assert out.get("needs_confirmation") is True and spy.calls == [], \
        "bulk delete chưa xác nhận mà đã chạy!"
    out2 = asyncio.run(mcp_server.bulk_action(email_ids=["e1"], action="mark_read"))
    assert out2.get("success") is True and [c[0] for c in spy.calls] == ["bulk_action"]


def test_apply_labels_dao_duoc_khong_can_confirm(spy):
    out = asyncio.run(mcp_server.apply_labels(email_ids=["e1"], labels_to_add=["Work"]))
    assert out.get("success") is True and [c[0] for c in spy.calls] == ["apply_labels"]


# ── Lỗi tool → phong bì JSON (agent ngoài đọc được), không nổ exception giao thức ──
def test_loi_tool_tra_phong_bi_json(monkeypatch):
    class BoomRegistry:
        async def call(self, name, args, ctx):
            raise RuntimeError("Gmail 403: thiếu quyền")
    monkeypatch.setattr(mcp_server, "tool_registry", BoomRegistry())
    monkeypatch.setattr(mcp_server, "_resolve_ctx",
                        lambda: RequestContext(user_id="qa", access_token="tok"))
    out = asyncio.run(mcp_server.get_email(email_id="x"))
    assert out.get("success") is False and "403" in out.get("error", "")
    assert "hint" in out, "Thiếu hint hướng dẫn agent xử lý lỗi"


# ── Tiêu chí thầy: phơi ĐÚNG bộ tool hạt mịn + kỹ năng prompt ───────────────
def test_mcp_phoi_du_tool_hat_min_va_khong_co_tool_to():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = set(tools.keys() if isinstance(tools, dict) else [t.name for t in tools])
    required = {"search_emails", "semantic_search", "categorize_emails", "get_email", "list_labels",
                "send_email", "reply_email", "apply_labels", "bulk_action"}
    assert required <= names, f"Thiếu tool hạt mịn: {required - names}"
    # Q&A thầy: tool "to" gộp suy luận (summarize/process/auto) là rớt xuống 9đ
    coarse = {n for n in names if any(k in n.lower() for k in ("summarize", "process", "auto_"))}
    assert not coarse, f"Phát hiện tool 'to' gộp suy luận vào app: {coarse}"


def test_mcp_co_3_ky_nang_prompt():
    prompts = asyncio.run(mcp_server.mcp.list_prompts())
    names = set(prompts.keys() if isinstance(prompts, dict) else [p.name for p in prompts])
    assert {"daily_digest", "triage_inbox", "meeting_brief"} <= names, \
        f"Thiếu kỹ năng prompt cho Claude Desktop: {names}"
