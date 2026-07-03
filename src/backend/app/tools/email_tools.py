# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/tools/email_tools.py — ĐƯỜNG NỐI "não → tay" (Pha 2 tích hợp)  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là chỗ bộ não (agent/develop) CHẠM vào đôi tay (services/quan).║
# ║ Mỗi tool nhận `ctx.access_token` (do api/deps cấp, đã tự refresh)  ║
# ║ rồi gọi thẳng gmail_service / gmail_actions / gmail_send của quan. ║
# ║ Service là ĐỒNG BỘ (httpx blocking) → bọc asyncio.to_thread để     ║
# ║ KHÔNG chẹn event loop của agent.                                  ║
# ║ Đăng ký qua tool_registry → agent (LangGraph) lẫn MCP đều gọi được.║
# ╚══════════════════════════════════════════════════════════════════╝

import asyncio
from datetime import datetime, timezone

from app.services import gmail_service, gmail_actions, gmail_send
from app.schemas.email import Email
from app.tools.registry import tool_registry, ToolCategory, RequestContext
from app.tools.schemas import (
    SearchEmailsInput, SearchEmailsOutput, EmailSummary,
    SemanticSearchInput,
    GetEmailInput, GetEmailOutput, EmailDetail,
    SendEmailInput, SendEmailOutput,
    ReplyEmailInput, ReplyEmailOutput,
    ApplyLabelsInput, ApplyLabelsOutput,
    BulkActionInput, BulkActionOutput, BulkAction,
    ListLabelsInput, ListLabelsOutput,
)

_SYSTEM_LABELS = {"UNREAD", "STARRED", "INBOX", "IMPORTANT", "SPAM", "TRASH"}


def _parse_dt(s: str) -> datetime:
    """Email của quan giữ ngày dạng chuỗi 'dd/mm/YYYY HH:MM'. Đổi về datetime cho schema agent.
    Không parse được → mốc hiện tại (TODO: quan nên trả ISO 8601 để khỏi đoán)."""
    try:
        return datetime.strptime(s, "%d/%m/%Y %H:%M")
    except Exception:
        return datetime.now(timezone.utc)


def _to_summary(e: Email) -> EmailSummary:
    """Ánh xạ Email (khuôn FE của quan) → EmailSummary (khuôn agent của develop).
    (Đã đóng nợ threadId — giờ là id luồng THẬT từ Gmail; `category` màu FE ≠ enum agent
    vẫn để None vì phân loại thông minh là việc của UC009/AI, không đoán bừa.)"""
    return EmailSummary(
        id=e.id,
        thread_id=e.threadId or e.id,         # luồng THẬT từ Gmail; thiếu thì lùi về id
        sender=e.sender,
        subject=e.subject,
        recipient=[e.to] if e.to else [],
        date=_parse_dt(e.date),
        snippet=e.preview,
        is_read=not e.unread,
        labels=(["STARRED"] if e.starred else []),
        category=None,                        # TODO: map màu moss/sea… → EmailCategory enum
    )


# ── READ ─────────────────────────────────────────────────────────────
@tool_registry.register(category=ToolCategory.READ, input_schema=SearchEmailsInput)
async def search_emails(inp: SearchEmailsInput, ctx: RequestContext) -> SearchEmailsOutput:
    """Tìm email theo từ khoá hoặc cú pháp Gmail. Trả danh sách tóm tắt để agent chọn lọc."""
    q = inp.query or ""
    if inp.is_read is True:
        q = (q + " -is:unread").strip()       # chỉ thư đã đọc
    elif inp.is_read is False:
        q = (q + " is:unread").strip()        # chỉ thư chưa đọc
    emails, _ = await asyncio.to_thread(
        gmail_service.list_messages, ctx.access_token, q=(q or None), max_results=inp.limit,
    )
    items = [_to_summary(e) for e in emails]
    return SearchEmailsOutput(
        success=True, message=f"Tìm thấy {len(items)} thư.", data=items, total_found=len(items),
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=SemanticSearchInput)
async def semantic_search(inp: SemanticSearchInput, ctx: RequestContext) -> SearchEmailsOutput:
    """Tìm email theo Ý NGHĨA (semantic) — khớp cả khi thư không chứa đúng từ khoá.
    Dùng khi chủ đề mơ hồ ('thư về tiền nong', 'liên quan bảo mật'); từ khoá/cú pháp
    Gmail chính xác thì dùng search_emails. Trả cùng khuôn tóm tắt như search_emails."""
    from app.core.embeddings import embed_query, embed_texts, rank_by_similarity

    # 1) Lấy nhóm ứng viên = các thư GẦN NHẤT (re-rank tại chỗ, không cần index trước)
    emails, _ = await asyncio.to_thread(
        gmail_service.list_messages, ctx.access_token, max_results=inp.pool,
    )
    if not emails:
        return SearchEmailsOutput(success=True, message="Hộp thư trống.", data=[], total_found=0)

    # 2) Đổi câu hỏi + (tiêu đề — snippet) từng thư thành vector rồi xếp theo độ gần nghĩa.
    #    embed chạy blocking → đẩy sang thread như mọi lời gọi mạng khác ở file này.
    docs = [f"{e.subject}\n{e.preview}" for e in emails]
    q_vec, d_vecs = await asyncio.to_thread(
        lambda: (embed_query(inp.query), embed_texts(docs))
    )
    top = rank_by_similarity(q_vec, d_vecs, inp.limit)

    items = [_to_summary(emails[i]) for i, _score in top]
    return SearchEmailsOutput(
        success=True,
        message=f"Top {len(items)} thư khớp NGHĨA với '{inp.query}'.",
        data=items, total_found=len(items),
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=GetEmailInput)
async def get_email(inp: GetEmailInput, ctx: RequestContext) -> GetEmailOutput:
    """Lấy NỘI DUNG ĐẦY ĐỦ một email (thân thư + đính kèm) để đọc, tóm tắt hoặc trả lời."""
    e = await asyncio.to_thread(gmail_service.get_message, ctx.access_token, inp.email_id)
    detail = EmailDetail(
        body_text="\n\n".join(e.body),
        attachments=[a.name for a in (e.attachments or [])],
        cc=[], bcc=[],
    )
    return GetEmailOutput(success=True, message="Đã lấy nội dung thư.", data=detail)


@tool_registry.register(category=ToolCategory.READ, input_schema=ListLabelsInput)
async def list_labels(inp: ListLabelsInput, ctx: RequestContext) -> ListLabelsOutput:
    """Liệt kê tên mọi nhãn trong hộp thư (để dùng trước khi gắn/bỏ nhãn)."""
    names = await asyncio.to_thread(gmail_actions.list_label_names, ctx.access_token)
    return ListLabelsOutput(success=True, message=f"Có {len(names)} nhãn.", data=names)


# ── WRITE (gửi) ──────────────────────────────────────────────────────
@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE, input_schema=SendEmailInput)
async def send_email(inp: SendEmailInput, ctx: RequestContext) -> SendEmailOutput:
    """GỬI một email mới. Chỉ gọi sau khi người dùng đã xác nhận (registry tự đánh dấu cần duyệt)."""
    res = await asyncio.to_thread(
        gmail_send.send_email, ctx.access_token, ", ".join(inp.to), inp.subject, inp.body,
        cc=inp.cc or None, bcc=inp.bcc or None,
    )
    return SendEmailOutput(
        success=True, message="Đã gửi email.",
        data={"message_id": res.get("id", ""), "thread_id": res.get("threadId", "")},
    )


@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE, input_schema=ReplyEmailInput)
async def reply_email(inp: ReplyEmailInput, ctx: RequestContext) -> ReplyEmailOutput:
    """TRẢ LỜI một email (giữ đúng luồng). Lưu ý: `instructions` ở đây coi như NỘI DUNG ĐÃ CHỐT
    để gửi — agent nên soạn/duyệt nội dung TRƯỚC rồi mới gọi tool này (TODO nhóm: tách bước soạn)."""
    res = await asyncio.to_thread(
        gmail_send.reply_email, ctx.access_token, inp.email_id, inp.instructions,
    )
    return ReplyEmailOutput(
        success=True, message="Đã gửi trả lời.",
        data={"message_id": res.get("id", ""), "thread_id": res.get("threadId", "")},
    )


# ── MANAGEMENT (nhãn / hàng loạt) ────────────────────────────────────
@tool_registry.register(category=ToolCategory.WRITE_REVERSIBLE, input_schema=ApplyLabelsInput)
async def apply_labels(inp: ApplyLabelsInput, ctx: RequestContext) -> ApplyLabelsOutput:
    """Thêm/bớt nhãn cho email. Thêm: tạo nhãn nếu chưa có. Bớt: hiện hỗ trợ nhãn hệ thống."""
    modified = 0
    for name in inp.labels_to_add:
        modified += await asyncio.to_thread(
            gmail_actions.apply_label, ctx.access_token, inp.email_ids, name,
        )
    for name in inp.labels_to_remove:
        if name.upper() in _SYSTEM_LABELS:    # nhãn tự tạo cần resolve id → TODO nhóm
            await asyncio.to_thread(
                gmail_actions.modify_labels, ctx.access_token, inp.email_ids, None, [name.upper()],
            )
    return ApplyLabelsOutput(
        success=True, message=f"Đã cập nhật nhãn cho {len(inp.email_ids)} thư.",
        data={"modified_count": modified, "failed_ids": []},
    )


@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE, input_schema=BulkActionInput)
async def bulk_action(inp: BulkActionInput, ctx: RequestContext) -> BulkActionOutput:
    """Thao tác HÀNG LOẠT: xoá (thùng rác) / đánh dấu đã đọc / chưa đọc / gắn / bỏ nhãn."""
    a = inp.action
    if a == BulkAction.DELETE:
        n = await asyncio.to_thread(gmail_actions.trash, ctx.access_token, inp.email_ids)
    elif a == BulkAction.MARK_READ:
        n = await asyncio.to_thread(
            gmail_actions.modify_labels, ctx.access_token, inp.email_ids, None, ["UNREAD"])
    elif a == BulkAction.MARK_UNMARKED:
        n = await asyncio.to_thread(
            gmail_actions.modify_labels, ctx.access_token, inp.email_ids, ["UNREAD"], None)
    elif a == BulkAction.APPLY_LABEL:
        n = await asyncio.to_thread(
            gmail_actions.apply_label, ctx.access_token, inp.email_ids, inp.label_name)
    else:  # REMOVE_LABEL
        n = await asyncio.to_thread(
            gmail_actions.modify_labels, ctx.access_token, inp.email_ids, None, [inp.label_name])
    return BulkActionOutput(
        success=True, message=f"Đã xử lý {n}/{len(inp.email_ids)} thư.",
        data={"success_count": n, "failed_count": len(inp.email_ids) - n, "failed_ids": []},
    )
