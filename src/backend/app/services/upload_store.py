# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/upload_store.py — KHO tệp đính kèm TẠM (Nấc 8)        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: giữ NỘI DUNG (bytes) của tệp người dùng upload, để khi    ║
# ║ bấm Gửi thì lấy ra đính vào email.                                 ║
# ║ VÌ SAO TÁCH RA FILE RIÊNG: cả route /uploads (lúc nhận tệp) lẫn      ║
# ║ route /emails/send (lúc gửi) đều cần chạm kho này → đặt 1 chỗ dùng  ║
# ║ chung, tránh để biến toàn cục rải rác trong app.py.                ║
# ║ ⚠️ HỌC/sandbox: lưu trong RAM (dict). Tắt server là MẤT. Dự án thật  ║
# ║ phải lưu xuống đĩa hoặc cloud (S3...) + dọn tệp cũ theo thời gian.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import secrets

# id tệp → thông tin tệp. content là BYTES thật (khác trước: trước chỉ giữ metadata).
_UPLOADS: dict[str, dict] = {}


def _human_size(num: int) -> str:
    """Đổi số byte sang chuỗi dễ đọc cho FE hiển thị (vd 248 KB)."""
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num // 1024} KB"
    return f"{num / 1024 / 1024:.1f} MB"


def save(filename: str, content: bytes, mime: str | None) -> dict:
    """Cất 1 tệp, trả về {id, name, size} cho FE giữ lại (id để sau gắn vào email)."""
    fid = secrets.token_hex(8)                       # id ngẫu nhiên, khó đoán
    _UPLOADS[fid] = {"name": filename, "content": content, "mime": mime}
    return {"id": fid, "name": filename, "size": _human_size(len(content))}


def get(fid: str) -> dict | None:
    """Lấy lại 1 tệp theo id (None nếu không có / đã bị dọn)."""
    return _UPLOADS.get(fid)
