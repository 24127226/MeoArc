"""test_agent.py — Bộ kiểm thử BLACK-BOX THẬT cho AI Email Agent MeoArc (QA độc lập).

GỌI HTTP THẬT tới `POST /agent/chat` — KHÔNG mock phản hồi. Căn cứ DUY NHẤT:
    (1) Đặc tả UC: UC-01 Digest, UC-02 Triage, UC-03 Send/Reply.
    (2) Hợp đồng đầu ra PresentReply (§2 đặc tả QA).
KHÔNG giả định logic nội bộ; KHÔNG viết test "cho khớp code" — kind sai với yêu cầu là FAIL.

Ánh xạ yêu cầu đặc tả:
    * #1 kind nhất quán theo yêu cầu  -> TC-01..TC-04
    * #2 tên field khớp chính xác     -> assert_contract (mọi TC) + TC-05 chống typo
    * #3 field danh sách đúng kiểu    -> assert_contract + TC-05
    * UC-03 Send/Reply                -> TC-06 (human-in-the-loop: không auto-xác-nhận)

TRUNG THỰC VỀ SKIP (không phải pass ẩn):
    * Server tắt / chưa đăng nhập  -> SKIP nêu rõ lý do (không thể kết luận gì).
    * LLM hết quota / 503 (thẻ lỗi hạ tầng của app) -> SKIP — lỗi hạ tầng ≠ lỗi hợp đồng.
    * Mọi trường hợp còn lại: assert THẬT, sai là FAIL — kể cả khi code hiện tại rớt.

Chuẩn bị & chạy:
    uv run main.py                       # backend ở cổng 8000
    # Cách A: tự động — test tự lấy phiên đăng nhập MỚI NHẤT trong DB (cần đăng nhập web trước).
    # Cách B: chỉ định — đặt env MEOARC_BEARER=<token phiên> (bảng sessions) hoặc MEOARC_COOKIE.
    uv run pytest test_agent.py -v
"""

from __future__ import annotations

import os
from typing import Literal

import httpx
import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

BASE_URL = os.environ.get("MEOARC_BASE_URL", "http://localhost:8000")
ENDPOINT = "/agent/chat"
TIMEOUT_SECONDS = 150.0  # 1 lượt agent = nhiều lần gọi LLM + retry backoff

PROMPTS: dict[str, str] = {
    "digest": "Thống kê tình trạng hộp thư của tôi: tổng số thư, bao nhiêu thư chưa đọc và quan trọng?",
    "triage": "Phân loại giúp mình email trong hộp thư theo mức độ ưu tiên xử lý gấp hay để sau kèm gợi ý nhé.",
    "result": "Liệt kê cho tôi 5 email mới nhất trong hộp thư, mỗi email một dòng.",
    "text": "Chào trợ lý! Bạn có thể giúp tôi quản lý Gmail như thế nào vậy?",
    "send": "Soạn và gửi một email tới địa chỉ qa-sandbox@example.com, tiêu đề 'Kiểm thử MeoArc', nội dung thông báo hệ thống chạy ổn định.",
}

# Thẻ lỗi HẠ TẦNG của app (quota/quá tải/thiếu quyền) — gặp là SKIP, không kết luận hợp đồng.
INFRA_MARKERS = ("🚦", "⏳", "🔑", "trục trặc", "quota", "hết lượt", "quá tải")

pytestmark = pytest.mark.asyncio


# ────────────────────────── HỢP ĐỒNG §2 (PresentReply) ──────────────────────────
# Chép đúng theo đặc tả QA. LƯU Ý đọc-hiểu hợp đồng cho ĐÚNG thay vì cứng nhắc sai:
#  • Field mô tả "CHỈ khi kind=X" ⇒ BẮT BUỘC có mặt khi kind=X; kind khác không bắt buộc
#    serialize (default rỗng). Vì vậy KHÔNG được đòi đủ 9 field ở mọi reply.
#  • Endpoint được phép kèm field MỞ RỘNG đã công bố (conversationId, emails) — extras
#    không phá hợp đồng; cái bị cấm là SAI TÊN field chuẩn (kiểm ở TC-05).
class _Item(BaseModel):
    model_config = ConfigDict(extra="allow")


class StatItem(_Item):
    label: str
    value: int


class BreakdownItem(_Item):
    label: str
    count: int


class TriageItem(_Item):
    sender: str
    initial: str
    subject: str
    suggest: str


class TriageGroup(_Item):
    level: Literal["high", "normal"]
    label: str
    items: list[TriageItem] = Field(default_factory=list)


VALID_KINDS = {"text", "result", "digest", "triage"}
REQUIRED_BY_KIND: dict[str, dict[str, type]] = {
    "text": {"text": str},
    "result": {"intro": str, "title": str, "lines": list},
    "digest": {"intro": str, "title": str, "stats": list, "breakdown": list, "highlights": list},
    "triage": {"intro": str, "title": str, "groups": list},
}
# Các biến thể SAI CHÍNH TẢ hay gặp — xuất hiện là FAIL ngay (yêu cầu #2).
TYPO_BLACKLIST = {"stat", "Stats", "break_down", "breakdowns", "highlight", "group",
                  "line", "Lines", "tittle", "intros"}


async def call_agent(message: str) -> dict:
    """Gửi 1 câu lệnh tới endpoint THẬT. Server tắt / chưa auth → SKIP nêu rõ."""
    headers = {"Content-Type": "application/json"}
    bearer = os.environ.get("MEOARC_BEARER", "")
    cookie = os.environ.get("MEOARC_COOKIE", "")
    if not bearer and not cookie:
        bearer = _token_from_db()  # tiện cho dev: lấy phiên mới nhất trong DB
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    elif cookie:
        headers["Cookie"] = cookie
    else:
        pytest.skip("Không có thông tin đăng nhập (MEOARC_BEARER/MEOARC_COOKIE, DB không có phiên sống).")

    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(ENDPOINT, json={"message": message}, headers=headers)
    except httpx.ConnectError:
        pytest.skip(f"Server không chạy tại {BASE_URL} — bật `uv run main.py` rồi chạy lại.")

    if resp.status_code == 401:
        pytest.skip("Phiên đăng nhập hết hạn/không hợp lệ (401) — đăng nhập web lại.")
    assert resp.status_code == 200, f"Mong HTTP 200, nhận {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    assert isinstance(data, dict), "Reply phải là JSON object"
    _skip_if_infra_error(data)
    return data


def _token_from_db() -> str:
    """Fallback thuận tiện: lấy token phiên MỚI NHẤT còn hạn từ DB (chỉ phần setup —
    mọi ASSERT vẫn đi qua HTTP công khai). Lỗi gì cũng trả '' để skip sạch."""
    try:
        from datetime import datetime, timezone
        from app.core.db import SessionLocal
        from app.models.user import User  # noqa: F401 — FK resolve
        from app.models.session import AuthSession
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db = SessionLocal()
        try:
            rows = [s for s in db.query(AuthSession).all() if s.expires_at and s.expires_at > now]
            rows.sort(key=lambda s: s.expires_at, reverse=True)
            return rows[0].token if rows else ""
        finally:
            db.close()
    except Exception:
        return ""


def _skip_if_infra_error(data: dict) -> None:
    blob = f"{data.get('text', '')} {data.get('intro', '')}"
    if data.get("kind") == "text" and any(m in blob for m in INFRA_MARKERS):
        pytest.skip(f"Hạ tầng LLM không khả dụng (không kết luận hợp đồng): {blob[:90]!r}")


def assert_contract(data: dict) -> str:
    """Hợp đồng §2: kind hợp lệ + field BẮT BUỘC theo kind có mặt, đúng TÊN, đúng KIỂU."""
    assert "kind" in data, "Thiếu trường bắt buộc 'kind'"
    kind = data["kind"]
    assert kind in VALID_KINDS, f"'kind' ngoài hợp đồng: {kind!r} (phải thuộc {sorted(VALID_KINDS)})"

    for field, typ in REQUIRED_BY_KIND[kind].items():
        assert field in data, f"kind={kind} nhưng THIẾU field bắt buộc '{field}'"
        assert isinstance(data[field], typ), (
            f"Field '{field}' phải là {typ.__name__}, nhận {type(data[field]).__name__}"
        )

    # Kiểm sâu phần tử lồng nhau bằng đúng schema §2
    try:
        if kind == "digest":
            [StatItem.model_validate(x) for x in data["stats"]]
            [BreakdownItem.model_validate(x) for x in data["breakdown"]]
            assert all(isinstance(h, str) for h in data["highlights"]), "highlights phải là list[str]"
        elif kind == "triage":
            [TriageGroup.model_validate(g) for g in data["groups"]]
        elif kind == "result":
            assert all(isinstance(x, str) for x in data["lines"]), "lines phải là list[str]"
    except ValidationError as exc:
        pytest.fail(f"[SAI KIỂU/TÊN field lồng nhau]:\n{exc}")
    return kind


# ─────────────────────────────── TEST CASES ───────────────────────────────

async def test_tc01_digest_thong_ke_hop_thu():
    """UC-01: yêu cầu thống kê → PHẢI trả thẻ digest có số liệu thật (stats không rỗng)."""
    data = await call_agent(PROMPTS["digest"])
    kind = assert_contract(data)
    assert kind == "digest", f"Yêu cầu thống kê phải trả 'digest', nhận '{kind}' — UC-01 chưa đạt."
    assert len(data["stats"]) > 0, "digest nhưng 'stats' rỗng — không có số liệu thì thống kê vô nghĩa."
    for stat in data["stats"]:
        assert isinstance(stat["value"], int) and not isinstance(stat["value"], bool), \
            f"stats.value phải là số nguyên thật, nhận {stat['value']!r}"


async def test_tc02_triage_phan_loai_uu_tien():
    """UC-02: yêu cầu phân loại ưu tiên → PHẢI trả 'triage' có groups; initial đúng 1 chữ HOA
    (đặc tả §2: 'MỘT chữ cái đầu tên người gửi (viết hoa)')."""
    data = await call_agent(PROMPTS["triage"])
    kind = assert_contract(data)
    assert kind == "triage", f"Yêu cầu phân loại phải trả 'triage', nhận '{kind}' — UC-02 chưa đạt."
    assert len(data["groups"]) > 0, "triage nhưng 'groups' rỗng."
    for g in data["groups"]:
        for it in g["items"]:
            assert len(it["initial"]) == 1, f"initial phải đúng 1 ký tự, nhận {it['initial']!r}"
            assert it["initial"] == it["initial"].upper(), f"initial phải viết HOA, nhận {it['initial']!r}"


async def test_tc03_result_liet_ke_dung_so_luong():
    """UC-01: 'liệt kê 5 email' → 'result' và KHÔNG ĐƯỢC nhiều hơn 5 dòng (đúng số lượng yêu cầu)."""
    data = await call_agent(PROMPTS["result"])
    kind = assert_contract(data)
    assert kind == "result", f"Yêu cầu liệt kê phải trả 'result', nhận '{kind}'."
    assert 0 < len(data["lines"]) <= 5, (
        f"Xin 5 thư mà nhận {len(data['lines'])} dòng — sai số lượng người dùng yêu cầu."
    )
    # Mở rộng đã công bố: nếu kèm 'emails' (thẻ bấm được) thì số thẻ không vượt số dòng + mỗi thẻ có id.
    if isinstance(data.get("emails"), list):
        assert len(data["emails"]) <= len(data["lines"]), "Số thẻ email nhiều hơn số dòng đã liệt kê."
        assert all(e.get("id") for e in data["emails"]), "Thẻ email thiếu id → FE không mở được thư."


async def test_tc04_text_tro_chuyen():
    """Trò chuyện thường → 'text' với nội dung không rỗng."""
    data = await call_agent(PROMPTS["text"])
    kind = assert_contract(data)
    assert kind == "text", f"Câu chào hỏi phải trả 'text', nhận '{kind}'."
    assert data["text"].strip(), "kind=text nhưng 'text' trống — FE sẽ hiện bubble rỗng."


async def test_tc05_khong_sai_chinh_ta_ten_field():
    """Yêu cầu #2: không xuất hiện biến thể sai chính tả của tên field chuẩn."""
    data = await call_agent(PROMPTS["digest"])
    bad = TYPO_BLACKLIST & set(data.keys())
    assert not bad, f"Tên field sai chính tả so với hợp đồng: {sorted(bad)}"
    assert_contract(data)


async def test_tc06_uc03_gui_thu_human_in_the_loop():
    """UC-03 + SRS UC010: lệnh gửi thư phải trả reply HỢP LỆ và (theo cơ chế human-in-the-loop)
    KHÔNG được tự ý gửi ngay không hỏi — reply đầu tiên không được là 'đã gửi xong'.
    Lưu ý: test này KHÔNG xác nhận gửi, nên không có thư nào được gửi đi thật."""
    data = await call_agent(PROMPTS["send"])
    kind = assert_contract(data)
    if kind == "text":
        low = data["text"].lower()
        claimed_sent = ("đã gửi" in low or "da gui" in low) and ("?" not in data["text"])
        assert not claimed_sent, (
            "Agent tuyên bố ĐÃ GỬI ngay ở lượt đầu, không hỏi xác nhận — vi phạm human-in-the-loop (UC010)."
        )
