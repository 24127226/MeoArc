import os

from langchain.chat_models import init_chat_model

from app.core.config import settings
import logging


logger = logging.getLogger(__name__)


def _enable_langsmith_if_configured() -> None:
    """Observability (đúng proposal): điền LANGSMITH_API_KEY trong .env là BẬT tracing.
    pydantic-settings chỉ đọc .env cho settings, KHÔNG export ra process env — trong khi
    LangChain đọc os.environ → phải tự bơm sang. setdefault: env đặt tay luôn thắng.
    Đặt CẢ hai họ tên biến (LANGCHAIN_* cũ / LANGSMITH_* mới) cho chắc mọi version."""
    if not settings.langsmith_api_key:
        return
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
    logger.info("LangSmith tracing BẬT (project=%s)", settings.langsmith_project)


def create_llm():
    """Create LLM: Cloud AI or Local AI"""
    logger.info("Initializing LLM")
    _enable_langsmith_if_configured()
    model_kwargs = {
        "model": settings.model_name,
        "model_provider": settings.model_provider,
        # ── Reliability (NFR) ──
        # temperature=0: XÁC ĐỊNH, bám schema tool chặt. QUAN TRỌNG với Groq/Llama —
        #   temperature cao khiến model hay sinh cú gọi hàm SAI cú pháp (vd
        #   <function=search_emails({"limit":"5","is_read":"false"})>) → Groq trả 400
        #   tool_use_failed. Về 0 thì bám đúng JSON tool-call hơn hẳn. Gemini cũng
        #   ổn định hơn cho tác vụ chọn tool. Đổi qua .env (AGENT_TEMPERATURE) nếu
        #   muốn câu trả lời "bay" hơn — nhưng tool calling thì càng thấp càng chắc.
        "temperature": settings.agent_temperature,
        # max_retries: tự thử lại (có exponential backoff sẵn) khi model trả lỗi chớp nhoáng
        #   (429 theo phút / 5xx / timeout mạng). Lưu ý: hết quota theo NGÀY thì retry KHÔNG cứu được.
        # timeout: cắt lệnh gọi treo quá 60s để không "kẹt" cả vòng agent.
        "max_retries": 3,
        "timeout": 60,
    }

    if settings.ai_api_key:
        model_kwargs["api_key"] = settings.ai_api_key
        # Đổi NƠI GỬI khi có proxy (xem `ai_base_url` trong config.py và
        # `infra/cf-gemini-proxy/`). Google chặn Gemini theo vị trí máy chủ gọi, mà
        # bản triển khai nằm ở Hong Kong — vùng bị chặn. Proxy khiến lời gọi đi ra
        # từ nơi khác, không phải đổi vùng Azure.
        #
        # CHỈ cho nhà cung cấp Google: `base_url` của Groq/OpenAI trỏ tới máy chủ
        # CỦA HỌ, bơm URL proxy Gemini vào đó là gửi thư đi sai nhà — và sai kiểu
        # im lặng, chỉ lòi ra khi đọc log mạng.
        if settings.ai_base_url and settings.model_provider.startswith("google"):
            model_kwargs["base_url"] = settings.ai_base_url.rstrip("/")
            if settings.ai_proxy_secret:
                model_kwargs["additional_headers"] = {
                    "x-meoarc-proxy": settings.ai_proxy_secret,
                }
            logger.info("Gemini đi qua proxy: %s", settings.ai_base_url)
    elif settings.local_model_base_url:
        model_kwargs["base_url"] = settings.local_model_base_url
    else:
        logger.error("Environmental variables have not been assigned yet")
        raise ValueError(
            "Either AI_API_KEY or LOCAL_MODEL_BASE_URL must be configured."
        )

    try:
        llm = init_chat_model(**model_kwargs)
    except Exception:
        logger.exception(
            "Failed to initialize model=%s provider=%s",
            settings.model_name,
            settings.model_provider,
        )
        raise
    return llm