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


def create_llm(model_name: str | None = None):
    """Create LLM: Cloud AI or Local AI.

    `model_name` để trống thì dùng `settings.model_name`. Truyền vào để dựng các bản
    DỰ PHÒNG cho `create_llm_du_phong()` — xem hàm đó để biết vì sao cần."""
    logger.info("Initializing LLM")
    _enable_langsmith_if_configured()
    model_kwargs = {
        "model": model_name or settings.model_name,
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

def _la_loi_het_quota(e: BaseException) -> bool:
    """Chỉ nhận lỗi HẾT HẠN MỨC. Rơi sang model khác vì một lỗi khác (schema tool sai,
    khoá hỏng, mạng đứt) là che mất lỗi thật — nó sẽ chạy được ở model sau rồi im lặng
    trôi qua, và ta mất luôn tín hiệu."""
    t = str(e)
    return "RESOURCE_EXHAUSTED" in t or "429" in t


class LLMDuPhong:
    """Chuỗi LLM: gọi cái đầu, CHỈ KHI hết hạn mức thì rơi sang cái kế.

    Tự viết chứ không dùng `Runnable.with_fallbacks` vì tham số `exceptions_to_handle`
    của nó chỉ nhận LỚP ngoại lệ, không nhận hàm lọc. Mà quota và lỗi thật (schema tool
    sai, khoá hỏng) đều ném ra cùng một lớp `ChatGoogleGenerativeAIError` — lọc theo lớp
    thì mọi lỗi đều rơi sang model sau, chạy được, rồi trôi qua trong im lặng. Lúc đó ta
    mất luôn tín hiệu về lỗi thật, mà đó mới là thứ đắt nhất.
    """

    def __init__(self, chuoi: list):
        self._chuoi = chuoi

    def bind_tools(self, tools):
        """Bind cho TỪNG model rồi bọc lại — mỗi model phải tự biết danh sách tool."""
        return LLMDuPhong([m.bind_tools(tools) for m in self._chuoi])

    def with_structured_output(self, *a, **kw):
        return LLMDuPhong([m.with_structured_output(*a, **kw) for m in self._chuoi])

    async def ainvoke(self, dau_vao, **kw):
        cuoi = len(self._chuoi) - 1
        for i, m in enumerate(self._chuoi):
            try:
                return await m.ainvoke(dau_vao, **kw)
            except Exception as e:
                if i == cuoi or not _la_loi_het_quota(e):
                    raise
                logger.warning("Model thứ %d hết hạn mức, rơi sang model kế tiếp", i + 1)
        raise RuntimeError("chuỗi LLM rỗng")   # không tới được: __init__ luôn có ≥1

    def invoke(self, dau_vao, **kw):
        cuoi = len(self._chuoi) - 1
        for i, m in enumerate(self._chuoi):
            try:
                return m.invoke(dau_vao, **kw)
            except Exception as e:
                if i == cuoi or not _la_loi_het_quota(e):
                    raise
                logger.warning("Model thứ %d hết hạn mức, rơi sang model kế tiếp", i + 1)
        raise RuntimeError("chuỗi LLM rỗng")


def create_llm_du_phong():
    """LLM chính + chuỗi DỰ PHÒNG, tự rơi sang model khác khi hết hạn mức.

    ── VÌ SAO CẦN ──
    Hạn mức Gemini free tính RIÊNG CHO TỪNG MODEL. Đo thật ngày 29/08/2026:
    `gemini-2.5-flash-lite` trần **20 lượt/ngày** (chạm trần sau khoảng 15 lượt chat),
    trong khi `gemini-2.5-flash` vẫn còn nguyên hạn mức của nó.

    20 lượt/ngày nghĩa là buổi trình bày có thể chết giữa chừng, và chết bằng một
    thông báo lỗi đỏ chứ không phải bằng một câu trả lời chậm. Xâu chuỗi nhiều model
    thì tổng hạn mức cộng dồn, và khi model đầu cạn thì người dùng chỉ thấy câu trả
    lời hơi khác giọng, không thấy hỏng.

    CHỈ rơi khi hết hạn mức — xem `_la_loi_het_quota`.

    Danh sách đặt qua `MODEL_FALLBACKS` trong .env, cách nhau bằng dấu phẩy. Để trống
    thì không có dự phòng và hành vi y hệt `create_llm()`.
    """
    chinh = create_llm()
    ten_du_phong = [
        t.strip() for t in (settings.model_fallbacks or "").split(",") if t.strip()
    ]
    # Bỏ trùng với model chính: rơi sang chính nó thì chỉ tốn thêm một lần gọi hỏng.
    ten_du_phong = [t for t in ten_du_phong if t != settings.model_name]
    if not ten_du_phong:
        return chinh

    du_phong = []
    for ten in ten_du_phong:
        try:
            du_phong.append(create_llm(ten))
        except Exception:
            # Một model dự phòng dựng hỏng KHÔNG được làm chết cả agent — bỏ qua nó.
            logger.exception("Không dựng được model dự phòng %s, bỏ qua", ten)
    if not du_phong:
        return chinh

    logger.info("LLM dự phòng: %s → %s", settings.model_name, ", ".join(ten_du_phong))
    return LLMDuPhong([chinh, *du_phong])
