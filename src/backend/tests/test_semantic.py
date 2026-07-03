"""test_semantic.py — Tìm theo Ý NGHĨA (UC005 semantic, thay pgvector bằng re-rank).

Chuẩn khách quan:
  * Toán cosine đúng định nghĩa (trực giao=0, trùng=1) — không phụ thuộc code sản phẩm.
  * Xếp hạng: tài liệu GẦN NGHĨA câu hỏi phải đứng trước — kiểm bằng vector GIẢ đặt sẵn
    (không mạng, không quota) → thuật toán sai là FAIL bất kể model nào.
  * Hợp đồng tool: semantic_search là tool ĐỌC (không đòi confirm), trả CÙNG khuôn
    SearchEmailsOutput như search_emails (FE thẻ bấm-được dùng chung).

Chạy: uv run pytest tests/test_semantic.py -v   (KHÔNG cần mạng/quota)
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from app.core.embeddings import cosine, rank_by_similarity
from app.tools.schemas import SemanticSearchInput


# ── Toán thuần ───────────────────────────────────────────────────────────────
def test_cosine_dung_dinh_nghia():
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)      # trực giao → 0
    assert cosine([2, 0], [4, 0]) == pytest.approx(1.0)      # cùng hướng → 1
    assert cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)    # ngược hướng → -1
    assert cosine([0, 0], [1, 1]) == 0.0                     # vector 0 → 0 (không chia 0)


def test_rank_tai_lieu_gan_nghia_dung_truoc():
    q = [1.0, 0.0]
    docs = [[0.0, 1.0], [0.9, 0.1], [0.5, 0.5]]   # doc1 gần q nhất, rồi doc2, doc0
    top = rank_by_similarity(q, docs, top_k=2)
    assert [i for i, _ in top] == [1, 2], f"Xếp hạng sai: {top}"
    assert top[0][1] > top[1][1], "Điểm phải giảm dần"


# ── Schema công bố ───────────────────────────────────────────────────────────
def test_schema_bien():
    assert SemanticSearchInput(query="tiền nong").limit == 5
    with pytest.raises(ValidationError):
        SemanticSearchInput(query="x")            # query quá ngắn
    with pytest.raises(ValidationError):
        SemanticSearchInput(query="ok", limit=21) # vượt trần 20
    with pytest.raises(ValidationError):
        SemanticSearchInput(query="ok", pool=4)   # pool dưới sàn 5


# ── Tool end-to-end với embedding GIẢ (kiểm mạch, không kiểm model) ──────────
def _fake_email(i: int, subject: str, preview: str):
    from app.schemas.email import Email
    return Email(id=f"id{i}", sender=f"Người {i}", senderEmail=f"p{i}@x.vn",
                 senderInitial="N", to="", subject=subject, preview=preview,
                 body=[preview], time="09:00", date="Hôm nay, 09:00",
                 unread=False, starred=False, category="moss", threadId=f"th{i}")


def test_tool_semantic_xep_dung_va_dung_khuon(monkeypatch):
    import app.core.embeddings as emb
    import app.tools.email_tools as et
    from app.tools.registry import RequestContext

    emails = [
        _fake_email(0, "Ảnh chuyến du lịch Đà Lạt", "album ảnh đẹp"),
        _fake_email(1, "Invoice #123 payment due", "hoá đơn cần thanh toán"),
        _fake_email(2, "Họp nhóm tối nay", "nhớ tham gia"),
    ]
    monkeypatch.setattr(et.gmail_service, "list_messages",
                        lambda tok, max_results=30, **kw: (emails, None))
    # Vector giả: câu hỏi 'tiền nong' trùng hướng doc 1 (invoice)
    monkeypatch.setattr(emb, "embed_query", lambda q: [1.0, 0.0])
    monkeypatch.setattr(emb, "embed_texts",
                        lambda docs: [[0.0, 1.0], [0.95, 0.05], [0.3, 0.7]])

    out = asyncio.run(et.semantic_search(
        SemanticSearchInput(query="thư về tiền nong", limit=2),
        RequestContext(user_id="qa", access_token="tok")))

    assert out.success is True
    assert out.data[0].id == "id1", f"Thư invoice phải đứng đầu, nhận {out.data[0].id}"
    assert len(out.data) == 2, "Phải trả đúng limit"
    # Cùng khuôn search_emails → FE/extractor thẻ bấm-được dùng chung
    assert {"id", "sender", "subject", "snippet"} <= set(out.data[0].model_dump())
    assert out.data[0].thread_id == "th1", "threadId thật phải chảy qua semantic_search"


def test_semantic_la_tool_doc_khong_doi_confirm():
    import app.tools.email_tools  # noqa: F401
    from app.tools.registry import tool_registry
    spec = tool_registry.get_spec("semantic_search")
    assert spec.requires_confirmation is False, "Tool chỉ-đọc không được đòi duyệt"


def test_extractor_nhan_ket_qua_semantic():
    """Thẻ email bấm-được phải hoạt động với cả semantic_search (không chỉ search_emails)."""
    import json
    from app.api.app import _emails_from_search
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    payload = {"data": [{"id": "abc", "sender": "X", "subject": "S", "snippet": "", "is_read": True}]}
    msgs = [HumanMessage(content="tìm thư về tiền nong"), AIMessage(content=""),
            ToolMessage(content=json.dumps(payload), name="semantic_search", tool_call_id="t1"),
            AIMessage(content="đây")]
    res = _emails_from_search(msgs)
    assert len(res) == 1 and res[0]["id"] == "abc"
