# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_ops_endpoints.py — ĐIỂM BẮT MẠCH VẬN HÀNH              ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ /health và /metrics là thứ hệ thống giám sát gọi liên tục. Chúng    ║
# ║ hỏng thì mất luôn khả năng biết hệ thống đang sống hay chết — nên   ║
# ║ phải có test canh, y như các tính năng cho người dùng.             ║
# ║                                                                    ║
# ║ Test khởi động app qua TestClient nên đồng thời canh luôn một lỗi   ║
# ║ vận hành nghiêm trọng: vòng dọn dữ liệu chạy nền phải BỊ HUỶ khi    ║
# ║ tắt. Không huỷ thì mỗi lần triển khai bản mới đều treo ở khâu tắt.  ║
# ╚══════════════════════════════════════════════════════════════════╝

import time

from fastapi.testclient import TestClient

from app.api.app import app


def test_health_bao_duoc_trang_thai_database():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code in (200, 503)
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert body["db"] in ("up", "down")


def test_metrics_co_du_chi_so_can_de_biet_qua_tai():
    with TestClient(app) as c:
        r = c.get("/metrics")
    assert r.status_code == 200
    m = r.json()

    # Độ trễ: thứ người dùng CẢM nhận được
    assert "latency_ms" in m and {"p50", "p95", "p99"} <= set(m["latency_ms"])
    # Suất gọi ra ngoài còn trống: gần 0 nghĩa là đang nghẽn
    assert isinstance(m["provider_slots_free"], int)
    assert isinstance(m["llm_slots_free"], int)
    # Ngắt mạch: 'mo' nghĩa là dịch vụ ngoài đang sập
    assert m["ngat_mach"]["nha_cung_cap_thu"]["trang_thai"] in ("dong", "mo", "thu-lai")
    assert m["ngat_mach"]["mo_hinh_ai"]["trang_thai"] in ("dong", "mo", "thu-lai")
    # Kho KV và số worker: biết cấu hình đang chạy thật sự là gì
    assert m["kv_backend"] in ("memory", "redis", "memory (fallback)")
    assert isinstance(m["workers"], int)
    # /metrics KHÔNG được chạm database — giám sát gọi liên tục, phải nhẹ
    assert "table_rows" not in m


def test_metrics_tra_ve_nhanh_khong_treo():
    """Từng có deadlock im lặng ở đây: snapshot() của ngắt mạch giữ khoá rồi gọi
    property `state` — mà `state` cũng xin đúng khoá đó. Endpoint không lỗi,
    không log, chỉ đơ vĩnh viễn. Test canh bằng ngưỡng thời gian."""
    with TestClient(app) as c:
        t0 = time.perf_counter()
        r = c.get("/metrics")
        mat = time.perf_counter() - t0
    assert r.status_code == 200
    assert mat < 5, f"/metrics mất {mat:.1f}s — nghi bị treo do khoá lồng nhau"


def test_data_size_dem_duoc_so_dong_cac_bang():
    """Số dòng bảng nằm riêng ở đây vì có chạm database."""
    with TestClient(app) as c:
        r = c.get("/admin/data-size")
    assert r.status_code == 200
    rows = r.json()["table_rows"]
    assert {"sessions", "audit_logs", "notifications"} <= set(rows)


def test_noi_thread_pool_that_su_co_tac_dung():
    """Việc nới luồng từng IM LẶNG không có tác dụng vì đọc limiter ngoài ngữ cảnh
    async — /metrics chỉ báo 'n/a' chứ không báo lỗi. Test này canh đúng chỗ đó."""
    from app.core.config import settings

    with TestClient(app) as c:
        m = c.get("/metrics").json()

    assert m["thread_pool"] != "n/a", (
        "Không đọc được số luồng — nhiều khả năng việc nới thread pool không chạy"
    )
    assert m["thread_pool"] == settings.web_thread_pool


def test_tat_may_khong_bi_treo():
    """Vòng dọn dữ liệu là vòng lặp VÔ HẠN. Không huỷ nó khi tắt thì tiến trình
    không bao giờ thoát — mỗi lần triển khai bản mới sẽ treo."""
    t0 = time.perf_counter()
    with TestClient(app) as c:
        c.get("/health")
    mat = time.perf_counter() - t0

    assert mat < 20, f"Khởi động + tắt mất {mat:.1f}s — nghi vòng chạy nền không được huỷ"
