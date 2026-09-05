"""VÒNG XOÁ → THÙNG RÁC → KHÔI PHỤC → HỘP THƯ, chạy qua HTTP thật.

Các test khôi phục sẵn có chỉ kiểm SCHEMA (`BulkAction` có nhận chữ "restore" không).
Không cái nào chạy thật vòng: xoá một thư, liệt kê Thùng rác xem nó có ở đó, khôi phục,
rồi liệt kê Hộp thư xem nó có quay về. Mà đó mới đúng là thứ người dùng nhìn thấy —
và là chỗ vừa báo hỏng: "khôi phục rồi nhưng không thấy mail mới khôi phục".

Chạy trên nhánh STORE (mailbox_store_enabled = True), tức nhánh mà bản deploy dùng để
chống rate-limit. Nhánh này phục vụ danh sách TỪ DB chứ không hỏi Gmail, nên nếu
write-through không cập nhật cột `folder` thì Gmail đã khôi phục xong mà màn hình vẫn
trống — đúng triệu chứng được báo.

Gmail/Graph bị thay bằng hàm giả: ở đây kiểm tầng CỦA MÌNH (endpoint + repo + truy vấn
liệt kê), không kiểm nhà cung cấp.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.app import app
from app.core.config import settings
from app.core.deps import get_current_session, get_db, get_gmail_token, get_provider

USER_ID = 1
PROVIDER = "google"


class _Phien:
    user_id = USER_ID
    provider = PROVIDER
    google_access_token = "tok"


def _mem_db():
    from app.core.db import Base
    import app.models.user  # noqa: F401 — bảng users là đích của FK
    import app.models.email_store  # noqa: F401
    import app.models.audit  # noqa: F401
    import app.models.notification  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


@pytest.fixture()
def khach(monkeypatch):
    """TestClient đã đăng nhập sẵn, DB in-memory có 2 thư ở Hộp thư, store BẬT."""
    from app.models.email_store import StoredEmail
    from app.models.user import User
    from app.services import mail

    db = _mem_db()
    db.add(User(id=USER_ID, email="ai@example.com", name="Ai Đó", initial="A"))
    # `received_at` phải ĐẶT RÕ: để trống thì thứ tự rơi về `id DESC` và bộ test tự
    # khẳng định một thứ tự mà dữ liệu thật không hứa. m1 mới hơn ⇒ m1 đứng trước.
    for i, tieu_de in enumerate(["Thư một", "Thư hai"], start=1):
        db.add(StoredEmail(user_id=USER_ID, provider=PROVIDER, g_id=f"m{i}",
                           folder="inbox", sender="Người Gửi", sender_email="ng@example.com",
                           subject=tieu_de, preview="...",
                           received_at=datetime(2026, 9, 5, 12 - i, 0, 0)))
    db.commit()

    monkeypatch.setattr(settings, "mailbox_store_enabled", True, raising=False)
    # Nhà cung cấp: chỉ cần "chạy trót lọt" — phần Gmail thật không thuộc phạm vi test này.
    for ten in ("trash", "untrash", "archive"):
        monkeypatch.setattr(mail, ten, lambda *a, **k: 1, raising=False)

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_session] = lambda: _Phien()
    app.dependency_overrides[get_gmail_token] = lambda: "tok"
    app.dependency_overrides[get_provider] = lambda: PROVIDER
    yield TestClient(app), db
    app.dependency_overrides.clear()


def _ids(c: TestClient, folder: str) -> list[str]:
    r = c.get("/emails", params={"folder": folder})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("source") == "db", "phải đang chạy nhánh STORE, không phải nhánh live"
    return [e["id"] for e in data["items"]]


def test_vong_day_du_xoa_roi_khoi_phuc(khach):
    c, _ = khach
    assert _ids(c, "inbox") == ["m1", "m2"]
    assert _ids(c, "trash") == []

    assert c.post("/emails/actions/delete", json={"ids": ["m1"]}).status_code == 200
    assert _ids(c, "inbox") == ["m2"], "thư đã xoá phải rời Hộp thư"
    assert _ids(c, "trash") == ["m1"], "và phải THẬT SỰ nằm trong Thùng rác"

    assert c.post("/emails/actions/restore", json={"ids": ["m1"]}).status_code == 200
    assert _ids(c, "trash") == [], "khôi phục xong Thùng rác phải hết thư đó"
    assert "m1" in _ids(c, "inbox"), "và thư phải quay lại HỘP THƯ — chỗ vừa báo hỏng"


def test_khoi_phuc_nhieu_thu_mot_luot(khach):
    c, _ = khach
    c.post("/emails/actions/delete", json={"ids": ["m1", "m2"]})
    assert _ids(c, "inbox") == []
    c.post("/emails/actions/restore", json={"ids": ["m1", "m2"]})
    assert sorted(_ids(c, "inbox")) == ["m1", "m2"]


def test_luu_tru_KHONG_roi_vao_thung_rac(khach):
    c, _ = khach
    c.post("/emails/actions/archive", json={"ids": ["m1"]})
    assert _ids(c, "archive") == ["m1"]
    assert _ids(c, "trash") == [], "lưu trữ và xoá là hai chỗ khác nhau"


def test_khoi_phuc_thu_KHONG_o_thung_rac_thi_khong_pha_gi(khach):
    """Gọi nhầm id đang ở Hộp thư: không được nhân đôi hay làm mất thư."""
    c, _ = khach
    c.post("/emails/actions/restore", json={"ids": ["m2"]})
    assert _ids(c, "inbox") == ["m1", "m2"]


def test_ghi_DB_that_bai_thi_KHONG_bao_thanh_cong(khach, monkeypatch):
    """`_wt` nuốt mọi lỗi, nên write-through hỏng là hỏng TRONG IM LẶNG.

    Đây chính là hình dạng của lỗi được báo: Gmail khôi phục xong, endpoint trả 200,
    nhưng cột `folder` trong DB không đổi nên danh sách vẫn trống. Test này chốt rằng
    nếu điều đó xảy ra thì ÍT NHẤT nó phải quan sát được, chứ không phải một màn hình
    trống không ai giải thích nổi.
    """
    from app.repo import email_store_repo

    c, _ = khach
    c.post("/emails/actions/delete", json={"ids": ["m1"]})
    monkeypatch.setattr(email_store_repo, "move_folder",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("DB sập")))
    c.post("/emails/actions/restore", json={"ids": ["m1"]})
    assert _ids(c, "trash") == ["m1"], "ghi DB hỏng thì thư vẫn ở Thùng rác — KHÔNG được im lặng"


def test_khoi_phuc_thu_CU_thi_co_con_thay_duoc_khong(khach):
    """Hộp thư đầy hơn một trang: khôi phục một thư CŨ thì nó về đâu?

    Danh sách lấy 30 thư/trang, sắp theo `received_at` giảm dần. Thư khôi phục quay
    lại ĐÚNG vị trí thời gian của nó, nên nếu nó cũ hơn 30 thư mới nhất thì nó nằm ở
    trang 2 — người dùng bấm khôi phục, thấy toast báo xong, rồi nhìn Hộp thư không
    thấy gì mới. Test này ghi lại hành vi thật đó để biết đây có phải nguyên nhân của
    "khôi phục rồi nhưng không thấy mail" hay không.
    """
    from app.models.email_store import StoredEmail

    c, db = khach
    for i in range(3, 40):  # thêm 37 thư MỚI HƠN m1/m2 → đẩy chúng xuống dưới
        db.add(StoredEmail(user_id=USER_ID, provider=PROVIDER, g_id=f"n{i}",
                           folder="inbox", sender="Ai Đó", sender_email="x@example.com",
                           subject=f"Thư {i}", preview="...",
                           received_at=datetime(2026, 9, 6, 0, 0, 0) + timedelta(minutes=i)))
    db.commit()

    trang1 = _ids(c, "inbox")
    assert "m1" not in trang1, "tiền đề: m1 vốn đã nằm ngoài trang 1"

    c.post("/emails/actions/delete", json={"ids": ["m1"]})
    assert _ids(c, "trash") == ["m1"]
    c.post("/emails/actions/restore", json={"ids": ["m1"]})

    # DB đã đúng...
    from app.repo import email_store_repo
    assert email_store_repo.get_one(db, USER_ID, PROVIDER, "m1").folder == "inbox"
    # ...nhưng người dùng nhìn trang 1 thì KHÔNG thấy nó.
    assert "m1" not in _ids(c, "inbox"), (
        "Nếu assert này đỏ thì giả thuyết phân trang sai; nếu xanh thì đây chính là "
        "lý do người dùng 'khôi phục rồi mà không thấy mail'."
    )
