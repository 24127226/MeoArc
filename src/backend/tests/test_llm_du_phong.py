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
    monkeypatch.setattr(mod.settings, "model_name", "gemini-2.5-flash")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "gemini-2.5-flash")
    monkeypatch.setattr(mod, "create_llm", lambda ten=None: _Model(ten or "chinh"))
    ra = mod.create_llm_du_phong()
    assert not isinstance(ra, LLMDuPhong), "trùng tên thì không nên dựng chuỗi"


def test_khong_cau_hinh_du_phong_thi_tra_ve_llm_thuong(monkeypatch):
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "model_fallbacks", "")
    monkeypatch.setattr(mod, "create_llm", lambda ten=None: _Model(ten or "chinh"))
    assert not isinstance(mod.create_llm_du_phong(), LLMDuPhong)


def test_model_du_phong_dung_hong_KHONG_lam_chet_agent(monkeypatch):
    """Một tên model gõ sai trong .env không được làm chết cả agent — bỏ qua nó thôi."""
    from app.core import llm as mod
    monkeypatch.setattr(mod.settings, "model_name", "chinh")
    monkeypatch.setattr(mod.settings, "model_fallbacks", "hong,tot")

    def gia(ten=None):
        if ten == "hong":
            raise RuntimeError("không dựng được")
        return _Model(ten or "chinh")

    monkeypatch.setattr(mod, "create_llm", gia)
    ra = mod.create_llm_du_phong()
    assert isinstance(ra, LLMDuPhong)
    assert len(ra._chuoi) == 2, "phải còn model chính + model dự phòng dựng được"
