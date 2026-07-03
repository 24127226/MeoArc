"""test_kv.py — Kho key-value CẮM-RÚT (Redis ↔ in-memory) cho cache + rate-limit.

Chuẩn khách quan:
  * Ngữ nghĩa KV chuẩn: set rồi get lại được; hết TTL thì mất; xoá theo tiền tố.
  * Đếm cửa sổ (rate-limit): tăng dần trong cửa sổ, reset khi cửa sổ mới.
  * Reliability công bố: REDIS_URL đặt SAI/Redis chết → app KHÔNG sập, tự rơi về in-memory.

Chạy: uv run pytest tests/test_kv.py -v   (không cần Redis thật)
"""

from __future__ import annotations

import time

from app.core.kv import KV, _MemoryBackend


def test_memory_set_get_ttl():
    m = _MemoryBackend()
    m.set("k1", {"a": 1}, ttl=60)
    assert m.get("k1") == {"a": 1}
    # hết hạn → mất (giả lập bằng cách ghi đè mốc hết hạn)
    m._d["k1"] = (time.time() - 1, {"a": 1})
    assert m.get("k1") is None, "Quá TTL vẫn trả dữ liệu — cache thiu!"


def test_memory_delete_prefix_dung_pham_vi():
    m = _MemoryBackend()
    m.set("gmail:u1:list", 1, ttl=60)
    m.set("gmail:u1:msg", 2, ttl=60)
    m.set("gmail:u2:list", 3, ttl=60)
    m.delete_prefix("gmail:u1:")
    assert m.get("gmail:u1:list") is None and m.get("gmail:u1:msg") is None
    assert m.get("gmail:u2:list") == 3, "Xoá lấn sang cache của người khác!"


def test_memory_co_tran_so_khoa():
    m = _MemoryBackend()
    for i in range(600):
        m.set(f"k{i}", i, ttl=300)
    assert len(m._d) <= 512, f"Kho phình {len(m._d)} khoá — vượt trần 512 (NFR-Memory)"


def test_incr_window_dem_va_reset():
    m = _MemoryBackend()
    assert [m.incr_window("r:1", 60) for _ in range(3)] == [1, 2, 3]
    # sang cửa sổ mới → đếm lại từ 1 (giả lập hết hạn cửa sổ)
    exp, n = m._d["r:1"]
    m._d["r:1"] = (time.time() - 1, n)
    assert m.incr_window("r:1", 60) == 1, "Cửa sổ mới phải reset bộ đếm"


def test_redis_sai_khong_lam_sap_app(monkeypatch):
    """REDIS_URL trỏ vào nơi không có Redis → KV phải tự rơi về memory, không ném lỗi."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:1/0")  # cổng chết
    k = KV()  # không được raise
    assert k.backend_name == "memory", f"Phải fallback memory, nhận {k.backend_name!r}"
    k.set("x", 1, ttl=10)
    assert k.get("x") == 1, "Fallback memory phải hoạt động đầy đủ"
