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
from datetime import datetime, timezone, timedelta, date

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
    LietKeCamKetInput, LietKeCamKetOutput, CamKetItem,
    ApLucLichTrinhInput, ApLucLichTrinhOutput,
    DeXuatDiLaiInput, DeXuatDiLaiOutput,
    TimChuyenBayInput, TimChuyenBayOutput,
    TimKhachSanInput, TimKhachSanOutput,
    DatChoMoPhongInput, DatChoMoPhongOutput,
)
from app.core import labeling
from app.core import cam_ket as _cam_ket
from app.services import dat_cho as _dat_cho
from app.services import dat_cho_gia_lap as _gia_lap
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


# ── LỊCH TRÌNH ────────────────────────────────────────────────────────────────
# Trước đây bộ trích cam kết CHỈ chạy trong trình duyệt (frontend/src/lib/cam-ket.ts),
# nên agent hoàn toàn mù trước lịch trình: hỏi "tuần sau deadline nào nặng nhất" thì nó
# chỉ có thể đọc lại thư từ đầu rồi đoán. Đo thật 29/08/2026: grep `app/tools/` ra 0
# công cụ nào liên quan cam kết. Hai tool dưới đây lấp đúng khoảng đó.

@tool_registry.register(category=ToolCategory.READ, input_schema=LietKeCamKetInput)
async def liet_ke_cam_ket(inp: LietKeCamKetInput, ctx: RequestContext) -> LietKeCamKetOutput:
    """Liệt kê VIỆC PHẢI LÀM (cam kết, deadline, hạn nộp) trích từ hộp thư, kèm hạn và
    người đang chờ. DÙNG TOOL NÀY cho mọi câu hỏi về deadline / lịch trình / việc sắp
    tới / "tuần sau có gì" — đừng tự đọc từng thư rồi đoán."""
    # `list_messages` trả về TUPLE (danh_sách, thông_tin_phân_trang) và chỉ nhận
    # tham số theo TÊN — truyền "inbox" ở vị trí thứ ba là nhét vào `provider` của
    # hàm bọc, sai kiểu im lặng. Quét rộng hơn mặc định vì lịch trình cần nhìn cả
    # tháng, không chỉ vài thư mới nhất.
    thu, _ = await asyncio.to_thread(
        lambda: mail.list_messages(ctx.email_provider, ctx.access_token, max_results=60)
    )
    moc = datetime.now()
    ds = _cam_ket.trich_cam_ket(thu, moc)

    han_chot = moc + timedelta(days=inp.so_ngay_toi)
    loc = []
    for c in ds:
        if inp.chi_con_han:
            if c.trang_thai == "xong":
                continue
            # Việc không có hạn (vd thư đã gửi đang chờ hồi âm) VẪN giữ: nó là việc
            # hay bị quên nhất, mà lọc theo hạn thì nó rụng đầu tiên.
            if c.han and (c.han < moc or c.han > han_chot):
                continue
        loc.append(c)

    loc.sort(key=lambda c: (-c.muc_uu_tien, c.han or datetime.max))
    return LietKeCamKetOutput(
        success=True,
        message=f"Có {len(loc)} việc trong {inp.so_ngay_toi} ngày tới.",
        data=[
            CamKetItem(
                noi_dung=c.noi_dung,
                han=c.han.strftime("%d/%m/%Y %H:%M") if c.han else None,
                bat_dau=c.bat_dau.strftime("%d/%m/%Y") if c.bat_dau else None,
                han_suy_ra=c.han_suy_ra,
                nguoi_cho=c.nguoi_cho,
                email_id=c.email_id,
                uoc_luong_phut=c.uoc_luong_phut,
                muc_uu_tien=c.muc_uu_tien,
                do_tin_cay=c.do_tin_cay,
            )
            for c in loc
        ],
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=ApLucLichTrinhInput)
async def ap_luc_lich_trinh(inp: ApLucLichTrinhInput, ctx: RequestContext) -> ApLucLichTrinhOutput:
    """Tải công việc MỖI NGÀY trong những ngày tới: bao nhiêu việc, bao nhiêu phút, có
    quá tải không. DÙNG khi người dùng hỏi "tuần này có nặng không", "ngày nào rảnh",
    "mình có kham nổi không".

    Tính theo KHOẢNG LÀM chứ không theo ngày hạn: một việc 8 tiếng hạn thứ Sáu thì thứ
    Tư và thứ Năm cũng có tải."""
    # `list_messages` trả về TUPLE (danh_sách, thông_tin_phân_trang) và chỉ nhận
    # tham số theo TÊN — truyền "inbox" ở vị trí thứ ba là nhét vào `provider` của
    # hàm bọc, sai kiểu im lặng. Quét rộng hơn mặc định vì lịch trình cần nhìn cả
    # tháng, không chỉ vài thư mới nhất.
    thu, _ = await asyncio.to_thread(
        lambda: mail.list_messages(ctx.email_provider, ctx.access_token, max_results=60)
    )
    moc = datetime.now()
    ds = _cam_ket.trich_cam_ket(thu, moc)
    bang = _cam_ket.ap_luc_theo_ngay(ds, inp.so_ngay, moc)
    so_qua_tai = sum(1 for x in bang if x["qua_tai"])
    return ApLucLichTrinhOutput(
        success=True,
        message=(f"{so_qua_tai} ngày quá tải trong {inp.so_ngay} ngày tới."
                 if so_qua_tai else f"Không ngày nào quá tải trong {inp.so_ngay} ngày tới."),
        data=bang,
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=DeXuatDiLaiInput)
async def de_xuat_di_lai(inp: DeXuatDiLaiInput, ctx: RequestContext) -> DeXuatDiLaiOutput:
    """Tìm những việc trong hộp thư NGỤ Ý PHẢI ĐI XA (buổi bảo vệ, chung kết, phỏng vấn
    ở thành phố khác) và ĐỀ XUẤT ngày nên có mặt.

    CHỈ ĐỀ XUẤT — tool này KHÔNG đặt vé, KHÔNG đặt phòng, không gọi ra ngoài. Người
    dùng hỏi thẳng "đặt vé giúp mình" thì vẫn phải gọi `tu_choi_ngoai_pham_vi`."""
    thu, _ = await asyncio.to_thread(
        lambda: mail.list_messages(ctx.email_provider, ctx.access_token, max_results=60)
    )
    moc = datetime.now()
    ds = _cam_ket.trich_cam_ket(thu, moc)

    han_chot = moc + timedelta(days=inp.so_ngay_toi)
    ds = [c for c in ds if c.han and moc <= c.han <= han_chot]

    # Địa điểm nằm trong THÂN THƯ, mà CamKet chỉ giữ một câu tóm tắt — nên phải dựng
    # bản đồ id → toàn văn rồi truyền vào.
    van = {}
    for e in thu:
        body = getattr(e, "body", None) or []
        van[str(getattr(e, "id", ""))] = f"{getattr(e, 'subject', '')} {' '.join(body)}"

    y_dinh = _cam_ket.suy_y_dinh_di_lai(ds, van, inp.tu_thanh_pho)
    return DeXuatDiLaiOutput(
        success=True,
        message=(f"Có {len(y_dinh)} việc cần đi xa trong {inp.so_ngay_toi} ngày tới."
                 if y_dinh else "Không có việc nào cần đi xa."),
        data=[y.to_dict() for y in y_dinh],
    )


# ── GIAI ĐOẠN 2: TRA CỨU (vẫn CHỈ ĐỌC, chưa tiêu tiền) ───────────────────────

def _doc_ngay_vn(s: str) -> date:
    """Đọc 'dd/mm/yyyy'. Sai định dạng thì NÉM LỖI chứ không đoán — đoán nhầm ngày
    bay là loại nhầm mà người dùng chỉ phát hiện ở sân bay."""
    return datetime.strptime(s.strip(), "%d/%m/%Y").date()


@tool_registry.register(category=ToolCategory.READ, input_schema=TimChuyenBayInput)
async def tim_chuyen_bay(inp: TimChuyenBayInput, ctx: RequestContext) -> TimChuyenBayOutput:
    """TRA CỨU chuyến bay theo chặng và ngày. Trả danh sách lựa chọn kèm giá, giờ, số
    điểm dừng.

    CHỈ TRA CỨU — tool này KHÔNG giữ chỗ, KHÔNG đặt, KHÔNG thanh toán. Mỗi kết quả mang
    trường `nguon`: "mo_phong" nghĩa là SỐ MÔ PHỎNG, phải nói rõ cho người dùng biết,
    tuyệt đối không trình bày như giá thật."""
    ncc = _dat_cho.lay_nha_cung_cap()
    try:
        ngay = _doc_ngay_vn(inp.ngay)
    except ValueError:
        return TimChuyenBayOutput(
            success=False, message=f"Ngày '{inp.ngay}' không đúng dạng dd/mm/yyyy.", data=[],
        )
    ds = await asyncio.to_thread(
        ncc.tim_chuyen_bay, inp.tu.upper(), inp.den.upper(), ngay, inp.so_ket_qua
    )
    mo_phong = bool(ds) and ds[0].nguon == "mo_phong"
    return TimChuyenBayOutput(
        success=True,
        message=(f"Có {len(ds)} chuyến {inp.tu.upper()}→{inp.den.upper()} ngày {inp.ngay}."
                 + (" ĐÂY LÀ SỐ MÔ PHỎNG, không phải giá thật." if mo_phong else "")),
        data=[c.to_dict() for c in ds],
    )


@tool_registry.register(category=ToolCategory.READ, input_schema=TimKhachSanInput)
async def tim_khach_san(inp: TimKhachSanInput, ctx: RequestContext) -> TimKhachSanOutput:
    """TRA CỨU khách sạn theo thành phố và ngày. Trả lựa chọn kèm giá mỗi đêm, tổng
    tiền, số sao, khoảng cách trung tâm, có huỷ miễn phí không.

    CHỈ TRA CỨU — không giữ chỗ, không đặt, không thanh toán. Xem trường `nguon` như
    `tim_chuyen_bay`."""
    ncc = _dat_cho.lay_nha_cung_cap()
    try:
        nhan, tra = _doc_ngay_vn(inp.nhan_phong), _doc_ngay_vn(inp.tra_phong)
    except ValueError:
        return TimKhachSanOutput(
            success=False, message="Ngày không đúng dạng dd/mm/yyyy.", data=[],
        )
    if tra <= nhan:
        return TimKhachSanOutput(
            success=False, message="Ngày trả phòng phải sau ngày nhận phòng.", data=[],
        )
    try:
        ds = await asyncio.to_thread(
            ncc.tim_khach_san, inp.thanh_pho, nhan, tra, inp.so_ket_qua
        )
    except NotImplementedError as e:
        return TimKhachSanOutput(success=False, message=str(e), data=[])

    mo_phong = bool(ds) and ds[0].nguon == "mo_phong"
    return TimKhachSanOutput(
        success=True,
        message=(f"Có {len(ds)} khách sạn ở {inp.thanh_pho}."
                 + (" ĐÂY LÀ SỐ MÔ PHỎNG, không phải giá thật." if mo_phong else "")),
        data=[k.to_dict() for k in ds],
    )


# ── GIAI ĐOẠN 3: ĐẶT CHỖ MÔ PHỎNG, đi qua CỔNG XÁC NHẬN + CỔNG TIỀN ──────────
@tool_registry.register(category=ToolCategory.WRITE_DESTRUCTIVE,
                        input_schema=DatChoMoPhongInput)
async def dat_cho_mo_phong(inp: DatChoMoPhongInput, ctx: RequestContext) -> DatChoMoPhongOutput:
    """ĐẶT CHỖ MÔ PHỎNG một chuyến bay hoặc khách sạn đã tra cứu được.

    KHÔNG PHẢI ĐẶT THẬT: không có vé, không có phòng, không đồng nào được thanh toán.
    MeoArc chưa nối với hệ thống đặt chỗ nào. Tool này tồn tại để trình bày cơ chế
    duyệt-trước-khi-tiêu-tiền, và người dùng PHẢI được nói rõ điều đó.

    Gọi tool này thì hệ thống TỰ CHẶN lại thành thẻ chờ duyệt — đừng nói 'đã đặt xong'."""
    # Tên hàm mang chữ "mo_phong" là CÓ CHỦ Ý: agent đọc danh sách tool sẽ thấy ngay,
    # và nó không thể vô tình trình bày đây như đặt thật.
    if _gia_lap.co_nha_cung_cap_that():
        # Có khoá Amadeus mà vẫn chạy mô phỏng là kiểu nhầm tệ nhất: người vận hành
        # tưởng hệ thống đã đặt thật. Thà từ chối.
        return DatChoMoPhongOutput(
            success=False,
            message="Hệ thống đang cấu hình nhà cung cấp THẬT, mà phần đặt chỗ thật "
                    "chưa nối. Không chạy mô phỏng trong tình huống này.",
            data=None,
        )

    from app.core.db import SessionLocal
    from app.services import cong_tien

    chi_tiet = {
        "loai": inp.loai, "ma_lua_chon": inp.ma_lua_chon,
        "ngay": inp.ngay, "hoan_duoc": inp.hoan_duoc,
    }
    db = SessionLocal()
    try:
        try:
            don = cong_tien.tao_du_dinh(
                db, user_id=int(ctx.user_id), loai=inp.loai, mo_ta=inp.mo_ta,
                so_tien_vnd=inp.so_tien_vnd, chi_tiet=chi_tiet,
            )
        except cong_tien.CongTienTuChoi as e:
            # Vượt trần chi tiêu → nói thẳng lý do, đừng nuốt thành lỗi chung chung.
            return DatChoMoPhongOutput(success=False, message=str(e), data=None)

        don = await asyncio.to_thread(
            cong_tien.thuc_thi, db,
            don=don,
            # Tới được đây nghĩa là người dùng ĐÃ bấm duyệt trên giao diện — endpoint
            # /confirmations/{id}/approve mới gọi tool này.
            nguoi_duyet=f"user:{ctx.user_id}",
            chay=lambda: _gia_lap.dat_cho_mo_phong(inp.loai, chi_tiet),
        )
        return DatChoMoPhongOutput(
            success=True,
            message=f"Đã tạo đặt chỗ MÔ PHỎNG {don.ket_qua.get('ma_dat_cho')}. "
                    "Đây không phải vé thật.",
            data={"don_id": don.id, "trang_thai": don.trang_thai, **(don.ket_qua or {})},
        )
    finally:
        db.close()
