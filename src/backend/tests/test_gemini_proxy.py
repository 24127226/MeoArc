"""Đi vòng qua rào chặn theo vùng của Gemini — khoá lại phần nối dây.

Google chặn `generativelanguage.googleapis.com` theo vị trí MÁY CHỦ GỌI, mà bản
triển khai nằm trên Azure East Asia (Hong Kong) — vùng bị chặn. Cách chữa là đẩy
lời gọi qua Cloudflare Worker trong `infra/cf-gemini-proxy/`.

Mọi thứ ở đây đều hỏng theo kiểu IM LẶNG nếu nối dây sai: không ném lỗi, không ghi
log, chỉ là lời gọi vẫn đi thẳng ra Google từ Hong Kong như cũ — và triệu chứng thì
y hệt lúc chưa sửa gì. Đó là lý do đáng có test riêng.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from app.core import llm as mod_llm

GOC = Path(__file__).resolve().parents[3]
THU_MUC_WORKER = GOC / "infra" / "cf-gemini-proxy"


@pytest.fixture
def bat_kwargs(monkeypatch):
    """Chặn `init_chat_model` để xem create_llm() ĐỊNH gửi gì, khỏi gọi mạng thật."""
    da_bat: dict = {}

    def gia(**kwargs):
        da_bat.clear()
        da_bat.update(kwargs)
        return object()

    monkeypatch.setattr(mod_llm, "init_chat_model", gia)
    monkeypatch.setattr(mod_llm.settings, "ai_api_key", "khoa-gia")
    monkeypatch.setattr(mod_llm.settings, "model_provider", "google_genai")
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "")
    monkeypatch.setattr(mod_llm.settings, "ai_proxy_secret", "")
    return da_bat


# ── Nối dây phía Python ─────────────────────────────────────────────────────

def test_khong_dat_proxy_thi_goi_thang(bat_kwargs, monkeypatch):
    """Mặc định phải là gọi thẳng Google. Người chạy máy nhà không việc gì phải
    dựng Cloudflare mới dùng được agent."""
    mod_llm.create_llm()
    assert "base_url" not in bat_kwargs


def test_dat_proxy_thi_doi_noi_gui(bat_kwargs, monkeypatch):
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "https://proxy.workers.dev")
    mod_llm.create_llm()
    assert bat_kwargs["base_url"] == "https://proxy.workers.dev"


def test_cat_dau_gach_cheo_thua(bat_kwargs, monkeypatch):
    """SDK tự nối `/v1beta/...` vào sau. Còn gạch chéo cuối thì thành `//v1beta`,
    và Worker sẽ trả 404 vì đường dẫn không khớp danh sách cho phép. Dán URL từ
    bảng điều khiển Cloudflare thì rất hay dính gạch chéo cuối."""
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "https://proxy.workers.dev/")
    mod_llm.create_llm()
    assert bat_kwargs["base_url"] == "https://proxy.workers.dev"


def test_KHONG_ap_proxy_cho_nha_cung_cap_khac(bat_kwargs, monkeypatch):
    """Groq/OpenAI cũng có field `base_url` nhưng nó trỏ tới máy chủ CỦA HỌ. Bơm URL
    proxy Gemini vào đó là gửi thư sai nhà — và sai im lặng, vì cấu hình trông vẫn
    hợp lệ. Đây là lý do nhánh này phải kiểm tra nhà cung cấp chứ không chỉ kiểm tra
    'có đặt AI_BASE_URL hay không'."""
    monkeypatch.setattr(mod_llm.settings, "model_provider", "groq")
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "https://proxy.workers.dev")
    mod_llm.create_llm()
    assert "base_url" not in bat_kwargs


def test_bi_mat_di_kem_khi_co_dat(bat_kwargs, monkeypatch):
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "https://proxy.workers.dev")
    monkeypatch.setattr(mod_llm.settings, "ai_proxy_secret", "abc123")
    mod_llm.create_llm()
    assert bat_kwargs["additional_headers"] == {"x-meoarc-proxy": "abc123"}


def test_khong_dat_bi_mat_thi_khong_gui_header_rong(bat_kwargs, monkeypatch):
    """Gửi header rỗng thì Worker (nếu có đặt bí mật) sẽ từ chối với 401 mà thông
    điệp lại giống hệt lúc gõ sai khoá — mất công lần nhầm sang phía Google."""
    monkeypatch.setattr(mod_llm.settings, "ai_base_url", "https://proxy.workers.dev")
    mod_llm.create_llm()
    assert "additional_headers" not in bat_kwargs


def test_embeddings_cung_di_qua_proxy(monkeypatch):
    """Embedding gọi CÙNG máy chủ nên dính CÙNG lệnh chặn. Quên chỗ này thì agent
    chạy được mà tìm-theo-nghĩa vẫn hỏng — nửa sống nửa chết, rất khó khoanh."""
    from app.core import embeddings as mod_emb

    da_bat: dict = {}

    class GiaEmbed:
        def __init__(self, **kw):
            da_bat.update(kw)

    import langchain_google_genai as lgg
    monkeypatch.setattr(lgg, "GoogleGenerativeAIEmbeddings", GiaEmbed)
    monkeypatch.setattr(mod_emb.settings, "ai_api_key", "khoa-gia")
    monkeypatch.setattr(mod_emb.settings, "ai_base_url", "https://proxy.workers.dev")
    monkeypatch.setattr(mod_emb.settings, "ai_proxy_secret", "abc123")
    monkeypatch.setattr(mod_emb, "_embedder", None)

    mod_emb._get_embedder()
    assert da_bat["base_url"] == "https://proxy.workers.dev"
    assert da_bat["additional_headers"] == {"x-meoarc-proxy": "abc123"}
    mod_emb._embedder = None  # trả lại trạng thái sạch cho test khác


# ── Phía Worker: những chỗ sai là hỏng lặng ─────────────────────────────────

def _doc_worker() -> str:
    return (THU_MUC_WORKER / "src" / "worker.js").read_text(encoding="utf-8")


def test_worker_cho_qua_dung_duong_dan_ma_SDK_that_su_goi():
    """Đã đo bằng máy chủ giả: SDK gọi `/v1beta/models/<model>:generateContent`.
    Danh sách cho phép mà lệch tiền tố thì mọi lời gọi ăn 404 từ chính proxy."""
    assert "'/v1beta/'" in _doc_worker()


def test_worker_chuyen_tiep_dung_header_mang_khoa():
    """SDK gửi khoá ở `x-goog-api-key` (đã đo). Thiếu tên này trong danh sách cho
    phép thì Google nhận lời gọi KHÔNG có khoá và trả 401 — trông y như khoá hỏng."""
    assert "'x-goog-api-key'" in _doc_worker()


def test_worker_KHONG_chuyen_bi_mat_rieng_sang_google():
    """`x-meoarc-proxy` là chuyện riêng giữa backend và Worker. Lọt sang Google là
    rò bí mật ra bên thứ ba mà không có dấu hiệu nào."""
    noi_dung = _doc_worker()
    dau = noi_dung.index("HEADER_CHO_PHEP")
    cuoi = noi_dung.index("])", dau)
    assert "x-meoarc-proxy" not in noi_dung[dau:cuoi]


def test_worker_dung_durable_object_chu_khong_phai_fetch_thang():
    """CỐT LÕI của cả bản sửa. Worker thường chạy ở PoP gần người gọi nhất — tức là
    Hong Kong — nên lời gọi vẫn đi ra từ vùng bị chặn. Chỉ Durable Object mới ghim
    được vị trí. Bỏ mất chỗ này thì proxy vẫn 'chạy' và vẫn bị chặn y như cũ, mà
    nhìn vào thì tưởng đã sửa rồi."""
    noi_dung = _doc_worker()
    assert "locationHint" in noi_dung
    assert "CHUYEN_TIEP" in noi_dung


def test_cau_hinh_dung_kho_sqlite_de_chay_duoc_goi_MIEN_PHI():
    """Durable Object chỉ mở cho gói Workers miễn phí khi khai `new_sqlite_classes`.
    Dùng `new_classes` thì `wrangler deploy` đòi nâng gói."""
    cau_hinh = tomllib.loads((THU_MUC_WORKER / "wrangler.toml").read_text(encoding="utf-8"))
    di_tru = cau_hinh["migrations"][0]
    assert "new_sqlite_classes" in di_tru
    assert "new_classes" not in di_tru


def test_vung_ghim_KHONG_duoc_la_apac():
    """`apac` bao gồm cả Hong Kong. Chọn nó là có xác suất rơi đúng vào vùng đang bị
    chặn — sửa xong mà lúc được lúc không, kiểu lỗi tệ nhất để đi tìm."""
    cau_hinh = tomllib.loads((THU_MUC_WORKER / "wrangler.toml").read_text(encoding="utf-8"))
    assert cau_hinh["vars"]["VUNG"] in {"wnam", "enam", "weur", "eeur", "sam"}
