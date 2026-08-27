from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from app.tools.registry import RequestContext  # (tích hợp) thêm tiền tố app. cho khớp layout


class PendingConfirmation(TypedDict, total=False):
    """
    Populated bởi output_guardrail khi agent gọi request_confirmation.
    Graph đọc field này để pause loop và chờ user response.
    Reset về None sau khi user confirm/deny.
    """
    action_summary: str
    affected_items: list[str]
    action_type: str


class State(TypedDict):
    """
    Single source of truth trong suốt một ReAct loop run.

    LangGraph convention:
      - Mỗi node nhận State, trả về dict[str, Any] chứa các field cần update.
      - `messages` dùng add_messages reducer — append-only, không overwrite.
      - Các field còn lại dùng default reducer — last-write-wins.
    """
    # Chứa: HumanMessage, AIMessage (với tool_calls), ToolMessage (tool results).
    messages: Annotated[list, add_messages]

    # Build một lần ở deps.py, inject khi khởi tạo graph run.
    # tool_node đọc field này để pass ctx vào registry.call().
    # Không bao giờ mutate trong suốt một run.
    request_ctx: RequestContext

    # Nội dung markdown từ skill_loader.py — inject vào system prompt của agent_node.
    # Empty string nếu không có skill nào match request hiện tại.
    # Được set một lần trước khi vào graph loop, không thay đổi mid-run.
    skill_context: str

    # Sở thích cá nhân đã kết tinh thành văn (user_preference_repo.prompt_context):
    # tên xưng hô, giọng văn, chữ ký, dặn dò riêng. Cũng inject vào system prompt.
    # Empty string khi người dùng chưa đặt gì — KHÔNG nhét khối rỗng vào prompt.
    # Tách khỏi skill_context vì hai thứ có vòng đời khác nhau: skill đổi theo TỪNG
    # yêu cầu, còn sở thích gắn với NGƯỜI và gần như không đổi giữa các lượt.
    user_context: str

    # None  = không có action nào đang chờ confirm.
    # dict  = agent đã gọi request_confirmation, loop bị pause.
    #         Graph conditional edge đọc field này để route sang confirmation_node
    #         thay vì tiếp tục agent_node.
    # Reset về None bởi confirmation_node sau khi user respond.
    pending_confirmation: PendingConfirmation | None

    # ── Loop Guard ────────────────────────────────────────────────────────────
    # Tăng 1 mỗi khi agent_node được invoke.
    # graph.py đọc field này trong conditional edge — force END nếu vượt MAX_ITERATIONS.
    # Tránh infinite loop khi LLM bị stuck (ví dụ: tool cứ fail, LLM cứ retry).
    iteration_count: int

    # ── Kết quả cuối ──────────────────────────────────────────────────────────
    # dict AgentReply (kind/intro/lines/...) ĐÃ đóng gói để gửi thẳng về FE.
    # responder_node ghi vào đây ở cuối graph; app.py đọc ra trả cho frontend.
    # PHẢI khai báo là 1 "channel" của State, nếu không LangGraph báo lỗi key lạ.
    final_output: dict | None