"""test_nfr.py — Kiểm các Yêu cầu PHI CHỨC NĂNG bằng chuẩn công bố, không phải bằng code.

Chuẩn khách quan:
  * /health: ngữ nghĩa health-check chuẩn production (200 + status/db khi sống).
  * Header bảo mật: khuyến nghị OWASP (nosniff / X-Frame-Options / Referrer-Policy).
  * Rate limit: ngưỡng CÔNG BỐ trong Settings (agent_rate_limit_per_min) phải được cưỡng chế.
  * Upload: trần CÔNG BỐ (upload_max_mb) phải chặn tệp vượt mức bằng HTTP 413.
  * Kho RAM (upload_store, cache Gmail): PHẢI có trần — vượt là phải dọn (chống OOM).
  * tool_node: N tool 1 lượt chạy SONG SONG (tổng thời gian ≈ tool chậm nhất).

Chạy: uv run pytest tests/test_nfr.py -v   (KHÔNG cần server ngoài, KHÔNG tốn quota LLM)
"""

from __future__ import annotations

import asyncio
import time
import types

import pytest


# ─────────────────────── dàn cảnh TestClient (in-process) ───────────────────────
@pytest.fixture()
def client_auth():
    """Endpoint thật trong tiến trình + auth giả (SETUP); assert nhắm hành vi công khai."""
    try:
        from fastapi.testclient import TestClient
        from app.api.app import app
        from app.core import deps
    except Exception as exc:
        pytest.skip(f"Không import được app (DB tắt?): {exc}")
    fake = types.SimpleNamespace(user_id=424242, token="qa")
    app.dependency_overrides[deps.get_current_session] = lambda: fake
    app.dependency_overrides[deps.get_gmail_token] = lambda: "fake-token"
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── Reliability: /health đúng ngữ nghĩa health-check ─────────────────────────
def test_health_song_va_db_up(client_auth):
    r = client_auth.get("/health")
    assert r.status_code == 200, "App + DB đang sống thì /health phải 200"
    body = r.json()
    assert body["status"] == "ok" and body["db"] == "up"
    assert isinstance(body["uptime_s"], int) and body["uptime_s"] >= 0


# ── Security + Observability: header trên MỌI response ──────────────────────
def test_header_bao_mat_va_quan_sat(client_auth):
    r = client_auth.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff", "Thiếu chống MIME-sniffing (OWASP)"
    assert r.headers.get("X-Frame-Options") == "DENY", "Thiếu chống clickjacking (OWASP)"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("X-Request-ID"), "Thiếu request-id → không truy vết được log theo request"
    assert float(r.headers.get("X-Process-Time-Ms", "-1")) >= 0, "Thiếu số đo thời gian xử lý"


# ── Reliability: rate limit theo ngưỡng CÔNG BỐ ──────────────────────────────
def test_rate_limit_dung_nguong_cong_bo(client_auth, monkeypatch):
    from app.core.config import settings
    from app.core.kv import kv
    # Tắt LLM để các lượt hợp lệ trả lời nhanh (nhánh 'chưa cấu hình khoá') — không tốn quota.
    monkeypatch.setattr(settings, "ai_api_key", "")
    monkeypatch.setattr(settings, "local_model_base_url", "")
    kv.delete_prefix("rate:agent:")  # cửa sổ sạch cho test

    limit = settings.agent_rate_limit_per_min
    texts = []
    for _ in range(limit + 2):
        r = client_auth.post("/agent/chat", json={"message": "đếm lượt"})
        assert r.status_code == 200
        texts.append(r.json().get("text", ""))

    over_quota_replies = [t for t in texts if "🐢" in t]
    assert len(over_quota_replies) == 2, (
        f"Ngưỡng công bố {limit}/phút: gửi {limit + 2} lượt thì đúng 2 lượt cuối phải bị chặn, "
        f"thực tế chặn {len(over_quota_replies)}."
    )
    assert all("🐢" not in t for t in texts[:limit]), "Chặn nhầm lượt còn trong hạn mức!"
    kv.delete_prefix("rate:agent:")


# ── Memory/Security: upload vượt trần công bố phải bị 413 ───────────────────
def test_upload_vuot_tran_bi_413(client_auth, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "upload_max_mb", 1)  # hạ trần còn 1MB cho test nhẹ

    big = b"x" * (1024 * 1024 + 1)
    r = client_auth.post("/uploads", files={"file": ("big.bin", big, "application/octet-stream")})
    assert r.status_code == 413, f"Tệp vượt trần phải bị 413, nhận {r.status_code}"

    small = b"y" * 1024
    r2 = client_auth.post("/uploads", files={"file": ("ok.txt", small, "text/plain")})
    assert r2.status_code == 200 and r2.json().get("id"), "Tệp trong hạn mức phải được nhận"


# ── Memory: kho upload TỰ DỌN (TTL + trần tổng dung lượng) ───────────────────
def test_upload_store_co_tran_va_ttl():
    from app.services import upload_store as us
    us._UPLOADS.clear()

    # vượt trần tổng → tệp CŨ NHẤT phải bị bỏ
    chunk = b"z" * (10 * 1024 * 1024)          # 10MB/tệp, trần 25MB
    first = us.save("a.bin", chunk, None)
    us.save("b.bin", chunk, None)
    us.save("c.bin", chunk, None)              # 30MB > 25MB → 'a' bị dọn
    total = sum(len(v["content"]) for v in us._UPLOADS.values())
    assert total <= us._MAX_TOTAL_BYTES, f"Tổng {total}B vượt trần {us._MAX_TOTAL_BYTES}B"
    assert us.get(first["id"]) is None, "Tệp cũ nhất phải bị dọn khi kho chật"

    # quá hạn TTL → get phải trả None (và dọn luôn)
    fid = us.save("old.txt", b"data", None)["id"]
    us._UPLOADS[fid]["ts"] = time.time() - us._TTL_SECONDS - 1
    assert us.get(fid) is None, "Tệp quá hạn TTL vẫn lấy được — kho không tự dọn"
    us._UPLOADS.clear()


# ── Memory: cache Gmail qua KV — hoạt động đúng + token KHÔNG lộ thô trong khoá ──
def test_gmail_cache_qua_kv():
    from app.services import gmail_service as gs

    key = ("list", "secret-token-abc", "inbox", "q")
    gs._cache_set(key, {"v": 1})
    assert gs._cache_get(key) == {"v": 1}, "set xong phải get lại được (trong TTL)"
    assert "secret-token-abc" not in gs._kv_key(key), "Token thô bị lộ trong khoá cache!"

    gs.invalidate_cache("secret-token-abc")
    assert gs._cache_get(key) is None, "invalidate phải xoá sạch cache của đúng người đó"


# ── Observability: LangSmith opt-in đúng công bố (điền key = bật, trống = tắt) ──
def test_langsmith_opt_in(monkeypatch):
    from app.core import llm as llm_mod
    from app.core.config import settings
    for var in ("LANGCHAIN_TRACING_V2", "LANGSMITH_TRACING", "LANGCHAIN_API_KEY",
                "LANGSMITH_API_KEY", "LANGCHAIN_PROJECT", "LANGSMITH_PROJECT"):
        monkeypatch.delenv(var, raising=False)

    # Trống (mặc định) → KHÔNG bật tracing (dữ liệu email không rời máy)
    monkeypatch.setattr(settings, "langsmith_api_key", "")
    llm_mod._enable_langsmith_if_configured()
    import os
    assert "LANGCHAIN_TRACING_V2" not in os.environ, "Chưa điền key mà tracing tự bật!"

    # Điền key → bật, đúng project
    monkeypatch.setattr(settings, "langsmith_api_key", "ls-test-key")
    monkeypatch.setattr(settings, "langsmith_project", "meoarc-test")
    llm_mod._enable_langsmith_if_configured()
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGSMITH_API_KEY") == "ls-test-key"
    assert os.environ.get("LANGCHAIN_PROJECT") == "meoarc-test"
    for var in ("LANGCHAIN_TRACING_V2", "LANGSMITH_TRACING", "LANGCHAIN_API_KEY",
                "LANGSMITH_API_KEY", "LANGCHAIN_PROJECT", "LANGSMITH_PROJECT"):
        monkeypatch.delenv(var, raising=False)


# ── Speed: N tool 1 lượt phải chạy SONG SONG, kết quả giữ đúng thứ tự ────────
def test_tool_node_chay_song_song(monkeypatch):
    import app.agent.nodes.tool_node as tn
    from langchain_core.messages import AIMessage

    DELAY = 0.35

    class SlowRegistry:
        async def call(self, name, args, ctx):
            await asyncio.sleep(DELAY)
            return {"tool": name}

    monkeypatch.setattr(tn, "tool_registry", SlowRegistry())
    ai = AIMessage(content="", tool_calls=[
        {"name": "t1", "args": {}, "id": "id1"},
        {"name": "t2", "args": {}, "id": "id2"},
        {"name": "t3", "args": {}, "id": "id3"},
    ])
    state = {"messages": [ai], "request_ctx": None}

    t0 = time.perf_counter()
    out = asyncio.run(tn.tool_node(state))
    elapsed = time.perf_counter() - t0

    assert elapsed < DELAY * 2.2, (
        f"3 tool x {DELAY}s mất {elapsed:.2f}s — vẫn chạy TUẦN TỰ (song song phải ≈ {DELAY}s)"
    )
    ids = [m.tool_call_id for m in out["messages"]]
    assert ids == ["id1", "id2", "id3"], f"Sai thứ tự kết quả: {ids} — LLM sẽ ghép nhầm tool"
