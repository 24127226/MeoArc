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
import time

# id tệp → thông tin tệp. content là BYTES thật (khác trước: trước chỉ giữ metadata).
_UPLOADS: dict[str, dict] = {}

# ── NFR-Memory: kho RAM phải CÓ TRẦN, không thì rò rỉ tới OOM ────────────────
# Trước đây tệp nằm trong RAM VĨNH VIỄN (không ai dọn) → upload nhiều là phình mãi.
# Luật dọn: (1) tệp quá 30 phút không dùng → bỏ (người dùng đã gửi/огừng soạn từ lâu);
# (2) tổng dung lượng vượt 25MB → bỏ tệp CŨ NHẤT trước (FIFO) cho tới khi đủ chỗ.
_TTL_SECONDS = 30 * 60
_MAX_TOTAL_BYTES = 25 * 1024 * 1024


def _prune(incoming: int = 0) -> None:
    """Dọn kho: hết hạn trước, rồi FIFO nếu vẫn chật (chừa chỗ cho tệp sắp vào)."""
    now = time.time()
    for fid in [k for k, v in _UPLOADS.items() if now - v["ts"] > _TTL_SECONDS]:
        _UPLOADS.pop(fid, None)
    total = sum(len(v["content"]) for v in _UPLOADS.values()) + incoming
    while total > _MAX_TOTAL_BYTES and _UPLOADS:
        oldest = min(_UPLOADS, key=lambda k: _UPLOADS[k]["ts"])
        total -= len(_UPLOADS[oldest]["content"])
        _UPLOADS.pop(oldest, None)


def _human_size(num: int) -> str:
    """Đổi số byte sang chuỗi dễ đọc cho FE hiển thị (vd 248 KB)."""
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num // 1024} KB"
    return f"{num / 1024 / 1024:.1f} MB"


def save(filename: str, content: bytes, mime: str | None) -> dict:
    """Cất 1 tệp, trả về {id, name, size} cho FE giữ lại (id để sau gắn vào email)."""
    _prune(incoming=len(content))                    # dọn trước khi cất (giữ trần RAM)
    fid = secrets.token_hex(8)                       # id ngẫu nhiên, khó đoán
    _UPLOADS[fid] = {"name": filename, "content": content, "mime": mime, "ts": time.time()}
    return {"id": fid, "name": filename, "size": _human_size(len(content))}


def get(fid: str) -> dict | None:
    """Lấy lại 1 tệp theo id (None nếu không có / đã bị dọn quá hạn)."""
    item = _UPLOADS.get(fid)
    if item and time.time() - item["ts"] > _TTL_SECONDS:
        _UPLOADS.pop(fid, None)
        return None
    return item
