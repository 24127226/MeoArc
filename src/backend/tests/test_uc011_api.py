"""test_uc011_api.py — UC011 (lịch sử hội thoại) qua HTTP THẬT: ngữ nghĩa REST + quyền sở hữu.

TÍNH KHÁCH QUAN — chuẩn lấy từ 2 nguồn độc lập với code backend:
  (1) Hợp đồng FE: frontend/src/lib/api.ts — ConversationSummary{id,title,pinned,updatedAt,
      messageCount,preview}, ConversationDetail{...,createdAt,messages}, StoredMessage{role,...}.
      FE đọc ĐÚNG các tên này (camelCase); backend trả khác tên là drawer vỡ.
  (2) Ngữ nghĩa REST + SRS: PATCH phải BỀN (GET sau đó thấy thay đổi); DELETE xong GET → 404;
      user KHÁC không được đọc phiên của mình (agent chỉ hành động "trong phạm vi quyền user cấp").

Setup dùng DB trực tiếp (seed phiên + user thứ hai) — chỉ là DÀN CẢNH; mọi ASSERT đều nhắm
vào endpoint HTTP công khai. Server tắt / chưa đăng nhập → SKIP nêu rõ (không pass ẩn).

Chạy: uv run main.py  (cửa sổ khác)  →  uv run pytest tests/test_uc011_api.py -v
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest

BASE_URL = os.environ.get("MEOARC_BASE_URL", "http://localhost:8000")

# Tên field FE đọc (chép tay từ frontend/src/lib/api.ts) — sai 1 ký tự là FAIL.
FE_SUMMARY_FIELDS = {"id", "title", "pinned", "updatedAt", "messageCount", "preview"}
FE_DETAIL_FIELDS = {"id", "title", "pinned", "createdAt", "updatedAt", "messages"}


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture(scope="module")
def env():
    """Dàn cảnh: user A (phiên đăng nhập thật mới nhất) + 1 phiên hội thoại seed
    + user B tạm (để kiểm quyền sở hữu). Dọn sạch sau khi chạy xong module."""
    try:
        from app.core.db import SessionLocal
        from app.models.user import User
        from app.models.session import AuthSession
        from app.repo import conversation_repo
    except Exception as exc:
        pytest.skip(f"Không import được app/DB: {exc}")

    # server phải đang chạy
    try:
        httpx.get(f"{BASE_URL}/docs", timeout=5)
    except httpx.ConnectError:
        pytest.skip(f"Server không chạy tại {BASE_URL} — bật `uv run main.py` trước.")

    db = SessionLocal()
    now = _utcnow()
    live = [s for s in db.query(AuthSession).all() if s.expires_at and s.expires_at > now]
    live.sort(key=lambda s: s.expires_at, reverse=True)
    if not live:
        db.close()
        pytest.skip("DB không có phiên đăng nhập sống — đăng nhập web trước khi chạy.")
    sess_a = live[0]

    # seed 1 phiên hội thoại cho user A (nội dung tối thiểu đúng khuôn StoredMessage)
    conv = conversation_repo.get_or_create(db, None, sess_a.user_id)
    conversation_repo.save_turn(
        db, conv, agent_messages=[],
        display_messages=[{"role": "user", "text": "câu hỏi seed"},
                          {"role": "agent", "reply": {"kind": "text", "text": "trả lời seed"}}],
        first_user_text="phiên seed để kiểm thử UC011",
    )

    # user B tạm + phiên đăng nhập B (chỉ để gọi API bằng danh tính khác)
    ub_email = f"qa-uc011-{uuid.uuid4().hex[:8]}@test.local"
    user_b = User(email=ub_email, name="QA Bot", initial="Q", created_at=now)
    db.add(user_b); db.commit(); db.refresh(user_b)
    tok_b = "qa-" + uuid.uuid4().hex
    db.add(AuthSession(token=tok_b, user_id=user_b.id, expires_at=now + timedelta(hours=1)))
    db.commit()

    data = {"tok_a": sess_a.token, "tok_b": tok_b, "conv_id": conv.id, "user_b_id": user_b.id}
    yield data

    # ── dọn dẹp ──
    try:
        from app.models.conversation import Conversation
        db.expire_all()  # bỏ cache ORM: conv có thể đã bị test DELETE qua API rồi
        c = db.get(Conversation, data["conv_id"])
        if c:
            db.delete(c)
        sb = db.get(AuthSession, tok_b)
        if sb:
            db.delete(sb)
        ub = db.get(User, data["user_b_id"])
        if ub:
            db.delete(ub)
        db.commit()
    finally:
        db.close()


def _client(token: str) -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30,
                        headers={"Authorization": f"Bearer {token}"})


def test_list_dung_khuon_fe(env):
    """GET /agent/conversations: phiên seed có mặt; mỗi dòng đủ ĐÚNG TÊN field FE cần."""
    with _client(env["tok_a"]) as c:
        r = c.get("/agent/conversations")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    mine = [x for x in rows if x.get("id") == env["conv_id"]]
    assert mine, "Phiên vừa seed không xuất hiện trong danh sách của chính chủ"
    row = mine[0]
    missing = FE_SUMMARY_FIELDS - set(row)
    assert not missing, f"Thiếu field FE cần (api.ts ConversationSummary): {sorted(missing)}"
    assert isinstance(row["pinned"], bool)
    assert isinstance(row["messageCount"], int) and row["messageCount"] == 2
    assert isinstance(row["preview"], str) and row["preview"], "preview rỗng — drawer trắng dòng"


def test_detail_dung_khuon_fe(env):
    with _client(env["tok_a"]) as c:
        r = c.get(f"/agent/conversations/{env['conv_id']}")
    assert r.status_code == 200
    d = r.json()
    missing = FE_DETAIL_FIELDS - set(d)
    assert not missing, f"Thiếu field FE cần (api.ts ConversationDetail): {sorted(missing)}"
    assert len(d["messages"]) == 2
    roles = [m.get("role") for m in d["messages"]]
    assert roles == ["user", "agent"], f"StoredMessage.role phải là user/agent, nhận {roles}"
    assert d["messages"][1]["reply"]["kind"] == "text"


def test_patch_ben_vung(env):
    """PATCH đổi tên + ghim → GET lại PHẢI thấy thay đổi (REST: cập nhật là bền)."""
    with _client(env["tok_a"]) as c:
        r = c.patch(f"/agent/conversations/{env['conv_id']}",
                    json={"title": "Đã đổi tên QA", "pinned": True})
        assert r.status_code == 200
        r2 = c.get(f"/agent/conversations/{env['conv_id']}")
    d = r2.json()
    assert d["title"] == "Đã đổi tên QA", "PATCH title không bền — GET lại vẫn tên cũ"
    assert d["pinned"] is True, "PATCH pinned không bền"


def test_quyen_so_huu_user_khac_khong_doc_duoc(env):
    """User B không được đọc/sửa/xoá phiên của user A (an toàn dữ liệu — SRS)."""
    with _client(env["tok_b"]) as c:
        assert c.get(f"/agent/conversations/{env['conv_id']}").status_code == 404, \
            "User khác ĐỌC ĐƯỢC phiên không phải của mình — lỗ hổng dữ liệu!"
        assert c.patch(f"/agent/conversations/{env['conv_id']}",
                       json={"title": "hack"}).status_code == 404
        assert c.delete(f"/agent/conversations/{env['conv_id']}").status_code == 404
        # và danh sách của B không chứa phiên của A
        rows = c.get("/agent/conversations").json()
        assert all(x["id"] != env["conv_id"] for x in rows)


def test_delete_xong_404(env):
    """DELETE 204 → GET lại phải 404 (đã xoá là mất khỏi tài nguyên công khai)."""
    with _client(env["tok_a"]) as c:
        assert c.delete(f"/agent/conversations/{env['conv_id']}").status_code == 204
        assert c.get(f"/agent/conversations/{env['conv_id']}").status_code == 404
