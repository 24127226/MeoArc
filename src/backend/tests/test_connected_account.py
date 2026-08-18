# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_connected_account.py — KẾT NỐI HỘP THƯ (v6 §7, FR-01)  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Điểm của việc tách kết nối ra khỏi phiên đăng nhập: một người nối  ║
# ║ được nhiều hộp thư, và kết nối sống lâu hơn phiên.                 ║
# ║                                                                    ║
# ║ Ca đáng canh nhất ở đây là `refresh_token`: Google KHÔNG trả nó ở  ║
# ║ lần cấp quyền lại. Ghi đè vô điều kiện là xoá mất cái đang dùng    ║
# ║ được — người dùng bị đá ra ngay khi access token hết hạn, mà không ║
# ║ có lỗi nào xuất hiện lúc gây ra.                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.connected_account import ACTIVE, REVOKED
from app.repo import connected_account_repo as repo


def _mem_db():
    from app.core.db import Base
    import app.models.user               # noqa: F401 — đích của khoá ngoại
    import app.models.connected_account  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    db = sessionmaker(bind=eng)()
    from app.models.user import User
    for uid in (1, 2):
        db.add(User(id=uid, email=f"u{uid}@x.vn", name=f"U{uid}", initial="U"))
    db.commit()
    return db


def _noi(db, user_id=1, provider="google", puid="g-001", **kw):
    return repo.upsert(db, user_id=user_id, provider=provider, provider_user_id=puid,
                       email_address=kw.pop("email", "a@gmail.com"), **kw)


# ── FR-01.2: một người nối được nhiều hộp thư ───────────────────────────────
def test_noi_duoc_hai_hop_thu_khac_nha_cung_cap():
    db = _mem_db()
    g = _noi(db, provider="google", puid="g-1", email="a@gmail.com")
    o = _noi(db, provider="microsoft", puid="m-1", email="a@outlook.com")

    ds = repo.list_for_user(db, 1)
    assert len(ds) == 2
    assert {x.provider for x in ds} == {"google", "microsoft"}
    assert g.account_id != o.account_id


def test_noi_lai_cung_hop_thu_khong_tao_ban_ghi_thu_hai():
    """Nối hai lần mà đẻ hai bản ghi thì đồng bộ chạy hai lượt, thư về gấp đôi."""
    db = _mem_db()
    a1 = _noi(db, puid="g-1")
    a2 = _noi(db, puid="g-1", email="doi-ten@gmail.com")

    assert a1.account_id == a2.account_id
    assert len(repo.list_for_user(db, 1)) == 1
    assert a2.email_address == "doi-ten@gmail.com", "Nối lại phải cập nhật thông tin mới"


def test_moi_nha_cung_cap_co_bang_con_rieng():
    db = _mem_db()
    g = _noi(db, provider="google", puid="g-1")
    o = _noi(db, provider="microsoft", puid="m-1")

    from app.models.connected_account import GmailAccount, OutlookAccount
    assert isinstance(repo.sync_state(db, g), GmailAccount)
    assert isinstance(repo.sync_state(db, o), OutlookAccount)


def test_con_tro_dong_bo_cua_hai_ben_khong_lan_nhau():
    """history_id của Gmail và delta_link của Outlook phải nằm hai chỗ riêng."""
    db = _mem_db()
    g = repo.sync_state(db, _noi(db, provider="google", puid="g-1"))
    o = repo.sync_state(db, _noi(db, provider="microsoft", puid="m-1"))

    g.history_id = "123456"
    o.delta_link = "https://graph.microsoft.com/delta?token=abc"
    db.commit()

    assert g.history_id == "123456" and not hasattr(g, "delta_link")
    assert o.delta_link.endswith("abc") and not hasattr(o, "history_id")


# ── Chỗ dễ hỏng nhất: refresh_token ─────────────────────────────────────────
def test_cap_quyen_lai_khong_lam_mat_refresh_token_dang_dung():
    """Google không trả refresh token ở lần cấp quyền lại. Nếu ghi đè vô điều kiện
    thì cái đang dùng được bị xoá — và không có lỗi nào xuất hiện lúc đó, người dùng
    chỉ bị đá ra khi access token hết hạn, hàng giờ sau."""
    db = _mem_db()
    _noi(db, puid="g-1", access_token="at-1", refresh_token="rt-GIU-LAY")

    # Lần cấp quyền lại: chỉ có access token mới, không có refresh token
    a = _noi(db, puid="g-1", access_token="at-2", refresh_token=None)

    assert a.access_token == "at-2"
    assert a.refresh_token == "rt-GIU-LAY", "Refresh token đang dùng được đã bị xoá mất"


def test_co_refresh_token_moi_thi_ghi_de():
    db = _mem_db()
    _noi(db, puid="g-1", refresh_token="rt-cu")
    a = _noi(db, puid="g-1", refresh_token="rt-moi")
    assert a.refresh_token == "rt-moi"


# ── UC002: thu hồi quyền ────────────────────────────────────────────────────
def test_thu_hoi_xoa_token_nhung_giu_ban_ghi():
    """Xoá bản ghi là mất luôn dấu vết ai đã làm gì trên hộp thư nào."""
    db = _mem_db()
    a = _noi(db, puid="g-1", access_token="at", refresh_token="rt")
    repo.revoke(db, a)

    assert a.status == REVOKED
    assert a.access_token is None and a.refresh_token is None
    assert repo.get_owned(db, a.account_id, 1) is not None, "Bản ghi phải còn"
    assert repo.list_for_user(db, 1) == [], "Nhưng không còn trong danh sách đang hoạt động"


def test_thu_hoi_mot_hop_thu_khong_dung_toi_hop_thu_kia():
    db = _mem_db()
    g = _noi(db, provider="google", puid="g-1")
    _noi(db, provider="microsoft", puid="m-1")
    repo.revoke(db, g)

    con_lai = repo.list_for_user(db, 1)
    assert len(con_lai) == 1 and con_lai[0].provider == "microsoft"


def test_noi_lai_sau_khi_thu_hoi_thi_song_lai():
    db = _mem_db()
    a = _noi(db, puid="g-1")
    repo.revoke(db, a)
    b = _noi(db, puid="g-1", access_token="at-moi")

    assert b.account_id == a.account_id and b.status == ACTIVE


# ── Quyền sở hữu ────────────────────────────────────────────────────────────
def test_nguoi_khac_khong_cham_duoc_hop_thu_cua_minh():
    db = _mem_db()
    a = _noi(db, user_id=1, puid="g-1")
    assert repo.get_owned(db, a.account_id, user_id=2) is None
    assert repo.get_owned(db, a.account_id, user_id=1) is not None


def test_hop_thu_mac_dinh_la_cai_noi_som_nhat():
    """Nối thêm hộp thư phụ không được lặng lẽ đổi hộp thư chính đang dùng hằng ngày."""
    db = _mem_db()
    dau = _noi(db, provider="google", puid="g-1")
    _noi(db, provider="microsoft", puid="m-1")
    assert repo.primary_for(db, 1).account_id == dau.account_id
    assert repo.primary_for(db, 1, provider="microsoft").provider == "microsoft"


# ── Phạm vi quyền (FR-05.2) ─────────────────────────────────────────────────
def test_luu_va_thay_the_pham_vi_quyen():
    db = _mem_db()
    a = _noi(db, puid="g-1", scopes=["gmail.readonly", "gmail.readonly", "gmail.send"])
    assert sorted(repo.scopes_of(db, a.account_id)) == ["gmail.readonly", "gmail.send"]

    _noi(db, puid="g-1", scopes=["gmail.modify"])
    assert repo.scopes_of(db, a.account_id) == ["gmail.modify"], "Cấp quyền lại phải THAY THẾ, không cộng dồn"


def test_khuon_tra_ra_ngoai_khong_lo_token():
    db = _mem_db()
    a = _noi(db, puid="g-1", access_token="at-bi-mat", refresh_token="rt-bi-mat")
    d = repo.to_dict(a)
    assert "at-bi-mat" not in str(d) and "rt-bi-mat" not in str(d)
    assert d["provider"] == "google" and d["status"] == ACTIVE


def test_lam_moi_token_cap_nhat_ca_han():
    db = _mem_db()
    a = _noi(db, puid="g-1", access_token="cu")
    han = datetime(2026, 8, 9, 12, 0)
    repo.update_access_token(db, a, "moi", han)
    assert a.access_token == "moi" and a.token_expiry == han
