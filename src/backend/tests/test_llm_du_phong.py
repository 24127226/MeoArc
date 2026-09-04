"""Dự phòng nhiều model — cứu buổi trình bày khỏi chết vì hết hạn mức.

── SỐ ĐO GỐC (29/08/2026) ──
Gemini free tính hạn mức RIÊNG TỪNG MODEL, mỗi model **20 lượt/ngày** — khoảng 10–15
lượt chat. Đủ để chết giữa buổi bảo vệ.

Đo ngày 29/08/2026 còn lộ thêm hai chuyện mà một chuỗi dự phòng "viết cho có" sẽ bỏ sót:
  • Đích dự phòng có thể BIẾN MẤT. `gemini-2.5-flash` bị Google gỡ ("no longer available
    to new users") ngay trong ngày — chuỗi rơi đúng, nhưng rơi vào một model 404. Chuỗi
    dự phòng phải được kiểm định kỳ, không phải đặt một lần rồi quên.
  • Hai model trong chuỗi = 40 lượt/ngày, KHÔNG phải vô hạn. Kịch bản đo tốn 2-3 lượt mỗi
    câu hỏi nên tự nó đốt sạch cả hai model trước khi chạy xong.

Điều quan trọng nhất được khoá ở đây KHÔNG phải "có rơi sang model khác không", mà là
"CÓ RƠI NHẦM KHÔNG": rơi sang model sau vì một lỗi thật (schema tool sai, khoá hỏng) thì
lỗi đó được che đi trong im lặng, và ta mất luôn tín hiệu duy nhất về nó.
"""

from __future__ import annotations

import pytest

from app.core.llm import LLMDuPhong, _la_loi_het_quota


class _Model:
    """Model giả: hoặc ném lỗi định sẵn, hoặc trả về tên mình."""

    def __init__(self, ten: str, loi: Exception | None = None):
        self.ten = ten
        self.loi = loi
        self.so_lan_goi = 0

    def bind_tools(self, tools):
        return _Model(self.ten + "+tools", self.loi)

    def with_structured_output(self, *a, **kw):
        return _Model(self.ten + "+struct", self.loi)

    async def ainvoke(self, _dau_vao, **kw):
        self.so_lan_goi += 1
        if self.loi:
            raise self.loi
        return self.ten

    def invoke(self, _dau_vao, **kw):
        self.so_lan_goi += 1
        if self.loi:
            raise self.loi
        return self.ten


HET_QUOTA = RuntimeError(
    "Error calling model 'gemini-2.5-flash-lite' (RESOURCE_EXHAUSTED): 429 ..."
)
LOI_THAT = ValueError("Invalid input for tool 'search_emails': field required")


# ── Nhận diện lỗi ────────────────────────────────────────────────────────────

def test_nhan_dung_loi_het_quota():
    assert _la_loi_het_quota(HET_QUOTA) is True


def test_KHONG_nham_loi_that_thanh_het_quota():
    """Đây là phép kiểm quan trọng nhất trong file. Nhận nhầm thì mọi lỗi đều được
    chữa bằng cách đổi model, và bug thật không bao giờ lộ ra."""
    assert _la_loi_het_quota(LOI_THAT) is False


# ── Hành vi rơi ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_binh_thuong_chi_goi_model_dau():
    a, b = _Model("A"), _Model("B")
    assert await LLMDuPhong([a, b]).ainvoke("x") == "A"
    assert b.so_lan_goi == 0, "model dự phòng KHÔNG được gọi khi model đầu chạy được"


@pytest.mark.asyncio
async def test_het_quota_thi_roi_sang_model_ke():
    a, b = _Model("A", HET_QUOTA), _Model("B")
    assert await LLMDuPhong([a, b]).ainvoke("x") == "B"
    assert b.so_lan_goi == 1


@pytest.mark.asyncio
async def test_roi_qua_NHIEU_bac():
    a, b, c = _Model("A", HET_QUOTA), _Model("B", HET_QUOTA), _Model("C")
    assert await LLMDuPhong([a, b, c]).ainvoke("x") == "C"


@pytest.mark.asyncio
async def test_loi_THAT_thi_nem_ra_ngay_KHONG_roi():
    """Lỗi thật phải nổi lên nguyên vẹn ở model ĐẦU TIÊN — không thử model khác."""
    a, b = _Model("A", LOI_THAT), _Model("B")
    with pytest.raises(ValueError):
        await LLMDuPhong([a, b]).ainvoke("x")
    assert b.so_lan_goi == 0, "lỗi thật không được che bằng cách đổi model"


@pytest.mark.asyncio
async def test_het_quota_o_model_CUOI_thi_nem_ra():
    """Cạn sạch mọi model thì phải báo lỗi, không được nuốt rồi trả rỗng."""
    a, b = _Model("A", HET_QUOTA), _Model("B", HET_QUOTA)
    with pytest.raises(RuntimeError):
        await LLMDuPhong([a, b]).ainvoke("x")


# ── Bọc lại phải giữ nguyên chuỗi ────────────────────────────────────────────

def test_bind_tools_ap_cho_MOI_model():
    """Bind cho mỗi model một lần. Thiếu một cái thì lúc rơi xuống nó, model đó không
    biết tool nào cả và agent lập tức bịa câu trả lời — đúng lỗi từng gặp trước đây."""
    goi = LLMDuPhong([_Model("A"), _Model("B")]).bind_tools([])
    assert len(goi._chuoi) == 2
    assert all(m.ten.endswith("+tools") for m in goi._chuoi)


def test_with_structured_output_ap_cho_MOI_model():
    goi = LLMDuPhong([_Model("A"), _Model("B")]).with_structured_output(dict)
    assert all(m.ten.endswith("+struct") for m in goi._chuoi)


# ── Dựng chuỗi từ cấu hình ───────────────────────────────────────────────────

def test_bo_model_du_phong_TRUNG_voi_model_chinh(monkeypatch):
    """Rơi sang chính mình thì chỉ tốn thêm một lần gọi hỏng rồi vẫn lỗi như cũ."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1")
    monkeypatch.setattr(mod.settings, "model_name", "gemini-2.5-flash")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "gemini-2.5-flash")
    monkeypatch.setattr(mod, "create_llm", lambda ten=None, khoa=None: _Model(ten or "chinh"))
    ra = mod.create_llm_du_phong()
    assert not isinstance(ra, LLMDuPhong), "trùng tên thì không nên dựng chuỗi"


def test_khong_cau_hinh_du_phong_thi_tra_ve_llm_thuong(monkeypatch):
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "")
    monkeypatch.setattr(mod, "create_llm", lambda ten=None, khoa=None: _Model(ten or "chinh"))
    assert not isinstance(mod.create_llm_du_phong(), LLMDuPhong)


def test_model_du_phong_dung_hong_KHONG_lam_chet_agent(monkeypatch):
    """Một tên model gõ sai trong .env không được làm chết cả agent — bỏ qua nó thôi."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1")
    monkeypatch.setattr(mod.settings, "model_name", "chinh")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "hong,tot")

    def gia(ten=None, khoa=None):
        if ten == "hong":
            raise RuntimeError("không dựng được")
        return _Model(ten or "chinh")

    monkeypatch.setattr(mod, "create_llm", gia)
    ra = mod.create_llm_du_phong()
    assert isinstance(ra, LLMDuPhong)
    assert len(ra._chuoi) == 2, "phải còn model chính + model dự phòng dựng được"


# ══════════════════════════════════════════════════════════════════════════════
# TRỤC THỨ HAI: NHIỀU KHOÁ
#
# Vì sao có phần này. Khoá chỉ được đọc MỘT LẦN lúc dựng `settings`, còn client LLM
# thì nằm trong biến toàn cục ở agent_node — nên đổi khoá bắt buộc phải khởi động lại
# tiến trình. Máy nhà 2 giây; trên Azure là khởi động lại cả container, đo được 2–4
# phút và không có tín hiệu nào cho biết còn bao lâu. Nạp sẵn mọi khoá thì lúc cạn
# không phải đụng vào Azure giữa buổi trình bày nữa.
# ══════════════════════════════════════════════════════════════════════════════

from app.core.config import Settings
from app.core.llm import _NGHI, _cho_nghi, _dang_nghi, _nhan_bac, trang_thai_khoa


@pytest.fixture(autouse=True)
def _don_bo_nho_nghi():
    """`_NGHI` sống ở tầng module nên nó RÒ TỪ CA NÀY SANG CA KHÁC. Một ca đánh dấu
    "bậc 1 nghỉ" là mọi ca sau đó chạy trên một chuỗi đã bị xếp lại thứ tự — hỏng theo
    kiểu chạy riêng thì xanh, chạy cả file thì đỏ, và rất lâu mới lần ra."""
    _NGHI.clear()
    yield
    _NGHI.clear()


# ── Tách danh sách khoá ──────────────────────────────────────────────────────

def test_mot_khoa_van_nhu_cu():
    """Không ai phải sửa .env vì tính năng này."""
    assert Settings(ai_api_key="AIzaMotKhoa").danh_sach_khoa_ai == ["AIzaMotKhoa"]


def test_tach_nhieu_khoa_theo_dau_phay_va_xuong_dong():
    """Dán từ AI Studio ra hay dính sẵn dòng mới và khoảng trắng."""
    s = Settings(ai_api_key="k1, k2\nk3,  k4 ")
    assert s.danh_sach_khoa_ai == ["k1", "k2", "k3", "k4"]


def test_bo_khoa_TRUNG_nhung_giu_thu_tu():
    """Khoá đứng hai lần = khi nó cạn, chuỗi thử lại đúng nó lần nữa: tốn thêm một
    lượt gọi CHẮC CHẮN hỏng, đúng lúc đang cần câu trả lời nhất."""
    assert Settings(ai_api_key="k1,k2,k1,k3").danh_sach_khoa_ai == ["k1", "k2", "k3"]


def test_khong_co_khoa_thi_danh_sach_rong():
    assert Settings(ai_api_key="").danh_sach_khoa_ai == []
    assert Settings(ai_api_key="").khoa_ai_dau_tien == ""


def test_khoa_dau_tien_KHONG_phai_ca_chuoi():
    """Chỗ nào không có chuỗi dự phòng (embeddings) mà đọc thẳng `ai_api_key` thì đang
    dán cả "k1,k2,k3" vào header x-goog-api-key → 400, và thông báo lỗi của Google
    không hề nhắc gì tới dấu phẩy nên rất lâu mới lần ra."""
    assert Settings(ai_api_key="k1,k2,k3").khoa_ai_dau_tien == "k1"


# ── Dựng chuỗi model × khoá ──────────────────────────────────────────────────

def _bay_create_llm(monkeypatch, mod):
    """Ghi lại đúng thứ tự (model, khoá) mà chuỗi được dựng."""
    da_dung: list[tuple] = []

    def gia(ten=None, khoa=None):
        da_dung.append((ten, khoa))
        return _Model(f"{ten}|{khoa}")

    monkeypatch.setattr(mod, "create_llm", gia)
    return da_dung


def test_chuoi_no_ra_thanh_model_NHAN_khoa(monkeypatch):
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1,k2,k3")
    monkeypatch.setattr(mod.settings, "model_name", "m1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "m2")
    _bay_create_llm(monkeypatch, mod)

    ra = mod.create_llm_du_phong()
    assert isinstance(ra, LLMDuPhong)
    assert len(ra._chuoi) == 6, "2 model × 3 khoá"


def test_DOI_KHOA_TRUOC_roi_moi_ha_model(monkeypatch):
    """Phép kiểm quan trọng nhất của phần này.

    Đổi khoá thì người dùng không nhận ra gì — cùng model, cùng chất lượng. Hạ model
    thì giọng văn và khả năng suy luận đổi theo. Nên phải vét sạch khoá của model tốt
    TRƯỚC khi chịu xuống model kém hơn. Xếp ngược lại thì câu hỏi thứ hai của buổi
    demo đã chạy bằng model dự phòng trong khi model chính vẫn còn nguyên hạn mức ở
    khoá #2."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1,k2")
    monkeypatch.setattr(mod.settings, "model_name", "m1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "m2")
    da_dung = _bay_create_llm(monkeypatch, mod)

    mod.create_llm_du_phong()
    assert da_dung == [("m1", "k1"), ("m1", "k2"), ("m2", "k1"), ("m2", "k2")]


def test_mot_khoa_thi_chuoi_y_HET_nhu_truoc(monkeypatch):
    """Không có khoá thứ hai thì không được đẻ thêm bậc nào."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1")
    monkeypatch.setattr(mod.settings, "model_name", "m1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "m2")
    _bay_create_llm(monkeypatch, mod)
    assert len(mod.create_llm_du_phong()._chuoi) == 2


def test_nhieu_khoa_MOT_model_van_dung_chuoi(monkeypatch):
    """Không khai MODEL_FALLBACKS nhưng có 3 khoá thì vẫn phải có 3 bậc — nếu không,
    người dùng dán đủ 3 khoá vào .env rồi vẫn chết ở khoá đầu mà không hiểu vì sao."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1,k2,k3")
    monkeypatch.setattr(mod.settings, "model_name", "m1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "")
    _bay_create_llm(monkeypatch, mod)
    assert len(mod.create_llm_du_phong()._chuoi) == 3


@pytest.mark.asyncio
async def test_het_quota_khoa_1_thi_sang_khoa_2_CUNG_model(monkeypatch):
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "ai_api_key", "k1,k2")
    monkeypatch.setattr(mod.settings, "model_name", "m1")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "m2")
    monkeypatch.setattr(
        mod, "create_llm",
        lambda ten=None, khoa=None: _Model(f"{ten}|{khoa}",
                                           HET_QUOTA if khoa == "k1" else None),
    )
    assert await mod.create_llm_du_phong().ainvoke("x") == "m1|k2"


# ── Nhãn bậc KHÔNG được chứa khoá ────────────────────────────────────────────

def test_nhan_bac_KHONG_lo_khoa():
    """Nhãn đi thẳng vào log và vào /metrics. Lọt khoá vào đây là phát tán bí mật ra
    một nơi ai cũng đọc được, và không có cách nào thu lại."""
    nhan = _nhan_bac("gemini-2.5-flash-lite", 2, 3)
    assert "khoá #2" in nhan
    assert "AIza" not in nhan and "k1" not in nhan


def test_mot_khoa_thi_nhan_KHONG_deo_them_so():
    """Một con số luôn bằng 1 thì chỉ làm log ồn."""
    assert _nhan_bac("m1", 1, 1) == "m1"


# ── Nhớ bậc đã cạn ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bac_da_can_thi_LAN_SAU_khong_thu_lai(monkeypatch):
    """Không nhớ thì mỗi câu hỏi lại đâm vào đúng bậc đã chết — mà mỗi lần đâm còn
    kèm `max_retries=3` và backoff của riêng nó. Người dùng không thấy lỗi, chỉ thấy
    trợ lý chậm dần đều."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    a, b = _Model("A", HET_QUOTA), _Model("B")
    chuoi = LLMDuPhong([a, b], ["A", "B"])

    assert await chuoi.ainvoke("x") == "B"
    assert a.so_lan_goi == 1

    assert await chuoi.ainvoke("x") == "B"
    assert a.so_lan_goi == 1, "bậc đã cạn KHÔNG được gọi lại trong thời gian nghỉ"
    assert b.so_lan_goi == 2


@pytest.mark.asyncio
async def test_bo_nho_nghi_DUNG_CHUNG_giua_cac_chuoi(monkeypatch):
    """agent và bộ trình bày là HAI chuỗi khác nhau nhưng cùng đi qua một khoá. Nhớ
    riêng thì agent học được "khoá #1 chết" còn bộ trình bày vẫn tự đâm đầu vào lần
    nữa — mỗi câu hỏi đốt oan thêm một lượt."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    a1, b1 = _Model("A", HET_QUOTA), _Model("B")
    await LLMDuPhong([a1, b1], ["A", "B"]).ainvoke("x")

    a2, b2 = _Model("A", HET_QUOTA), _Model("B")
    assert await LLMDuPhong([a2, b2], ["A", "B"]).ainvoke("x") == "B"
    assert a2.so_lan_goi == 0, "chuỗi thứ hai phải THỪA HƯỞNG hiểu biết của chuỗi đầu"


@pytest.mark.asyncio
async def test_moi_bac_deu_nghi_thi_VAN_THU_chu_khong_tu_choi(monkeypatch):
    """Thời gian nghỉ chỉ là phỏng đoán (Google trả cùng một mã cho hạn mức phút và
    hạn mức ngày). Nó đủ để SẮP LẠI THỨ TỰ, không đủ để tự cho phép mình từ chối phục
    vụ — biết đâu hạn mức đã hồi rồi."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    _cho_nghi("A")
    _cho_nghi("B")
    b = _Model("B")
    assert await LLMDuPhong([_Model("A", HET_QUOTA), b], ["A", "B"]).ainvoke("x") == "B"
    assert b.so_lan_goi == 1


@pytest.mark.asyncio
async def test_bac_dang_nghi_XUONG_CUOI_chu_khong_bi_bo(monkeypatch):
    """Bậc nghỉ vẫn là lưới cuối. Bỏ hẳn thì lúc mọi bậc cùng nghỉ ta phải bịa ra một
    lỗi mới để ném, trong khi thứ người dùng cần lúc đó là cứ thử."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    _cho_nghi("A")
    a = _Model("A")
    assert await LLMDuPhong([a, _Model("B", HET_QUOTA)], ["A", "B"]).ainvoke("x") == "A"


@pytest.mark.asyncio
async def test_loi_THAT_khong_lam_bac_bi_cho_nghi(monkeypatch):
    """Cho một bậc nghỉ vì lỗi schema tool thì ta vừa che mất lỗi thật, vừa tự tay
    loại một bậc còn nguyên hạn mức — hỏng gấp đôi."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(ValueError):
        await LLMDuPhong([_Model("A", LOI_THAT), _Model("B")], ["A", "B"]).ainvoke("x")
    assert not _dang_nghi("A")


@pytest.mark.asyncio
async def test_can_SACH_ca_day_thi_van_nem_loi(monkeypatch):
    """Cạn sạch thì phải ném lỗi, không được nuốt rồi trả rỗng.

    ── CA NÀY TỪNG KHẲNG ĐỊNH NGƯỢC LẠI ──
    Bản đầu còn assert thêm rằng cả hai bậc đều bị treo. Đo thật trên bản triển khai
    ngày 02/09/2026 cho thấy niềm tin đó sai và sai đắt: 20/20 bậc bị treo trong một
    khoảng 50 giây, tức là tự tắt trợ lý 15 phút ngay giữa lúc đang dùng. Cả dây cùng
    chết trong một lượt là dấu hiệu sự cố CHUNG, không phải từng khoá cạn — xem
    `_go_nghi_neu_CA_DAY_cung_chet` và ca `test_CA_DAY_het_quota_thi_KHONG_treo_bac_nao`.

    Phần "nhớ bậc đã cạn" vẫn còn nguyên cho ca thường gặp hơn: MỘT PHẦN chuỗi cạn còn
    phần khác chạy được (`test_chi_MOT_PHAN_can_thi_VAN_treo_dung_nhung_bac_do`)."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(RuntimeError):
        await LLMDuPhong(
            [_Model("A", HET_QUOTA), _Model("B", HET_QUOTA)], ["A", "B"]
        ).ainvoke("x")


def test_loi_dong_bo_cung_ghi_nho(monkeypatch):
    """`invoke` và `ainvoke` phải cư xử y hệt — chúng dùng chung `_xu_ly_loi`."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    ra = LLMDuPhong([_Model("A", HET_QUOTA), _Model("B")], ["A", "B"]).invoke("x")
    assert ra == "B"
    assert _dang_nghi("A")


def test_cooldown_0_thi_TAT_han_viec_nho(monkeypatch):
    """Lối thoát khi muốn quay lại hành vi cũ mà không phải sửa mã."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 0)
    _cho_nghi("A")
    assert not _dang_nghi("A")


# ── /metrics ─────────────────────────────────────────────────────────────────

def test_trang_thai_khoa_chi_liet_ke_bac_DANG_nghi(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    _cho_nghi("m1 - khoa 1")
    ra = trang_thai_khoa()
    assert len(ra) == 1
    assert ra[0]["bac"] == "m1 - khoa 1"
    assert 0 < ra[0]["nghi_them_giay"] <= 15 * 60


def test_trang_thai_khoa_rong_khi_moi_thu_con_song():
    assert trang_thai_khoa() == []


# ══════════════════════════════════════════════════════════════════════════════
# 503 "QUÁ TẢI" — ĐO ĐƯỢC TRÊN BẢN TRIỂN KHAI 02/09/2026
#
# Người dùng nạp 10 khoá của 10 project khác nhau, hỏi "thư nào cần xử lý trước", và
# nhận "Mô hình AI của Google đang quá tải". Hỏi lại thì nhận "hết quota". /metrics
# cho thấy CẢ 20 bậc (2 model × 10 khoá) bị treo trong một khoảng 50 giây.
#
# Hai lỗi lộ ra từ đó, và bộ ca dưới khoá cả hai lại:
#   1. Chuỗi CHỈ rơi khi hết hạn mức → một cú 503 ở bậc 1 giết cả yêu cầu trong khi
#      19 bậc còn lại ngồi không. Đúng là loại lỗi mà đổi bậc có ích nhất.
#   2. Cả dây cùng chết trong một lượt thì cả dây bị treo 15 phút — tự khoá mình ra
#      ngoài vì một sự cố CHUNG chẳng liên quan gì tới hạn mức.
# ══════════════════════════════════════════════════════════════════════════════

from app.core.llm import (
    _LOI_GAN_NHAT, _che_khoa, _la_loi_qua_tai_nhat_thoi, _nen_doi_bac,
    loi_llm_gan_nhat,
)

QUA_TAI = RuntimeError(
    "503 UNAVAILABLE. {'error': {'code': 503, 'message': 'The model is overloaded. "
    "Please try again later.', 'status': 'UNAVAILABLE'}}"
)


@pytest.fixture(autouse=True)
def _don_loi_gan_nhat():
    _LOI_GAN_NHAT.clear()
    yield
    _LOI_GAN_NHAT.clear()


# ── Nhận diện ────────────────────────────────────────────────────────────────

def test_nhan_dung_loi_qua_tai():
    assert _la_loi_qua_tai_nhat_thoi(QUA_TAI) is True


def test_qua_tai_KHONG_bi_nham_thanh_het_quota():
    """Hai bệnh khác nhau: hết quota là mình hết lượt, quá tải là Google đang đông.
    Chữa giống nhau thì lời khuyên cho người dùng sai, và bậc còn tốt bị treo oan."""
    assert _la_loi_het_quota(QUA_TAI) is False


def test_loi_THAT_khong_duoc_coi_la_dang_doi_bac():
    """Vẫn phải giữ nguyên tính chất cũ: lỗi schema tool không được chữa bằng đổi bậc."""
    assert _nen_doi_bac(LOI_THAT) is False
    assert _nen_doi_bac(HET_QUOTA) is True
    assert _nen_doi_bac(QUA_TAI) is True


# ── Hành vi rơi khi 503 ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_qua_tai_thi_VAN_ROI_sang_bac_ke(monkeypatch):
    """Lỗi đúng như người dùng gặp: bậc 1 quá tải, bậc 2 sống. Bản trước ném thẳng lỗi
    ra dù còn 19 bậc chưa dùng."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    a, b = _Model("A", QUA_TAI), _Model("B")
    assert await LLMDuPhong([a, b], ["A", "B"]).ainvoke("x") == "B"
    assert b.so_lan_goi == 1


@pytest.mark.asyncio
async def test_qua_tai_KHONG_cho_bac_do_nghi(monkeypatch):
    """Khoá không mất gì cả — Google chỉ đang bận. Treo nó 15 phút là tự vứt một bậc
    còn nguyên hạn mức, rồi câu hỏi sau phải chạy bằng model kém hơn."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    await LLMDuPhong([_Model("A", QUA_TAI), _Model("B")], ["A", "B"]).ainvoke("x")
    assert not _dang_nghi("A"), "503 KHÔNG được treo bậc"


@pytest.mark.asyncio
async def test_het_quota_VAN_cho_nghi_nhu_cu(monkeypatch):
    """Đừng sửa lỗi này mà làm hỏng lỗi kia."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    await LLMDuPhong([_Model("A", HET_QUOTA), _Model("B")], ["A", "B"]).ainvoke("x")
    assert _dang_nghi("A")


# ── Cả dây cùng chết = sự cố CHUNG ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_CA_DAY_het_quota_thi_KHONG_treo_bac_nao(monkeypatch):
    """Đây là ca đã xảy ra thật: 20/20 bậc bị treo trong 50 giây.

    Mười khoá của mười project KHÔNG THỂ cùng cạn hạn mức ngày trong vài chục giây —
    nên đó là sự cố chung, và treo cả dây là tự tắt trợ lý 15 phút giữa buổi bảo vệ."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = [f"k{i}" for i in range(4)]
    chuoi = LLMDuPhong([_Model(n, HET_QUOTA) for n in nhan], nhan)
    with pytest.raises(RuntimeError):
        await chuoi.ainvoke("x")
    assert not any(_dang_nghi(n) for n in nhan), (
        "cả dây cùng chết là dấu hiệu sự cố CHUNG — không được treo bậc nào"
    )


@pytest.mark.asyncio
async def test_chi_MOT_PHAN_can_thi_VAN_treo_dung_nhung_bac_do(monkeypatch):
    """Ranh giới của quy tắc trên. Một vài khoá cạn còn khoá khác chạy được là chuyện
    BÌNH THƯỜNG và có thật — lúc đó phải nhớ, nếu không thì mỗi câu hỏi lại đâm vào
    đúng những bậc đã chết."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    chuoi = LLMDuPhong(
        [_Model("k0", HET_QUOTA), _Model("k1", HET_QUOTA), _Model("k2")],
        ["k0", "k1", "k2"],
    )
    assert await chuoi.ainvoke("x") == "k2"
    assert _dang_nghi("k0") and _dang_nghi("k1")
    assert not _dang_nghi("k2")


@pytest.mark.asyncio
async def test_ca_day_QUA_TAI_thi_van_nem_loi_nhung_khong_treo(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["k0", "k1"]
    with pytest.raises(RuntimeError):
        await LLMDuPhong([_Model(n, QUA_TAI) for n in nhan], nhan).ainvoke("x")
    assert not any(_dang_nghi(n) for n in nhan)


def test_ca_day_chet_o_loi_dong_bo_cung_KHONG_treo(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["k0", "k1"]
    with pytest.raises(RuntimeError):
        LLMDuPhong([_Model(n, HET_QUOTA) for n in nhan], nhan).invoke("x")
    assert not any(_dang_nghi(n) for n in nhan)


# ── Nguyên văn lỗi cho /metrics ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ghi_lai_NGUYEN_VAN_loi_gan_nhat(monkeypatch):
    """Người dùng chỉ thấy câu tiếng Việt đã dịch sẵn. Khi bản dịch đoán SAI bệnh thì
    không còn đường nào lần ra — trừ chỗ này."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    await LLMDuPhong([_Model("A", QUA_TAI), _Model("B")], ["A", "B"]).ainvoke("x")
    ra = loi_llm_gan_nhat()
    assert ra["bac"] == "A"
    assert "overloaded" in ra["loi"]
    assert ra["cach_day_giay"] >= 0


def test_loi_gan_nhat_rong_khi_chua_co_gi():
    assert loi_llm_gan_nhat() == {}


def test_che_khoa_truoc_khi_ra_metrics(monkeypatch):
    """Thông báo lỗi của nhà cung cấp CÓ THỂ vọng lại khoá vừa gửi. /metrics không có
    xác thực, nên lọt khoá ra đây là phát tán bí mật và không thu lại được."""
    monkeypatch.setattr("app.core.llm.settings", Settings(ai_api_key="AIzaBIMAT123"))
    ra = _che_khoa("API key not valid: AIzaBIMAT123 rejected")
    assert "AIzaBIMAT123" not in ra
    assert "[da-che]" in ra


@pytest.mark.asyncio
async def test_loi_THAT_cung_duoc_ghi_lai(monkeypatch):
    """Lỗi thật vẫn ném ra nguyên vẹn, nhưng vẫn phải ghi — đó là loại đáng xem nhất."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(ValueError):
        await LLMDuPhong([_Model("A", LOI_THAT)], ["A"]).ainvoke("x")
    assert loi_llm_gan_nhat()["bac"] == "A"


# ══════════════════════════════════════════════════════════════════════════════
# BÓC CON SỐ HẠN MỨC RA KHỎI THÔNG BÁO LỖI
#
# Nguyên văn lỗi thật lấy từ bản triển khai 02/09/2026. Bản trước cắt chuỗi ở 400 ký
# tự và cắt mất đúng đoạn quan trọng: `Quota exceeded for metric: generati…`. Con số
# `limit` nằm ngay sau đó, và nó phân biệt HAI BỆNH KHÁC HẲN NHAU:
#   • limit: 0   → model không có gói free. Mọi khoá hỏng ngay. Thêm khoá VÔ ÍCH.
#   • limit: 250 → hạn mức thật, đã dùng hết. Thêm khoá ở project khác thì có thêm.
# Chữa nhầm bệnh này bằng thuốc của bệnh kia là mất cả buổi.
# ══════════════════════════════════════════════════════════════════════════════

LOI_THAT_TU_AZURE = RuntimeError(
    "Error calling model 'gemini-3.6-flash' (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. "
    "{'error': {'code': 429, 'message': 'You exceeded your current quota, please check "
    "your plan and billing details. For more information on this error, head to: "
    "https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, "
    "head to: https://ai.dev/rate-limit. \\n* Quota exceeded for metric: "
    "generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0"
    "'}}"
)


@pytest.mark.asyncio
async def test_boc_duoc_metric_va_gia_tri_han_muc(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(RuntimeError):
        await LLMDuPhong([_Model("A", LOI_THAT_TU_AZURE)], ["A"]).ainvoke("x")
    hm = loi_llm_gan_nhat()["han_muc"]
    assert "free_tier_requests" in hm["metric"]
    assert hm["gia_tri"] == 0


@pytest.mark.asyncio
async def test_limit_0_thi_noi_thang_la_PHAI_DOI_MODEL(monkeypatch):
    """Không bắt người đọc tự suy ra từ một con số 0. Đây là chỗ dễ đọc lướt qua nhất
    mà lại quyết định làm gì tiếp theo."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(RuntimeError):
        await LLMDuPhong([_Model("A", LOI_THAT_TU_AZURE)], ["A"]).ainvoke("x")
    assert "ĐỔI MODEL" in loi_llm_gan_nhat()["han_muc"]["nghia"]


@pytest.mark.asyncio
async def test_limit_KHAC_0_thi_khuyen_them_khoa(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    loi = RuntimeError(
        "429 RESOURCE_EXHAUSTED * Quota exceeded for metric: "
        "generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 250"
    )
    with pytest.raises(RuntimeError):
        await LLMDuPhong([_Model("A", loi)], ["A"]).ainvoke("x")
    hm = loi_llm_gan_nhat()["han_muc"]
    assert hm["gia_tri"] == 250
    assert "project khác" in hm["nghia"]


@pytest.mark.asyncio
async def test_giu_du_dai_de_KHONG_cat_mat_doan_han_muc(monkeypatch):
    """Chính lỗi đã vấp: 400 ký tự cắt đúng chỗ `Quota exceeded for metric: generati`."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(RuntimeError):
        await LLMDuPhong([_Model("A", LOI_THAT_TU_AZURE)], ["A"]).ainvoke("x")
    assert "limit: 0" in loi_llm_gan_nhat()["loi"]


@pytest.mark.asyncio
async def test_loi_khong_co_han_muc_thi_de_trong_chu_khong_bia(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    with pytest.raises(ValueError):
        await LLMDuPhong([_Model("A", LOI_THAT)], ["A"]).ainvoke("x")
    assert loi_llm_gan_nhat()["han_muc"] == {}


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE GỠ MODEL GIỮA CHỪNG — LẦN THỨ HAI (02/09/2026)
#
# Nguyên văn: "This model models/gemini-2.5-flash-lite is no longer available to new
# users. Please update your code to use models/gemini-3.5-flash-lite".
#
# Nghiệt ở mệnh đề "TO NEW USERS": khoá cũ vẫn gọi được, khoá VỪA TẠO thì 404. Nên
# thao tác "lập thêm project để có thêm hạn mức" lại chính là thao tác làm mất model
# chính — hai việc trông chẳng liên quan gì nhau, và triệu chứng thì giống hệt một
# lỗi cấu hình.
#
# 404 trước đó KHÔNG nằm trong danh sách được phép rơi, nên nó giết cả yêu cầu ngay ở
# bậc 1 dù 10 bậc của model kia vẫn dùng được.
# ══════════════════════════════════════════════════════════════════════════════

from app.core.llm import _la_loi_model_bien_mat, _ten_model

MODEL_GO = RuntimeError(
    "Error calling model 'gemini-2.5-flash-lite' (NOT_FOUND): 404 NOT_FOUND. "
    "{'error': {'code': 404, 'message': 'This model models/gemini-2.5-flash-lite is no "
    "longer available to new users. Please update your code to use "
    "models/gemini-3.5-flash-lite for the latest features and improvements.', "
    "'status': 'NOT_FOUND'}}"
)


def test_nhan_dung_loi_model_bi_go():
    assert _la_loi_model_bien_mat(MODEL_GO) is True


def test_KHONG_nham_model_bi_go_thanh_het_quota():
    """Ba bệnh, ba cách chữa khác hẳn. Nhầm 404 thành quota là đi thay khoá cho một
    vấn đề mà thay khoá không chữa được."""
    assert _la_loi_het_quota(MODEL_GO) is False
    assert _la_loi_model_bien_mat(HET_QUOTA) is False
    assert _la_loi_model_bien_mat(LOI_THAT) is False


def test_KHONG_dung_tim_chuoi_con_404():
    """Đã vấp đúng bẫy này với "429": ba ký tự số nằm trong id / URL / lịch sử thử lại
    cũng khớp, và một lần dán nhãn sai làm cả buổi đi tìm lỗi ở chỗ không có lỗi."""
    assert _la_loi_model_bien_mat(RuntimeError("tool call id abc404def failed")) is False


def test_tach_ten_model_khoi_nhan_bac():
    assert _ten_model("gemini-3.6-flash · khoá #2") == "gemini-3.6-flash"
    assert _ten_model("gemini-3.6-flash") == "gemini-3.6-flash"


@pytest.mark.asyncio
async def test_model_bi_go_thi_ROI_sang_model_khac(monkeypatch):
    """Lỗi đúng như người dùng gặp: model chính bị gỡ, model dự phòng vẫn sống."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["mA · khoá #1", "mB · khoá #1"]
    chuoi = LLMDuPhong([_Model("A", MODEL_GO), _Model("B")], nhan)
    assert await chuoi.ainvoke("x") == "B"


@pytest.mark.asyncio
async def test_model_bi_go_thi_BO_QUA_MOI_KHOA_cua_model_do(monkeypatch):
    """Phép kiểm quan trọng nhất ở đây. Model bị gỡ thì CẢ 10 khoá của nó đều 404 —
    đâm tiếp 9 lượt nữa là 9 lần chờ mạng vô ích, người dùng ngồi nhìn màn hình đứng
    im. Phải loại cả cụm ngay trong lượt hiện tại, không đợi lượt sau."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    chet = [_Model(f"A{i}", MODEL_GO) for i in range(3)]
    song = _Model("B")
    nhan = ["mA · khoá #1", "mA · khoá #2", "mA · khoá #3", "mB · khoá #1"]
    assert await LLMDuPhong([*chet, song], nhan).ainvoke("x") == "B"
    assert chet[0].so_lan_goi == 1
    assert chet[1].so_lan_goi == 0, "khoá #2 của model đã chết KHÔNG được gọi"
    assert chet[2].so_lan_goi == 0, "khoá #3 của model đã chết KHÔNG được gọi"


@pytest.mark.asyncio
async def test_model_bi_go_thi_treo_CA_CUM_cho_luot_sau(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["mA · khoá #1", "mA · khoá #2", "mB · khoá #1"]
    chuoi = LLMDuPhong(
        [_Model("A1", MODEL_GO), _Model("A2", MODEL_GO), _Model("B")], nhan)
    await chuoi.ainvoke("x")
    assert _dang_nghi("mA · khoá #1") and _dang_nghi("mA · khoá #2")
    assert not _dang_nghi("mB · khoá #1")


@pytest.mark.asyncio
async def test_moi_model_deu_bi_go_thi_bao_DUNG_BENH(monkeypatch):
    """Không còn bậc nào để thử thì vẫn phải nói rõ là MODEL bị gỡ, chứ không phải hết
    lượt — nếu không, người đọc lại đi thay khoá lần nữa."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["mA · khoá #1", "mA · khoá #2"]
    with pytest.raises(RuntimeError) as ex:
        await LLMDuPhong(
            [_Model("A1", MODEL_GO), _Model("A2", MODEL_GO)], nhan).ainvoke("x")
    assert "NOT_FOUND" in str(ex.value)
    assert "mA" in str(ex.value)


def test_model_bi_go_o_loi_dong_bo_cung_bo_qua_ca_cum(monkeypatch):
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    a2 = _Model("A2", MODEL_GO)
    nhan = ["mA · khoá #1", "mA · khoá #2", "mB · khoá #1"]
    ra = LLMDuPhong([_Model("A1", MODEL_GO), a2, _Model("B")], nhan).invoke("x")
    assert ra == "B"
    assert a2.so_lan_goi == 0


@pytest.mark.asyncio
async def test_model_go_KHONG_bi_quy_tac_ca_day_go_mat(monkeypatch):
    """Quy tắc "cả dây cùng chết thì gỡ hết đánh dấu" chỉ áp cho HẾT HẠN MỨC — đó là
    chỗ ta không phân biệt được sự cố chung với cạn thật. Model bị gỡ thì Google đã
    nói thẳng tên model, không có gì để đoán, nên đánh dấu phải được giữ."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    nhan = ["mA · khoá #1", "mA · khoá #2"]
    with pytest.raises(RuntimeError):
        await LLMDuPhong(
            [_Model("A1", MODEL_GO), _Model("A2", MODEL_GO)], nhan).ainvoke("x")
    assert _dang_nghi("mA · khoá #1"), "đánh dấu model-bị-gỡ KHÔNG được gỡ bỏ"


# ══════════════════════════════════════════════════════════════════════════════
# 499 CANCELLED và 504 DEADLINE_EXCEEDED — đo được khi chạy đủ 36 câu (03/09/2026)
#
# Ba câu chết vì chúng: Q8 (499), Q10 và Q11 (504). Không phải trả lời sai — là KHÔNG
# TRẢ LỜI ĐƯỢC, vì hai mã đó không nằm trong danh sách lỗi được phép rơi nên chúng
# giết cả yêu cầu thay vì sang model kế. Mà đây đúng là loại lỗi đổi bậc cứu được:
# cùng câu hỏi, model khác, thường chạy được ngay.
# ══════════════════════════════════════════════════════════════════════════════

CANCELLED = RuntimeError(
    "Error calling model 'gemini-3.5-flash' (CANCELLED): 499 CANCELLED. "
    "{'error': {'code': 499, 'message': 'The operation was cancelled.', "
    "'status': 'CANCELLED'}}"
)
QUA_HAN = RuntimeError(
    "504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired "
    "before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}}"
)


def test_nhan_dung_499_cancelled():
    assert _la_loi_qua_tai_nhat_thoi(CANCELLED) is True
    assert _nen_doi_bac(CANCELLED) is True


def test_nhan_dung_504_deadline():
    assert _la_loi_qua_tai_nhat_thoi(QUA_HAN) is True
    assert _nen_doi_bac(QUA_HAN) is True


def test_hai_ma_moi_KHONG_bi_coi_la_het_quota():
    """Phải rơi sang bậc kế NHƯNG không được treo bậc đó: model không mất gì cả,
    chỉ là lượt gọi đó trục trặc."""
    assert _la_loi_het_quota(CANCELLED) is False
    assert _la_loi_het_quota(QUA_HAN) is False


@pytest.mark.asyncio
async def test_499_thi_ROI_sang_bac_ke_va_KHONG_treo(monkeypatch):
    """Đúng ca Q8 đã gặp."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    assert await LLMDuPhong([_Model("A", CANCELLED), _Model("B")], ["A", "B"]).ainvoke("x") == "B"
    assert not _dang_nghi("A")


@pytest.mark.asyncio
async def test_504_thi_ROI_sang_bac_ke_va_KHONG_treo(monkeypatch):
    """Đúng ca Q10/Q11 đã gặp."""
    monkeypatch.setattr("app.core.llm.settings.quota_cooldown_min", 15)
    assert await LLMDuPhong([_Model("A", QUA_HAN), _Model("B")], ["A", "B"]).ainvoke("x") == "B"
    assert not _dang_nghi("A")


def test_KHONG_bat_bang_con_so_tran():
    """Lặp lại bài học từ "429" và "404": bắt bằng ba ký tự số thì id, URL hay lịch sử
    thử lại cũng khớp. Ở đây chỉ khớp TÊN MÃ, nên một chuỗi có số 504/499 lẫn trong id
    không được nhận nhầm."""
    assert _la_loi_qua_tai_nhat_thoi(RuntimeError("tool call id ab504cd failed")) is False
    assert _la_loi_qua_tai_nhat_thoi(RuntimeError("thread 499xyz not found")) is False
