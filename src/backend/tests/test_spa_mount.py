# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_spa_mount.py — backend phục vụ luôn frontend            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Bộ bắt-tất-cả phục vụ SPA là con dao hai lưỡi. Nó PHẢI trả         ║
# ║ index.html cho đường dẫn của React Router, nhưng TUYỆT ĐỐI không   ║
# ║ được nuốt API. Nuốt nhầm thì hỏng theo kiểu tệ nhất: lệnh gọi API  ║
# ║ nhận về HTML kèm mã 200, client cố đọc JSON rồi ngã ở chỗ khác     ║
# ║ hẳn, và người sửa lỗi đi tìm nhầm hướng hàng giờ.                  ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.spa import gan_frontend


@pytest.fixture()
def dist(tmp_path: Path) -> Path:
    """Thư mục build giả — chỉ cần index.html là đủ để coi như đã build."""
    d = tmp_path / "dist"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    (d / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    (d / "favicon.ico").write_text("x", encoding="utf-8")
    return d


def _app(dist: Path | None) -> FastAPI:
    """App tối giản: một route API, rồi mới gắn SPA — đúng thứ tự như app.py thật."""
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/emails")
    def emails():
        from fastapi import HTTPException
        raise HTTPException(401, "Chưa đăng nhập")

    gan_frontend(app, str(dist) if dist else "/khong/ton/tai")
    return app


# ── Chưa build thì không được đụng gì tới app ───────────────────────────────
def test_chua_build_thi_backend_chay_y_nhu_cu():
    """Vercel vẫn là đường chính. Không có thư mục build thì phải lặng lẽ bỏ qua,
    không nổ, và KHÔNG thêm route nào."""
    app = _app(None)
    c = TestClient(app)

    assert c.get("/health").status_code == 200
    # Không có bộ bắt-tất-cả → đường lạ phải là 404 của FastAPI
    assert c.get("/app").status_code == 404


def test_bao_dung_co_gan_hay_khong(dist):
    assert gan_frontend(FastAPI(), str(dist)) is True
    assert gan_frontend(FastAPI(), "/khong/ton/tai") is False


# ── Đã build: SPA chạy nhưng KHÔNG được nuốt API ────────────────────────────
def test_duong_dan_react_router_tra_ve_trang_ung_dung(dist):
    c = TestClient(_app(dist))
    for p in ("/app", "/settings", "/app/hop-thu/123"):
        r = c.get(p)
        assert r.status_code == 200, p
        assert "text/html" in r.headers["content-type"], p
        assert "id=root" in r.text, p


def test_api_van_tra_json_chu_khong_phai_html(dist):
    """Phép thử quan trọng nhất file này. Sai chỗ này là hỏng âm thầm."""
    c = TestClient(_app(dist))

    r = c.get("/health")
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    assert r.json()["status"] == "ok"


def test_api_loi_van_giu_nguyen_ma_loi(dist):
    """401 phải ra 401. Nếu bộ bắt-tất-cả nuốt mất thì client nhận HTML 200 và
    tưởng là đăng nhập thành công."""
    c = TestClient(_app(dist))
    r = c.get("/emails")

    assert r.status_code == 401
    assert "application/json" in r.headers["content-type"]


def test_endpoint_api_khong_ton_tai_tra_404_chu_khong_phai_trang(dist):
    """Tiền tố API viết đúng nhưng không có route → 404 thật, không trả HTML."""
    c = TestClient(_app(dist))
    r = c.get("/agent/khong-co-endpoint-nay")

    assert r.status_code == 404
    assert "text/html" not in r.headers.get("content-type", "")


# ── Tệp tĩnh ────────────────────────────────────────────────────────────────
def test_tep_o_goc_thu_muc_build_phuc_vu_duoc(dist):
    c = TestClient(_app(dist))
    assert c.get("/favicon.ico").status_code == 200


def test_khong_doc_trom_duoc_tep_ngoai_thu_muc_build(dist, tmp_path):
    """Path traversal: `../` leo ra ngoài dist đọc tệp hệ thống. Cổ điển và chết người."""
    (tmp_path / "bi-mat.txt").write_text("TOKEN_ENCRYPTION_KEY=...", encoding="utf-8")
    c = TestClient(_app(dist))

    r = c.get("/../bi-mat.txt")
    assert "TOKEN_ENCRYPTION_KEY" not in r.text
