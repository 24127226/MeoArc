"""Bảng tổng kết cho các bộ chạy prompt. THUẦN — không tác dụng phụ khi import.

── VÌ SAO Ở FILE RIÊNG ──
Hàm này nằm trong `thu_prompt_demo.py`, mà file đó bọc lại `sys.stdout` ngay lúc
import (cần thiết để in tiếng Việt trên console Windows). Test import nó vào là pytest
mất luồng ghi đã bắt, và 471 test đổ theo với "I/O operation on closed file" — không
test nào trong số đó có lỗi gì cả.

Thứ đáng test là PHÉP ĐẾM, không phải phần dựng cảnh. Tách ra thì test import được mà
không kéo theo gì, và cả hai bộ chạy dùng CHUNG một bảng đếm — hai bản đếm khác nhau
cho cùng một thứ là cách chắc chắn để hai con số dần lệch nhau mà không ai biết.
"""

from __future__ import annotations


def tom_ket(ket: list[tuple[int, str]]) -> str:
    """Tách bạch BỐN trạng thái, vì gộp lại là nói dối theo cả hai chiều.

    Gộp 'loi' vào ĐẠT → báo xanh giả. Đã xảy ra thật ngày 05/09: hạn mức cạn từ trước
      câu đầu tiên, 24/26 câu mô hình không đáp nổi một chữ, mà bảng in ra "9 đạt" —
      bảy trong số đó là câu tự-chấm đã BÁO LỖI. Con số đó suýt được mang đi trình bày.
    Gộp 'loi' vào SAI → tự vu cho mình, và người đọc không biết nên đi sửa code hay chỉ
      cần đợi hạn mức hồi.
    """
    def lay(t: str) -> list[int]:
        return [so for so, x in ket if x == t]

    dat, lech, loi, tu = lay("dat"), lay("lech"), lay("loi"), lay("tu_cham")

    def ten(ds: list[int]) -> str:
        return "  -> " + ", ".join(f"Q{s}" for s in ds) if ds else ""

    dong = [
        f"Da chay {len(ket)} cau",
        f"  DAT (dung the)      : {len(dat):>3}",
        f"  LECH THE (loi ta)   : {len(lech):>3}{ten(lech)}",
        f"  TU CHAM (doc tay)   : {len(tu):>3}{ten(tu)}",
        f"  KHONG CHAY DUOC     : {len(loi):>3}{ten(loi)}",
    ]
    if loi:
        dong += [
            "",
            "  Nhom cuoi la han muc / su co phia nha cung cap, KHONG phai loi phan",
            "  mem. Chay lai dung nhung cau do khi han muc hoi roi moi ket luan.",
        ]
    return "\n".join(dong)
