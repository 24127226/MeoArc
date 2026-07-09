"""test_llm_smoke.py — SMOKE TEST LLM THẬT (Groq / Gemini / Ollama...).

Chỉ cần cấu hình LLM đúng trong .env (AI_API_KEY + MODEL_NAME + MODEL_PROVIDER) —
KHÔNG cần phiên Gmail, KHÔNG cần server. Mục đích: cô lập & xác nhận riêng phần "não"
gọi được, tách khỏi Gmail/agent để dễ khoanh lỗi khi đổi nhà cung cấp LLM.

Tự SKIP nếu chưa bật cờ (để không tốn request khi chạy suite thường / CI).

Bật (PowerShell):  $env:MEOARC_LLM_SMOKE=1 ; uv run pytest tests/test_llm_smoke.py -v
Bật (bash):        MEOARC_LLM_SMOKE=1 uv run pytest tests/test_llm_smoke.py -v
"""

from __future__ import annotations

import asyncio
import os

import pytest
from langchain_core.messages import HumanMessage

pytestmark = pytest.mark.skipif(
    os.environ.get("MEOARC_LLM_SMOKE") != "1",
    reason="Đặt MEOARC_LLM_SMOKE=1 để chạy smoke test gọi LLM thật (tốn 1 request).",
)


def test_llm_ket_noi_va_tra_loi_khong_rong():
    """create_llm() dựng đúng client từ .env → gọi 1 câu đơn giản → có câu trả lời chuỗi, không rỗng."""
    from app.core.llm import create_llm

    llm = create_llm()
    ai = asyncio.run(
        llm.ainvoke([HumanMessage(content="Trả lời NGẮN gọn bằng tiếng Việt: thủ đô của Việt Nam?")])
    )
    text = ai.content if isinstance(ai.content, str) else str(ai.content)
    assert text.strip(), "LLM trả RỖNG — kiểm tra AI_API_KEY / MODEL_PROVIDER / MODEL_NAME trong .env"
    print(f"\n[LLM smoke] provider trả về: {text[:120]!r}")
