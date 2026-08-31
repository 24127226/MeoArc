# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_deps_token_source.py — TOKEN LẤY TỪ ĐÂU               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Sau khi tách kết nối hộp thư ra khỏi phiên đăng nhập, token có    ║
# ║ HAI chỗ có thể nằm. Chọn nhầm nguồn là lỗi âm thầm điển hình:      ║
# ║ đọc ở chỗ này mà làm mới ở chỗ kia thì hai bản token lệch nhau,    ║
# ║ mọi thứ vẫn chạy, và vài giờ sau người dùng đột ngột bị 401.       ║
# ║                                                                    ║
# ║ Nên ba điều được đóng đinh ở đây:                                  ║
# ║   • Có kết nối  → LẤY từ kết nối, không phải từ phiên              ║
# ║   • Chưa có     → lùi về phiên (phiên cũ chưa kịp chuyển)          ║
# ║   • Làm mới     → ghi vào ĐÚNG nơi vừa đọc ra                      ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import types
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import deps
from app.repo import connected_account_repo as ca_repo


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture()
def db():
    from app.core.db import Base
    import app.models.user               # noqa: F401
    import app.models.connected_account  # noqa: F401
    import app.models.session            # noqa: F401 — nhánh lùi đọc provider của phiên
    import app.models.session_provider   # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng)()
    from app.models.user import User
    s.add(User(id=1, email="u1@x.vn", name="U1", initial="U"))
    s.commit()
    return s


def _phien(**kw):
    """Phiên giả — chỉ cần vài thuộc tính mà deps đụng tới."""
    mac_dinh = dict(token="sess-1", user_id=1, google_access_token=None,
                    google_refresh_token=None, google_token_expiry=None)
    mac_dinh.update(kw)
    return types.SimpleNamespace(**mac_dinh)


# ── Có kết nối → phải lấy từ kết nối ────────────────────────────────────────
def test_uu_tien_token_cua_ket_noi_hon_token_trong_phien(db):
    ca_repo.upsert(db, user_id=1, provider="google", provider_user_id="g-1",
                   access_token="TOKEN-KET-NOI",
                   token_expiry=_utcnow() + timedelta(hours=1))
    phien = _phien(google_access_token="TOKEN-PHIEN-CU",
                   google_token_expiry=_utcnow() + timedelta(hours=1))

    assert deps.get_gmail_token(session=phien, db=db) == "TOKEN-KET-NOI"


def test_nha_cung_cap_lay_theo_ket_noi(db):
    """Một người nối được cả hai hộp thư, lúc đó 'nhà cung cấp của phiên đăng nhập'
    không còn là câu hỏi có nghĩa."""
    ca_repo.upsert(db, user_id=1, provider="microsoft", provider_user_id="m-1",
                   access_token="t", token_expiry=_utcnow() + timedelta(hours=1))
    assert deps.get_provider(session=_phien(), db=db) == "microsoft"


# ── Chưa có kết nối → lùi về phiên ──────────────────────────────────────────
def test_chua_co_ket_noi_thi_dung_token_trong_phien(db):
    """Phiên đăng nhập cũ (tạo trước khi tách bảng) vẫn phải dùng được."""
    phien = _phien(google_access_token="TOKEN-PHIEN-CU",
                   google_token_expiry=_utcnow() + timedelta(hours=1))
    assert deps.get_gmail_token(session=phien, db=db) == "TOKEN-PHIEN-CU"


def test_khong_co_token_o_dau_ca_thi_bao_401(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        deps.get_gmail_token(session=_phien(), db=db)
    assert e.value.status_code == 401


# ── Làm mới phải ghi vào ĐÚNG nơi vừa đọc ra ────────────────────────────────
def test_lam_moi_thi_ghi_nguoc_vao_ket_noi(db, monkeypatch):
    """Đọc ở kết nối mà làm mới vào phiên là kiểu hỏng không ai thấy: lần sau lại đọc
    kết nối và vẫn gặp token cũ đã hết hạn, cứ thế làm mới mãi."""
    from app.services import auth_service

    acc = ca_repo.upsert(db, user_id=1, provider="google", provider_user_id="g-1",
                         access_token="CU", refresh_token="rt",
                         token_expiry=_utcnow() - timedelta(minutes=5))   # đã hết hạn
    monkeypatch.setattr(auth_service, "refresh_access_token", lambda rt: ("MOI", 3600))

    assert deps.get_gmail_token(session=_phien(), db=db) == "MOI"

    db.refresh(acc)
    assert acc.access_token == "MOI", "Token mới không được ghi vào bản ghi kết nối"
    assert acc.token_expiry > _utcnow(), "Hạn mới chưa được cập nhật"


def test_lam_moi_hong_thi_tra_token_cu_chu_khong_lam_sap_request(db, monkeypatch):
    """Refresh token bị thu hồi → vẫn trả token cũ để nhà cung cấp tự báo lỗi rõ ràng,
    thay vì làm sập request bằng một ngoại lệ không nói lên điều gì."""
    from app.services import auth_service

    ca_repo.upsert(db, user_id=1, provider="google", provider_user_id="g-1",
                   access_token="CU", refresh_token="rt-da-bi-thu-hoi",
                   token_expiry=_utcnow() - timedelta(minutes=5))

    def no(_rt):
        raise RuntimeError("invalid_grant")
    monkeypatch.setattr(auth_service, "refresh_access_token", no)

    assert deps.get_gmail_token(session=_phien(), db=db) == "CU"


def test_hop_thu_microsoft_lam_moi_bang_endpoint_microsoft(db, monkeypatch):
    """Định tuyến sai nhà cung cấp thì gọi Google để làm mới token Microsoft — lỗi khó
    lần vì thông báo trả về nói về một dịch vụ chẳng liên quan."""
    from app.services import auth_service, auth_service_ms

    ca_repo.upsert(db, user_id=1, provider="microsoft", provider_user_id="m-1",
                   access_token="CU", refresh_token="rt",
                   token_expiry=_utcnow() - timedelta(minutes=5))

    monkeypatch.setattr(auth_service_ms, "refresh_access_token", lambda rt: ("MS-MOI", 3600))
    monkeypatch.setattr(auth_service, "refresh_access_token",
                        lambda rt: pytest.fail("Đã gọi nhầm sang Google cho hộp thư Microsoft"))

    assert deps.get_gmail_token(session=_phien(), db=db) == "MS-MOI"


def test_ket_noi_da_thu_hoi_thi_khong_duoc_dung_nua(db):
    """Thu hồi quyền (UC002) rồi thì kết nối không còn được chọn làm nguồn token."""
    acc = ca_repo.upsert(db, user_id=1, provider="google", provider_user_id="g-1",
                         access_token="TOKEN-KET-NOI",
                         token_expiry=_utcnow() + timedelta(hours=1))
    ca_repo.revoke(db, acc)

    phien = _phien(google_access_token="TOKEN-PHIEN-CU",
                   google_token_expiry=_utcnow() + timedelta(hours=1))
    assert deps.get_gmail_token(session=phien, db=db) == "TOKEN-PHIEN-CU"
