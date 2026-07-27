"""test_output_guardrail.py — Output Guardrail (3 lớp: tool call, content, format).

Chạy: uv run pytest tests/test_output_guardrail.py -v   (KHÔNG cần server/Gmail/LLM)
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.agent.guardrails.output_guardrail import (
    check_content,
    check_tool_call,
    has_harmful_content,
    sanitize_content,
    validate_format,
)


# ══════════════════════════════════════════════════════════════════════
# 1. TOOL CALL SAFETY
# ══════════════════════════════════════════════════════════════════════

class _FakeSchema(BaseModel):
    query: str
    limit: int = 10


def test_check_tool_call_tool_khong_ton_tai():
    """Tool không có trong registry → bị chặn."""
    ok, reason = check_tool_call("tool_khong_ton_tai", {})
    assert not ok
    assert "không tồn tại" in (reason or "")


def test_check_tool_call_args_sai(monkeypatch):
    """Tham số sai schema → bị chặn."""
    from app.tools.registry import tool_registry
    monkeypatch.setattr(tool_registry, "get_spec", lambda name: type(
        "Spec", (), {"input_schema": _FakeSchema}
    )())
    ok, reason = check_tool_call("test_tool", {"limit": "khong_phai_so"})
    assert not ok
    assert "không hợp lệ" in (reason or "")


def test_check_tool_call_send_email_nhieu_nguoi(monkeypatch):
    """send_email >50 người nhận → bị chặn."""
    from app.tools.registry import tool_registry
    monkeypatch.setattr(tool_registry, "get_spec", lambda name: type(
        "Spec", (), {"input_schema": type(
            "Schema", (BaseModel,), {"model_validate": staticmethod(lambda d: d)}
        )}
    )())
    to = [f"user{i}@example.com" for i in range(51)]
    ok, reason = check_tool_call("send_email", {"to": to, "subject": "X", "body": "Y"})
    assert not ok
    assert "vượt ngưỡng" in (reason or "")


def test_check_tool_call_ok(monkeypatch):
    """Tool call hợp lệ → cho phép."""
    from app.tools.registry import tool_registry
    monkeypatch.setattr(tool_registry, "get_spec", lambda name: type(
        "Spec", (), {"input_schema": type(
            "Schema", (BaseModel,), {"model_validate": staticmethod(lambda d: d)}
        )}
    )())
    ok, reason = check_tool_call("search_emails", {"query": "thư mới", "limit": 10})
    assert ok
    assert reason is None


# ══════════════════════════════════════════════════════════════════════
# 2. CONTENT CHECK — PII FILTERING
# ══════════════════════════════════════════════════════════════════════

def test_sanitize_content_pii_email():
    """Email trong văn bản bị che."""
    text = "Liên hệ tôi qua test@example.com để biết thêm."
    result = sanitize_content(text)
    assert "test@example.com" not in result
    assert "thông tin cá nhân" in result


def test_sanitize_content_pii_phone():
    """Số điện thoại VN bị che."""
    text = "Gọi 0912345678 hoặc +84987654321."
    result = sanitize_content(text)
    assert "0912345678" not in result
    assert "+84987654321" not in result


def test_sanitize_content_no_pii():
    """Văn bản sạch không bị ảnh hưởng."""
    text = "Mình đã tìm thấy 5 email cho bạn."
    result = sanitize_content(text)
    assert result == text


def test_sanitize_content_empty():
    """Chuỗi rỗng → không lỗi."""
    assert sanitize_content("") == ""
    assert sanitize_content(None) is None  # type: ignore


def test_sanitize_content_cccd():
    """Số CMND/CCCD bị che."""
    text = "Số CCCD: 079201012345, CMND: 123456789."
    result = sanitize_content(text)
    assert "079201012345" not in result
    assert "123456789" not in result


# ══════════════════════════════════════════════════════════════════════
# 3. CONTENT CHECK — HARMFUL CONTENT
# ══════════════════════════════════════════════════════════════════════

def test_has_harmful_content_phat_hien():
    """Nội dung độc hại bị phát hiện."""
    harmful_cases = [
        "tao sẽ giết mày",
        "khủng bố",
        "fuck you",
        "đồ bitch",
        "lăng mạ",
        "đe dọa",
    ]
    for case in harmful_cases:
        assert has_harmful_content(case), f"Không phát hiện: {case!r}"


def test_has_harmful_content_sach():
    sach = [
        "Cảm ơn bạn, tôi đã nhận được email.",
        "Hôm nay trời đẹp quá.",
        "Mình cần gấp báo giá nhé.",
        "Chết thật, mình quên mất (từ cảm thán thông thường).",
    ]
    for case in sach:
        assert not has_harmful_content(case), f"Dương tính giả: {case!r}"


def test_check_content_pii_duoc_che():
    """check_content tích hợp: PII bị che và harmful được phát hiện."""
    text = "SĐT: 0912345678, email: spam@spam.com"
    result = check_content(text)
    assert "0912345678" not in result
    assert "spam@spam.com" not in result


def test_check_content_harmful_them_canh_bao(tmp_path):
    """Nội dung độc hại → thêm appendix."""
    text = "đồ bitch"
    result = check_content(text)
    assert "kiểm duyệt" in result


# ══════════════════════════════════════════════════════════════════════
# 4. FORMAT VALIDATION
# ══════════════════════════════════════════════════════════════════════

def test_validate_format_kind_sai():
    """kind không hợp lệ → fallback về text."""
    result = validate_format({"kind": "invalid", "text": "X"})
    assert result["kind"] == "text"


def test_validate_format_thieu_text():
    """kind=text mà thiếu text → dùng mặc định."""
    result = validate_format({"kind": "text"})
    assert result["kind"] == "text"
    assert len(result["text"]) > 0


def test_validate_format_result_thieu_title():
    """kind=result mà thiếu title → thêm mặc định."""
    result = validate_format({"kind": "result", "lines": ["a", "b"]})
    assert result["kind"] == "result"
    assert result["title"] == "Kết quả"


def test_validate_format_result_lines_sai_kieu():
    """lines không phải list → ép thành list."""
    result = validate_format({"kind": "result", "title": "T", "lines": "abc"})
    assert isinstance(result["lines"], list)
    assert result["lines"] == ["abc"]


def test_validate_format_ok():
    """Output hợp lệ → không thay đổi."""
    out = {
        "kind": "text",
        "text": "Xin chào bạn.",
        "intro": "Chào",
    }
    result = validate_format(out)
    assert result["text"] == "Xin chào bạn."


def test_validate_format_khong_pha_dict():
    """Đầu vào không phải dict → fallback."""
    assert validate_format(None)["kind"] == "text"  # type: ignore
    assert validate_format("hello")["kind"] == "text"  # type: ignore


# ══════════════════════════════════════════════════════════════════════
# 5. TÍCH HỢP: guardrail trong ReAct loop (tool_node)
# ══════════════════════════════════════════════════════════════════════

def test_guardrail_chan_tool_khong_ton_tai_trong_graph():
    """Tool không tồn tại bị guardrail chặn trong graph."""
    import asyncio
    import json
    from langchain_core.messages import AIMessage, HumanMessage
    import app.agent.nodes.agent_node as agent_node
    from app.agent.graph import build_graph
    from app.agent.nodes.agent_node import PresentReply
    from app.tools.registry import RequestContext

    class _FakeLLM:
        def bind_tools(self, _tools):
            return self
        async def ainvoke(self, _messages):
            return AIMessage(
                content="", tool_calls=[
                    {"name": "tool_khong_co", "args": {}, "id": "t1"},
                ]
            )

    class _FakePresent:
        async def ainvoke(self, _msgs):
            return PresentReply(kind="text", intro="", text="Lỗi tool.")

    agent_node._llm_with_tools = _FakeLLM()
    agent_node._present_llm = _FakePresent()

    graph = build_graph()
    out = asyncio.run(graph.ainvoke({
        "messages": [HumanMessage(content="chạy tool lạ")],
        "request_ctx": RequestContext(user_id="test", access_token="fake"),
        "skill_context": "",
        "pending_confirmation": None,
        "iteration_count": 0,
        "final_output": None,
    }))

    tool_msgs = [m for m in out["messages"] if getattr(m, "type", None) == "tool"]
    assert len(tool_msgs) >= 1, "Phải có ToolMessage"
    data = json.loads(tool_msgs[0].content)
    assert data.get("blocked_by_guardrail") is True
    assert "không tồn tại" in data.get("reason", "")
