"""Dọn văn bản do MÔ HÌNH sinh ra trước khi nó thành thứ người dùng đọc hoặc gửi đi.

── VẤN ĐỀ ĐO ĐƯỢC ──
Bản nháp thư hiện ra một dòng dài, giữa các đoạn là hai ký tự `\\` và `n` chứ không
phải xuống dòng thật. Giao diện không sai: khối nháp đã có `whitespace-pre-line`, nên
xuống dòng THẬT thì hiện đúng. Sai ở chỗ chuỗi không hề có xuống dòng nào.

Gốc rễ: tham số tool là chuỗi thường, nhưng mô hình đã quen sinh JSON nên nó viết
`\\n` như thể đang viết chuỗi JSON. Chỗ nhận không giải mã lần nữa (và không được
phép giải mã bừa), thế là hai ký tự đó đi thẳng ra màn hình rồi ra hộp thư người nhận.

── VÌ SAO SỬA Ở TẦNG NÀY, KHÔNG SỬA Ở PROMPT ──
Dặn mô hình "đừng viết \\n" là một lời nhắc, không phải một bảo đảm: nó đúng phần lớn
lượt và sai vào đúng lượt xui. Một lá thư gửi đi thì không rút lại được. Nên chỗ chặn
phải là mã, còn prompt chỉ là lớp giảm tần suất.

── QUY TẮC HẸP CÓ CHỦ Ý ──
Chỉ đổi khi chuỗi KHÔNG có xuống dòng thật nào mà LẠI có `\\n`. Đó đúng là dấu vân tay
của lỗi: cả thân thư nằm trên một dòng. Nếu văn bản đã có xuống dòng thật thì `\\n`
còn lại nhiều khả năng là nội dung người ta cố ý viết (trích một đoạn mã chẳng hạn) —
đổi nó là sửa sai thành sai khác, mà lần này người dùng không ngờ tới.
"""

from __future__ import annotations

import re

# Chuỗi thoát viết bằng chữ mà mô hình hay sinh ra. Bỏ qua `\\\\n` (dấu chéo ngược đã
# được thoát) — đó là người ta thật sự muốn nói tới ký tự chéo ngược.
_THOAT = re.compile(r"(?<!\\)\\(n|r\\n|r|t)")

_DOI = {"n": "\n", "r": "\r", "t": "\t", "r\\n": "\r\n"}


def sua_xuong_dong(s: str) -> str:
    """Trả lại chuỗi có xuống dòng thật, nếu chuỗi đang mắc đúng lỗi nói trên.

    Không mắc lỗi thì trả nguyên xi — hàm này phải là phép đồng nhất với mọi văn bản
    bình thường, vì nó nằm trên đường đi của thư sắp gửi.
    """
    if not isinstance(s, str) or not s:
        return s
    if "\n" in s or "\r" in s:
        return s  # đã có xuống dòng thật → không đụng vào
    if "\\n" not in s and "\\r" not in s:
        return s
    return _THOAT.sub(lambda m: _DOI[m.group(1)], s)


# Tham số tool chứa VĂN XUÔI cho người đọc. Cố ý là danh sách hẹp: một truy vấn Gmail
# (`q="from:a\\nb"`) hay một mã thư không bao giờ được đụng tới.
TRUONG_VAN_XUOI = ("body", "instructions")


def don_args(args: dict) -> dict:
    """Dọn các trường văn xuôi trong args tool. Trả về dict MỚI, không sửa tại chỗ."""
    if not isinstance(args, dict):
        return args
    return {
        k: (sua_xuong_dong(v) if k in TRUONG_VAN_XUOI and isinstance(v, str) else v)
        for k, v in args.items()
    }
