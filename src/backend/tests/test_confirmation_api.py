# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_confirmation_api.py — CHỐNG BẤM TRÙNG Ở TẦNG HTTP      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ test_confirmation.py canh máy trạng thái. Ở đây canh cái người     ║
# ║ dùng thật sự chạm vào: gọi POST /confirmations/{id}/approve HAI    ║
# ║ lần thì hành động chỉ được chạy MỘT lần.                          ║
# ║                                                                    ║
# ║ Tách hai tầng vì máy trạng thái đúng mà endpoint vẫn chạy hành     ║
# ║ động trước khi hỏi nó thì test tầng dưới vẫn xanh, còn thư vẫn đi  ║
# ║ hai lần. Chỉ đếm số lần tool CHẠY THẬT mới kết luận được.          ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import types

import pytest


@pytest.fixture()
def app_client(monkeypatch):
    """App thật + phiên đăng nhập giả + tool send_email bị thay bằng bộ đếm."""
    try:
        from fastapi.testclient import TestClient
        from app.api.app import app
        from app.core import deps
    except Exception as exc:                       # pragma: no cover
        pytest.skip(f"Không import được app (DB tắt?): {exc}")

    fake = types.SimpleNamespace(user_id=515151, token="qa")
    app.dependency_overrides[deps.get_current_session] = lambda: fake
    app.dependency_overrides[deps.get_gmail_token] = lambda: "fake-token"

    dem = {"n": 0}

    async def gia_lap_call(name, args, ctx):
        dem["n"] += 1
        return {"success": True, "message": f"đã chạy {name}", "lan": dem["n"]}

    import app.api.app as app_mod
    from app.tools.registry import tool_registry
    monkeypatch.setattr(tool_registry, "call", gia_lap_call)
    # Ghi nhật ký chạm database thật — không phải thứ đang kiểm ở đây.
    monkeypatch.setattr(app_mod, "_record", lambda *a, **k: None)

    with TestClient(app) as c:
        yield c, dem, fake
    app.dependency_overrides.clear()


def _tao_yeu_cau(user_id: int, action="send_email"):
    """Tạo bản ghi chờ duyệt thẳng trong database mà app đang dùng."""
    from app.core.db import SessionLocal
    from app.repo import confirmation_repo

    db = SessionLocal()
    try:
        # user_id phải tồn tại vì bảng có khoá ngoại sang users.
        from app.models.user import User
        if db.get(User, user_id) is None:
            db.add(User(id=user_id, email=f"qa{user_id}@example.test",
                        name="QA", initial="Q"))
            db.commit()
        r = confirmation_repo.create(
            db, user_id=user_id, action=action,
            description="Gửi thư tới thien@example.com?",
            args={"to": ["thien@example.com"], "subject": "Chào", "body": "Nội dung"},
        )
        return r.id
    finally:
        db.close()


def test_bam_duyet_hai_lan_chi_gui_mot_lan(app_client):
    """Lỗi gửi trùng, đo ở tầng HTTP đúng như người dùng gây ra."""
    c, dem, fake = app_client
    rid = _tao_yeu_cau(fake.user_id)

    r1 = c.post(f"/confirmations/{rid}/approve")
    r2 = c.post(f"/confirmations/{rid}/approve")

    assert r1.status_code == 200 and r2.status_code == 200
    assert dem["n"] == 1, f"Hành động chạy {dem['n']} lần — phải đúng 1"

    assert r1.json()["already"] is False
    assert r2.json()["already"] is True, "Lần bấm sau phải được nhận ra là trùng"
    assert r2.json()["result"] == r1.json()["result"], "Phải trả lại đúng kết quả lần đầu"


def test_bam_lien_tuc_nam_lan_van_chi_gui_mot_lan(app_client):
    """Bấm dồn dập — kiểu người dùng sốt ruột khi mạng chậm."""
    c, dem, fake = app_client
    rid = _tao_yeu_cau(fake.user_id)

    ket_qua = [c.post(f"/confirmations/{rid}/approve").json() for _ in range(5)]

    assert dem["n"] == 1
    assert [k["already"] for k in ket_qua] == [False, True, True, True, True]


def test_tu_choi_thi_khong_chay_gi_ca(app_client):
    c, dem, fake = app_client
    rid = _tao_yeu_cau(fake.user_id)

    r = c.post(f"/confirmations/{rid}/reject")
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert dem["n"] == 0, "Từ chối mà vẫn chạy hành động"


def test_tu_choi_roi_thi_duyet_bi_chan(app_client):
    """Đã huỷ thì không ai 'cứu' lại được — kể cả bằng cách gọi thẳng API."""
    c, dem, fake = app_client
    rid = _tao_yeu_cau(fake.user_id)

    c.post(f"/confirmations/{rid}/reject")
    r = c.post(f"/confirmations/{rid}/approve")

    assert r.status_code == 409
    assert dem["n"] == 0


def test_nguoi_khac_khong_duyet_ho_duoc(app_client):
    """Yêu cầu của người khác → 404, và KHÔNG chạy gì.

    Trả 404 chứ không 403: 403 xác nhận 'id này có thật', đủ để dò ra id hợp lệ.
    """
    c, dem, fake = app_client
    rid = _tao_yeu_cau(user_id=fake.user_id + 1)     # của người dùng khác

    r = c.post(f"/confirmations/{rid}/approve")
    assert r.status_code == 404
    assert dem["n"] == 0


def test_id_bia_tra_404(app_client):
    c, dem, _ = app_client
    assert c.post("/confirmations/khong-co-that/approve").status_code == 404
    assert dem["n"] == 0


def test_danh_sach_cho_duyet_khong_lo_noi_dung_thu(app_client):
    c, _, fake = app_client
    _tao_yeu_cau(fake.user_id)

    r = c.get("/confirmations")
    assert r.status_code == 200
    ds = r.json()
    assert ds and all("args" not in x for x in ds), "API đang phơi nội dung thư ra ngoài"
    assert ds[0]["status"] == "pending"
