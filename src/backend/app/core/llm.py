import os
import re
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


def _la_loi_qua_tai_nhat_thoi(e: BaseException) -> bool:
    """503 / UNAVAILABLE / "model is overloaded" — GOOGLE đang đông, không phải khoá mình cạn.

    Đây CHÍNH LÀ trường hợp đổi bậc có ích nhất, mà bản trước lại không rơi: nó chỉ rơi
    khi hết hạn mức, nên một cú 503 ở bậc 1 giết cả yêu cầu trong khi 19 bậc còn lại đang
    ngồi không. Người dùng nhận đúng câu "Mô hình AI của Google đang quá tải" dù vừa nạp
    đủ 10 khoá — và không có cách nào hiểu vì sao 10 khoá không cứu nổi.

    Vẫn KHÁC quota ở một điểm quan trọng: 503 KHÔNG được cho bậc đó nghỉ. Khoá không mất
    gì cả, Google chỉ đang bận; treo nó 15 phút là tự vứt một bậc còn nguyên hạn mức."""
    t = str(e).lower()
    return (
        "unavailable" in t or "overloaded" in t or "high demand" in t
        or "503" in t or "internal error" in t or "500" in t
        # ── THÊM 03/09/2026: hai mã nữa, cùng bản chất "phía Google trục trặc" ──
        # Chạy đủ 36 câu prompt trên hệ thật thì ba câu chết vì chúng:
        #   Q8       → 499 CANCELLED
        #   Q10, Q11 → 504 DEADLINE_EXCEEDED
        # Không nằm trong danh sách nên chúng GIẾT cả yêu cầu thay vì sang model kế —
        # trong khi đây đúng là loại lỗi mà đổi bậc cứu được: cùng câu hỏi, model khác,
        # thường là chạy được ngay.
        #
        # Khớp bằng TÊN MÃ chứ không phải con số. Bắt "504"/"499" trần là lặp lại đúng
        # cái bẫy đã vấp với "429" và "404": ba ký tự số nằm trong id hay URL cũng khớp,
        # và một lần dán nhãn sai làm cả buổi đi tìm lỗi ở chỗ không có lỗi.
        or "deadline_exceeded" in t or "deadline expired" in t
        or "cancelled" in t or "canceled" in t
    )


def _la_loi_model_bien_mat(e: BaseException) -> bool:
    """404 — Google đã GỠ model đó. Không phải khoá có vấn đề, không phải hết lượt.

    Đo thật 02/09/2026: "This model models/gemini-2.5-flash-lite is no longer available
    to new users. Please update your code to use models/gemini-3.5-flash-lite". Nghiệt
    ở chỗ *to new users*: khoá cũ vẫn gọi được, khoá VỪA TẠO thì 404. Nên vừa lập thêm
    project để có thêm hạn mức là vừa mất luôn model chính — hai việc trông chẳng liên
    quan gì nhau. Đây là lần THỨ HAI Google gỡ model giữa chừng với dự án này
    (`gemini-2.5-flash`, 29/08 — xem đầu file test).

    KHÔNG dùng phép tìm chuỗi con `"404" in t`. Đã vấp đúng bẫy đó với `"429"`: ba ký
    tự số có thể nằm trong id, trong URL, trong lịch sử thử lại — và một lần dán nhãn
    sai làm cả buổi đi tìm lỗi ở chỗ không có lỗi. Hai cụm dưới đây không mập mờ."""
    t = str(e).lower()
    return "not_found" in t or "no longer available" in t


def _nen_doi_bac(e: BaseException) -> bool:
    """Có đáng đổi sang bậc kế không. Ba loại: hết hạn mức, sự cố nhất thời phía nhà
    cung cấp, và model bị gỡ. Mọi thứ khác phải nổi lên nguyên vẹn — xem
    `_la_loi_het_quota`."""
    return (
        _la_loi_het_quota(e)
        or _la_loi_qua_tai_nhat_thoi(e)
        or _la_loi_model_bien_mat(e)
    )


def _ten_model(nhan: str) -> str:
    """Tách tên model khỏi nhãn bậc ("gemini-3.6-flash · khoá #2" → "gemini-3.6-flash").
    Model bị gỡ thì MỌI khoá của nó đều 404 — phải chặn theo model, không theo bậc."""
    return nhan.split(" · ")[0]


def _che_khoa(van: str) -> str:
    """Xoá mọi khoá đã cấu hình khỏi một chuỗi trước khi nó đi vào log hay /metrics.
    Thông báo lỗi của nhà cung cấp CÓ THỂ vọng lại khoá đã gửi — đưa nguyên xi ra một
    endpoint ai cũng đọc được là phát tán bí mật, và không thu lại được."""
    for k in settings.danh_sach_khoa_ai:
        if k:
            van = van.replace(k, "[da-che]")
    return van


# Lỗi THẬT gần nhất của chuỗi, cho /metrics. Không có nó thì mọi chẩn đoán đều là đoán:
# người dùng chỉ thấy câu tiếng Việt đã được dịch sẵn, còn nguyên văn lỗi của Google —
# thứ duy nhất nói được là quota hay 503 hay tên model sai — thì không ai nhìn thấy.
_LOI_GAN_NHAT: dict = {}


# Google nhét thông tin quyết định vào PHẦN ĐUÔI của thông báo lỗi:
#   * Quota exceeded for metric: generativelanguage.googleapis.com/…_free_tier_requests,
#     limit: 0
# `limit: 0` nghĩa là model đó KHÔNG có gói free — mọi khoá đều hỏng ngay lập tức, và
# thêm bao nhiêu khoá cũng vô ích. `limit: 250` nghĩa là hạn mức thật và đã dùng hết.
# Hai bệnh hoàn toàn khác nhau, mà chỉ phân biệt được bằng đúng con số này. Cắt chuỗi
# ở 400 ký tự thì cắt mất nó — đã vấp một lần rồi.
# Google viết cùng một thứ bằng HAI kiểu tuỳ đường trả lỗi, và phải bắt được cả hai:
#   • văn xuôi     : "* Quota exceeded for metric: generativelanguage.…, limit: 0"
#   • có cấu trúc  : "quota_metric": "generativelanguage.…"  (khối QuotaFailure)
# Chỉ khớp kiểu có cấu trúc là hụt đúng dạng đang gặp trên bản triển khai.
_RE_HAN_MUC = re.compile(
    r"(?:quota[_ ]?(?:metric|id)|quota exceeded for metric)"
    r"['\"]?\s*[:=]\s*['\"]?([\w./-]+)",
    re.I,
)
_RE_GIA_TRI = re.compile(r"(?:limit|quota_value)['\"]?\s*[:=]\s*['\"]?(\d+)", re.I)


def _ghi_loi_gan_nhat(nhan: str, e: BaseException) -> None:
    van = _che_khoa(str(e))
    han_muc: dict = {}
    m = _RE_HAN_MUC.search(van)
    if m:
        han_muc["metric"] = m.group(1)
    g = _RE_GIA_TRI.search(van)
    if g:
        han_muc["gia_tri"] = int(g.group(1))
        # Nói thẳng ra kết luận thay vì bắt người đọc tự suy: 0 là bệnh khác hẳn.
        han_muc["nghia"] = (
            "model KHÔNG có gói free — thêm khoá cũng vô ích, phải ĐỔI MODEL"
            if han_muc["gia_tri"] == 0
            else "hạn mức thật và đã dùng hết — thêm khoá ở project khác sẽ có thêm lượt"
        )
    _LOI_GAN_NHAT.clear()
    _LOI_GAN_NHAT.update({
        "bac": nhan,
        "luc": time.time(),
        "han_muc": han_muc,
        "loi": van[:1500],
    })


def loi_llm_gan_nhat() -> dict:
    """Nguyên văn lỗi gần nhất (đã che khoá) — cho /metrics."""
    if not _LOI_GAN_NHAT:
        return {}
    ra = dict(_LOI_GAN_NHAT)
    ra["cach_day_giay"] = int(time.time() - ra.pop("luc"))
    return ra


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


def _het_bac(model_chet: set[str]) -> Exception:
    """Lỗi ném ra khi bậc cuối bị BỎ QUA vì model của nó đã chết — không có ngoại lệ
    thật nào để ném lại. Thông báo phải nói ĐÚNG bệnh: model bị gỡ, không phải hết
    lượt. Nhầm hai cái này là đi thay khoá cho một vấn đề mà thay khoá không chữa."""
    ten = ", ".join(sorted(model_chet))
    return RuntimeError(
        f"NOT_FOUND: model đã bị Google gỡ ({ten}) và không còn bậc nào khác để thử. "
        f"Đổi MODEL_NAME / MODEL_FALLBACKS sang model còn phục vụ — xem "
        f"/admin/kiem-khoa để biết khoá của bạn dùng được model nào."
    )


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

    def _xu_ly_loi(self, nhan: str, e: BaseException) -> str | None:
        """Chung cho cả hai lối gọi — sửa một chỗ thì cả hai cùng đổi.

        Ném lại nguyên vẹn nếu là lỗi THẬT. Ngược lại trả về LOẠI bệnh: "quota" |
        "model" | None (nhất thời). Ba loại phải xử lý khác nhau, gộp lại là hỏng:
        quota thì treo đúng bậc đó, model bị gỡ thì treo CẢ MODEL, còn 503 thì không
        treo gì cả."""
        _ghi_loi_gan_nhat(nhan, e)
        if not _nen_doi_bac(e):
            raise e

        if _la_loi_model_bien_mat(e):
            # Google gỡ model → MỌI khoá của model đó đều 404. Treo cả cụm, và treo
            # LÂU: model bị gỡ không quay lại trong ngày. Nếu chỉ treo mỗi bậc này thì
            # lượt gọi kế đâm tiếp vào 9 khoá còn lại của đúng model đã chết.
            ten = _ten_model(nhan)
            for n in self._nhan:
                if _ten_model(n) == ten:
                    _NGHI[n] = time.time() + 24 * 3600
            logger.error(
                "MODEL %s đã bị Google gỡ (404). Treo toàn bộ %d bậc của model này và "
                "rơi sang model khác. Cần đổi MODEL_NAME/MODEL_FALLBACKS.",
                ten, sum(1 for n in self._nhan if _ten_model(n) == ten),
            )
            return "model"

        if _la_loi_het_quota(e):
            _cho_nghi(nhan)
            logger.warning(
                "%s hết hạn mức → nghỉ %d phút, rơi sang bậc kế",
                nhan, settings.quota_cooldown_min,
            )
            return "quota"

        # 503/UNAVAILABLE: đổi bậc nhưng KHÔNG treo bậc này. Khoá không mất gì, Google
        # chỉ đang bận — treo nó là tự vứt một bậc còn nguyên hạn mức.
        logger.warning("%s quá tải nhất thời → rơi sang bậc kế (KHÔNG cho nghỉ)", nhan)
        return None

    def _go_nghi_neu_CA_DAY_cung_chet(self, da_nghi: list[str], tong: int) -> None:
        """CẢ DÂY cùng chết trong MỘT lượt = nguyên nhân CHUNG, không phải từng khoá cạn.

        Mười khoá của mười project khác nhau KHÔNG THỂ cùng cạn hạn mức ngày trong vài
        chục giây. Khi chuyện đó xảy ra, thủ phạm nằm ở chỗ CHUNG trên đường đi — proxy
        chết, mạng đứt, tên model sai, tài khoản bị chặn — và mỗi bậc chỉ đang vọng lại
        cùng một sự cố.

        Đánh dấu cả dây "nghỉ 15 phút" lúc đó là tự khoá mình ra ngoài suốt 15 phút vì
        một sự cố chẳng liên quan gì tới hạn mức. ĐÃ ĐO THẬT trên bản triển khai: 20/20
        bậc bị treo trong một khoảng 50 giây, ngay giữa lúc đang cần dùng.

        Đúng là ta KHÔNG phân biệt được ca này với ca "mọi khoá cùng một project và đều
        cạn thật". Nhưng hai cái giá không bằng nhau: đoán sai kiểu này thì chỉ tốn một
        chuỗi gọi chậm cho thứ vốn đã hỏng, còn đoán sai kiểu kia thì tự tắt trợ lý 15
        phút giữa buổi bảo vệ."""
        if tong >= 2 and len(da_nghi) == tong:
            for n in da_nghi:
                _NGHI.pop(n, None)
            logger.error(
                "CẢ %d bậc cùng hỏng trong MỘT lượt — sự cố CHUNG chứ không phải hết hạn "
                "mức. Không cho bậc nào nghỉ. Nguyên văn lỗi: xem `llm_loi_gan_nhat` "
                "trong /metrics.", tong,
            )

    async def ainvoke(self, dau_vao, **kw):
        thu = self._thu_tu()
        cuoi = len(thu) - 1
        can_quota: list[str] = []
        model_chet: set[str] = set()
        for i, (nhan, m) in enumerate(thu):
            # Model này vừa 404 ở bậc trước → 9 khoá còn lại của nó cũng 404. Bỏ qua
            # NGAY trong lượt này, đừng đợi lần sau: mỗi lượt gọi vô ích là ~2 giây
            # người dùng ngồi nhìn màn hình đứng im.
            if _ten_model(nhan) in model_chet:
                if i == cuoi:
                    self._go_nghi_neu_CA_DAY_cung_chet(can_quota, len(thu))
                    raise _het_bac(model_chet)
                continue
            try:
                return await m.ainvoke(dau_vao, **kw)
            except Exception as e:
                loai = self._xu_ly_loi(nhan, e)
                if loai == "quota":
                    can_quota.append(nhan)
                elif loai == "model":
                    model_chet.add(_ten_model(nhan))
                if i == cuoi:
                    self._go_nghi_neu_CA_DAY_cung_chet(can_quota, len(thu))
                    raise
        raise RuntimeError("chuỗi LLM rỗng")   # không tới được: __init__ luôn có ≥1

    def invoke(self, dau_vao, **kw):
        thu = self._thu_tu()
        cuoi = len(thu) - 1
        can_quota: list[str] = []
        model_chet: set[str] = set()
        for i, (nhan, m) in enumerate(thu):
            if _ten_model(nhan) in model_chet:
                if i == cuoi:
                    self._go_nghi_neu_CA_DAY_cung_chet(can_quota, len(thu))
                    raise _het_bac(model_chet)
                continue
            try:
                return m.invoke(dau_vao, **kw)
            except Exception as e:
                loai = self._xu_ly_loi(nhan, e)
                if loai == "quota":
                    can_quota.append(nhan)
                elif loai == "model":
                    model_chet.add(_ten_model(nhan))
                if i == cuoi:
                    self._go_nghi_neu_CA_DAY_cung_chet(can_quota, len(thu))
                    raise
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
