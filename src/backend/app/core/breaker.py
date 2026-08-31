# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/breaker.py — NGẮT MẠCH (circuit breaker)                 ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Retry (retry.py) xử lý trục trặc CHỚP NHOÁNG: chờ chút rồi thử lại ║
# ║ là xong. Nhưng khi nhà cung cấp sập HẲN vài phút thì retry lại      ║
# ║ thành phản tác dụng:                                               ║
# ║   • mỗi request cố 3 lần, mỗi lần chờ tới 8s → người dùng ngồi đợi  ║
# ║     gần nửa phút chỉ để nhận lỗi;                                   ║
# ║   • các luồng xử lý bị giữ rịt, hàng đợi tắc, lan sang cả những     ║
# ║     tính năng không liên quan;                                      ║
# ║   • ta còn dội thêm tải vào một dịch vụ đang ốm.                    ║
# ║                                                                    ║
# ║ Ngắt mạch giải quyết đúng chỗ đó: hỏng liên tiếp quá ngưỡng thì     ║
# ║ MỞ MẠCH — từ chối ngay lập tức trong một khoảng, không gọi ra nữa.  ║
# ║ Hết khoảng thì cho MỘT lượt đi thử; thông thì đóng lại, vẫn hỏng    ║
# ║ thì mở tiếp. Hỏng nhanh và rõ ràng, thay vì chờ lâu rồi cũng hỏng.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import threading
import time
from contextlib import contextmanager

logger = logging.getLogger("app.breaker")


class CircuitOpen(Exception):
    """Mạch đang mở — từ chối ngay, không gọi ra ngoài."""

    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(
            f"Dịch vụ '{name}' đang gặp sự cố, tạm dừng gọi thêm "
            f"{retry_after:.0f}s để nó hồi phục."
        )


class CircuitBreaker:
    """Ba trạng thái: đóng (chạy bình thường) · mở (từ chối ngay) · thử lại (cho 1 lượt dò).

    Chỉ đếm lỗi HẠ TẦNG (mạng chết, 5xx, hết giờ). Không đếm lỗi nghiệp vụ như
    401/403/404 — token sai của một người không phải là dấu hiệu dịch vụ sập, và
    nếu đếm thì vài người nhập sai đủ để cắt dịch vụ của tất cả.
    """

    def __init__(self, name: str, fail_threshold: int = 5, reset_after_s: float = 30.0):
        self.name = name
        self.fail_threshold = fail_threshold
        self.reset_after_s = reset_after_s
        self._lock = threading.Lock()
        self._fails = 0
        self._opened_at: float | None = None
        self._probing = False
        self.opened_count = 0        # số lần đã mở mạch — để đưa lên /metrics

    def _state_khong_khoa(self) -> str:
        """Tính trạng thái mà KHÔNG xin khoá — chỉ gọi khi đã giữ khoá sẵn."""
        if self._opened_at is None:
            return "dong"
        if time.time() - self._opened_at >= self.reset_after_s:
            return "thu-lai"
        return "mo"

    @property
    def state(self) -> str:
        with self._lock:
            return self._state_khong_khoa()

    def _on_success(self) -> None:
        with self._lock:
            self._fails = 0
            self._opened_at = None
            self._probing = False

    def _on_failure(self) -> None:
        with self._lock:
            self._fails += 1
            self._probing = False
            if self._fails >= self.fail_threshold and self._opened_at is None:
                self._opened_at = time.time()
                self.opened_count += 1
                logger.warning(
                    "NGẮT MẠCH '%s': hỏng %s lần liên tiếp → tạm dừng %.0fs",
                    self.name, self._fails, self.reset_after_s,
                )

    def _allow(self) -> None:
        """Ném CircuitOpen nếu đang mở. Ở trạng thái thử lại thì cho đúng MỘT lượt đi dò."""
        with self._lock:
            if self._opened_at is None:
                return
            cho_den_gio = time.time() - self._opened_at >= self.reset_after_s
            if not cho_den_gio:
                raise CircuitOpen(self.name, self.reset_after_s - (time.time() - self._opened_at))
            if self._probing:
                # Đã có một lượt đang dò rồi — người đến sau chờ kết quả của lượt đó,
                # không dội cả đám vào dịch vụ vừa mới ốm dậy.
                raise CircuitOpen(self.name, 1.0)
            self._probing = True

    @contextmanager
    def guard(self, count_failure=lambda exc: True):
        """Bọc một lệnh gọi ra ngoài.

        `count_failure` quyết định lỗi nào được TÍNH là hỏng hạ tầng. Mặc định tính
        tất cả; nơi gọi nên truyền hàm riêng để bỏ qua lỗi nghiệp vụ (401/403/404).
        """
        self._allow()
        try:
            yield
        except CircuitOpen:
            raise
        except Exception as exc:
            if count_failure(exc):
                self._on_failure()
            else:
                # Lỗi nghiệp vụ: không phải dấu hiệu dịch vụ sập → coi như lượt gọi
                # vẫn tới nơi, reset bộ đếm để không mở mạch oan.
                self._on_success()
            raise
        else:
            self._on_success()

    def snapshot(self) -> dict:
        # ⚠️ Dùng _state_khong_khoa() chứ KHÔNG gọi property `state` ở đây.
        # `state` tự xin khoá, mà threading.Lock không tái nhập được → giữ khoá rồi
        # gọi `state` là treo cứng vĩnh viễn. Lỗi này từng làm /metrics không bao
        # giờ trả về, và nó im lặng: không log, không lỗi, chỉ đơ.
        with self._lock:
            return {
                "trang_thai": self._state_khong_khoa(),
                "so_lan_hong_lien_tiep": self._fails,
                "so_lan_da_mo_mach": self.opened_count,
            }


def _loi_ha_tang(exc: BaseException) -> bool:
    """Chỉ những lỗi này mới tính là 'dịch vụ đang hỏng'."""
    import httpx

    if isinstance(exc, httpx.TransportError):     # mạng chết, hết giờ, không nối được
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500    # lỗi phía họ
    # Lỗi mạng/hết giờ chung của thư viện khác (LLM SDK…)
    return isinstance(exc, (TimeoutError, ConnectionError))


# Hai mạch riêng: Gmail sập không được kéo theo trợ lý AI ngừng hoạt động và ngược lại.
provider_breaker = CircuitBreaker("nha-cung-cap-thu", fail_threshold=5, reset_after_s=30)
llm_breaker = CircuitBreaker("mo-hinh-ai", fail_threshold=4, reset_after_s=45)


def guard_provider():
    """Bọc lệnh gọi Gmail/Graph."""
    return provider_breaker.guard(count_failure=_loi_ha_tang)


def guard_llm():
    """Bọc lệnh gọi mô hình."""
    return llm_breaker.guard(count_failure=_loi_ha_tang)
