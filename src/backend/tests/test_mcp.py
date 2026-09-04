"""test_mcp.py — Kênh MCP cho agent NGOÀI (tiêu chí 10đ của thầy) + an toàn UC010.

Chuẩn khách quan (từ Q&A của thầy + SRS, KHÔNG từ code):
  * Thầy: "MCP server phải phơi TOOL HẠT MỊN (search_emails, get_email, send_email,
    apply_label, batch_delete...) để agent ngoài TỰ SUY LUẬN — không phơi tool to kiểu
    summarize_and_process" → kiểm danh sách tool phơi ra đúng hạt mịn, không có tool "to".
  * SRS UC010 (human-in-the-loop): hành động KHÔNG HOÀN TÁC phải được người dùng duyệt
    → confirm-gate: gọi lần đầu KHÔNG được thực thi, phải trả bản xem trước.
  * Hợp đồng BulkAction đã công bố: action nhận chữ thường 'delete'… (LLM viết hoa vẫn chạy).

Chạy: uv run pytest tests/test_mcp.py -v   (KHÔNG cần server/Gmail/LLM — registry được thay bằng gián điệp)
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

import app.mcp.server as mcp_server
from app.tools.registry import RequestContext
from app.tools.schemas import BulkAction, BulkActionInput


# ── Hợp đồng BulkAction: case-insensitive, đúng bộ giá trị công bố ───────────
@pytest.mark.parametrize("raw", ["delete", "Delete", "DELETE"])
def test_bulk_action_delete_moi_kieu_viet_deu_chay(raw):
    inp = BulkActionInput(email_ids=["id1"], action=raw)
    assert inp.action is BulkAction.DELETE


def test_bulk_action_gia_tri_bay_bi_tu_choi():
    with pytest.raises(ValidationError):
        BulkActionInput(email_ids=["id1"], action="obliterate_everything")


def test_bulk_action_qua_100_thu_bi_chan():
    """Hàng rào công bố: tối đa 100 thư/lần — chặn LLM 'hứng chí' xoá cả hộp thư."""
    with pytest.raises(ValidationError):
        BulkActionInput(email_ids=[f"id{i}" for i in range(101)], action="mark_read")


# ── Gián điệp registry: soi tool THẬT có bị gọi hay không ────────────────────
class SpyRegistry:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    async def call(self, name, args, ctx):
        self.calls.append((name, args))
        class R:  # giả ToolResult tối thiểu
            @staticmethod
            def model_dump():
                return {"success": True, "message": "spy-ok"}
        return R()


@pytest.fixture()
def spy(monkeypatch):
    s = SpyRegistry()
    monkeypatch.setattr(mcp_server, "tool_registry", s)
    monkeypatch.setattr(mcp_server, "_resolve_ctx",
                        lambda: RequestContext(user_id="qa", access_token="tok"))
    return s


# ── UC010 confirm-gate: KHÔNG HOÀN TÁC → lần đầu chỉ trả preview, KHÔNG thực thi ──
def test_send_email_lan_dau_khong_gui(spy):
    out = asyncio.run(mcp_server.send_email(to=["a@b.c"], subject="S", body="B" * 500))
    assert out.get("needs_confirmation") is True, "Thiếu confirm-gate cho send_email (UC010)!"
    assert spy.calls == [], "CHƯA xác nhận mà email ĐÃ bị gửi — vi phạm human-in-the-loop!"
    assert "body_preview" in out["preview"] and len(out["preview"]["body_preview"]) <= 310


def test_send_email_confirm_true_moi_gui_that(spy):
    out = asyncio.run(mcp_server.send_email(to=["a@b.c"], subject="S", body="B", confirm=True))
    assert out.get("success") is True
    assert [c[0] for c in spy.calls] == ["send_email"], "confirm=true phải thực thi đúng 1 lần"


def test_reply_email_confirm_gate(spy):
    out = asyncio.run(mcp_server.reply_email(email_id="e1", reply_body="Nội dung"))
    assert out.get("needs_confirmation") is True and spy.calls == []
    out2 = asyncio.run(mcp_server.reply_email(email_id="e1", reply_body="Nội dung", confirm=True))
    assert out2.get("success") is True and [c[0] for c in spy.calls] == ["reply_email"]


def test_bulk_delete_confirm_gate_nhung_mark_read_thi_khong(spy):
    """delete (mất dữ liệu) phải qua cổng duyệt; mark_read (đảo được) đi thẳng —
    duyệt đúng chỗ, không làm phiền người dùng vô lý."""
    out = asyncio.run(mcp_server.bulk_action(email_ids=["e1", "e2"], action="Delete"))
    assert out.get("needs_confirmation") is True and spy.calls == [], \
        "bulk delete chưa xác nhận mà đã chạy!"
    out2 = asyncio.run(mcp_server.bulk_action(email_ids=["e1"], action="mark_read"))
    assert out2.get("success") is True and [c[0] for c in spy.calls] == ["bulk_action"]


def test_apply_labels_dao_duoc_khong_can_confirm(spy):
    out = asyncio.run(mcp_server.apply_labels(email_ids=["e1"], labels_to_add=["Work"]))
    assert out.get("success") is True and [c[0] for c in spy.calls] == ["apply_labels"]


# ── Lỗi tool → phong bì JSON (agent ngoài đọc được), không nổ exception giao thức ──
def test_loi_tool_tra_phong_bi_json(monkeypatch):
    class BoomRegistry:
        async def call(self, name, args, ctx):
            raise RuntimeError("Gmail 403: thiếu quyền")
    monkeypatch.setattr(mcp_server, "tool_registry", BoomRegistry())
    monkeypatch.setattr(mcp_server, "_resolve_ctx",
                        lambda: RequestContext(user_id="qa", access_token="tok"))
    out = asyncio.run(mcp_server.get_email(email_id="x"))
    assert out.get("success") is False and "403" in out.get("error", "")
    assert "hint" in out, "Thiếu hint hướng dẫn agent xử lý lỗi"


# ── Tiêu chí thầy: phơi ĐÚNG bộ tool hạt mịn + kỹ năng prompt ───────────────
def test_mcp_phoi_du_tool_hat_min_va_khong_co_tool_to():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = set(tools.keys() if isinstance(tools, dict) else [t.name for t in tools])
    required = {"search_emails", "semantic_search", "categorize_emails", "get_email", "list_labels",
                "send_email", "reply_email", "apply_labels", "bulk_action"}
    assert required <= names, f"Thiếu tool hạt mịn: {required - names}"
    # Q&A thầy: tool "to" gộp suy luận (summarize/process/auto) là rớt xuống 9đ
    coarse = {n for n in names if any(k in n.lower() for k in ("summarize", "process", "auto_"))}
    assert not coarse, f"Phát hiện tool 'to' gộp suy luận vào app: {coarse}"


def test_mcp_co_3_ky_nang_prompt():
    prompts = asyncio.run(mcp_server.mcp.list_prompts())
    names = set(prompts.keys() if isinstance(prompts, dict) else [p.name for p in prompts])
    assert {"daily_digest", "triage_inbox", "meeting_brief"} <= names, \
        f"Thiếu kỹ năng prompt cho Claude Desktop: {names}"


# ── KÊNH MCP PHẢI PHƠI CẢ PHẦN LÀM NÊN MeoArc ───────────────────────────────

def test_kenh_MCP_co_du_tool_lich_trinh_va_di_lai():
    """Tiêu chí agent-native: agent NGOÀI phải làm được thứ app làm.

    Chín tool hộp thư thì agent nào nối vào Gmail cũng có. Bốn tool dưới mới là thứ
    MeoArc có mà Gmail không có — đọc cam kết, đo áp lực, gợi ý đi lại, tra chuyến bay.
    Mở kênh mà giữ lại phần hay nhất cho riêng mình thì kênh đó chưa hoàn chỉnh."""
    from app.mcp import server
    for ten in ("liet_ke_cam_ket", "ap_luc_lich_trinh", "de_xuat_di_lai",
                "tim_chuyen_bay", "tim_khach_san"):
        assert hasattr(server, ten), f"kênh MCP thiếu {ten}"


def test_tool_KHONG_HOAN_TAC_khong_duoc_phoi_qua_MCP():
    """`dat_cho_mo_phong` phải đi qua cổng xác nhận + cổng tiền, mà cổng đó gắn với
    phiên người dùng trên web. Phơi qua stdio là mở đường vòng qua chính lớp bảo vệ."""
    from app.mcp import server
    assert not hasattr(server, "dat_cho_mo_phong")


def test_MCP_mo_du_BA_nguyen_the_cua_giao_thuc():
    """Tools + prompts + resources. Chỉ có tool thì mới là "API có mô tả"; đủ ba mới
    là một máy chủ MCP hoàn chỉnh mà Claude Desktop dùng được ngay."""
    import inspect
    from app.mcp import server
    src = inspect.getsource(server)
    assert "@mcp.prompt()" in src and "@mcp.resource(" in src
    assert src.count("@mcp.prompt()") >= 3, "cần đủ bộ kỹ năng 1-click"


# ══════════════════════════════════════════════════════════════════════════════
# MÀN "MCP" PHẢI NÓI ĐÚNG NHỮNG GÌ SERVER THẬT SỰ MỞ RA
#
# Màn Cài đặt → MCP trước đây ghi cứng bảy tên tool, trong đó BỐN cái không tồn tại
# (`summarize`, `draft_reply`, `bulk_manage`, `extract_tasks`), một endpoint không có
# thật (`https://mcp.meoarc.dev/sse`), và dòng "đã kết nối · 1 client đang hoạt động"
# luôn hiện bất kể có ai kết nối hay không.
#
# Với một màn trang trí thì đó là chuyện nhỏ. Nhưng đây đúng là màn được mở ra để
# CHỨNG MINH tích hợp MCP — người xem chỉ cần gõ thử một tên tool là thấy. Sai ở đây
# không phải thiếu sót, nó là một lời khẳng định sai về thứ hệ thống làm được.
#
# Test này khoá đúng ranh giới đó: danh sách trên endpoint phải TRÙNG KHỚP tập tool
# đã đăng ký thật, không thừa không thiếu.
# ══════════════════════════════════════════════════════════════════════════════

def test_khai_bao_mcp_khop_dung_tool_da_dang_ky():
    from fastapi.testclient import TestClient
    from app.api.app import app
    from app.mcp import server as S

    d = TestClient(app).get("/mcp/thong-tin").json()
    assert d["san_sang"] is True

    that = {f.__name__ for f in (
        S.search_emails, S.semantic_search, S.categorize_emails, S.get_email,
        S.list_labels, S.send_email, S.reply_email, S.apply_labels, S.bulk_action,
        S.liet_ke_cam_ket, S.ap_luc_lich_trinh, S.de_xuat_di_lai,
        S.tim_chuyen_bay, S.tim_khach_san,
    )}
    assert set(d["tools"]) == that, f"lệch: {set(d['tools']) ^ that}"


def test_khong_hua_mot_endpoint_HTTP_khong_ton_tai():
    """Transport là stdio. Vẽ ra một URL cho gọn màn hình là hứa thứ không có — và bật
    transport từ xa khi chưa có xác thực thì ai có đường dẫn cũng đọc và gửi được thư."""
    from fastapi.testclient import TestClient
    from app.api.app import app
    d = TestClient(app).get("/mcp/thong-tin").json()
    assert d["transport"] == "stdio"
    assert not any(str(v).startswith("http") for v in d.values() if isinstance(v, str))


def test_noi_ro_hai_tool_CO_Y_khong_mo():
    """Người xem phải phân biệt được 'đã cân nhắc rồi không mở' với 'quên mất'."""
    from fastapi.testclient import TestClient
    from app.api.app import app
    d = TestClient(app).get("/mcp/thong-tin").json()
    assert set(d["khong_mo"]) == {"dat_cho_mo_phong", "tu_choi_ngoai_pham_vi"}
    assert all(name not in d["tools"] for name in d["khong_mo"])
