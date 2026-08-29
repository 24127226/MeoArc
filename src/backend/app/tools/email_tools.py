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

from app.services import gmail_service, gmail_actions, gmail_send, mail  # noqa: F401 (gmail_* giữ cho test monkeypatch)
from app.schemas.email import Email
from app.tools.registry import tool_registry, ToolCategory, RequestContext
from app.tools.schemas import (
    SearchEmailsInput, SearchEmailsOutput, EmailSummary,
    SemanticSearchInput,
    CategorizeEmailsInput, CategorizeEmailsOutput, CategorizedItem,
    GetEmailInput, GetEmailOutput, EmailDetail,
    SendEmailInput, SendEmailOutput,
    ReplyEmailInput, ReplyEmailOutput,
    ApplyLabelsInput, ApplyLabelsOutput,
    BulkActionInput, BulkActionOutput, BulkAction,
    ListLabelsInput, ListLabelsOutput,
    NgoaiPhamViInput, NgoaiPhamViOutput,
)
from app.core import labeling
from app.core.scope import cutoff_iso, scope_note

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
        mail.list_messages, ctx.email_provider, ctx.access_token, q=(q or None), max_results=inp.limit,
    )
    items = [_to_summary(e) for e in emails]
    return SearchEmailsOutput(
        success=True, message=f"Tìm thấy {len(items)} thư.", data=items, total_found=len(items),
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=CategorizeEmailsInput)
async def categorize_emails(inp: CategorizeEmailsInput, ctx: RequestContext) -> CategorizeEmailsOutput:
    """TỰ PHÂN LOẠI (UC009): đề xuất nhãn cho các thư gần nhất theo người gửi + nội dung
    (Học tập / Công việc / Tài chính / Mạng xã hội / Mua sắm & Ưu đãi / Cập nhật & Hệ thống /
    Cá nhân). CHỈ ĐỀ XUẤT — không áp nhãn ngay; người dùng duyệt/sửa rồi mới áp (human-in-the-loop).
    Đây là tool ĐỌC, chạy tất định (0 quota), nhanh."""
    # NFR-SCO-01: phân loại là tác vụ AI quét nội dung SẴN CÓ → giới hạn theo gói.
    emails, _ = await asyncio.to_thread(
        mail.list_messages, ctx.email_provider, ctx.access_token,
        q=(inp.query or None), max_results=inp.limit,
        scan_after=cutoff_iso(ctx.tier, days=ctx.scan_days),
    )
    items: list[CategorizedItem] = []
    summary: dict[str, int] = {}
    for e in emails:
        # Phân loại từ EMAIL người gửi (tín hiệu mạnh nhất) + tên + tiêu đề + snippet.
        c = labeling.classify(e.senderEmail, e.sender, e.subject, e.preview)
        items.append(CategorizedItem(
            id=e.id, thread_id=(e.threadId or e.id),
            sender=e.sender, subject=e.subject,
            label=c.category.label, category=c.category.color,
            confidence=c.confidence, reason=c.reason,
        ))
        summary[c.category.label] = summary.get(c.category.label, 0) + 1
    return CategorizeEmailsOutput(
        success=True,
        message=f"Đã đề xuất nhãn cho {len(items)} thư ({len(summary)} nhóm).",
        data=items, summary=summary,
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=SemanticSearchInput)
async def semantic_search(inp: SemanticSearchInput, ctx: RequestContext) -> SearchEmailsOutput:
    """Tìm email theo Ý NGHĨA (semantic) — khớp cả khi thư không chứa đúng từ khoá.
    Dùng khi chủ đề mơ hồ ('thư về tiền nong', 'liên quan bảo mật'); từ khoá/cú pháp
    Gmail chính xác thì dùng search_emails. Trả cùng khuôn tóm tắt như search_emails."""
    from app.core.embeddings import embed_query, embed_texts, rank_by_similarity

    # 1) Lấy nhóm ứng viên = các thư GẦN NHẤT (re-rank tại chỗ, không cần index trước)
    # NFR-SCO-01: tìm theo ngữ nghĩa là tác vụ AI quét nội dung SẴN CÓ → giới hạn theo gói.
    emails, _ = await asyncio.to_thread(
        mail.list_messages, ctx.email_provider, ctx.access_token, max_results=inp.pool,
        scan_after=cutoff_iso(ctx.tier, days=ctx.scan_days),
    )
    if not emails:
        # Rỗng ở đây có thể vì hộp thư trống THẬT, mà cũng có thể vì thư nằm ngoài cửa sổ
        # của gói. Nói rõ ra, chứ báo "hộp thư trống" cho người có 2000 thư là báo sai.
        return SearchEmailsOutput(
            success=True,
            message=f"Không có thư nào trong phạm vi quét. {scope_note(ctx.tier)}",
            data=[], total_found=0,
        )

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
    e = await asyncio.to_thread(mail.get_message, ctx.email_provider, ctx.access_token, inp.email_id)
    detail = EmailDetail(
        body_text="\n\n".join(e.body),
        attachments=[a.name for a in (e.attachments or [])],
        cc=[], bcc=[],
    )
    return GetEmailOutput(success=True, message="Đã lấy nội dung thư.", data=detail)


@tool_registry.register(category=ToolCategory.READ, input_schema=ListLabelsInput)
async def list_labels(inp: ListLabelsInput, ctx: RequestContext) -> ListLabelsOutput:
    """Liệt kê tên mọi nhãn trong hộp thư (để dùng trước khi gắn/bỏ nhãn)."""
    names = await asyncio.to_thread(mail.list_labels, ctx.email_provider, ctx.access_token)
    return ListLabelsOutput(success=True, message=f"Có {len(names)} nhãn.", data=names)


# ── WRITE (gửi) ──────────────────────────────────────────────────────
@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE, input_schema=SendEmailInput)
async def send_email(inp: SendEmailInput, ctx: RequestContext) -> SendEmailOutput:
    """GỬI một email mới. Chỉ gọi sau khi người dùng đã xác nhận (registry tự đánh dấu cần duyệt)."""
    res = await asyncio.to_thread(
        mail.send_email, ctx.email_provider, ctx.access_token, ", ".join(inp.to), inp.subject, inp.body,
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
        mail.reply_email, ctx.email_provider, ctx.access_token, inp.email_id, inp.instructions,
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
            mail.apply_label, ctx.email_provider, ctx.access_token, inp.email_ids, name,
        )
    for name in inp.labels_to_remove:
        await asyncio.to_thread(
            mail.remove_label, ctx.email_provider, ctx.access_token, inp.email_ids, name,
        )
    return ApplyLabelsOutput(
        success=True, message=f"Đã cập nhật nhãn cho {len(inp.email_ids)} thư.",
        data={"modified_count": modified, "failed_ids": []},
    )


@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE, input_schema=BulkActionInput)
async def bulk_action(inp: BulkActionInput, ctx: RequestContext) -> BulkActionOutput:
    """Thao tác HÀNG LOẠT: xoá (thùng rác) / đánh dấu đã đọc / chưa đọc / gắn / bỏ nhãn."""
    a = inp.action
    p, tok, ids = ctx.email_provider, ctx.access_token, inp.email_ids
    if a == BulkAction.DELETE:
        n = await asyncio.to_thread(mail.trash, p, tok, ids)
    elif a == BulkAction.MARK_READ:
        n = await asyncio.to_thread(mail.set_read, p, tok, ids, True)
    elif a == BulkAction.MARK_UNMARKED:
        n = await asyncio.to_thread(mail.set_read, p, tok, ids, False)
    elif a == BulkAction.APPLY_LABEL:
        n = await asyncio.to_thread(mail.apply_label, p, tok, ids, inp.label_name)
    else:  # REMOVE_LABEL
        n = await asyncio.to_thread(mail.remove_label, p, tok, ids, inp.label_name)
    return BulkActionOutput(
        success=True, message=f"Đã xử lý {n}/{len(inp.email_ids)} thư.",
        data={"success_count": n, "failed_count": len(inp.email_ids) - n, "failed_ids": []},
    )


# ── RANH GIỚI NĂNG LỰC ────────────────────────────────────────────────
@tool_registry.register(category=ToolCategory.SYSTEM, input_schema=NgoaiPhamViInput)
async def tu_choi_ngoai_pham_vi(inp: NgoaiPhamViInput, ctx: RequestContext) -> NgoaiPhamViOutput:
    """DÙNG KHI người dùng yêu cầu một việc MeoArc KHÔNG làm được: đặt vé máy bay, đặt
    khách sạn, gọi xe, thanh toán hoá đơn, đặt lịch hẹn ngoài, mua hàng, gọi điện, hay
    bất cứ hành động nào ngoài phạm vi hộp thư.

    ĐỪNG đi tìm thư về chủ đề đó rồi báo "không tìm thấy" — người dùng sẽ hiểu nhầm là
    hộp thư trống, chứ không hiểu là MeoArc không làm được việc đó. Gọi tool này để nói
    thẳng."""
    # Không chạm mạng, không chạm hộp thư: đây thuần tuý là một câu trả lời có cấu trúc.
    # Làm thành TOOL chứ không phải một dòng dặn trong prompt vì mô hình bám theo danh
    # sách tool chặt hơn hẳn bám theo lời cấm: cấm thì nó vẫn phải chọn MỘT hành động
    # nào đó, và hành động sẵn có gần nhất lại chính là search_emails.
    return NgoaiPhamViOutput(
        success=True,
        message="Việc này nằm ngoài phạm vi MeoArc.",
        data={
            "viec": inp.viec_nguoi_dung_muon,
            "ly_do": inp.vi_sao_khong_lam_duoc,
            "thay_the": inp.viec_gan_nhat_lam_duoc,
        },
    )
