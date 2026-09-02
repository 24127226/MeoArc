"""NHIỀU TÀI KHOẢN CÙNG LÚC — và cửa sau phải không được mở ra.

Trước đây một cookie = một tài khoản, nên muốn xem hộp thư khác là phải đăng xuất cái
đang mở. Người dùng đã quen cách Google làm tới mức không coi đó là tính năng — họ chỉ
thấy MeoArc thiếu một thứ hiển nhiên.

── CHỖ NGUY HIỂM NHẤT CỦA TÍNH NĂNG NÀY ──
`/auth/switch/{user_id}` nhận một con số từ bên ngoài. Nếu nó tra CSDL tìm phiên theo
user_id đó rồi cấp cookie, thì bất kỳ ai gọi endpoint cũng nhảy được vào hộp thư người
khác — trình đổi tài khoản trở thành cửa sau, và là loại cửa sau trông rất vô hại khi
đọc lướt.

Nên luật là: CHỈ chấp nhận phiên đã có sẵn trong cookie của chính trình duyệt đó.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.app import app
from app.api.auth import COOKIE_DS
from app.core.deps import COOKIE_NAME

c = TestClient(app)


class _PhienGia:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.provider = "gmail"
        self.google_access_token = "tok"


class _NguoiGia:
    def __init__(self, uid: int):
        self.id = uid
        self.email = f"nguoi{uid}@example.com"
        self.name = f"Người {uid}"


@pytest.fixture()
def _hai_tai_khoan(monkeypatch):
    """Trình duyệt đang giữ hai phiên: 'tok-a' (user 1) và 'tok-b' (user 2)."""
    from app.api import auth as A
    ban_do = {"tok-a": 1, "tok-b": 2}
    monkeypatch.setattr(A.session_repo, "get_valid_session",
                        lambda db, t: _PhienGia(ban_do[t]) if t in ban_do else None)
    monkeypatch.setattr(A, "User", object)   # chỉ để db.get(User, ...) có tham số
    import app.core.db as _db
    monkeypatch.setattr(type(next(_db.get_db())), "get",
                        lambda self, model, uid: _NguoiGia(uid), raising=False)
    return ban_do


def test_liet_ke_du_ca_hai_tai_khoan(_hai_tai_khoan):
    r = c.get("/auth/accounts", cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a,tok-b"})
    assert r.status_code == 200
    ds = r.json()["ket_qua"]
    assert [x["user_id"] for x in ds] == [1, 2]
    assert [x["dang_dung"] for x in ds] == [True, False]


def test_KHONG_tra_ve_token(_hai_tai_khoan):
    """Đưa token ra là biến một cookie httponly (JS không đọc được) thành chuỗi nằm
    trong bộ nhớ trang — mất sạch lớp bảo vệ trước XSS."""
    body = c.get("/auth/accounts",
                 cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a,tok-b"}).text
    assert "tok-a" not in body and "tok-b" not in body


def test_doi_sang_tai_khoan_DA_dang_nhap(_hai_tai_khoan):
    r = c.post("/auth/switch/2", cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a,tok-b"})
    assert r.status_code == 200
    # Cookie phiên hoạt động phải đổi sang tok-b.
    assert 'meoarc_session=tok-b' in r.headers.get("set-cookie", "")


def test_KHONG_doi_duoc_sang_tai_khoan_NGOAI_trinh_duyet(_hai_tai_khoan):
    """Cửa sau đáng sợ nhất: chỉ có tok-a trong cookie mà vẫn nhảy sang user 2."""
    r = c.post("/auth/switch/2", cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a"})
    assert r.status_code == 404, "đang cho phép nhảy vào hộp thư người khác"


def test_khong_co_cookie_thi_khong_doi_duoc(_hai_tai_khoan):
    assert c.post("/auth/switch/1").status_code == 404


def test_dang_xuat_CHI_bo_tai_khoan_dang_mo(_hai_tai_khoan, monkeypatch):
    """Đăng xuất một tài khoản mà mất luôn các tài khoản còn lại là hành vi người dùng
    không hề yêu cầu — và họ phải đăng nhập lại từng cái."""
    from app.api import auth as A
    monkeypatch.setattr(A.session_repo, "delete_session", lambda db, t: None)
    r = c.post("/auth/logout", cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a,tok-b"})
    assert r.status_code == 200
    ck = r.headers.get("set-cookie", "")
    assert "meoarc_session=tok-b" in ck, "còn tài khoản khác thì phải chuyển sang, không đá về login"


def test_dang_xuat_tai_khoan_CUOI_CUNG_thi_xoa_cookie(_hai_tai_khoan, monkeypatch):
    from app.api import auth as A
    monkeypatch.setattr(A.session_repo, "delete_session", lambda db, t: None)
    r = c.post("/auth/logout", cookies={COOKIE_NAME: "tok-a", COOKIE_DS: "tok-a"})
    ck = r.headers.get("set-cookie", "")
    assert 'meoarc_session=""' in ck or "meoarc_session=;" in ck or "Max-Age=0" in ck
