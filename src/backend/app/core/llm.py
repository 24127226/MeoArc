import os
import time

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


def create_llm(model_name: str | None = None, api_key: str | None = None):
    """Create LLM: Cloud AI or Local AI.

    `model_name` để trống thì dùng `settings.model_name`. Truyền vào để dựng các bản
    DỰ PHÒNG cho `create_llm_du_phong()` — xem hàm đó để biết vì sao cần.

    `api_key` để trống thì dùng khoá ĐẦU TIÊN trong AI_API_KEY. Truyền vào để dựng các
    bậc dùng khoá khác. Lưu ý phải là `khoa_ai_dau_tien` chứ không phải `ai_api_key`:
    trường đó nay có thể chứa cả danh sách "k1,k2,k3", dán nguyên vào header là 400."""
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

    khoa = api_key or settings.khoa_ai_dau_tien
    if khoa:
        model_kwargs["api_key"] = khoa
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


# ── BỘ NHỚ "BẬC NÀY ĐÃ CẠN" ──────────────────────────────────────────────────
# nhãn bậc → thời điểm (epoch giây) được phép dùng lại.
#
# VÌ SAO PHẢI NHỚ. Không có nó thì chuỗi vẫn ĐÚNG nhưng dùng không nổi: mỗi câu hỏi
# lại đi từ bậc 1, đâm vào đúng những bậc đã chết, rồi mới tới bậc sống. Với 9 khoá ×
# 2 model, một khoá cạn nghĩa là mỗi câu hỏi từ đó về sau phải trả giá bằng những lượt
# gọi chắc chắn hỏng — mà mỗi lượt còn `max_retries=3` kèm backoff của riêng nó. Triệu
# chứng: trợ lý không báo lỗi gì cả, chỉ chậm dần, và không ai đoán ra vì sao.
#
# ĐỂ Ở TẦNG MODULE, KHÔNG PHẢI TRONG INSTANCE. `create_llm_du_phong()` được gọi hai lần
# (một cho agent, một cho bộ trình bày ở agent_node) nên có HAI chuỗi khác nhau. Để
# trong instance thì agent học được "khoá #1 chết rồi" còn bộ trình bày vẫn phải tự đâm
# đầu vào lần nữa — mỗi câu hỏi đốt oan thêm một lượt. Cùng nhãn thì cùng biết.
#
# Nhãn KHÔNG chứa khoá, chỉ chứa tên model và số thứ tự. Khoá không bao giờ được đi vào
# log hay vào /metrics.
_NGHI: dict[str, float] = {}


def _dang_nghi(nhan: str) -> bool:
    return _NGHI.get(nhan, 0.0) > time.time()


def _cho_nghi(nhan: str) -> None:
    _NGHI[nhan] = time.time() + max(0, settings.quota_cooldown_min) * 60


def trang_thai_khoa() -> list[dict]:
    """Bậc nào đang nghỉ và còn bao lâu — cho /metrics.

    Ngày trình bày, câu hỏi đắt nhất là "còn lượt không, hay sắp chết giữa chừng?".
    Trước đây chỉ đoán được bằng cách hỏi thử rồi xem có lỗi đỏ không — tức là tốn
    đúng cái thứ đang muốn đo. Nhìn ở đây thì không tốn lượt nào."""
    bay_gio = time.time()
    return [
        {"bac": n, "nghi_them_giay": int(t - bay_gio)}
        for n, t in sorted(_NGHI.items())
        if t > bay_gio
    ]


class LLMDuPhong:
    """Chuỗi LLM: gọi cái đầu, CHỈ KHI hết hạn mức thì rơi sang cái kế.

    Tự viết chứ không dùng `Runnable.with_fallbacks` vì tham số `exceptions_to_handle`
    của nó chỉ nhận LỚP ngoại lệ, không nhận hàm lọc. Mà quota và lỗi thật (schema tool
    sai, khoá hỏng) đều ném ra cùng một lớp `ChatGoogleGenerativeAIError` — lọc theo lớp
    thì mọi lỗi đều rơi sang model sau, chạy được, rồi trôi qua trong im lặng. Lúc đó ta
    mất luôn tín hiệu về lỗi thật, mà đó mới là thứ đắt nhất.

    `nhan` là tên từng bậc, dùng cho log và cho bộ nhớ `_NGHI`. Để trống thì tự đánh số.
    """

    def __init__(self, chuoi: list, nhan: list[str] | None = None):
        self._chuoi = chuoi
        self._nhan = list(nhan) if nhan else [f"bậc {i + 1}" for i in range(len(chuoi))]

    def bind_tools(self, tools):
        """Bind cho TỪNG model rồi bọc lại — mỗi model phải tự biết danh sách tool."""
        return LLMDuPhong([m.bind_tools(tools) for m in self._chuoi], self._nhan)

    def with_structured_output(self, *a, **kw):
        return LLMDuPhong(
            [m.with_structured_output(*a, **kw) for m in self._chuoi], self._nhan
        )

    def _thu_tu(self) -> list[tuple[str, object]]:
        """Bậc còn sống lên trước, bậc đang nghỉ XUỐNG CUỐI — không bỏ hẳn.

        Bỏ hẳn thì khi mọi bậc cùng nghỉ, chuỗi rỗng và ta phải bịa ra một lỗi mới để
        ném; trong khi thứ người dùng cần lúc đó là ta CỨ THỬ. Thời gian nghỉ chỉ là
        phỏng đoán (xem `quota_cooldown_min`) — đủ để sắp lại thứ tự, không đủ để tự
        cho phép mình từ chối phục vụ."""
        cap = list(zip(self._nhan, self._chuoi))
        return [x for x in cap if not _dang_nghi(x[0])] + [
            x for x in cap if _dang_nghi(x[0])
        ]

    def _xu_ly_loi(self, nhan: str, e: BaseException, cuoi: bool) -> None:
        """Chung cho cả hai lối gọi — sửa một chỗ thì cả hai cùng đổi."""
        if not _la_loi_het_quota(e):
            raise e
        _cho_nghi(nhan)
        if cuoi:
            raise e
        logger.warning(
            "%s hết hạn mức → nghỉ %d phút, rơi sang bậc kế",
            nhan, settings.quota_cooldown_min,
        )

    async def ainvoke(self, dau_vao, **kw):
        thu = self._thu_tu()
        cuoi = len(thu) - 1
        for i, (nhan, m) in enumerate(thu):
            try:
                return await m.ainvoke(dau_vao, **kw)
            except Exception as e:
                self._xu_ly_loi(nhan, e, i == cuoi)
        raise RuntimeError("chuỗi LLM rỗng")   # không tới được: __init__ luôn có ≥1

    def invoke(self, dau_vao, **kw):
        thu = self._thu_tu()
        cuoi = len(thu) - 1
        for i, (nhan, m) in enumerate(thu):
            try:
                return m.invoke(dau_vao, **kw)
            except Exception as e:
                self._xu_ly_loi(nhan, e, i == cuoi)
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

    ── TRỤC THỨ HAI: NHIỀU KHOÁ ──
    Hạn mức free tính theo TỪNG MODEL của TỪNG PROJECT. Nên ngoài trục model còn một
    trục nữa: nhiều khoá thuộc các project khác nhau. Đặt nhiều khoá vào AI_API_KEY,
    ngăn bằng dấu phẩy, là chuỗi tự nở ra thành `model × khoá`.

    VÌ SAO ĐÁNG LÀM. Khoá được đọc đúng một lần lúc dựng `settings`, và client LLM thì
    nằm trong biến toàn cục ở agent_node — nghĩa là đổi khoá BẮT BUỘC phải khởi động
    lại tiến trình. Ở máy nhà là 2 giây; trên Azure là khởi động lại cả container, đo
    được 2–4 phút, và trong lúc đó không có tín hiệu nào cho biết còn bao lâu. Nạp sẵn
    mọi khoá thì lúc cạn không phải đụng vào Azure nữa.

    ── VÌ SAO ĐỔI KHOÁ TRƯỚC, ĐỔI MODEL SAU ──
    Thứ tự là `for model: for khoá`, tức cạn khoá #1 thì thử khoá #2 CÙNG MODEL ĐÓ,
    hết khoá mới hạ xuống model kế. Đổi khoá thì người dùng không nhận ra gì; đổi model
    thì giọng văn và chất lượng suy luận đổi theo. Giữ model tốt càng lâu càng tốt.

    ── CẢNH BÁO: NHIỀU KHOÁ ≠ NHIỀU HẠN MỨC ──
    Hạn mức free tính theo PROJECT chứ không theo khoá. Tạo 9 khoá trong CÙNG một
    project trên AI Studio thì cả 9 dùng chung đúng một hạn mức, và chuỗi này không
    thêm được lượt nào — nó chỉ tốn thêm những lượt gọi hỏng. Muốn cộng dồn thật thì
    mỗi khoá phải ở một project (hoặc một tài khoản Google) khác nhau.
    """
    khoa = settings.danh_sach_khoa_ai or [""]   # "" = không dùng khoá (model chạy local)
    ten_model = [settings.model_name] + [
        t.strip() for t in (settings.model_fallbacks or "").split(",") if t.strip()
    ]
    # Bỏ trùng: rơi sang chính nó thì chỉ tốn thêm một lần gọi hỏng rồi vẫn lỗi như cũ.
    ten_model = list(dict.fromkeys(ten_model))

    # Bậc ĐẦU dựng riêng và KHÔNG bọc try: chưa cấu hình gì thì `create_llm` ném
    # ValueError, và đó là lỗi phải nổi lên tận nơi. Nuốt nó ở đây thì app im lặng
    # chạy tiếp mà không có LLM nào, rồi hỏng ở chỗ khác chẳng liên quan.
    chuoi = [create_llm(ten_model[0], khoa[0] or None)]
    nhan = [_nhan_bac(ten_model[0], 1, len(khoa))]

    for j, ten in enumerate(ten_model):
        for i, k in enumerate(khoa, start=1):
            if j == 0 and i == 1:
                continue                      # đã dựng ở trên
            try:
                chuoi.append(create_llm(ten, k or None))
                nhan.append(_nhan_bac(ten, i, len(khoa)))
            except Exception:
                # Một bậc dựng hỏng KHÔNG được làm chết cả agent — bỏ qua nó.
                logger.exception("Không dựng được bậc %s, bỏ qua", _nhan_bac(ten, i, len(khoa)))

    if len(chuoi) == 1:
        return chuoi[0]

    logger.info(
        "Chuỗi LLM %d bậc (%d model × %d khoá): %s",
        len(chuoi), len(ten_model), len(khoa), " → ".join(nhan),
    )
    return LLMDuPhong(chuoi, nhan)


def _nhan_bac(ten_model: str, so_khoa: int, tong_khoa: int) -> str:
    """Tên một bậc, dùng cho log và cho `_NGHI`. KHÔNG bao giờ chứa khoá — chỉ số thứ tự.
    Một khoá thì bỏ hẳn phần "khoá #1" cho log khỏi ồn vì một con số luôn bằng 1."""
    return ten_model if tong_khoa <= 1 else f"{ten_model} · khoá #{so_khoa}"
