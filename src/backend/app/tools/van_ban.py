"""Dọn chữ do MÔ HÌNH viết ra, trước khi nó thành thứ người khác đọc.

Đặt ở tầng `tools` chứ không ở `services`: `services` phục vụ cả chữ người dùng tự
gõ, mà chữ người dùng gõ thì phải đi nguyên xi.
"""

from __future__ import annotations

import re

# Chuỗi thoát xuống dòng ở dạng CHỮ: `\n`, `\r\n`, và bản bị escape hai lượt `\\n`.
# Bắt cả cụm `\r\n` trước để không để lại một `\r` mồ côi.
_THOAT = re.compile(r"\\{1,2}r?\\{0,2}n")


def go_chuoi_thoat(gia_tri):
    """Đổi chuỗi thoát xuống dòng dạng CHỮ thành ký tự xuống dòng thật.

    CHỈ làm khi cả chuỗi KHÔNG có lấy một dấu xuống dòng thật nào — đó là dấu vân
    tay của lỗi: mô hình dùng chuỗi thoát THAY CHO xuống dòng nên không thể có cả
    hai. Còn khi đã có xuống dòng thật thì mọi `\\n` còn lại nhiều khả năng là chữ
    người ta cố ý viết (một đường dẫn Windows chẳng hạn), và tự ý đổi nó là bịa lại
    nội dung thư — cái giá đắt hơn hẳn.

    Nhận kiểu gì cũng không ném lỗi: nó chạy ở `mode="before"` của Pydantic, nên
    kiểu sai phải để chính Pydantic báo bằng thông điệp của nó, không phải bằng một
    traceback từ đây.
    """
    if not isinstance(gia_tri, str) or "\n" in gia_tri:
        return gia_tri
    return _THOAT.sub("\n", gia_tri)
