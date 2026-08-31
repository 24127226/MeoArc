"""Ảnh đại diện người gửi — /avatars/{ten_mien}.

Điểm cần khoá lại: endpoint này nhận một chuỗi DO NGƯỜI DÙNG ĐƯA VÀO rồi dùng
nó để GỌI MẠNG RA NGOÀI. Đó đúng là hình dạng của lỗ hổng SSRF (Server-Side
Request Forgery): kẻ tấn công đưa `169.254.169.254` — endpoint metadata của máy
ảo trên mọi nền tảng đám mây — và máy chủ ngoan ngoãn đi lấy hộ, trả về khoá và
token của chính nó.

Nên phần lớn test ở đây không kiểm "ảnh có hiện không" mà kiểm "cái gì bị chặn".
"""

from __future__ import annotations

import pytest

from app.api.avatar import _don_ten_mien


@pytest.mark.parametrize("doc_hai", [
    "169.254.169.254",          # metadata máy ảo — mục tiêu SSRF kinh điển
    "127.0.0.1",
    "10.0.0.1",
    "localhost",
    "metadata.google.internal",
    "redis.local",
    "db.internal",
    "../../etc/passwd",
    "evil.com/../x",
    "evil.com?x=1",
    "a" * 300,                  # quá dài
    "",
    "khongcodauchamnao",
    ".mo-dau-bang-cham.com",
])
def test_chan_moi_dau_vao_nguy_hiem(doc_hai):
    """Không cái nào trong số này được phép trở thành một lệnh gọi mạng."""
    assert _don_ten_mien(doc_hai) is None, f"LỌT: {doc_hai!r}"


@pytest.mark.parametrize("pho_thong", [
    "gmail.com", "outlook.com", "yahoo.com", "icloud.com", "proton.me",
])
def test_hop_thu_pho_thong_khong_lay_bieu_tuong(pho_thong):
    """Tên miền của NHÀ CUNG CẤP, không phải của người gửi.

    Lấy biểu tượng gmail.com cho một cá nhân dùng Gmail thì mọi cá nhân trong hộp
    thư đều đeo chung một logo Gmail — vô nghĩa, và còn tệ hơn chữ cái đầu vì chữ
    cái ít nhất còn phân biệt được người này với người kia.
    """
    assert _don_ten_mien(pho_thong) is None


@pytest.mark.parametrize("hop_le", [
    ("github.com", "github.com"),
    ("GitHub.COM", "github.com"),        # chuẩn hoá về chữ thường
    ("@vercel.com", "vercel.com"),       # bỏ @ nếu lỡ truyền cả phần đuôi địa chỉ
    ("  hcmus.edu.vn  ", "hcmus.edu.vn"),
    ("sub.domain.co.uk", "sub.domain.co.uk"),
])
def test_ten_mien_that_duoc_qua(hop_le):
    raw, mong_doi = hop_le
    assert _don_ten_mien(raw) == mong_doi


def test_duong_dan_la_tra_404_chu_khong_phai_trang_html(client_khong_dang_nhap):
    """`avatars` phải nằm trong API_PREFIXES của spa.py.

    Thiếu nó thì bộ bắt-tất-cả của SPA nuốt mất route: một lệnh gọi hỏng trả về
    trang HTML kèm mã 200, và lỗi đó rất khó lần vì nhìn từ ngoài "có phản hồi
    thành công".
    """
    r = client_khong_dang_nhap.get("/avatars/gmail.com")
    assert r.status_code == 404
    assert "application/json" in r.headers.get("content-type", "")


@pytest.fixture
def client_khong_dang_nhap():
    from fastapi.testclient import TestClient

    from app.api.app import app

    return TestClient(app)
