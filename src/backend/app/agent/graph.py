# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/agent/graph.py — SƠ ĐỒ AGENT (LangGraph, Pha 3 tích hợp)       ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Lắp 2 node thành một VÒNG ReAct (Reason + Act):                   ║
# ║                                                                    ║
# ║      (vào) → agent (nghĩ) ──có gọi tool?──► tools (chạy) ─┐        ║
# ║                   ▲                                        │        ║
# ║                   └──────────── quay lại đọc kết quả ◄─────┘        ║
# ║                   │                                                 ║
# ║                   └──không gọi tool / hết vòng──► (KẾT THÚC)        ║
# ║                                                                    ║
# ║ build_graph() trả về 1 graph ĐÃ COMPILE, gọi `.ainvoke(state)` là  ║
# ║ chạy cả vòng cho tới khi agent có câu trả lời cuối.               ║
# ╚══════════════════════════════════════════════════════════════════╝

from langgraph.graph import StateGraph, END
from app.agent.state import State
from app.agent.nodes.agent_node import agent_node, responder_node, MAX_ITERATIONS
from app.agent.nodes.tool_node import tool_node


def _should_continue(state: State) -> str:
    """'Ngã rẽ' sau mỗi lần agent nghĩ: chạy tool, ép thẻ, hay dừng luôn?

    • Vượt MAX_ITERATIONS → 'responder' (chốt an toàn + đóng gói gọn).
    • AIMessage cuối CÓ tool_calls → 'tools' (LLM muốn dùng tool, đi chạy).
    • Câu trả lời cuối CÓ dữ liệu tool ở lượt này → 'responder' (ép thành THẺ đẹp).
    • Câu trả lời cuối THUẦN VĂN BẢN (chào hỏi, hỏi xác nhận…) → 'end' NGAY:
      không có dữ liệu để lên thẻ nên KHỎI gọi LLM lần 2 → nhanh hơn + đỡ tốn quota.
    """
    last = state["messages"][-1]
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        return "responder"
    if getattr(last, "tool_calls", None):
        return "tools"
    # Có ToolMessage nào trong LƯỢT hiện tại (từ HumanMessage gần nhất) không?
    msgs = state["messages"]
    last_human = max((i for i, m in enumerate(msgs) if getattr(m, "type", None) == "human"), default=0)
    has_tool_data = any(getattr(m, "type", None) == "tool" for m in msgs[last_human:])
    return "responder" if has_tool_data else "end"


def build_graph():
    """Dựng + biên dịch graph. Gọi 1 lần, tái dùng cho mọi request."""
    g = StateGraph(State)              # State = "bộ nhớ" của 1 lượt chạy (xem state.py)
    g.add_node("agent", agent_node)    # node nghĩ
    g.add_node("tools", tool_node)     # node chạy tool
    g.add_node("responder", responder_node) # Đăng ký thêm node trình bày
    g.set_entry_point("agent")         # bắt đầu từ "nghĩ"

    # Sau "agent": rẽ theo _should_continue → "tools" (chạy), "responder" (ép thẻ), hoặc END (thuần text).
    g.add_conditional_edges("agent", _should_continue,
                            {"tools": "tools", "responder": "responder", "end": END})
    # Sau "tools": LUÔN quay lại "agent" để nó ĐỌC kết quả tool rồi nghĩ tiếp.
    g.add_edge("tools", "agent")
    g.add_edge("responder", END)  # responder đóng gói final_output xong → kết thúc graph

    return g.compile()
