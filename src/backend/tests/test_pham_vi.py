"""Chặn 01 — RANH GIỚI NĂNG LỰC: agent phải biết việc gì nó KHÔNG làm được.

── LỖI ĐÃ ĐO ĐƯỢC (29/08/2026, Gemini thật + Gmail thật) ──
Hỏi "Đặt vé máy bay đi Đà Nẵng ngày 12/9 giúp mình" → agent gọi `search_emails` rồi
trả lời "Không tìm thấy thư nào liên quan đến việc đặt vé máy bay".

Người dùng đọc câu đó sẽ hiểu là HỘP THƯ TRỐNG, chứ không hiểu là MEOARC KHÔNG ĐẶT
VÉ ĐƯỢC. Với một agent sắp được nối vào việc tiêu tiền, đây là tính chất nguy hiểm
nhất: một yêu cầu ngoài tầm bị âm thầm diễn giải thành việc khác rồi báo thành công.

── VÌ SAO TEST OFFLINE ──
Gemini free tier chỉ cho 20 lượt/ngày với gemini-2.5-flash-lite (đã chạm trần khi đo).
Một bộ test phụ thuộc quota là bộ test không ai chạy. Ở đây kiểm phần MeoArc kiểm soát
được — tool có tồn tại, có đúng loại, prompt có nói rõ ranh giới — bằng kịch bản
deterministic. Phần "mô hình có nghe lời không" thì đo riêng bằng kịch bản LLM thật.
"""

from __future__ import annotations

import pytest

from app.tools import email_tools  # noqa: F401  — nạp để decorator register chạy
from app.tools.registry import tool_registry, ToolCategory
from app.agent.nodes import agent_node


TEN = "tu_choi_ngoai_pham_vi"


# ── Công cụ phải TỒN TẠI và đúng loại ────────────────────────────────────────

def test_co_cong_cu_tu_choi():
    """Làm thành TOOL chứ không phải một dòng cấm trong prompt là CÓ CHỦ Ý: mô hình
    bám theo danh sách tool chặt hơn hẳn bám theo lời cấm. Cấm suông thì nó vẫn phải
    chọn MỘT hành động, và hành động sẵn có gần nhất lại đúng là `search_emails`."""
    assert TEN in tool_registry.list_tools(), "thiếu tool tu_choi_ngoai_pham_vi trong registry"


def test_tu_choi_KHONG_can_xac_nhan():
    """Từ chối là việc vô hại. Bắt người dùng bấm duyệt một lời từ chối thì cổng xác
    nhận mất thiêng — mà cổng đó sắp phải gác việc tiêu tiền thật."""
    s = tool_registry.get_spec(TEN)
    assert s.category is ToolCategory.SYSTEM
    assert s.requires_confirmation is False


# ── Prompt phải NÓI RÕ ranh giới, và nói TRƯỚC luật "luôn phải search" ───────

def test_prompt_liet_ke_viec_KHONG_lam_duoc():
    p = agent_node._SYSTEM_BASE
    for viec in ("gọi được xe", "thanh toán hoá đơn", "mua hàng", "Calendar"):
        assert viec in p, f"prompt chưa nói rõ là không làm được: {viec}"


def test_prompt_PHAN_BIET_tra_cuu_voi_dat_cho():
    """Ranh giới đã DỊCH sau Giai đoạn 2: agent TRA CỨU được chuyến bay nhưng vẫn KHÔNG
    đặt được. Đây là chỗ dễ hỏng theo cả hai chiều — nói không được gì cả thì hai tool
    tra cứu thành vô dụng, còn nói làm được hết thì nó hứa đặt vé mà không đặt nổi.

    Ranh giới thật nằm ở chỗ TIÊU TIỀN, và prompt phải nói đúng chữ đó."""
    p = agent_node._SYSTEM_BASE
    assert "tim_chuyen_bay" in p, "prompt phải cho phép TRA CỨU"
    assert "TIÊU TIỀN" in p, "prompt phải nêu ranh giới thật nằm ở đâu"
    # Vẫn phải từ chối việc ĐẶT
    i_dat = p.index("'ĐẶT vé'")
    assert "tu_choi_ngoai_pham_vi" in p[i_dat:i_dat + 400]


def test_prompt_canh_bao_gia_MO_PHONG():
    """Số mô phỏng lọt ra ngoài dưới dạng giá thật là chỗ hỏng nặng nhất của Giai đoạn 2:
    người dùng ra quyết định tiền bạc dựa trên con số không tồn tại."""
    p = agent_node._SYSTEM_BASE
    assert "mo_phong" in p and "không đưa ra như giá thật" in p


def test_phan_pham_vi_dung_TRUOC_luat_luon_search():
    """THỨ TỰ QUAN TRỌNG. Luật "bất kỳ yêu cầu nào về hộp thư đều phải search trước"
    chính là thứ đẩy agent đi tìm thư về vé máy bay. Khối Phạm Vi phải nằm TRƯỚC nó
    thì mô hình mới lọc ra yêu cầu ngoài tầm trước khi rơi vào luật đó."""
    p = agent_node._SYSTEM_BASE
    assert p.index("## PHẠM VI") < p.index("Nguyên tắc CHÍNH XÁC")


def test_prompt_cam_bien_yeu_cau_hanh_dong_thanh_tim_thu():
    """Đây là câu chặn đúng lỗi đã đo, viết bằng chính ví dụ đã gây ra lỗi — người
    sửa prompt sau này đọc tới đây sẽ biết vì sao dòng đó tồn tại."""
    p = agent_node._SYSTEM_BASE
    assert "KHÔNG PHẢI là 'tìm thư về vé máy bay" in p


# ── Bản thân công cụ chạy đúng ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tra_ve_ly_do_va_viec_thay_the():
    from app.tools.schemas import NgoaiPhamViInput
    from app.agent.state import RequestContext

    ra = await email_tools.tu_choi_ngoai_pham_vi(
        NgoaiPhamViInput(
            viec_nguoi_dung_muon="đặt vé máy bay đi Đà Nẵng ngày 12/9",
            vi_sao_khong_lam_duoc="MeoArc chưa kết nối với hệ thống bán vé nào",
            viec_gan_nhat_lam_duoc="tìm trong hộp thư các thư xác nhận vé đã đặt",
        ),
        RequestContext(user_id="1", access_token="x", email_provider="gmail"),
    )
    assert ra.success is True
    assert ra.data["viec"].startswith("đặt vé")
    assert "chưa kết nối" in ra.data["ly_do"]
    assert ra.data["thay_the"] is not None


@pytest.mark.asyncio
async def test_khong_bia_viec_thay_the():
    """`viec_gan_nhat_lam_duoc` để trống được. Ép luôn phải có thì mô hình sẽ bịa ra
    một việc thay thế vô nghĩa, và một gợi ý vô nghĩa còn tệ hơn không gợi ý."""
    from app.tools.schemas import NgoaiPhamViInput
    from app.agent.state import RequestContext

    ra = await email_tools.tu_choi_ngoai_pham_vi(
        NgoaiPhamViInput(
            viec_nguoi_dung_muon="in báo cáo ra giấy A4",
            vi_sao_khong_lam_duoc="MeoArc không điều khiển được máy in",
        ),
        RequestContext(user_id="1", access_token="x", email_provider="gmail"),
    )
    assert ra.data["thay_the"] is None


def test_tool_KHONG_cham_mang_hay_hop_thu():
    """Từ chối phải là thao tác thuần cục bộ. Nếu nó lỡ gọi Gmail thì mỗi lời từ chối
    lại đốt một lượt hạn ngạch — mà quota Gemini free chỉ có 20 lượt/ngày."""
    import inspect
    src = inspect.getsource(email_tools.tu_choi_ngoai_pham_vi)
    for cam in ("mail.", "gmail_service", "asyncio.to_thread", "httpx"):
        assert cam not in src, f"tool từ chối không được gọi {cam}"
