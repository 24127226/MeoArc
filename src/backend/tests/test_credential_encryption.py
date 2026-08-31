# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_credential_encryption.py — SEC-TC05                    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ "Không lưu thông tin đăng nhập dạng chữ thường" là loại khẳng định  ║
# ║ RẤT dễ sai mà không ai biết: cột vẫn là VARCHAR, ứng dụng đọc ra    ║
# ║ vẫn đúng chuỗi cũ, mọi thứ chạy y như trước. Chỉ khi mở thẳng       ║
# ║ database ra nhìn mới thấy token nằm phơi ở đó.                      ║
# ║                                                                    ║
# ║ Nên phép thử ở đây KHÔNG hỏi model, mà đọc BẰNG SQL THÔ để thấy    ║
# ║ đúng những byte thật sự nằm trên đĩa.                              ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import crypto

TOKEN_THAT = "ya29.a0AfB_byC-mat-khong-duoc-lo-ra-ngoai"


@pytest.fixture()
def db():
    from app.core.db import Base
    import app.models.user      # noqa: F401
    import app.models.session   # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng)()
    from app.models.user import User
    s.add(User(id=1, email="u1@x.vn", name="U1", initial="U"))
    s.commit()
    return s


def _ghi_phien(db, token_google: str):
    from app.models.session import AuthSession
    db.add(AuthSession(
        token="phien-1", user_id=1,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        google_access_token=token_google,
        google_refresh_token=token_google + "-refresh",
    ))
    db.commit()


def _doc_tho(db, cot: str) -> str:
    """Đọc thẳng bằng SQL — bỏ qua mọi lớp giải mã của ORM."""
    return db.execute(
        text(f"SELECT {cot} FROM sessions WHERE token = 'phien-1'")
    ).scalar_one()


# ── Điều kiện tiên quyết: mã hoá phải đang BẬT ──────────────────────────────
def test_khoa_ma_hoa_phai_duoc_cau_hinh():
    """EncryptedStr TỰ TẮT khi không có khoá — và tắt trong im lặng, không báo gì.
    Thiếu phép thử này thì cả file có thể xanh trên một hệ thống đang lưu token
    phơi ra, vì 'không mã hoá' cũng là một đường chạy hợp lệ của code."""
    from app.core.config import settings
    assert settings.token_encryption_key, (
        "TOKEN_ENCRYPTION_KEY chưa đặt trong .env → mã hoá đang TẮT, "
        "token Google đang được lưu dạng chữ thường"
    )


# ── Phần chính: byte trên đĩa không được chứa token ─────────────────────────
def test_token_tren_dia_khong_phai_chu_thuong(db):
    _ghi_phien(db, TOKEN_THAT)

    tren_dia = _doc_tho(db, "google_access_token")

    assert TOKEN_THAT not in tren_dia, (
        "Token Google nằm nguyên dạng chữ thường trong database"
    )
    assert tren_dia.startswith("enc:"), (
        f"Giá trị lưu xuống không mang dấu đã-mã-hoá: {tren_dia[:24]!r}"
    )


def test_ca_refresh_token_cung_duoc_ma_hoa(db):
    """Refresh token nguy hiểm hơn access token — nó sống rất lâu."""
    _ghi_phien(db, TOKEN_THAT)

    tren_dia = _doc_tho(db, "google_refresh_token")

    assert TOKEN_THAT not in tren_dia
    assert tren_dia.startswith("enc:")


def test_doc_ra_van_dung_chuoi_ban_dau(db):
    """Mã hoá mà không giải mã lại được thì mọi lệnh gọi Gmail sẽ hỏng."""
    from app.models.session import AuthSession
    _ghi_phien(db, TOKEN_THAT)
    db.expire_all()

    s = db.get(AuthSession, "phien-1")
    assert s.google_access_token == TOKEN_THAT
    assert s.google_refresh_token == TOKEN_THAT + "-refresh"


def test_hai_lan_ma_hoa_ra_hai_chuoi_khac_nhau():
    """Fernet có vector khởi tạo ngẫu nhiên. Nếu hai lần mã hoá cùng một chuỗi mà ra
    kết quả giống hệt thì đang dùng phép mã hoá tất định — kẻ tấn công đọc được
    database sẽ nhận ra hai người dùng có cùng token."""
    a = crypto.encrypt_token(TOKEN_THAT)
    b = crypto.encrypt_token(TOKEN_THAT)

    assert a != b, "Hai lần mã hoá cho ra chuỗi giống nhau"
    assert crypto.decrypt_token(a) == crypto.decrypt_token(b) == TOKEN_THAT


def test_khong_co_cot_token_nao_bi_bo_sot():
    """Chống hồi quy: thêm cột token mới mà quên EncryptedStr là lỗi âm thầm điển hình
    — không ai thấy gì cho tới lúc lộ dữ liệu."""
    from app.core.crypto import EncryptedStr
    from app.models.session import AuthSession

    # Chỉ xét cột KẾT THÚC bằng _token: loại được google_token_expiry (mốc thời gian,
    # không phải thông tin đăng nhập) và cột khoá chính `token` của chính phiên.
    cot_token = [c for c in AuthSession.__table__.columns if c.name.endswith("_token")]
    assert cot_token, "Không tìm thấy cột token nào để kiểm"
    for c in cot_token:
        assert isinstance(c.type, EncryptedStr), (
            f"Cột {c.name!r} giữ thông tin đăng nhập nhưng KHÔNG dùng EncryptedStr"
        )
