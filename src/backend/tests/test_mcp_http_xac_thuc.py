"""MCP QUA HTTP — cửa phải THẬT SỰ khoá.

Mở MCP ra HTTP là ném đi tiền đề đã cho phép bản stdio không cần xác thực ("agent chạy
cùng máy nên vốn đã có quyền trên máy đó"). Từ lúc địa chỉ nằm trên mạng, mọi giả định
cũ phải được kiểm lại bằng test, vì cái giá của một lỗ ở đây là hộp thư thật của người
dùng — không phải một màn hình vẽ sai.

Bộ này kiểm đúng những chỗ dễ sai mà tự thử một mình KHÔNG BAO GIỜ lộ ra:
  • thẻ lưu dạng băm, không lưu bản gốc
  • thẻ hết hạn / bị thu hồi thì hết hiệu lực NGAY
  • thẻ của người này KHÔNG thu hồi được thẻ của người kia
  • cache ngữ cảnh tách theo NGƯỜI (bản trước là một ô nhớ chung — hai người gọi gần
    nhau là người sau thao tác hộp thư người trước)
  • lối tắt env MEOARC_ACCESS_TOKEN KHÔNG được áp cho đường HTTP
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.repo import mcp_token_repo


def _mem_db():
    from app.core.db import Base
    import app.models.user  # noqa: F401
    import app.models.mcp_token  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


@pytest.fixture()
def db():
    from app.models.user import User

    d = _mem_db()
    d.add(User(id=1, email="a@example.com", name="A", initial="A"))
    d.add(User(id=2, email="b@example.com", name="B", initial="B"))
    d.commit()
    return d


# ── Thẻ: lưu trữ và vòng đời ────────────────────────────────────────────────

def test_CSDL_khong_giu_the_goc(db):
    """Lộ CSDL không được kéo theo lộ mọi hộp thư."""
    row, raw = mcp_token_repo.tao(db, 1, "máy nhà")
    assert row.token_hash != raw
    assert raw not in row.token_hash
    assert len(row.token_hash) == 64            # sha256 hex
    # Tiền tố lưu lại chỉ để NHẬN RA thẻ, phải quá ngắn để đoán ngược.
    assert row.tien_to and len(row.tien_to) < len(raw) // 2
    assert raw.startswith(mcp_token_repo.TIEN_TO)


def test_the_dung_thi_ra_dung_nguoi(db):
    row, raw = mcp_token_repo.tao(db, 2, "codex")
    ra = mcp_token_repo.xac_thuc(db, raw)
    assert ra is not None and ra.user_id == 2


def test_the_sai_bi_tu_choi(db):
    mcp_token_repo.tao(db, 1)
    assert mcp_token_repo.xac_thuc(db, "meoarc_mcp_saibet") is None
    assert mcp_token_repo.xac_thuc(db, "") is None
    assert mcp_token_repo.xac_thuc(db, "khong-co-tien-to") is None


def test_thu_hoi_co_hieu_luc_NGAY(db):
    row, raw = mcp_token_repo.tao(db, 1)
    assert mcp_token_repo.xac_thuc(db, raw) is not None
    assert mcp_token_repo.thu_hoi(db, 1, row.id) is True
    assert mcp_token_repo.xac_thuc(db, raw) is None, "thu hồi mà vẫn dùng được thì vô nghĩa"


def test_the_het_han_thi_het_hieu_luc(db):
    row, raw = mcp_token_repo.tao(db, 1)
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    assert mcp_token_repo.xac_thuc(db, raw) is None


def test_KHONG_thu_hoi_duoc_the_cua_NGUOI_KHAC(db):
    """Chỗ này là cửa sau trông rất vô hại khi đọc lướt: thiếu điều kiện user_id thì
    đoán số id là vô hiệu hoá được thẻ của bất kỳ ai."""
    row, raw = mcp_token_repo.tao(db, 1, "của người 1")
    assert mcp_token_repo.thu_hoi(db, 2, row.id) is False
    assert mcp_token_repo.xac_thuc(db, raw) is not None, "thẻ người 1 phải còn nguyên"


def test_han_luon_nam_trong_khoang_cho_phep(db):
    """Không có thẻ vô hạn, và cũng không có thẻ chết ngay lúc sinh ra.

    `so_ngay=0` được đọc là "không truyền" → về mặc định, chứ không phải "hết hạn tức
    thì": một thẻ hết hạn ngay lúc tạo là thứ không ai cố ý muốn, và im lặng phát ra
    một thẻ chết thì người dùng chỉ phát hiện lúc nó không chạy.
    """
    r_mac_dinh, _ = mcp_token_repo.tao(db, 1, so_ngay=0)
    r_am, _ = mcp_token_repo.tao(db, 1, so_ngay=-5)
    r_dai, _ = mcp_token_repo.tao(db, 1, so_ngay=99999)

    assert (r_mac_dinh.expires_at - r_mac_dinh.created_at).days == mcp_token_repo.HAN_MAC_DINH
    assert (r_am.expires_at - r_am.created_at).days >= 1, "số âm phải kẹp lên, không tạo thẻ chết"
    assert (r_dai.expires_at - r_dai.created_at).days <= mcp_token_repo.HAN_TOI_DA


def test_moi_the_moi_moi_lan_MOT_khac(db):
    _, a = mcp_token_repo.tao(db, 1)
    _, b = mcp_token_repo.tao(db, 1)
    assert a != b


def test_liet_ke_chi_thay_the_cua_MINH(db):
    mcp_token_repo.tao(db, 1, "một")
    mcp_token_repo.tao(db, 2, "hai")
    assert [r.ten for r in mcp_token_repo.liet_ke(db, 1)] == ["một"]


# ── Cửa xác thực cắm vào FastMCP ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cua_xac_thuc_tra_ve_dung_chu_the(db, monkeypatch):
    from app.mcp import xac_thuc as X

    monkeypatch.setattr(X, "SessionLocal", lambda: db)
    _, raw = mcp_token_repo.tao(db, 2, "codex")
    at = await X.XacThucBangThe().verify_token(raw)
    assert at is not None
    assert at.subject == "2", "subject là mắt xích DUY NHẤT nối yêu cầu HTTP với người dùng"


@pytest.mark.asyncio
async def test_cua_xac_thuc_tu_choi_the_sai(db, monkeypatch):
    from app.mcp import xac_thuc as X

    monkeypatch.setattr(X, "SessionLocal", lambda: db)
    assert await X.XacThucBangThe().verify_token("meoarc_mcp_bay-bay") is None


@pytest.mark.asyncio
async def test_CSDL_hong_thi_DONG_cua_chu_khong_mo(monkeypatch):
    """Cửa xác thực 'mở khi có sự cố' là cửa không khoá — mà sự cố thì kẻ tấn công
    tạo ra được."""
    from app.mcp import xac_thuc as X

    def _no():
        raise RuntimeError("DB sập")

    monkeypatch.setattr(X, "SessionLocal", _no)
    assert await X.XacThucBangThe().verify_token("meoarc_mcp_gi-do") is None


# ── Ngữ cảnh: KHÔNG được lẫn giữa người này với người kia ────────────────────

def test_cache_ngu_canh_TACH_theo_nguoi(monkeypatch):
    """Bản trước cache ngữ cảnh trong MỘT ô nhớ dùng chung. Đúng khi cả tiến trình chỉ
    phục vụ một người qua stdio; qua HTTP thì người gọi sau nhận nguyên ngữ cảnh của
    người gọi trước — tức thao tác hộp thư của người khác. Lỗi này không bao giờ lộ ra
    khi tự thử một mình, nên chỉ test giữ được nó.
    """
    from app.mcp import server as S
    from app.tools.registry import RequestContext

    S._CTX_CACHE.clear()
    S._CTX_CACHE["1"] = (RequestContext(user_id="1", access_token="tok-cua-1",
                                        email_provider="google"), 9e18)
    S._CTX_CACHE["2"] = (RequestContext(user_id="2", access_token="tok-cua-2",
                                        email_provider="google"), 9e18)

    monkeypatch.setattr(S, "_uid_tu_http", lambda: 1)
    assert S._resolve_ctx().access_token == "tok-cua-1"
    monkeypatch.setattr(S, "_uid_tu_http", lambda: 2)
    assert S._resolve_ctx().access_token == "tok-cua-2"
    S._CTX_CACHE.clear()


def test_loi_tat_ENV_khong_ap_cho_duong_HTTP(monkeypatch):
    """MEOARC_ACCESS_TOKEN là lối tắt demo cho stdio. Nếu nó cũng ăn trên đường HTTP thì
    đặt một biến môi trường là mọi người mang thẻ khác nhau đều rơi vào chung một hộp
    thư — cả lớp xác thực vừa dựng thành hình thức."""
    from app.mcp import server as S

    monkeypatch.setenv("MEOARC_ACCESS_TOKEN", "token-demo")
    S._CTX_CACHE.clear()

    # stdio (không có thẻ HTTP) → vẫn dùng lối tắt như cũ
    monkeypatch.setattr(S, "_uid_tu_http", lambda: None)
    assert S._resolve_ctx().user_id == "env"

    # HTTP (có thẻ) → PHẢI bỏ qua lối tắt, đi tra phiên của đúng người
    monkeypatch.setattr(S, "_uid_tu_http", lambda: 7)
    monkeypatch.setattr(S, "SessionLocal", lambda: (_ for _ in ()).throw(
        RuntimeError("phải đi đường DB, không được ăn lối tắt env")))
    with pytest.raises(RuntimeError):
        S._resolve_ctx()
    S._CTX_CACHE.clear()


# ── Cờ bật/tắt ──────────────────────────────────────────────────────────────

def test_MAC_DINH_KHONG_mo_HTTP():
    """Mở sẵn là hỏng: người triển khai không chọn bật thì không được có cổng nào mở."""
    from app.core.config import Settings

    assert Settings().mcp_http_enabled is False
    assert Settings().mcp_http_cho_phep_khong_tls is False


def test_bat_co_ma_KHONG_co_TLS_thi_van_khong_mo(monkeypatch):
    """Thẻ Bearer qua HTTP trần là gửi chìa khoá dạng chữ thường cho cả đường truyền."""
    from app.api import app as A

    monkeypatch.setattr(A.settings, "mcp_http_enabled", True, raising=False)
    monkeypatch.setattr(A.settings, "mcp_http_cho_phep_khong_tls", False, raising=False)
    monkeypatch.setattr(A, "_sau_tls", lambda: False)
    monkeypatch.setattr(A, "_MCP_HTTP_DA_MOUNT", False, raising=False)

    goi = []
    monkeypatch.setattr(A.app, "mount", lambda *a, **k: goi.append(a))
    A._gan_mcp_http()
    assert goi == [], "chưa có HTTPS thì không được mount"


# ── ĐẦU-CUỐI qua HTTP thật: không thẻ thì KHÔNG vào được ─────────────────────

def _app_mcp_rieng(db, monkeypatch):
    """Dựng một app RIÊNG chỉ để thử tầng HTTP của MCP.

    Không mount lên `app.api.app` thật: mount là thay đổi toàn cục, làm vậy thì các test
    khác chạy sau sẽ thấy một cổng MCP mở mà chúng không hề dựng — và một cổng mở ngoài
    dự tính là đúng thứ bộ test này tồn tại để ngăn.
    """
    from fastapi import FastAPI
    from app.mcp import xac_thuc as X
    from app.mcp.server import mcp as mcp_server

    monkeypatch.setattr(X, "SessionLocal", lambda: db)
    con = mcp_server.http_app(path="/", transport="http", stateless_http=True)
    # App con có vòng đời riêng; app rỗng này không có on_event nào nên truyền thẳng
    # lifespan vào constructor được (app thật thì không — xem ghi chú ở app/api/app.py).
    ngoai = FastAPI(lifespan=con.lifespan)
    ngoai.mount("/mcp/rpc", con)
    return ngoai


def _goi(client, token: str | None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/mcp/rpc/", json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "0"}},
    }, headers=headers)


def test_HTTP_khong_co_the_thi_bi_chan(db, monkeypatch):
    from fastapi.testclient import TestClient

    with TestClient(_app_mcp_rieng(db, monkeypatch)) as c:
        assert _goi(c, None).status_code == 401


def test_HTTP_the_bay_bi_chan(db, monkeypatch):
    from fastapi.testclient import TestClient

    with TestClient(_app_mcp_rieng(db, monkeypatch)) as c:
        assert _goi(c, "meoarc_mcp_hoan-toan-bia").status_code == 401


def test_HTTP_the_da_THU_HOI_bi_chan_ngay(db, monkeypatch):
    from fastapi.testclient import TestClient

    row, raw = mcp_token_repo.tao(db, 1, "sẽ thu hồi")
    with TestClient(_app_mcp_rieng(db, monkeypatch)) as c:
        assert _goi(c, raw).status_code != 401, "tiền đề: thẻ tốt thì vào được"
        mcp_token_repo.thu_hoi(db, 1, row.id)
        assert _goi(c, raw).status_code == 401, "thu hồi xong phải chặn NGAY, không chờ hết hạn"


def test_HTTP_the_dung_thi_vao_duoc(db, monkeypatch):
    from fastapi.testclient import TestClient

    _, raw = mcp_token_repo.tao(db, 1, "máy nhà")
    with TestClient(_app_mcp_rieng(db, monkeypatch)) as c:
        r = _goi(c, raw)
        assert r.status_code == 200, r.text
        assert "MeoArc" in r.text
