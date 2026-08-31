# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/kv.py — KHO KEY-VALUE CẮM-RÚT (Redis ↔ in-memory)          ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đúng proposal: "Redis (cache/session)". Cách làm KHÔNG rủi ro demo: ║
# ║  • Đặt REDIS_URL trong .env  → cache + rate-limit chạy trên Redis   ║
# ║    (chia sẻ được giữa NHIỀU tiến trình/worker khi scale).           ║
# ║  • Không đặt (mặc định)      → in-memory y như trước, 0 phụ thuộc.  ║
# ║  • Redis đang chạy mà CHẾT giữa chừng → tự rơi về memory, app sống. ║
# ║ Hai khách hàng: gmail_service (cache 60s) + /agent/chat (rate-limit)║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import pickle
import time

from app.core.config import settings

logger = logging.getLogger("app.kv")


class _MemoryBackend:
    """Bản in-memory: dict {key: (hết_hạn_epoch, giá_trị)} — đủ cho 1 tiến trình."""

    def __init__(self) -> None:
        self._d: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        hit = self._d.get(key)
        if hit is None:
            return None
        exp, val = hit
        if time.time() >= exp:
            self._d.pop(key, None)
            return None
        return val

    def set(self, key: str, value, ttl: int) -> None:
        # dọn mục hết hạn + trần 512 khoá (NFR-Memory: không phình vô hạn)
        now = time.time()
        for k in [k for k, (e, _) in self._d.items() if now >= e]:
            self._d.pop(k, None)
        while len(self._d) >= 512:
            self._d.pop(next(iter(self._d)))
        self._d[key] = (now + ttl, value)

    def delete_prefix(self, prefix: str) -> None:
        for k in [k for k in self._d if k.startswith(prefix)]:
            self._d.pop(k, None)

    def incr_window(self, key: str, window: int) -> int:
        """Đếm lượt trong cửa sổ cố định `window` giây (cho rate-limit). Trả số đếm MỚI."""
        now = time.time()
        hit = self._d.get(key)
        if hit is None or now >= hit[0]:
            self._d[key] = (now + window, 1)
            return 1
        exp, n = hit
        self._d[key] = (exp, n + 1)
        return n + 1


class _RedisBackend:
    """Bản Redis: pickle giá trị Python; mọi lỗi mạng → ném lên để KV tự rơi về memory."""

    def __init__(self, url: str) -> None:
        import redis
        # timeout ngắn: Redis chết không được kéo sập request (fail-fast rồi fallback)
        self._r = redis.Redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)
        self._r.ping()

    def get(self, key: str):
        raw = self._r.get(key)
        return None if raw is None else pickle.loads(raw)

    def set(self, key: str, value, ttl: int) -> None:
        self._r.setex(key, ttl, pickle.dumps(value))

    def delete_prefix(self, prefix: str) -> None:
        keys = list(self._r.scan_iter(match=prefix + "*", count=200))
        if keys:
            self._r.delete(*keys)

    def incr_window(self, key: str, window: int) -> int:
        n = self._r.incr(key)
        if n == 1:
            self._r.expire(key, window)
        return int(n)


class KV:
    """Mặt tiền: chọn backend theo cấu hình; Redis lỗi giữa chừng → fallback memory (log 1 lần)."""

    def __init__(self) -> None:
        self._mem = _MemoryBackend()
        self._redis: _RedisBackend | None = None
        self.backend_name = "memory"
        if settings.redis_url:
            try:
                self._redis = _RedisBackend(settings.redis_url)
                self.backend_name = "redis"
                logger.info("KV dùng Redis: %s", settings.redis_url)
            except Exception as exc:
                logger.warning("REDIS_URL đặt nhưng không nối được (%s) → dùng in-memory.", exc)

    def _do(self, op: str, *args):
        if self._redis is not None:
            try:
                return getattr(self._redis, op)(*args)
            except Exception as exc:
                logger.warning("Redis lỗi giữa chừng (%s) → chuyển hẳn về in-memory.", exc)
                self._redis = None       # không thử lại mỗi call — tránh chậm dây chuyền
                self.backend_name = "memory (fallback)"
        return getattr(self._mem, op)(*args)

    def get(self, key: str):
        return self._do("get", key)

    def set(self, key: str, value, ttl: int) -> None:
        self._do("set", key, value, ttl)

    def delete_prefix(self, prefix: str) -> None:
        self._do("delete_prefix", prefix)

    def incr_window(self, key: str, window: int) -> int:
        return self._do("incr_window", key, window)


kv = KV()  # instance dùng chung toàn app
