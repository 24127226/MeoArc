"""
test_agent.py — Bộ kiểm thử HỢP ĐỒNG (contract tests) cho MeoArc AI Email Agent.

Kiểm tra endpoint  POST http://localhost:8000/agent/chat  trả JSON khớp schema PresentReply
(agent_node.py): kind ∈ {text, result, digest, triage}; tên trường + kiểu `list` đúng theo kind.

CÁCH CHẠY
  1) uv add --dev pytest pytest-asyncio          # cài công cụ test (httpx đã có sẵn)
  2) uv run main.py                              # chạy backend ở cổng 8000
  3) Đăng nhập web → DevTools → Application → Cookies → copy cookie phiên, rồi:
        PowerShell:  $env:MEOARC_COOKIE = "session=...."
        bash:        export MEOARC_COOKIE="session=...."
  4) uv run pytest tests/test_agent.py -v

GHI CHÚ KHÁCH QUAN (QA ghi nhận — không giả định logic nội bộ)
  • /agent/chat YÊU CẦU đăng nhập (session cookie). Thiếu cookie → test tự SKIP (không fail oan).
  • Agent dùng LLM (Gemini) nên đầu ra CÓ TÍNH XÁC SUẤT: cùng câu hỏi, 'kind' có thể đổi. Vì vậy
    test KHÔNG ép cứng "digest ⇒ kind==digest" (dễ flaky). Thay vào đó kiểm HỢP ĐỒNG: reply trả về
    kind nào thì các trường tương ứng phải đúng TÊN + đúng KIỂU. (Đặt STRICT_KIND=1 để ép cứng kind.)
  • Nếu hết quota / khoá / model quá tải, agent trả thẻ 'text' báo lỗi → test SKIP (đây là lỗi hạ
    tầng, không phải lỗi hợp đồng).
"""

import os
import pytest
import httpx

BASE_URL = os.environ.get("MEOARC_BASE_URL", "http://localhost:8000")
COOKIE = os.environ.get("MEOARC_COOKIE", "")
STRICT_KIND = os.environ.get("STRICT_KIND", "") == "1"

# 4 giá trị hợp lệ DUY NHẤT của trường 'kind' (theo Literal trong PresentReply).
VALID_KINDS = {"text", "result", "digest", "triage"}

# Dấu hiệu agent KHÔNG chạy được (quota/khoá/quá tải) → nên SKIP thay vì FAIL.
_UNAVAILABLE = ("quota", "hết lượt", "trục trặc", "quá tải", "503", "chưa được cấp khoá")

pytestmark = pytest.mark.asyncio  # mọi test async (cần pytest-asyncio)


@pytest.fixture()
def headers() -> dict:
    if not COOKIE:
        pytest.skip("Chưa set MEOARC_COOKIE (cookie đăng nhập) → bỏ qua test gọi API thật.")
    return {"Cookie": COOKIE, "Content-Type": "application/json"}


async def ask(message: str, headers: dict) -> dict:
    """Giả lập gửi MỘT câu lệnh người dùng tới /agent/chat, trả về JSON reply."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        resp = await client.post("/agent/chat", json={"message": message}, headers=headers)
    assert resp.status_code == 200, f"Mong HTTP 200, nhận {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    assert isinstance(data, dict), "Reply phải là JSON object"
    return data


def skip_if_unavailable(data: dict) -> None:
    blob = f"{data.get('text', '')} {data.get('intro', '')}".lower()
    if data.get("kind") == "text" and any(m in blob for m in _UNAVAILABLE):
        pytest.skip(f"Agent tạm không khả dụng (hạ tầng): {blob[:90]}")


def assert_common(data: dict) -> str:
    """Hợp đồng CHUNG: reply phải có 'kind' hợp lệ. Trả về kind."""
    assert "kind" in data, "Reply thiếu trường bắt buộc 'kind'"
    kind = data["kind"]
    assert kind in VALID_KINDS, f"'kind' không hợp lệ: {kind!r} — phải ∈ {VALID_KINDS}"
    return kind


def assert_structure(data: dict) -> None:
    """Kiểm HỢP ĐỒNG theo từng kind: đúng TÊN trường (không sai 1 ký tự) + đúng KIỂU list."""
    kind = data["kind"]
    if "intro" in data:
        assert isinstance(data["intro"], str), "'intro' phải là chuỗi"

    if kind == "result":
        assert "lines" in data, "kind=result phải có 'lines'"
        assert isinstance(data["lines"], list), "'lines' phải là kiểu list"
        assert all(isinstance(x, str) for x in data["lines"]), "mỗi phần tử 'lines' phải là chuỗi"
        assert isinstance(data.get("title", ""), str), "'title' phải là chuỗi"

    elif kind == "digest":
        for key in ("stats", "breakdown", "highlights"):
            assert key in data, f"kind=digest phải có '{key}'"
            assert isinstance(data[key], list), f"'{key}' phải là kiểu list"
        for s in data["stats"]:
            assert {"label", "value"} <= set(s), "mỗi 'stats' item phải có 'label' và 'value'"
            assert isinstance(s["label"], str), "stats.label phải là chuỗi"
            assert isinstance(s["value"], int), "stats.value phải là số nguyên"
        for b in data["breakdown"]:
            assert {"label", "count"} <= set(b), "mỗi 'breakdown' item phải có 'label' và 'count'"

    elif kind == "triage":
        assert "groups" in data, "kind=triage phải có 'groups'"
        assert isinstance(data["groups"], list), "'groups' phải là kiểu list"
        for g in data["groups"]:
            assert g.get("level") in ("high", "normal"), "group.level phải ∈ {high, normal}"
            assert isinstance(g.get("label"), str), "group.label phải là chuỗi"
            assert isinstance(g.get("items"), list), "group.items phải là kiểu list"
            for it in g["items"]:
                assert {"sender", "initial", "subject", "suggest"} <= set(it), (
                    "mỗi triage item phải có đủ sender/initial/subject/suggest"
                )

    elif kind == "text":
        assert "text" in data, "kind=text phải có 'text'"
        assert isinstance(data["text"], str), "'text' phải là chuỗi"


# ══════════════════════════ TEST CASES ══════════════════════════════

async def test_reply_kind_always_valid(headers):
    """[#1] Mọi reply phải có 'kind' thuộc đúng enum {text,result,digest,triage}."""
    data = await ask("Chào MeoArc, bạn khỏe không?", headers)
    assert_common(data)
    assert_structure(data)


async def test_uc01_digest_contract(headers):
    """[UC-01] Digest — yêu cầu thống kê → kiểm hợp đồng: stats/breakdown/highlights là list."""
    data = await ask("Thống kê hộp thư: đếm thư chưa đọc và điểm qua vài thư nổi bật hôm nay", headers)
    skip_if_unavailable(data)
    kind = assert_common(data)
    assert_structure(data)
    if STRICT_KIND:
        assert kind == "digest", f"[STRICT] mong 'digest', nhận {kind!r}"


async def test_uc02_triage_contract(headers):
    """[UC-02] Triage — phân loại ưu tiên → kiểm hợp đồng: groups là list, level ∈ high/normal."""
    data = await ask("Phân loại email trong hộp thư theo mức độ ưu tiên xử lý (cao/thường)", headers)
    skip_if_unavailable(data)
    kind = assert_common(data)
    assert_structure(data)
    if STRICT_KIND:
        assert kind == "triage", f"[STRICT] mong 'triage', nhận {kind!r}"


async def test_result_contract(headers):
    """[UC-01] Liệt kê — 'lines' phải là mảng list[str]."""
    data = await ask("Liệt kê 5 email mới nhất trong hộp thư", headers)
    skip_if_unavailable(data)
    kind = assert_common(data)
    assert_structure(data)
    if STRICT_KIND:
        assert kind == "result", f"[STRICT] mong 'result', nhận {kind!r}"


async def test_uc03_send_safe_reply(headers):
    """[UC-03] Send — lệnh gửi thư phải trả reply HỢP LỆ (agent xin xác nhận trước — human-in-the-loop),
    tuyệt đối không vỡ hợp đồng / trả 500."""
    data = await ask('Gửi email tới test@example.com tiêu đề "QA" nội dung "kiểm thử tự động"', headers)
    skip_if_unavailable(data)
    assert_common(data)
    assert_structure(data)


async def test_field_names_no_typo(headers):
    """[#2] Tên trường phải KHỚP CHÍNH XÁC PresentReply — không có biến thể sai chính tả."""
    data = await ask("Cho mình xin thống kê nhanh tình trạng hộp thư", headers)
    skip_if_unavailable(data)
    kind = assert_common(data)
    typos = {"stat", "group", "line", "breakdowns", "highlight", "intros", "titles"}
    assert typos.isdisjoint(data.keys()), f"Có tên trường sai chính tả: {typos & set(data.keys())}"
    if kind == "digest":
        assert {"stats", "breakdown", "highlights"} <= set(data), "digest phải đủ 3 tên chuẩn"
