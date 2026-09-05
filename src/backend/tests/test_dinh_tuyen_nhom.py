"""Nhóm theo TÍNH CHẤT và nhóm theo NGƯỜI GỬI phải đi hai đường khác nhau.

Đo được ở bộ 26 prompt: câu "đánh dấu đã đọc tất cả thư từ noreply" ra thẻ `categorize`
thay vì thao tác hàng loạt. Nguyên nhân không phải mô hình dở mà là luật trong system
prompt gộp hai loại nhóm làm một: nó bảo "thao tác trên cả nhóm thì gọi
`categorize_emails` rồi mới `bulk_action`", kèm ba ví dụ đều là nhóm theo tính chất
(thư Cá nhân / quảng cáo / bản tin). Nhóm theo người gửi thì `search_emails` đã trả
đúng danh sách, phân loại thêm chỉ tốn một lượt mô hình và dễ làm lạc việc.

Test này không kiểm câu chữ, chỉ chốt rằng luật CÒN PHÂN BIỆT hai loại nhóm — gộp lại
lần nữa là lỗi cũ quay về, mà lỗi đó chỉ lộ ra khi chạy mô hình thật (tốn quota).
"""

from __future__ import annotations

from app.agent.nodes.agent_node import _SYSTEM_BASE


def test_luat_nhom_phan_biet_TINH_CHAT_voi_NGUOI_GUI():
    assert "categorize_emails" in _SYSTEM_BASE
    assert "search_emails" in _SYSTEM_BASE
    # Nhóm theo người gửi/từ khoá phải được nêu ĐÍCH DANH kèm cú pháp Gmail,
    # nếu không mô hình lại rơi về nhánh phân loại như cũ.
    assert "from:" in _SYSTEM_BASE, "phải chỉ rõ cú pháp lọc theo người gửi"
    assert "noreply" in _SYSTEM_BASE, "giữ đúng ví dụ đã từng chạy sai làm mốc"


def test_co_cam_RO_RANG_viec_phan_loai_cho_nhom_theo_nguoi_gui():
    """Chỉ nêu ví dụ là chưa đủ — bản trước cũng có ví dụ mà mô hình vẫn chọn nhầm."""
    doan = _SYSTEM_BASE[_SYSTEM_BASE.index("THAO TÁC TRÊN CẢ MỘT NHÓM"):]
    doan = doan[: doan.index("\n\n")] if "\n\n" in doan else doan
    assert "KHÔNG gọi" in doan or "KHÔNG dùng" in doan, (
        "cần một câu cấm thẳng, không chỉ gợi ý"
    )
