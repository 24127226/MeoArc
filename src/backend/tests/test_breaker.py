# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_breaker.py — NGẮT MẠCH                                 ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Điểm dễ sai nhất của ngắt mạch KHÔNG phải là "có mở được không",   ║
# ║ mà là "mở NHẦM lúc nào". Đếm cả lỗi nghiệp vụ (401/403/404) thì    ║
# ║ vài người nhập sai token đủ để cắt dịch vụ của tất cả mọi người.   ║
# ╚══════════════════════════════════════════════════════════════════╝

import time

import httpx
import pytest

from app.core.breaker import CircuitBreaker, CircuitOpen, _loi_ha_tang


def _loi_http(status: int) -> httpx.HTTPStatusError:
    req = httpx.Request("GET", "https://example.test")
    return httpx.HTTPStatusError("loi", request=req, response=httpx.Response(status, request=req))


def test_hong_du_nguong_thi_mo_mach_va_tu_choi_ngay():
    cb = CircuitBreaker("thu", fail_threshold=3, reset_after_s=60)

    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            with cb.guard(count_failure=_loi_ha_tang):
                raise _loi_http(503)

    assert cb.state == "mo"
    # Lượt tiếp theo bị chặn NGAY, không gọi ra ngoài nữa
    with pytest.raises(CircuitOpen):
        with cb.guard(count_failure=_loi_ha_tang):
            pytest.fail("Không được chạy tới đây khi mạch đang mở")


def test_khong_mo_mach_vi_loi_nghiep_vu():
    """401/403/404 là lỗi của MỘT người dùng, không phải dịch vụ sập.
    Đếm chúng thì vài người nhập sai token sẽ cắt dịch vụ của tất cả."""
    cb = CircuitBreaker("thu", fail_threshold=3, reset_after_s=60)

    for status in (401, 403, 404, 400, 422):
        with pytest.raises(httpx.HTTPStatusError):
            with cb.guard(count_failure=_loi_ha_tang):
                raise _loi_http(status)

    assert cb.state == "dong", "Lỗi nghiệp vụ không được làm mở mạch"


def test_thanh_cong_thi_reset_bo_dem():
    cb = CircuitBreaker("thu", fail_threshold=3, reset_after_s=60)

    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            with cb.guard(count_failure=_loi_ha_tang):
                raise _loi_http(500)

    with cb.guard(count_failure=_loi_ha_tang):
        pass  # một lượt thành công

    # Hỏng thêm 2 lần nữa vẫn chưa đủ ngưỡng vì bộ đếm đã về 0
    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            with cb.guard(count_failure=_loi_ha_tang):
                raise _loi_http(500)

    assert cb.state == "dong"


def test_het_gio_thi_cho_mot_luot_di_do_va_dong_lai_neu_thong():
    cb = CircuitBreaker("thu", fail_threshold=2, reset_after_s=0.2)

    for _ in range(2):
        with pytest.raises(httpx.HTTPStatusError):
            with cb.guard(count_failure=_loi_ha_tang):
                raise _loi_http(502)
    assert cb.state == "mo"

    time.sleep(0.25)
    assert cb.state == "thu-lai"

    with cb.guard(count_failure=_loi_ha_tang):
        pass  # lượt dò thành công

    assert cb.state == "dong", "Dịch vụ hồi phục thì mạch phải đóng lại"


def test_dang_do_thi_nguoi_den_sau_bi_chan():
    """Chỉ MỘT lượt được đi dò. Nếu thả cả đám vào dịch vụ vừa ốm dậy thì
    nó sập lại ngay."""
    cb = CircuitBreaker("thu", fail_threshold=1, reset_after_s=0.1)

    with pytest.raises(httpx.HTTPStatusError):
        with cb.guard(count_failure=_loi_ha_tang):
            raise _loi_http(500)
    time.sleep(0.15)

    ctx = cb.guard(count_failure=_loi_ha_tang)
    ctx.__enter__()                    # lượt dò thứ nhất đang chạy
    try:
        with pytest.raises(CircuitOpen):
            with cb.guard(count_failure=_loi_ha_tang):
                pytest.fail("Người đến sau phải bị chặn trong lúc đang dò")
    finally:
        ctx.__exit__(None, None, None)


def test_snapshot_khong_bi_treo():
    """Canh đúng lỗi đã gặp: snapshot() giữ khoá rồi gọi property `state` — mà
    `state` cũng xin khoá đó. threading.Lock không tái nhập → TREO CỨNG, im lặng,
    không log gì. Nó từng làm /metrics không bao giờ trả về."""
    import threading

    cb = CircuitBreaker("thu", fail_threshold=2, reset_after_s=5)
    ket_qua = {}

    def chay():
        ket_qua["snap"] = cb.snapshot()

    t = threading.Thread(target=chay, daemon=True)
    t.start()
    t.join(timeout=3)

    assert not t.is_alive(), "snapshot() bị treo — nhiều khả năng deadlock do khoá lồng nhau"
    assert ket_qua["snap"]["trang_thai"] in ("dong", "mo", "thu-lai")


def test_snapshot_van_dung_khi_mach_dang_mo():
    cb = CircuitBreaker("thu", fail_threshold=1, reset_after_s=30)
    with pytest.raises(httpx.HTTPStatusError):
        with cb.guard(count_failure=_loi_ha_tang):
            raise _loi_http(500)

    snap = cb.snapshot()
    assert snap["trang_thai"] == "mo"
    assert snap["so_lan_da_mo_mach"] == 1


def test_hai_mach_doc_lap_nhau():
    """Gmail sập không được kéo theo trợ lý AI ngừng hoạt động."""
    from app.core.breaker import llm_breaker, provider_breaker

    truoc = llm_breaker.state
    cb = provider_breaker
    assert cb is not llm_breaker
    assert llm_breaker.state == truoc
