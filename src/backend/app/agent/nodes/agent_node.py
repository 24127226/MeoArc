# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/agent/nodes/agent_node.py — NODE "SUY NGHĨ" (Pha 3 tích hợp)   ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là "bộ não": gọi LLM (Gemini) với LỊCH SỬ hội thoại + kiến     ║
# ║ thức skill, để LLM TỰ QUYẾT: trả lời thẳng, HAY gọi 1 tool (đọc/   ║
# ║ gửi/đổi nhãn email...). LangGraph gọi node này nhiều lần (vòng     ║
# ║ ReAct): nghĩ → gọi tool → đọc kết quả → nghĩ tiếp → ... → trả lời. ║
# ╚══════════════════════════════════════════════════════════════════╝

from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from app.core.llm import create_llm
from app.tools.registry import tool_registry
from app.agent.state import State

# Trần số vòng lặp: tránh agent "nghĩ mãi" (tool fail → LLM cứ thử lại vô tận) → tốn tiền/treo.
MAX_ITERATIONS = 6

# Lời dặn (system prompt) định hình TÍNH CÁCH + LUẬT cho agent.
_SYSTEM_BASE = (
    "Bạn là MeoArc — trợ lý email cao cấp, nói TIẾNG VIỆT chỉn chu, lịch sự mà gần gũi.\n\n"
    "## Nguyên tắc CHÍNH XÁC (quan trọng nhất — đừng bao giờ vi phạm)\n"
    "- LUÔN gọi tool để lấy dữ liệu THẬT trước khi trả lời. TUYỆT ĐỐI KHÔNG bịa người gửi,\n"
    "  tiêu đề, nội dung hay thời gian. Chỉ nói đúng những gì tool trả về.\n"
    "- BẤT KỲ yêu cầu nào về hộp thư/email hiện có — liệt kê, tóm tắt, PHÂN LOẠI, sắp xếp theo\n"
    "  ƯU TIÊN, tìm, đếm — BẮT BUỘC gọi search_emails TRƯỚC (MỘT lần, snippet là đủ), ĐỪNG mở từng\n"
    "  thư. TUYỆT ĐỐI KHÔNG trả lời 'không có dữ liệu'/'không tìm thấy email' khi CHƯA gọi tool —\n"
    "  hộp thư trống là điều hiếm; chưa search mà nói trống là BỊA. Có dữ liệu rồi thì trả lời NGAY\n"
    "  bằng nội dung thật — KHÔNG nói 'đã xong' chung chung. Chỉ get_email khi hỏi CHI TIẾT 1 thư.\n"
    "- TÌM KIẾM thông minh: nhiều thư viết bằng TIẾNG ANH, nên khi tìm theo chủ đề hãy thử cả từ khoá\n"
    "  tiếng Anh tương đương (vd 'cảnh báo bảo mật'→'security alert', 'hoá đơn'→'invoice/receipt',\n"
    "  'đặt lịch'→'booking'). Chủ đề MƠ HỒ/mô tả ý ('thư về tiền nong', 'liên quan bảo mật') → dùng\n"
    "  semantic_search (tìm theo NGHĨA, khớp cả khi không chung từ). search_emails không thấy →\n"
    "  thử semantic_search TRƯỚC khi kết luận là không có.\n"
    "- PHÂN LOẠI/GẮN NHÃN TỰ ĐỘNG (vd 'phân loại hộp thư', 'gắn nhãn giúp mình', 'sắp xếp email theo\n"
    "  nhóm'): gọi categorize_emails (nó tự đề xuất nhãn Học tập/Công việc/Tài chính/Mạng xã hội/…).\n"
    "  ĐỪNG tự bịa nhãn, ĐỪNG áp nhãn ngay — chỉ đề xuất để người dùng duyệt.\n"
    "- Thời gian: dùng đúng giờ tool trả về (đã là giờ Việt Nam), không tự đổi.\n\n"
    "## Văn phong & bố cục (để câu trả lời SANG, dễ đọc)\n"
    "- Mở đầu MỘT câu ngắn dẫn dắt, rồi xuống dòng.\n"
    "- Liệt kê bằng gạch đầu dòng bắt đầu bằng '• ', MỖI mục một dòng riêng (xuống dòng thật),\n"
    "  ngắn gọn, nêu thông tin then chốt: người gửi — tiêu đề — ý chính.\n"
    "- Kết bằng một câu gợi ý hành động tiếp theo nếu hợp lý.\n"
    "- Giọng chuyên nghiệp, ấm áp; KHÔNG lan man; KHÔNG dùng ký hiệu markdown rườm rà (**, ##).\n\n"
    "## An toàn (human-in-the-loop)\n"
    "- Hành động KHÔNG HOÀN TÁC (gửi/trả lời thư, xoá, thao tác hàng loạt): SOẠN nội dung\n"
    "  hoàn chỉnh rồi GỌI THẲNG tool tương ứng (send_email/reply_email/bulk_action) —\n"
    "  hệ thống sẽ TỰ CHẶN lại thành THẺ DUYỆT CÓ NÚT BẤM cho người dùng. ĐỪNG hỏi xác\n"
    "  nhận bằng lời qua lại nhiều lượt.\n"
    "- Khi tool trả về needs_confirmation: nói NGẮN GỌN rằng bản nháp/kế hoạch đang chờ\n"
    "  người dùng bấm duyệt ngay bên dưới. TUYỆT ĐỐI KHÔNG nói 'đã gửi'/'đã xoá' — chưa\n"
    "  có gì được thực hiện cả. Yêu cầu mơ hồ (thiếu người nhận/nội dung) → hỏi lại cho rõ."
)

# Dựng LLM MỘT LẦN rồi tái dùng (lazy singleton) — tránh khởi tạo lại mỗi request cho nhanh.
_llm_with_tools = None


def _get_llm():
    """Lấy LLM ĐÃ 'bind' sẵn danh sách tool. 'bind_tools' = đưa MÔ TẢ + SCHEMA các tool cho
    LLM biết → LLM tự sinh 'tool_calls' (tên tool + tham số) khi muốn dùng. Việc CHẠY tool
    là của tool_node, không phải ở đây."""
    global _llm_with_tools
    if _llm_with_tools is None:
        # QUAN TRỌNG: phải IMPORT email_tools để các @tool_registry.register CHẠY → 7 tool vào
        # registry. Thiếu dòng này thì registry RỖNG → LLM không có tool → agent "bịa" câu trả lời
        # thay vì gọi Gmail. (MCP server đã import sẵn; luồng in-app /agent/chat trước đây thì chưa.)
        import app.tools.email_tools  # noqa: F401 — side-effect: đăng ký tool vào registry
        base = create_llm()                          # tạo client Gemini từ config (.env)
        tools = tool_registry.to_langchain_tools()   # 7 tool email (đã sửa bug lọc ở registry)
        _llm_with_tools = base.bind_tools(tools)
    return _llm_with_tools


async def agent_node(state: State) -> dict:
    """Một lượt 'suy nghĩ'. Nhận State (toàn bộ hội thoại) → trả về phần CẦN CẬP NHẬT.

    LangGraph quy ước: node trả dict các field cần đổi. Ở đây:
      • messages        → THÊM 1 AIMessage (nhờ reducer add_messages, không ghi đè cũ).
      • iteration_count → +1 để graph biết đã nghĩ mấy vòng (chặn lặp vô tận).
    """
    llm = _get_llm()
    system = _SYSTEM_BASE
    if state.get("skill_context"):
        system += "\n\n# Kiến thức bổ sung cho yêu cầu này:\n" + state["skill_context"]
    if state.get("guardrail_warning"):
        system += "\n\n## Cảnh báo an toàn\n" + state["guardrail_warning"]
    messages = [SystemMessage(content=system), *state["messages"]]
    messages = [SystemMessage(content=system), *state["messages"]]
    ai = await llm.ainvoke(messages)   # gọi Gemini (bất đồng bộ) → ra 1 AIMessage
    return {"messages": [ai], "iteration_count": state.get("iteration_count", 0) + 1}


# ╔══════════════════════════════════════════════════════════════════╗
# ║ BỘ TRÌNH BÀY — đổi câu trả lời (chữ) → THẺ cho FE vẽ đẹp           ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ FE đã có renderer thẻ bento sang trọng cho AgentReply kind        ║
# ║ 'result' ({intro,title,lines}). Vấn đề: agent trả 'text' nên FE   ║
# ║ chỉ vẽ bong bóng chữ (chán). Ở đây dùng 'structured output' ép    ║
# ║ câu trả lời cuối thành cấu trúc → FE tự lên thẻ. Dữ liệu GIỮ NGUYÊN║
# ║ (chỉ định dạng lại, không bịa thêm).                              ║
# ╚══════════════════════════════════════════════════════════════════╝
# Các "mảnh" dữ liệu cho từng loại thẻ (khớp khuôn FE đang render):
class StatItem(BaseModel):
    label: str = Field(description="tên số liệu, vd 'Tổng thư', 'Chưa đọc', 'Quan trọng'")
    value: int = Field(description="con số")


class BreakdownItem(BaseModel):
    label: str = Field(description="tên nhóm/nhãn")
    count: int


class TriageItem(BaseModel):
    sender: str
    initial: str = Field(description="MỘT chữ cái đầu tên người gửi (viết hoa)")
    subject: str
    suggest: str = Field(description="gợi ý hành động ngắn, vd 'Trả lời ngay', 'Đọc khi rảnh'")


class TriageGroup(BaseModel):
    level: Literal["high", "normal"] = Field(description="'high'=ưu tiên cao, 'normal'=bình thường")
    label: str = Field(description="tên nhóm, vd 'Cần xử lý', 'Để sau'")
    items: list[TriageItem] = Field(default_factory=list)


class PresentReply(BaseModel):
    """Khuôn trình bày — agent CHỌN loại THẺ hợp nhất để FE vẽ đẹp (thay vì chữ trơn)."""
    kind: Literal["text", "result", "digest", "triage"] = Field(
        description=(
            "'result' = danh sách/tóm tắt nhiều mục; "
            "'digest' = khi có SỐ LIỆU (tổng thư/chưa đọc/quan trọng + phân bổ theo nhãn); "
            "'triage' = phân NHÓM theo ưu tiên (cao/thường) kèm gợi ý xử lý; "
            "'text' = câu trả lời ngắn/trò chuyện."
        )
    )
    intro: str = Field(description="MỘT câu dẫn ngắn, thân thiện (hiện ở bong bóng trên thẻ)")
    title: str = Field(default="", description="tiêu đề thẻ ngắn (≤6 từ)")
    text: str = Field(default="", description="câu trả lời đầy đủ — CHỈ khi kind=text")
    lines: list[str] = Field(default_factory=list, description="mỗi mục 1 dòng — CHỈ khi kind=result")
    stats: list[StatItem] = Field(default_factory=list, description="ô số liệu — CHỈ khi kind=digest")
    breakdown: list[BreakdownItem] = Field(default_factory=list, description="phân bổ theo nhãn — kind=digest")
    highlights: list[str] = Field(default_factory=list, description="vài thư/điểm nổi bật — kind=digest")
    groups: list[TriageGroup] = Field(default_factory=list, description="các nhóm ưu tiên — CHỈ khi kind=triage")


_present_llm = None


def _get_present_llm():
    """LLM riêng cho việc trình bày — bind SCHEMA (structured output)
    Ép phương thức cấu trúc phù hợp nhất với Gemini API để tránh lỗi hiển thị.
    """
    global _present_llm
    if _present_llm is None:
        # Thêm cấu hình cụ thể method="json_mode" để Gemini trả về JSON chuẩn theo cấu trúc
        _present_llm = create_llm().with_structured_output(PresentReply, method="json_mode")
    return _present_llm


_PRESENT_SYS = (
    "Bạn là bộ TỔNG HỢP + TRÌNH BÀY của trợ lý email MeoArc. Dựa vào YÊU CẦU người dùng và "
    "DỮ LIỆU email THẬT bên dưới, hãy TẠO câu trả lời gọn — dùng ĐÚNG dữ liệu (TUYỆT ĐỐI không bịa "
    "người gửi/tiêu đề/giờ), rồi chọn loại THẺ hợp nhất:\n"
    "- Liệt kê/tóm tắt nhiều email → 'result' (mỗi email MỘT dòng trong 'lines': 'Người gửi — Tiêu đề').\n"
    "- Có số liệu thống kê → 'digest' (điền 'stats', 'breakdown', 'highlights').\n"
    "- Phân nhóm theo ưu tiên → 'triage' (điền 'groups'; mỗi mục initial = chữ đầu tên người gửi).\n"
    "- Trả lời ngắn/trò chuyện → 'text' (điền 'text').\n"
    "LUẬT ĐỊNH TUYẾN CỨNG (ưu tiên hơn cảm nhận của bạn): nếu ngữ cảnh có dòng 'GỢI Ý ĐỊNH TUYẾN: "
    "kind=X' và có dữ liệu email → BẮT BUỘC dùng kind=X. Hỏi phân loại/ưu tiên mà trả 'text' là SAI.\n"
    "TUYỆT ĐỐI KHÔNG trả lời kiểu 'đã xong' chung chung — phải đưa NỘI DUNG thật.\n"
    "Người dùng nêu SỐ LƯỢNG cụ thể (vd '5 thư mới nhất') → liệt kê ĐÚNG số đó, không hơn.\n"
    "Luôn có 'intro' 1 câu + 'title' ngắn (trừ kind=text). Tiếng Việt chỉn chu, lịch sự."
)

# ── ĐỊNH TUYẾN TẤT ĐỊNH (fix TC-02): đoán kind từ Ý ĐỊNH người dùng bằng regex ──
# Vấn đề: flash-lite lúc chọn 'triage' lúc tụt về 'text' cho cùng câu "phân loại ưu tiên".
# Giải pháp: lớp regex 0-quota đoán ý định RÕ RÀNG → bơm 'GỢI Ý ĐỊNH TUYẾN' vào ngữ cảnh
# (kết hợp LUẬT CỨNG trong _PRESENT_SYS). Ý định mơ hồ → không gợi ý, LLM tự chọn như cũ.
import re as _re
import unicodedata as _ud

_KIND_HINTS: list[tuple[str, str]] = [
    # (pattern trên chữ đã bỏ dấu + thường, kind gợi ý)
    (r"(uu tien|triage|phan loai|sap xep.*(uu tien|quan trong)|gap hay|xu ly truoc)", "triage"),
    (r"(thong ke|bao nhieu (thu|email)|so luong|tong quan|digest|diem tin|bao cao)", "digest"),
    (r"(liet ke|danh sach|tim (thu|email)|nhung (thu|email) nao)", "result"),
]


def _strip_accents(s: str) -> str:
    return "".join(c for c in _ud.normalize("NFD", s) if _ud.category(c) != "Mn")


def suggest_kind(user_message: str) -> str | None:
    """Trả 'triage'/'digest'/'result' nếu ý định RÕ, ngược lại None (để LLM tự quyết)."""
    plain = _strip_accents((user_message or "").lower())
    for pat, kind in _KIND_HINTS:
        if _re.search(pat, plain):
            return kind
    return None


def _one_line(s: str) -> str:
    """Gộp mọi khoảng trắng/xuống dòng thành MỘT dấu cách + cắt rìa.
    Gemini đôi khi chèn '\\n' giữa dòng → thẻ bento FE vỡ bố cục; chuẩn hoá để mỗi mục gọn 1 dòng."""
    return " ".join((s or "").split())


def coerce_text(content) -> str:
    """ÉP KIỂU content của LangChain message về CHUỖI chuẩn.
    Tuỳ model, `content` có thể là str HOẶC list các 'part' (vd gemini-flash-latest trả
    [{'type':'text','text':'...'}]). Nếu nhét thẳng list vào JSON, FE nhận mảng thay vì chuỗi
    → render sai + TTS vỡ. Hàm này gom mọi dạng về str an toàn."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and isinstance(p.get("text"), str):
                parts.append(p["text"])
        return "\n".join(parts)
    return "" if content is None else str(content)


async def responder_node(state: State) -> dict:
    """Node cuối cùng: Tổng hợp lịch sử hội thoại thành ngữ cảnh thô
    sau đó yêu cầu Gemini ép cấu trúc sang định dạng thẻ Bento của FE.
    """
    try:
        structured_llm = _get_present_llm()
        
        # 1. CHỈ lấy LƯỢT HIỆN TẠI (từ HumanMessage gần nhất) để thẻ phản ánh đúng yêu cầu mới.
        #    Vì đã có conversation memory, state["messages"] chứa cả các lượt CŨ — nếu gom hết
        #    dữ liệu tool cũ vào thẻ sẽ bị "trộn" (vd lượt trước liệt kê thư, lượt này gửi mail
        #    lại hiện danh sách cũ). Slice từ HumanMessage cuối cùng để tránh điều đó.
        all_msgs = state["messages"]
        last_human = max((i for i, m in enumerate(all_msgs) if getattr(m, "type", None) == "human"), default=0)
        turn_msgs = all_msgs[last_human:]

        conversation_history = []
        tool_results = []
        for msg in turn_msgs:
            body = coerce_text(msg.content)  # ép về str (content có thể là list part tuỳ model)
            if msg.type == "human":
                conversation_history.append(f"Người dùng: {body}")
            elif msg.type == "ai" and body:
                conversation_history.append(f"Trợ lý: {body}")
            elif msg.type == "tool":
                tool_results.append(body)
        
        # 2. Xây dựng văn bản ngữ cảnh duy nhất (tránh lỗi trùng lặp cấu trúc tin nhắn Gemini)
        formatted_context = (
            f"=== LỊCH SỬ HỘI THOẠI ===\n"
            f"{'\n'.join(conversation_history)}\n\n"
            f"=== DỮ LIỆU EMAIL THỰC TẾ TỪ HỆ THỐNG ===\n"
            f"{'\n'.join(tool_results) if tool_results else 'Không có dữ liệu công cụ.'}"
        )

        # 2b. (fix TC-02) Ý định người dùng RÕ RÀNG → chốt kind bằng gợi ý tất định
        #     (regex, 0 quota) + luật cứng trong _PRESENT_SYS. Hết cảnh cùng câu hỏi
        #     "phân loại ưu tiên" mà lúc ra thẻ triage, lúc tụt về text.
        last_user = next((coerce_text(m.content) for m in reversed(turn_msgs)
                          if getattr(m, "type", None) == "human"), "")
        hinted = suggest_kind(last_user)
        if hinted and tool_results:
            formatted_context += f"\n\nGỢI Ý ĐỊNH TUYẾN: kind={hinted}"
        
        # 3. Gọi mô hình có cấu trúc
        pres: PresentReply = await structured_llm.ainvoke([
            SystemMessage(content=_PRESENT_SYS),
            HumanMessage(content=formatted_context)
        ])

        # ── OUTPUT GUARDRAIL — content check ─────────────────────────────────
        from app.agent.guardrails.output_guardrail import check_content
        pres.text = check_content(pres.text)
        pres.intro = check_content(pres.intro)
        pres.lines = [check_content(l) for l in pres.lines if l]
        pres.highlights = [check_content(h) for h in pres.highlights if h]
        for g in pres.groups:
            g.label = check_content(g.label)
            for item in g.items:
                item.sender = check_content(item.sender)
                item.subject = check_content(item.subject)
                item.suggest = check_content(item.suggest)

        # 4. Map dữ liệu trả về chính xác cho Frontend render
        output_dict = {"kind": pres.kind, "intro": pres.intro}
        if pres.kind == "result":
            output_dict.update({"title": pres.title, "lines": [_one_line(x) for x in pres.lines]})
        elif pres.kind == "digest":
            output_dict.update({
                "title": pres.title,
                "stats": [s.model_dump() for s in pres.stats],
                "breakdown": [b.model_dump() for b in pres.breakdown],
                "highlights": [_one_line(x) for x in pres.highlights]
            })
        elif pres.kind == "triage":
            output_dict.update({
                "title": pres.title,
                "groups": [{
                    "level": g.level,
                    "label": g.label,
                    # initial do LLM sinh có thể dài/rỗng → CHUẨN HOÁ về đúng 1 chữ cái hoa
                    # (khớp khuôn MiniAvatar của FE), sender rỗng thì lấy chữ đầu người gửi.
                    "items": [{
                        **it.model_dump(),
                        "initial": ((it.initial or it.sender or "•").strip()[:1] or "•").upper(),
                    } for it in g.items],
                } for g in pres.groups]
            })
        else:
            # kind=text: model đôi khi dồn NỘI DUNG vào 'intro' mà bỏ trống 'text' — nếu chỉ lấy
            # pres.text sẽ MẤT câu trả lời (FE không đọc intro ở thẻ text). Ưu tiên text → intro.
            output_dict.update({"text": pres.text or pres.intro or "Mình đã xử lý thông tin email cho bạn."})

        return {"final_output": output_dict}

    except Exception as e:
        # Fallback an toàn nếu Gemini bị lỗi hạn ngạch (Quota) hoặc không thể parse cấu trúc.
        import logging
        logging.getLogger(__name__).error(f"Lỗi responder_node: {str(e)}")

        # Tin cuối có thể là AIMessage mang tool_calls với content RỖNG (hoặc content dạng list)
        # → quét ngược tìm câu AI có chữ thật, ép str; không có thì dùng câu generic (tránh bubble trống).
        fallback_text = ""
        for m in reversed(state.get("messages") or []):
            if getattr(m, "type", None) == "ai":
                fallback_text = coerce_text(m.content).strip()
                if fallback_text:
                    break
        return {"final_output": {"kind": "text", "text": fallback_text or "Mình đã thực hiện xong yêu cầu, nhưng phần trình bày đang gặp trục trặc nhỏ. Bạn hỏi lại giúp mình nhé."}}