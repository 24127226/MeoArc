"""BẢNG TỔNG KẾT BỘ PROMPT KHÔNG ĐƯỢC BÁO XANH GIẢ.

── CHUYỆN ĐÃ XẢY RA ──
Ngày 05/09, ngay trước buổi bảo vệ, bộ chạy 26 câu in ra:

    Đã chạy 26/26 câu · 9 đạt · 17 chưa đạt

Sự thật: hạn mức Gemini đã cạn TỪ TRƯỚC câu đầu tiên. Chỉ Q1 và Q2 lách được qua
chuỗi model dự phòng; 24 câu còn lại mô hình không đáp nổi một chữ. Bảy câu trong số
"9 đạt" là những câu có thẻ mong đợi `*`, và dòng đếm loại hẳn chúng khỏi danh sách
hỏng — nên một câu `*` BÁO LỖI vẫn được cộng vào cột đạt.

Một bản báo xanh giả ngay trước buổi bảo vệ là thứ tệ nhất có thể xảy ra: nó nói
rằng thứ chưa hề chạy đã chạy tốt, và người đọc mang con số đó đi trình bày.

Ranh giới cần khoá: KHÔNG GỌI ĐƯỢC MÔ HÌNH là một trạng thái RIÊNG — không phải đạt
(chưa chứng minh gì), cũng không phải sai (không phải lỗi phần mềm).
"""

from __future__ import annotations

import re

from scripts.tom_ket import tom_ket


def _so(bang: str, nhan: str) -> int:
    # Nhãn có phần chú trong ngoặc trước dấu hai chấm: "LECH THE (loi ta)   :   0".
    m = re.search(nhan + r"[^:\n]*:\s*(\d+)", bang)
    assert m, f"không thấy dòng {nhan!r} trong:\n{bang}"
    return int(m.group(1))


def test_ca_bo_LOI_thi_KHONG_co_cau_nao_dat():
    """Chính ca đã lừa được người đọc."""
    bang = tom_ket([(i, "loi") for i in range(1, 27)])
    assert _so(bang, "DAT") == 0
    assert _so(bang, "KHONG CHAY DUOC") == 26


def test_cau_TU_CHAM_bi_loi_KHONG_duoc_tinh_la_dat():
    """Đúng bảy câu đã bị cộng nhầm hôm 05/09 (Q15, Q16, Q21–Q25)."""
    bang = tom_ket([(15, "loi"), (16, "loi"), (21, "loi")])
    assert _so(bang, "DAT") == 0
    assert _so(bang, "TU CHAM") == 0
    assert _so(bang, "KHONG CHAY DUOC") == 3


def test_LOI_khong_bi_gop_vao_SAI():
    """Chiều ngược lại cũng phải đúng: gộp lỗi hạ tầng vào 'sai' là tự vu cho mình,
    và người đọc không biết nên đi sửa code hay chỉ cần đợi hạn mức hồi."""
    bang = tom_ket([(1, "loi"), (2, "loi")])
    assert _so(bang, "LECH THE") == 0


def test_dem_dung_khi_du_ca_bon_trang_thai():
    bang = tom_ket([(1, "dat"), (2, "dat"), (3, "lech"),
                    (4, "tu_cham"), (5, "loi"), (6, "loi")])
    assert _so(bang, "DAT") == 2
    assert _so(bang, "LECH THE") == 1
    assert _so(bang, "TU CHAM") == 1
    assert _so(bang, "KHONG CHAY DUOC") == 2
    assert "Q3" in bang and "Q5" in bang and "Q6" in bang


def test_co_loi_thi_bang_PHAI_noi_ro_do_khong_phai_loi_phan_mem():
    """Con số thôi chưa đủ — người đọc phải biết nên làm gì tiếp."""
    bang = tom_ket([(1, "loi")])
    assert "han muc" in bang.lower()


def test_khong_co_loi_thi_khong_in_loi_giai_thich_thua():
    bang = tom_ket([(1, "dat")])
    assert "han muc" not in bang.lower()
