# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/agent/nodes/tool_node.py — NODE "THỰC THI TOOL" (Pha 3)        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Sau khi agent_node (LLM) QUYẾT gọi tool, AIMessage cuối sẽ kèm     ║
# ║ danh sách `tool_calls` (tên tool + tham số do LLM điền). Node này  ║
# ║ CHẠY THẬT từng tool đó qua `tool_registry.call(...)` — chính là    ║
# ║ chỗ "não" chạm "tay" (email_tools → gmail_service của quan).       ║
# ║ Kết quả gói thành ToolMessage để vòng sau LLM đọc và nói lại.      ║
# ╚══════════════════════════════════════════════════════════════════╝

import asyncio
import json
from langchain_core.messages import ToolMessage
from app.tools.registry import tool_registry
from app.agent.state import State


async def _run_one(call: dict, ctx) -> ToolMessage:
    """Chạy 1 tool call → gói kết quả/lỗi thành ToolMessage. Tự nuốt exception để
    1 tool hỏng KHÔNG kéo sập các tool chạy cùng lượt."""
    name = call.get("name", "")
    args = call.get("args", {}) or {}
    call_id = call.get("id", "")
    try:
        result = await tool_registry.call(name, args, ctx)   # CHẠY tool thật
        # Kết quả là Pydantic model (vd SearchEmailsOutput) → đổi sang dict rồi JSON
        # để nhét vào ToolMessage (LLM đọc dạng text). default=str: phòng kiểu lạ (datetime).
        payload = result.model_dump() if hasattr(result, "model_dump") else result
        content = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:
        # Tool lỗi (vd thiếu quyền, id sai) → BÁO cho LLM biết để nó xử lý/nói lại,
        # KHÔNG ném ra ngoài làm sập cả vòng agent.
        content = json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)
    # tool_call_id phải KHỚP id của lệnh gọi → LLM ghép đúng "kết quả nào của tool nào".
    return ToolMessage(content=content, name=name, tool_call_id=call_id)


async def tool_node(state: State) -> dict:
    """Chạy MỌI tool mà LLM yêu cầu ở AIMessage cuối, trả về các ToolMessage tương ứng.

    `state["request_ctx"]` = RequestContext (chứa access_token Gmail) — bơm vào mỗi tool để
    nó gọi đúng hộp thư của người dùng. registry.call() tự VALIDATE tham số trước khi chạy.

    NFR-Speed: các tool chạy SONG SONG (asyncio.gather) thay vì xếp hàng — LLM xin 3 tool
    một lượt (vd search + list_labels + get_email) thì tổng thời gian ≈ tool chậm nhất,
    không phải tổng cộng cả ba. gather giữ NGUYÊN THỨ TỰ kết quả theo thứ tự tool_calls.
    """
    last = state["messages"][-1]            # AIMessage vừa rồi (có tool_calls)
    ctx = state["request_ctx"]
    calls = getattr(last, "tool_calls", None) or []
    outputs = list(await asyncio.gather(*(_run_one(c, ctx) for c in calls)))
    return {"messages": outputs}
