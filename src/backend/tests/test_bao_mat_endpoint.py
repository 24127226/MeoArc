"""AI GỌI ĐƯỢC CÁI GÌ KHI CHƯA ĐĂNG NHẬP.

Rà soát endpoint tìm ra bốn chỗ mở mà đáng lẽ phải đóng. Không chỗ nào rò dữ liệu
người dùng, nhưng ba trong bốn cái đủ để một người lạ làm hỏng buổi trình bày:

  • POST /dev/users        — TẠO người dùng trong CSDL thật, không cần gì cả.
  • GET  /dev/users        — trả về email của MỌI người đã đăng ký (dữ liệu cá nhân).
  • POST /emails/compose/suggest — GỌI LLM. Gói Gemini free 20 lượt/ngày mỗi model,
                             nên vài chục lời gọi từ bên ngoài là buổi bảo vệ mất trợ lý.
  • GET  /tra-cuu/chuyen-bay — mỗi lần tìm tốn 2 lượt AeroDataBox (gói free tính lượt).

Điểm chung của cả bốn: chúng không lấy được gì, nhưng làm CẠN một tài nguyên có hạn.
Đây là loại lỗ hổng dễ bỏ qua nhất khi rà, vì nhìn vào thì "có mất dữ liệu gì đâu".

Bài kiểm ở đây cố ý CHỈ hỏi "có chặn không", không hỏi endpoint chạy đúng chưa —
phần đó nằm ở các tệp test riêng của từng tính năng.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import app
from app.core.config import settings

c = TestClient(app)

# 401/403 = chặn đúng. 404 cũng chấp nhận với /dev/* — không xác nhận là endpoint có
# tồn tại thì càng tốt.
_DA_CHAN = {401, 403, 404}


@pytest.mark.parametrize("method,path,body", [
    ("post", "/emails/compose/suggest", {"subject": "x", "body": "y"}),
    ("get", "/admin/data-size", None),
    ("get", "/tra-cuu/chuyen-bay?tu=SGN&den=DAD&ngay=16/09/2026", None),
    ("get", "/tra-cuu/khach-san?thanh_pho=Đà Nẵng&nhan_phong=16/09/2026&tra_phong=18/09/2026", None),
])
def test_chua_dang_nhap_thi_KHONG_goi_duoc(method, path, body):
    r = c.post(path, json=body) if method == "post" else c.get(path)
    assert r.status_code in _DA_CHAN, (
        f"{method.upper()} {path} trả {r.status_code} — endpoint này tốn hạn mức "
        f"(LLM hoặc nhà cung cấp) nên không được để mở"
    )


@pytest.mark.parametrize("env", ["production", "PRODUCTION", "staging"])
def test_dev_users_bi_KHOA_o_moi_truong_that(monkeypatch, env):
    """Trên máy dev thì tiện; trên bản deploy thì bất kỳ ai cũng tạo được tài khoản
    trong CSDL thật, và GET còn trả về email của mọi người đã đăng ký."""
    monkeypatch.setattr(settings, "app_env", env)
    assert c.get("/dev/users").status_code == 404
    assert c.post("/dev/users", json={"email": "ke_la@example.com"}).status_code == 404


def test_dev_users_VAN_dung_duoc_o_may_dev(monkeypatch):
    """Khoá quá tay thì không ai dựng được dữ liệu mẫu, và người ta sẽ tắt hẳn lớp
    kiểm tra thay vì đi vòng — kết cục còn tệ hơn."""
    monkeypatch.setattr(settings, "app_env", "development")
    assert c.get("/dev/users").status_code == 200


@pytest.mark.parametrize("path", ["/health", "/tra-cuu/trang-thai", "/tra-cuu/san-bay"])
def test_endpoint_SIEU_DU_LIEU_van_mo_co_chu_y(path):
    """Ba cái này KHÔNG gọi ra ngoài, KHÔNG chạm dữ liệu của ai. Giữ mở để hệ giám sát
    và người vận hành kiểm được cấu hình bản deploy mà không phải đăng nhập."""
    assert c.get(path).status_code == 200


def test_trang_thai_van_KHONG_lo_khoa(monkeypatch):
    """Endpoint mở thì càng phải chắc nó không nói gì thừa."""
    monkeypatch.setattr(settings, "aerodatabox_key", "khoa-that-abc", raising=False)
    assert "khoa-that-abc" not in c.get("/tra-cuu/trang-thai").text


def test_outlook_chua_cau_hinh_thi_BAO_RO_chu_khong_day_sang_microsoft(monkeypatch):
    """Thiếu MS_CLIENT_ID mà vẫn redirect thì Microsoft trả về:

        AADSTS900144: The request body must contain the following parameter: 'client_id'

    Người dùng đọc câu đó sẽ tưởng TÀI KHOẢN MICROSOFT của mình có vấn đề, và đi sửa ở
    đúng chỗ không hề có lỗi. Sự thật là MeoArc chưa được cấu hình — một điều chỉ máy
    chủ này biết, nên nó phải là nơi nói ra.
    """
    monkeypatch.setattr(settings, "ms_client_id", "")
    r = c.get("/auth/outlook/start", follow_redirects=False)
    assert r.status_code == 503, f"trả {r.status_code} — đang đẩy sang Microsoft với client_id rỗng"
    assert "MS_CLIENT_ID" in r.text


def test_co_cau_hinh_thi_VAN_day_sang_microsoft(monkeypatch):
    """Chặn quá tay thì Outlook không bao giờ dùng được, kể cả khi đã cấu hình đúng."""
    monkeypatch.setattr(settings, "ms_client_id", "id-that")
    r = c.get("/auth/outlook/start", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "login.microsoftonline.com" in r.headers.get("location", "")
