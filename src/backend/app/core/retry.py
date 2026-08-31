# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/retry.py — TỰ THỬ LẠI khi gọi API chớp nhoáng (NFR)      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Gmail API đôi lúc trả 429 (quá nhiều lượt/phút) hoặc 5xx/timeout   ║
# ║ mạng — những lỗi này thường TỰ HẾT nếu chờ chút rồi thử lại.       ║
# ║ ⚠️ CHỈ bọc thao tác ĐỌC (idempotent). TUYỆT ĐỐI không retry gửi/    ║
# ║ xoá/gắn nhãn: thử lại lệnh GHI có thể GỬI TRÙNG / XOÁ 2 lần.        ║
# ╚══════════════════════════════════════════════════════════════════╝

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception


def _is_transient(exc: BaseException) -> bool:
    """Chỉ coi là 'đáng thử lại' khi: lỗi mạng (timeout/kết nối) HOẶC HTTP 429/5xx.
    Các lỗi 4xx khác (401/403 thiếu quyền, 404 không thấy) là lỗi THẬT → không thử lại."""
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return False


# Backoff mũ: chờ ~1s, 2s, 4s (tối đa 8s) giữa các lần; thử tối đa 3 lần rồi ném lỗi gốc ra.
gmail_read_retry = retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
