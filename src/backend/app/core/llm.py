from langchain.chat_models import init_chat_model

from app.core.config import settings
import logging


logger = logging.getLogger(__name__)

def create_llm():
    """Create LLM: Cloud AI or Local AI"""
    logger.info("Initializing LLM")
    model_kwargs = {
        "model": settings.model_name,
        "model_provider": settings.model_provider,
    }

    if settings.ai_api_key:
        model_kwargs["api_key"] = settings.ai_api_key
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