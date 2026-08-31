"""test_agent_offline.py — VÒNG ReAct ĐẦY ĐỦ chạy OFFLINE (không key/quota/mạng).

Lấp lỗ hổng: test_agent.py & test_live_e2e.py cần key/cookie/server nên tự SKIP →
vòng suy luận (agent nghĩ → gọi tool → nghĩ tiếp → đóng thẻ) chưa có test tất định.
Ở đây thay 'não' (LLM) bằng KỊCH BẢN cố định (test double / stub — Sommerville Ch.8):
  • Lượt 1: agent QUYẾT gọi search_emails.
  • Lượt 2: agent chốt câu trả lời (không tool nữa).
  • tool_node vẫn chạy tool THẬT, nhưng Gmail được thay bằng dữ liệu giả
    (monkeypatch list_messages) — đúng pattern test_labeling/test_semantic.
  • responder_node dùng LLM giả trả PresentReply.

Kiểm được (deterministic, 0 quota): định tuyến tool, ghép ToolMessage đúng lượt,
loop guard, đóng gói final_output đúng khuôn FE.

Chạy: uv run pytest tests/test_agent_offline.py -v
"""

from __future__ import annotations

import asyncio

import pytest
from langchain_core.messages import AIMessage, HumanMessage

import app.agent.nodes.agent_node as agent_node
from app.agent.graph import build_graph
from app.agent.nodes.agent_node import PresentReply
from app.tools.registry import RequestContext

# Nạp các tool vào registry. Import này trông như thừa nhưng KHÔNG được bỏ: các tool
# chỉ tồn tại nhờ decorator @tool_registry.register chạy lúc import module này.
# Thiếu nó, chạy RIÊNG một test trong file sẽ gặp registry rỗng → tool_node không tìm
# thấy send_email và trả về lỗi thay vì phiếu chờ duyệt. Nguy hiểm ở chỗ phép thử
# "chưa gửi thật" vẫn xanh — nhưng xanh vì không có tool để gọi, chứ không phải vì
# cổng xác nhận giữ được.
import app.tools.email_tools  # noqa: E402,F401


class _ScriptedLLM:
    """LLM giả có KỊCH BẢN: mỗi lần ainvoke trả AIMessage kế tiếp trong script.
    bind_tools bị bỏ qua (ta tự kịch bản hoá tool_calls nên không cần schema thật)."""

    def __init__(self, script: list[AIMessage]):
        self._script = list(script)
        self._i = 0

    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, _messages):
        msg = self._script[min(self._i, len(self._script) - 1)]
        self._i += 1
        return msg


class _FakePresentLLM:
    """LLM giả cho responder_node — trả thẳng một PresentReply đã dựng sẵn."""

    def __init__(self, reply: PresentReply):
        self.reply = reply

    async def ainvoke(self, _msgs):
        return self.reply


def _fake_email(i: int, sender: str, sender_email: str, subject: str):
    from app.schemas.email import Email

    return Email(
        id=f"id{i}", sender=sender, senderEmail=sender_email, senderInitial=sender[:1],
        to="", subject=subject, preview="", body=[""], time="09:00",
        date="Hôm nay, 09:00", unread=True, starred=False, category="moss", threadId=f"th{i}",
    )


@pytest.fixture(autouse=True)
def _reset_llm_singletons():
    """Trả 2 singleton LLM (agent + present) về None sau mỗi test → không rò rỉ fake sang test khác."""
    yield
    agent_node._llm_with_tools = None
    agent_node._present_llm = None


def _base_state(user_msg: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_msg)],
        "request_ctx": RequestContext(user_id="qa", access_token="fake-token"),
        "skill_context": "",
        "pending_confirmation": None,
        "iteration_count": 0,
        "final_output": None,
    }


def test_react_loop_goi_tool_roi_dong_the(monkeypatch):
    """Yêu cầu 'liệt kê thư' → agent gọi search_emails → tool chạy (Gmail giả) →
    agent chốt → responder ra thẻ 'result' đúng khuôn FE. Tất cả OFFLINE."""
    import app.tools.email_tools as et

    emails = [
        _fake_email(0, "Giáo vụ HCMUS", "giaovu@fit.hcmus.edu.vn", "Nhắc nộp SRS"),
        _fake_email(1, "GitHub", "noreply@github.com", "PR review"),
    ]
    monkeypatch.setattr(
        et.gmail_service, "list_messages",
        lambda tok, q=None, max_results=20, **kw: (emails, None),
    )

    # Não giả: lượt 1 xin gọi tool, lượt 2 chốt bằng văn bản (không tool → responder → END).
    agent_node._llm_with_tools = _ScriptedLLM([
        AIMessage(content="", tool_calls=[
            {"name": "search_emails", "args": {"query": "thư mới", "limit": 5}, "id": "t1"},
        ]),
        AIMessage(content="Mình đã tìm được các thư mới cho bạn."),
    ])
    agent_node._present_llm = _FakePresentLLM(PresentReply(
        kind="result", intro="Mình đã tìm giúp bạn:", title="Thư mới",
        lines=["Giáo vụ HCMUS — Nhắc nộp SRS", "GitHub — PR review"],
    ))

    graph = build_graph()
    out = asyncio.run(graph.ainvoke(_base_state("liệt kê thư mới")))

    # 1) Tool THẬT đã chạy trong graph: có ToolMessage của search_emails.
    tool_msgs = [m for m in out["messages"]
                 if getattr(m, "type", None) == "tool" and getattr(m, "name", "") == "search_emails"]
    assert tool_msgs, "graph chưa thực thi search_emails (định tuyến agent→tools sai?)"

    # 2) Đóng gói final_output đúng khuôn FE 'result'.
    fo = out["final_output"]
    assert fo and fo["kind"] == "result", f"final_output không phải thẻ result: {fo!r}"
    assert fo["lines"] == ["Giáo vụ HCMUS — Nhắc nộp SRS", "GitHub — PR review"]

    # 3) Loop guard: chỉ nghĩ 2 lượt (agent→tools→agent→responder), dưới trần MAX_ITERATIONS.
    assert out["iteration_count"] == 2, f"số vòng nghĩ bất thường: {out['iteration_count']}"


def test_confirm_gate_chan_send_va_ra_the_draft(monkeypatch):
    """HUMAN-IN-THE-LOOP (UC010): agent gọi send_email → tool_node phải CHẶN (không gửi
    thật), và app.py dựng được thẻ 'draft' CÓ NÚT cho FE từ đúng args LLM đã soạn.
    Đây là hàng rào chống hồi quy cho bug: 'LLM nói đã gửi nhưng không có thư'."""
    import json

    import app.services.gmail_send as gs

    # Chuông báo: nếu gmail_send.send_email bị gọi nghĩa là cổng confirm THỦNG.
    called = {"n": 0}
    monkeypatch.setattr(gs, "send_email",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1) or {})

    agent_node._llm_with_tools = _ScriptedLLM([
        AIMessage(content="", tool_calls=[{
            "name": "send_email",
            "args": {"to": ["thien@example.com"], "subject": "Chào Thiên", "body": "Nội dung thư."},
            "id": "t1",
        }]),
        AIMessage(content="Bản nháp đang chờ bạn duyệt."),
    ])
    agent_node._present_llm = _FakePresentLLM(
        PresentReply(kind="text", intro="", text="Bản nháp đang chờ bạn duyệt.")
    )

    graph = build_graph()
    out = asyncio.run(graph.ainvoke(_base_state("gửi mail chào Thiên giúp mình")))

    # 1) TUYỆT ĐỐI chưa gửi thật.
    assert called["n"] == 0, "cổng confirm THỦNG: gmail_send.send_email đã bị gọi khi chưa duyệt"

    # 2) ToolMessage bị chặn mang needs_confirmation + đủ args.
    tool_msg = next(m for m in out["messages"] if getattr(m, "type", None) == "tool")
    data = json.loads(tool_msg.content)
    assert data["needs_confirmation"] is True and data["args"]["subject"] == "Chào Thiên"

    # 3) app.py dựng thẻ draft đúng khuôn FE (có nút Niêm phong & Gửi).
    from app.api.app import _confirm_card
    card = _confirm_card(out["messages"])
    assert card and card["kind"] == "draft"
    assert card["subject"] == "Chào Thiên" and "thien@example.com" in card["to"]
    assert card["body"] == "Nội dung thư."


def test_confirm_gate_khong_chan_tool_doc(monkeypatch):
    """Tool CHỈ ĐỌC (search_emails) phải đi qua cổng bình thường — gate chỉ chặn destructive."""
    import app.tools.email_tools as et

    monkeypatch.setattr(et.gmail_service, "list_messages",
                        lambda tok, q=None, max_results=20, **kw: ([], None))
    agent_node._llm_with_tools = _ScriptedLLM([
        AIMessage(content="", tool_calls=[
            {"name": "search_emails", "args": {"query": "x"}, "id": "t1"},
        ]),
        AIMessage(content="Không có thư nào khớp."),
    ])
    agent_node._present_llm = _FakePresentLLM(
        PresentReply(kind="text", intro="", text="Không có thư nào khớp.")
    )
    graph = build_graph()
    out = asyncio.run(graph.ainvoke(_base_state("tìm thư x")))
    import json
    tool_msg = next(m for m in out["messages"] if getattr(m, "type", None) == "tool")
    assert not json.loads(tool_msg.content).get("needs_confirmation"), \
        "tool ĐỌC bị gate chặn nhầm — agent sẽ không đọc được hộp thư"


def test_react_tra_loi_thang_khong_goi_tool(monkeypatch):
    """Câu chào 'xin chào' → agent trả text ngay, KHÔNG gọi tool, KHÔNG cần responder
    (nhánh 'end' của _should_continue). Đảm bảo agent không 'bịa' gọi tool vô cớ."""
    agent_node._llm_with_tools = _ScriptedLLM([
        AIMessage(content="Chào bạn 👋 Mình là MeoArc, mình giúp gì được cho bạn?"),
    ])

    graph = build_graph()
    out = asyncio.run(graph.ainvoke(_base_state("xin chào")))

    assert not any(getattr(m, "type", None) == "tool" for m in out["messages"]), \
        "câu chào không nên kích hoạt tool nào"
    # Nhánh 'end' không qua responder → final_output vẫn None (app.py sẽ lấy text từ AIMessage cuối).
    assert out["final_output"] is None
    last = out["messages"][-1]
    assert getattr(last, "type", None) == "ai" and "MeoArc" in last.content


def test_ba_buoc_chay_dung_thu_tu_nghiep_vu(monkeypatch):
    """UC007-TC02 (§3.2.7): yêu cầu nhiều bước phải chạy ĐÚNG THỨ TỰ nghiệp vụ.

    Vì sao thứ tự là thứ đáng kiểm chứ không phải "có gọi đủ ba tool":
    gắn nhãn TRƯỚC khi tìm thì gắn vào tập rỗng — không tool nào báo lỗi, không có
    ngoại lệ nào được ném, và nhìn nhật ký thì vẫn thấy đủ ba lời gọi thành công.
    Người dùng chỉ phát hiện khi mở hộp thư ra và thấy chẳng thư nào được gắn nhãn.

    Ở đây dùng LLM có kịch bản (stub) thay vì mô hình thật: mô hình thật có quyền
    diễn đạt khác đi hoặc chèn thêm một bước ở lần chạy sau, nên phép thử sẽ đỏ mà
    không hề có lỗi nào — đúng cái bẫy đã nêu ở §3.2.6.
    """
    import app.tools.email_tools as et

    emails = [_fake_email(0, "Giáo vụ HCMUS", "giaovu@fit.hcmus.edu.vn", "Hạn nộp SRS")]
    monkeypatch.setattr(
        et.gmail_service, "list_messages",
        lambda tok, q=None, max_results=20, **kw: (emails, None),
    )

    # Sổ ghi: mỗi lần một nhãn được gắn thì ghi lại tên, theo đúng thứ tự xảy ra.
    da_gan: list[str] = []
    monkeypatch.setattr(
        et.mail, "apply_label",
        lambda provider, token, ids, name: (da_gan.append(name), len(ids))[1],
    )

    # Não giả: ba lượt, mỗi lượt xin một tool; lượt bốn chốt bằng văn bản.
    agent_node._llm_with_tools = _ScriptedLLM([
        AIMessage(content="", tool_calls=[
            {"name": "search_emails", "args": {"query": "hạn nộp tuần này", "limit": 5}, "id": "t1"},
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "apply_labels",
             "args": {"email_ids": ["m0"], "labels_to_add": ["Công việc"]}, "id": "t2"},
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "apply_labels",
             "args": {"email_ids": ["m0"], "labels_to_add": ["Ưu tiên cao"]}, "id": "t3"},
        ]),
        AIMessage(content="Đã tìm, gắn nhãn Công việc và đánh dấu ưu tiên."),
    ])
    agent_node._present_llm = _FakePresentLLM(PresentReply(
        kind="text", intro="", text="Đã tìm, gắn nhãn Công việc và đánh dấu ưu tiên."))

    graph = build_graph()
    out = asyncio.run(graph.ainvoke(_base_state(
        "tìm thư hạn nộp tuần này, gắn nhãn Công việc rồi đánh dấu ưu tiên")))

    # 1) Đủ ba lời gọi, KHÔNG bước nào bị bỏ.
    ten_tool = [m.name for m in out["messages"] if getattr(m, "type", None) == "tool"]
    assert ten_tool == ["search_emails", "apply_labels", "apply_labels"], (
        f"Thứ tự tool sai hoặc thiếu bước: {ten_tool}"
    )

    # 2) Tìm phải xảy ra TRƯỚC lần gắn nhãn đầu tiên.
    assert ten_tool.index("search_emails") == 0, "Gắn nhãn trước khi tìm → gắn vào tập rỗng"

    # 3) Hai nhãn được gắn đúng thứ tự nghiệp vụ: phân loại trước, ưu tiên sau.
    assert da_gan == ["Công việc", "Ưu tiên cao"], f"Thứ tự gắn nhãn sai: {da_gan}"
