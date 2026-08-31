"""Chặn 02 — hai công cụ lịch trình cho agent.

── VÌ SAO CHÚNG TỒN TẠI ──
Bộ trích cam kết vốn CHỈ chạy trong trình duyệt, nên agent hoàn toàn mù trước lịch
trình. Đo thật 29/08/2026: hỏi "tuần sau mình có deadline nào nặng nhất?" → agent gọi
`search_emails` một lần rồi trả lời "Tuần sau bạn không có deadline nào" — nó không có
cách nào biết được, và grep cả `app/tools/` ra 0 công cụ liên quan cam kết.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.tools import email_tools as T
from app.tools.registry import tool_registry, ToolCategory, RequestContext
from app.tools.schemas import LietKeCamKetInput, ApLucLichTrinhInput
from app.schemas.email import Email

CTX = RequestContext(user_id="1", access_token="x", email_provider="gmail")


def _thu(i: int, subject: str, body: str, priority: str | None = None) -> Email:
    return Email(
        id=str(i), sender="Giáo vụ HCMUS", senderEmail="gv@hcmus.edu.vn",
        senderInitial="G", to="me", subject=subject, preview=body[:40],
        body=[body], time="08:00", date="01/09/2026 08:00",
        unread=True, starred=False, category="moss", priority=priority,
    )


@pytest.fixture
def hop_thu(monkeypatch):
    """Thay Gmail bằng hộp thư giả — test không được phụ thuộc mạng hay hạn ngạch."""
    def dat(ds):
        monkeypatch.setattr(T.mail, "list_messages", lambda *a, **kw: (ds, None))
    return dat


def _ngay(n: int) -> str:
    d = datetime.now() + timedelta(days=n)
    return f"{d.day}/{d.month}"


# ── Đăng ký ──────────────────────────────────────────────────────────────────

def test_hai_tool_da_dang_ky_va_la_READ():
    """READ nghĩa là KHÔNG cần xác nhận. Xem lịch mà phải bấm duyệt thì cổng xác nhận
    mất thiêng — nó phải để dành cho việc không hoàn tác được."""
    for ten in ("liet_ke_cam_ket", "ap_luc_lich_trinh"):
        assert ten in tool_registry.list_tools()
        s = tool_registry.get_spec(ten)
        assert s.category is ToolCategory.READ
        assert s.requires_confirmation is False


# ── liet_ke_cam_ket ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_liet_ke_tra_ve_han_va_nguoi_cho(hop_thu):
    hop_thu([_thu(1, "Nhắc nộp báo cáo",
                  f"Các nhóm nộp báo cáo trước 23:59 ngày {_ngay(5)}.", "High")])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(), CTX)
    assert ra.success and len(ra.data) == 1
    assert ra.data[0].han is not None
    assert ra.data[0].nguoi_cho == "Giáo vụ HCMUS"
    assert ra.data[0].email_id == "1"


@pytest.mark.asyncio
async def test_loc_bo_thu_KHONG_phai_cam_ket(hop_thu):
    """Thư có ngày tháng nhưng không có nghĩa vụ phải bị bỏ. Nhồi rác vào danh sách
    việc thì người dùng thôi mở nó, và lúc đó nó vô dụng hoàn toàn."""
    hop_thu([
        _thu(1, "Nhắc nộp báo cáo", f"Nộp báo cáo trước 23:59 ngày {_ngay(3)}.", "High"),
        _thu(2, "Sale 9.9", "Đừng bỏ lỡ ngày hội mua sắm 9/9 giảm 50%."),
        _thu(3, "Sinh nhật 15/9", "Hẹn gặp lại mọi người ngày 15/9 nha."),
    ])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(), CTX)
    assert len(ra.data) == 1, [d.noi_dung for d in ra.data]


@pytest.mark.asyncio
async def test_xep_viec_GAP_len_dau(hop_thu):
    """Trả về theo thứ tự ưu tiên. Agent thường chỉ đọc vài mục đầu, nên thứ tự ở đây
    quyết định câu trả lời — trả lộn xộn thì 'việc nào gấp nhất' ra sai."""
    hop_thu([
        _thu(1, "Việc xa", f"Nộp bản mô tả trước 23:59 ngày {_ngay(12)}.", "Low"),
        _thu(2, "Việc gấp", f"Nộp gấp báo cáo trước 23:59 ngày {_ngay(1)}.", "High"),
    ])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(), CTX)
    assert ra.data[0].muc_uu_tien >= ra.data[-1].muc_uu_tien
    assert "gấp" in ra.data[0].noi_dung.lower()


@pytest.mark.asyncio
async def test_cat_viec_NGOAI_cua_so_ngay(hop_thu):
    hop_thu([_thu(1, "Việc rất xa", f"Nộp báo cáo trước 23:59 ngày {_ngay(40)}.", "High")])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(so_ngay_toi=14), CTX)
    assert len(ra.data) == 0
    rong = await T.liet_ke_cam_ket(LietKeCamKetInput(so_ngay_toi=60), CTX)
    assert len(rong.data) == 1


@pytest.mark.asyncio
async def test_GIU_viec_khong_co_han(hop_thu):
    """Thư đã gửi = đang chờ hồi âm, không có hạn. Lọc theo hạn thì nó rụng đầu tiên —
    mà đó lại là loại việc hay bị quên nhất."""
    e = _thu(1, "Hỏi về học phí", "Em xin hỏi về học phí ạ.")
    e.folder = "sent"
    hop_thu([e])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(), CTX)
    assert len(ra.data) == 1
    assert ra.data[0].han is None


@pytest.mark.asyncio
async def test_bao_ro_han_la_SUY_RA(hop_thu):
    """`han_suy_ra` phải tới được agent, nếu không nó khẳng định chắc nịch một phỏng
    đoán — cách nhanh nhất làm người dùng mất tin vào cả tính năng."""
    hop_thu([_thu(1, "Chia việc", "Bạn gửi lại đặc tả tool trước thứ Năm nhé.", "Medium")])
    ra = await T.liet_ke_cam_ket(LietKeCamKetInput(), CTX)
    assert len(ra.data) == 1
    assert ra.data[0].han_suy_ra is True


# ── ap_luc_lich_trinh ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ap_luc_tra_du_so_ngay(hop_thu):
    hop_thu([_thu(1, "Nộp báo cáo", f"Nộp báo cáo trước 23:59 ngày {_ngay(2)}.", "High")])
    ra = await T.ap_luc_lich_trinh(ApLucLichTrinhInput(so_ngay=7), CTX)
    assert len(ra.data) == 7
    assert all({"ngay", "phut", "so_viec", "qua_tai"} <= set(x) for x in ra.data)


@pytest.mark.asyncio
async def test_hop_thu_rong_KHONG_no(hop_thu):
    hop_thu([])
    ra = await T.ap_luc_lich_trinh(ApLucLichTrinhInput(), CTX)
    assert ra.success and all(x["so_viec"] == 0 for x in ra.data)


# ── Prompt đã dạy agent dùng ─────────────────────────────────────────────────

def test_prompt_day_dung_tool_lich_trinh():
    """Có tool mà prompt không nhắc thì agent vẫn quay về `search_emails` — đúng hành
    vi đã đo được trước khi có hai tool này."""
    from app.agent.nodes import agent_node
    p = agent_node._SYSTEM_BASE
    assert "liet_ke_cam_ket" in p
    assert "ap_luc_lich_trinh" in p
    assert "han_suy_ra" in p
