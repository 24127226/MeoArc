# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/limits.py — HÀNG RÀO CHỊU TẢI (backpressure)             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Một đồ án lớp học chỉ có 1-2 người bấm nên "chạy được" là xong.    ║
# ║ Hệ thống thật có hàng trăm người bấm CÙNG LÚC, và cái vỡ đầu tiên  ║
# ║ không phải CPU mà là các TÀI NGUYÊN CÓ HẠN:                        ║
# ║   • luồng xử lý của web server (mỗi request I/O giữ 1 luồng)       ║
# ║   • hạn ngạch API bên ngoài (Gmail/Graph/Gemini tính theo giây)    ║
# ║   • kết nối database (pool có 20+10)                              ║
# ║                                                                    ║
# ║ Nguyên tắc: THÀ TỪ CHỐI SỚM VÀ LỊCH SỰ còn hơn nhận hết rồi chết   ║
# ║ chùm. Mọi thứ ở đây đều nhằm đặt TRẦN cho từng loại tài nguyên.    ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import threading
import time
from contextlib import contextmanager

from app.core.config import settings
from app.core.kv import kv

logger = logging.getLogger("app.limits")

# ── 1. TRẦN THAM SỐ ĐẦU VÀO ──────────────────────────────────────────
# Vì sao: /emails?limit=5000 khiến server gọi Gmail 5000 lần cho MỘT request.
# Một người dùng nghịch (hoặc script lỗi) đủ sức làm nghẽn cả hệ thống và đốt
# sạch hạn ngạch API của mọi người. Trần này là tuyến phòng thủ đầu tiên.
MAX_PAGE_SIZE = 50          # số thư tối đa cho một trang

# Số thư mà TRANG LỊCH và các tool lịch trình cùng quét.
#
# PHẢI ≤ MAX_PAGE_SIZE. Đã vấp: trang lịch xin 60 trong khi API chặn ở 50 → FastAPI
# trả 422 → `.catch()` ở frontend nuốt lỗi → cuốn lịch TRỐNG TRƠN, không một dấu hiệu
# nào. Và vì trợ lý gọi tool trong tiến trình (không qua HTTP) nên nó vẫn thấy đủ thư
# → "AI bảo có việc mà lịch trống", đúng thứ bản sửa trước định chữa.
#
# Một hằng số cho cả hai bên là cách duy nhất khiến chúng không thể lệch nữa.
QUET_LICH_TRINH = 50
MAX_QUERY_LEN = 200         # độ dài từ khoá tìm kiếm
MAX_MESSAGE_LEN = 4_000     # độ dài một tin nhắn gửi cho trợ lý
MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB — chặn upload/payload khổng lồ


def clamp_page_size(n: int | None, default: int = 30) -> int:
    """Ép cỡ trang về khoảng an toàn. Không tin số client gửi lên."""
    if n is None:
        return default
    return max(1, min(int(n), MAX_PAGE_SIZE))


# ── 2. TRẦN SỐ LỆNH GỌI RA NGOÀI CÙNG LÚC ────────────────────────────
# Vì sao: mỗi request dựng danh sách thư bắn 8 lệnh gọi Gmail song song.
# 50 người cùng mở hộp thư = 400 kết nối đồng thời → Gmail trả 429 hàng loạt
# và mọi người cùng hỏng. Semaphore đặt TRẦN TOÀN CỤC cho cả tiến trình:
# quá trần thì xếp hàng chờ, chứ không bắn thêm.
def _per_worker(total: int) -> int:
    """Chia trần TỔNG cho số tiến trình đang chạy.

    Semaphore chỉ có tác dụng TRONG một tiến trình. Chạy `--workers 4` mà giữ
    nguyên trần 32 thì thực tế thành 4×32 = 128 kết nối ra ngoài — vượt gấp bốn
    ý định và vẫn làm nhà cung cấp trả 429. Chia đều để tổng toàn cụm đúng bằng
    con số đã đặt; luôn để lại ít nhất 1 suất cho mỗi worker.
    """
    workers = max(1, settings.web_concurrency)
    return max(1, total // workers)


_provider_gate = threading.BoundedSemaphore(_per_worker(settings.max_provider_concurrency))
_llm_gate = threading.BoundedSemaphore(_per_worker(settings.max_llm_concurrency))


@contextmanager
def provider_slot(timeout: float = 8.0):
    """Xin một suất gọi nhà cung cấp thư. Chờ quá lâu → báo bận thay vì treo mãi."""
    got = _provider_gate.acquire(timeout=timeout)
    if not got:
        raise ProviderBusy("Hệ thống đang bận đọc thư, bạn thử lại sau giây lát.")
    try:
        yield
    finally:
        _provider_gate.release()


@contextmanager
def llm_slot(timeout: float = 3.0):
    """Xin một suất gọi mô hình. LLM đắt và chậm nhất → trần chặt hơn."""
    got = _llm_gate.acquire(timeout=timeout)
    if not got:
        raise ProviderBusy("Trợ lý đang xử lý nhiều yêu cầu, bạn chờ chút rồi thử lại.")
    try:
        yield
    finally:
        _llm_gate.release()


class ProviderBusy(Exception):
    """Quá tải có kiểm soát → API trả 503 kèm Retry-After, không phải lỗi 500."""


# ── 3. GIỚI HẠN TẦN SUẤT THEO NGƯỜI ──────────────────────────────────
# Rate limit cũ chỉ bảo vệ /agent/chat. Nhưng endpoint đọc thư mới là chỗ tốn
# I/O nhất. Đặt trần riêng cho từng nhóm, đếm trên Redis nên đúng cả khi chạy
# nhiều worker.
def rate_limited(bucket: str, user_id: int, per_min: int) -> bool:
    """True nếu người này đã vượt hạn mức của nhóm `bucket` trong 60 giây."""
    n = kv.incr_window(f"rate:{bucket}:{user_id}", window=60)
    if n > per_min:
        logger.info("Chặn tần suất bucket=%s user=%s n=%s/%s", bucket, user_id, n, per_min)
        return True
    return False


# ── 4. SỐ LIỆU VẬN HÀNH ──────────────────────────────────────────────
# Không đo thì không biết lúc nào sắp quá tải. Giữ bộ đếm nhẹ trong tiến trình,
# phơi ra /metrics để dashboard/giám khảo nhìn thấy hệ thống đang thở thế nào.
class _Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests = 0
        self.errors = 0
        self.rejected_busy = 0
        self.rejected_rate = 0
        self._durations: list[float] = []
        self.started_at = time.time()

    def observe(self, ms: float, status: int) -> None:
        with self._lock:
            self.requests += 1
            if status >= 500:
                self.errors += 1
            self._durations.append(ms)
            if len(self._durations) > 1000:      # chỉ giữ 1000 mẫu gần nhất
                self._durations = self._durations[-1000:]

    def note_rejection(self, kind: str) -> None:
        with self._lock:
            if kind == "busy":
                self.rejected_busy += 1
            else:
                self.rejected_rate += 1

    def snapshot(self) -> dict:
        with self._lock:
            d = sorted(self._durations)
        def pct(p: float) -> float:
            if not d:
                return 0.0
            return round(d[min(len(d) - 1, int(len(d) * p))], 1)
        return {
            "uptime_s": int(time.time() - self.started_at),
            "requests": self.requests,
            "errors_5xx": self.errors,
            "rejected_busy": self.rejected_busy,
            "rejected_rate_limit": self.rejected_rate,
            "latency_ms": {"p50": pct(0.5), "p95": pct(0.95), "p99": pct(0.99)},
            "provider_slots_free": _provider_gate._value,   # noqa: SLF001 — chỉ để quan sát
            "llm_slots_free": _llm_gate._value,             # noqa: SLF001
        }


metrics = _Metrics()
