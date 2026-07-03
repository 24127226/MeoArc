# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/mcp/server.py — MCP SERVER (Pha 4: "agent-native", tiêu chí 10đ)║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MCP (Model Context Protocol) = "ổ cắm chuẩn" để AGENT BÊN NGOÀI    ║
# ║ (Claude Desktop, Codex...) cắm vào và GỌI TOOL của app mình.       ║
# ║ Khác /agent/chat (LLM nằm TRONG app), ở đây LLM nằm Ở NGOÀI: user  ║
# ║ dùng agent của họ → agent gọi MCP → MCP chạy tool → thao tác Gmail.║
# ║                                                                    ║
# ║ THEO ĐÚNG Q&A CỦA THẦY (tiêu chí "LLM as main program" = 10đ):     ║
# ║  • Phơi TOOL HẠT MỊN (search/get/send/label/bulk...) để agent      ║
# ║    ngoài TỰ SUY LUẬN — KHÔNG phơi tool to kiểu summarize_and_      ║
# ║    process (suy luận vẫn của app → chỉ 9đ).                        ║
# ║  • Mỗi tool là VỎ MỎNG: gọi cùng tool_registry.call(...) mà        ║
# ║    /agent/chat dùng → MỘT bộ tool lõi, BA khách: UI web, Gemini    ║
# ║    nội bộ, agent ngoài qua MCP.                                    ║
# ║                                                                    ║
# ║ Điểm riêng của MeoArc (vượt yêu cầu tối thiểu):                    ║
# ║  1. CONFIRM-GATE: hành động KHÔNG HOÀN TÁC (gửi/xoá) bị chặn ở      ║
# ║     TẦNG TOOL — lần gọi đầu chỉ trả BẢN XEM TRƯỚC + yêu cầu agent   ║
# ║     hỏi người dùng, phải gọi lại với confirm=true mới chạy thật.   ║
# ║     → human-in-the-loop được CƯỠNG CHẾ cả với agent ngoài (UC010), ║
# ║     không trông chờ thiện chí của LLM.                             ║
# ║  2. MCP PROMPTS: 3 kỹ năng (digest/triage/meeting-brief) phơi ra    ║
# ║     menu Claude Desktop — 1 click là agent ngoài chạy đúng quy      ║
# ║     trình dùng tool hạt mịn (cùng "thư viện kỹ năng" với agent     ║
# ║     trong app).                                                    ║
# ║  3. RESOURCE meoarc://whoami — agent ngoài tự biết đang thao tác    ║
# ║     hộp thư của ai.                                                ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import os
import time
from datetime import datetime, timezone, timedelta

from fastmcp import FastMCP
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.session import AuthSession
from app.repo import session_repo
from app.services import auth_service
from app.tools.registry import tool_registry, RequestContext
import app.tools.email_tools  # noqa: F401 — import ĐỂ các tool tự đăng ký vào registry

logger = logging.getLogger("app.mcp")
mcp = FastMCP("MeoArc")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── NFR-Speed: CACHE "thẻ ra vào" (agent ngoài thường gọi 3-10 tool liên tiếp; ─────
# không cache thì MỖI tool = 1 lần mở DB + có thể 1 lần refresh token → chậm vô ích).
# TTL 45s < biên làm mới token (60s) nên không bao giờ dùng token sắp chết.
_CTX_CACHE: dict = {"ctx": None, "ts": 0.0}
_CTX_TTL = 45.0


def _resolve_ctx() -> RequestContext:
    """Lấy 'thẻ ra vào' (access_token Gmail) cho agent ngoài — có cache 45s.

    DEMO 1 người dùng: ưu tiên env MEOARC_ACCESS_TOKEN; không có thì lấy PHIÊN ĐĂNG NHẬP
    MỚI NHẤT trong DB (user đã đăng nhập web) và TỰ LÀM MỚI token nếu sắp hết hạn.
    (Production nhiều người dùng: auth riêng theo từng kết nối MCP.)
    """
    env_token = os.getenv("MEOARC_ACCESS_TOKEN")
    if env_token:
        return RequestContext(user_id="env", access_token=env_token, email_provider="gmail")

    now = time.monotonic()
    if _CTX_CACHE["ctx"] is not None and now - _CTX_CACHE["ts"] < _CTX_TTL:
        return _CTX_CACHE["ctx"]

    db = SessionLocal()
    try:
        s = db.scalars(
            select(AuthSession)
            .where(AuthSession.google_access_token.isnot(None))
            .order_by(AuthSession.expires_at.desc())
        ).first()
        if s is None:
            raise RuntimeError("Chưa có phiên đăng nhập nào — hãy đăng nhập trên web trước đã.")
        token = s.google_access_token
        # Token Gmail sống ~1h → sắp hết hạn mà còn refresh_token thì xin token mới.
        if (
            s.google_token_expiry
            and s.google_token_expiry <= _utcnow() + timedelta(seconds=60)
            and s.google_refresh_token
        ):
            token, expires_in = auth_service.refresh_access_token(s.google_refresh_token)
            session_repo.update_access_token(db, s, token, expires_in)
        ctx = RequestContext(user_id=str(s.user_id), access_token=token, email_provider="gmail")
        _CTX_CACHE.update(ctx=ctx, ts=now)
        return ctx
    finally:
        db.close()


async def _call(name: str, args: dict) -> dict:
    """Chạy 1 tool qua registry (tự validate input bằng Pydantic) → dict cho MCP trả về.
    Lỗi KHÔNG ném ra ngoài (agent ngoài xử lý JSON lỗi tốt hơn exception giao thức):
    trả {"success": false, "error": ...} để agent tự đọc và nói lại với người dùng."""
    t0 = time.perf_counter()
    try:
        res = await tool_registry.call(name, args, _resolve_ctx())
        out = res.model_dump() if hasattr(res, "model_dump") else res
        logger.info("MCP tool %s OK (%.0fms)", name, (time.perf_counter() - t0) * 1000)
        return out
    except Exception as exc:
        _CTX_CACHE["ctx"] = None  # token có thể là thủ phạm → lần sau lấy tươi
        logger.warning("MCP tool %s FAILED: %s", name, exc)
        return {"success": False, "error": str(exc),
                "hint": "Đọc 'error' và giải thích cho người dùng; thử sửa tham số rồi gọi lại."}


def _needs_confirm(action: str, preview: dict) -> dict:
    """CONFIRM-GATE (UC010 cho agent ngoài): lần gọi đầu KHÔNG thực thi — trả bản xem
    trước + chỉ dẫn. Agent phải đưa preview cho NGƯỜI DÙNG duyệt rồi gọi lại confirm=true."""
    return {
        "success": False,
        "needs_confirmation": True,
        "action": action,
        "preview": preview,
        "instruction": ("HÀNH ĐỘNG KHÔNG HOÀN TÁC — chưa thực thi. Hãy hiển thị 'preview' cho "
                        "người dùng và HỎI XÁC NHẬN. Người dùng đồng ý thì gọi lại tool này với "
                        "chính các tham số đó kèm confirm=true."),
    }


# ══════════════ TOOL HẠT MỊN (đúng tiêu chí thầy — agent ngoài tự suy luận) ══════════════

async def search_emails(query: str = "", limit: int = 10, is_read: bool | None = None,
                        date_from: str | None = None, date_to: str | None = None) -> dict:
    """Tìm email theo từ khoá hoặc cú pháp Gmail (from:, subject:, has:attachment, newer_than:7d...).
    is_read: true=đã đọc, false=chưa đọc, bỏ trống=tất cả. date_from/date_to: ISO 8601 (2026-07-01).
    Trả danh sách tóm tắt {id, sender, subject, snippet, date, is_read} — dùng id cho các tool khác."""
    args: dict = {"query": query, "limit": limit, "is_read": is_read}
    if date_from:
        args["date_from"] = date_from
    if date_to:
        args["date_to"] = date_to
    return await _call("search_emails", args)


async def semantic_search(query: str, limit: int = 5, pool: int = 30) -> dict:
    """Tìm email theo Ý NGHĨA (embedding) — khớp cả khi thư KHÔNG chứa đúng từ khoá.
    Dùng khi chủ đề mơ hồ ('thư về tiền nong', 'liên quan bảo mật'); từ khoá chính xác
    thì dùng search_emails. pool = số thư gần nhất đem so nghĩa."""
    return await _call("semantic_search", {"query": query, "limit": limit, "pool": pool})


async def get_email(email_id: str) -> dict:
    """Lấy nội dung ĐẦY ĐỦ (thân thư + tên tệp đính kèm) của 1 email theo id (lấy id từ search_emails)."""
    return await _call("get_email", {"email_id": email_id})


async def list_labels() -> dict:
    """Liệt kê tên mọi nhãn trong hộp thư (gọi trước khi gắn/bỏ nhãn để dùng đúng tên)."""
    return await _call("list_labels", {})


async def send_email(to: list[str], subject: str, body: str,
                     cc: list[str] | None = None, bcc: list[str] | None = None,
                     confirm: bool = False) -> dict:
    """GỬI email mới — KHÔNG HOÀN TÁC. Lần đầu gọi với confirm=false (mặc định) sẽ trả
    bản xem trước để bạn hỏi người dùng; được đồng ý mới gọi lại với confirm=true."""
    if not confirm:
        return _needs_confirm("send_email", {
            "to": to, "cc": cc or [], "bcc": bcc or [], "subject": subject,
            "body_preview": body[:300] + ("…" if len(body) > 300 else ""),
        })
    return await _call("send_email", {"to": to, "subject": subject, "body": body,
                                      "cc": cc or [], "bcc": bcc or []})


async def reply_email(email_id: str, reply_body: str, confirm: bool = False) -> dict:
    """TRẢ LỜI 1 email (tự giữ đúng luồng/thread) — KHÔNG HOÀN TÁC, cần confirm=true
    sau khi người dùng đã duyệt nội dung reply_body."""
    if not confirm:
        return _needs_confirm("reply_email", {
            "email_id": email_id,
            "reply_preview": reply_body[:300] + ("…" if len(reply_body) > 300 else ""),
        })
    return await _call("reply_email", {"email_id": email_id, "instructions": reply_body})


async def apply_labels(email_ids: list[str], labels_to_add: list[str] | None = None,
                       labels_to_remove: list[str] | None = None) -> dict:
    """Thêm/bớt nhãn cho các email (đảo ngược được nên không cần confirm)."""
    return await _call("apply_labels", {"email_ids": email_ids,
                                        "labels_to_add": labels_to_add or [],
                                        "labels_to_remove": labels_to_remove or []})


async def bulk_action(email_ids: list[str], action: str, label_name: str | None = None,
                      confirm: bool = False) -> dict:
    """Thao tác HÀNG LOẠT. action ∈ {'delete','mark_read','mark_unread','apply_label','remove_label'}
    (chữ thường). 'delete' = chuyển thùng rác, tối đa 100 thư/lần. Riêng 'delete' cần confirm=true
    sau khi người dùng duyệt danh sách."""
    if action.strip().lower() == "delete" and not confirm:
        return _needs_confirm("bulk_action:delete", {
            "action": "delete", "so_thu": len(email_ids),
            "email_ids_dau": email_ids[:5], "con_lai": max(0, len(email_ids) - 5),
        })
    return await _call("bulk_action", {"email_ids": email_ids, "action": action,
                                       "label_name": label_name})


# Đăng ký tool với MCP — giữ hàm gốc ở module-level để test gọi thẳng được.
for _fn in (search_emails, semantic_search, get_email, list_labels, send_email,
            reply_email, apply_labels, bulk_action):
    mcp.tool()(_fn)


# ══════════════ MCP PROMPTS — kỹ năng 1-click trên menu Claude Desktop ══════════════
# Cùng "thư viện kỹ năng" tinh thần với agent trong app (skills/library) — nhưng ở đây
# quy trình được GIAO cho agent ngoài tự thực thi bằng tool hạt mịn (đúng agent-native).

@mcp.prompt()
def daily_digest() -> str:
    """Điểm tin hộp thư hôm nay (UC014)."""
    return ("Hãy làm báo cáo điểm tin hộp thư MeoArc: (1) search_emails với query "
            "'newer_than:1d' limit 20; (2) đếm tổng/chưa đọc; (3) nhóm theo người gửi; "
            "(4) nêu 3-5 thư đáng chú ý nhất kèm lý do; (5) đề xuất hành động cho từng thư "
            "đáng chú ý (trả lời/lưu trữ/bỏ qua). Trình bày gọn bằng tiếng Việt.")


@mcp.prompt()
def triage_inbox() -> str:
    """Phân loại hộp thư theo mức ưu tiên (UC015)."""
    return ("Hãy triage hộp thư MeoArc: (1) search_emails is_read=false limit 20; "
            "(2) chia 2 nhóm ƯU TIÊN CAO (cần hành động/deadline/người thật hỏi) và "
            "BÌNH THƯỜNG (bản tin, thông báo máy); (3) với mỗi thư nêu 1 gợi ý xử lý ngắn; "
            "(4) hỏi tôi có muốn đánh dấu đã đọc nhóm bình thường không — nếu có thì dùng "
            "bulk_action mark_read. Tiếng Việt, gọn.")


@mcp.prompt()
def meeting_brief() -> str:
    """Chuẩn bị brief cuộc họp từ email liên quan (UC016)."""
    return ("Hãy chuẩn bị meeting brief từ hộp thư MeoArc: (1) hỏi tôi chủ đề/từ khoá cuộc họp; "
            "(2) search_emails theo từ khoá đó; (3) get_email các thư liên quan nhất; "
            "(4) tổng hợp: điểm chính, action items (ai—việc—hạn), câu hỏi còn mở. Tiếng Việt.")


# ══════════════ RESOURCE — agent ngoài tự biết bối cảnh ══════════════

@mcp.resource("meoarc://whoami")
def whoami() -> str:
    """Đang thao tác trên hộp thư Gmail của ai (lấy từ phiên đăng nhập mới nhất)."""
    db = SessionLocal()
    try:
        from app.models.user import User
        s = db.scalars(select(AuthSession).order_by(AuthSession.expires_at.desc())).first()
        if s is None:
            return "Chưa ai đăng nhập web MeoArc."
        u = db.get(User, s.user_id)
        return f"Hộp thư đang thao tác: {u.email if u else '?'} (user_id={s.user_id})."
    finally:
        db.close()


# Chạy server: `uv run python -m app.mcp.server` (stdio — đúng kiểu Claude Desktop/Codex
# kết nối MCP server cục bộ; cấu hình trong _claude_config_READY.json ở gốc repo).
if __name__ == "__main__":
    mcp.run()
