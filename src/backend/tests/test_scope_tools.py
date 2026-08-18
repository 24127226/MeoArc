# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_scope_tools.py — CỬA SỔ QUÉT CÓ THẬT SỰ TỚI NƠI KHÔNG  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ test_scope.py canh phép TÍNH mốc. Ở đây canh phép TRUYỀN: mốc đó   ║
# ║ có đi tới lệnh gọi nhà cung cấp không, và có đi NHẦM chỗ không.    ║
# ║                                                                    ║
# ║ Tính đúng mà quên truyền là lỗi im lặng điển hình: không ai báo    ║
# ║ lỗi, hệ thống vẫn chạy, chỉ là giới hạn chưa từng có hiệu lực.     ║
# ║                                                                    ║
# ║ NFR-SCO-03 được canh riêng: tìm theo TỪ KHOÁ phải KHÔNG bị giới    ║
# ║ hạn. Áp nhầm vào đó là người dùng mất quyền tìm thư cũ của chính   ║
# ║ mình — siết quá tay cũng hỏng sản phẩm y như buông quá tay.        ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import asyncio

import pytest

from app.core.scope import cutoff_iso
from app.tools.registry import RequestContext
from app.tools.schemas import CategorizeEmailsInput, SearchEmailsInput, SemanticSearchInput


def _fake_email(i: int, subject: str = "S"):
    from app.schemas.email import Email
    return Email(id=f"id{i}", sender=f"N{i}", senderEmail=f"n{i}@x.vn", senderInitial="N",
                 to="", subject=subject, preview="p", body=["p"], time="09:00",
                 date="Hôm nay, 09:00", unread=False, starred=False,
                 category="moss", threadId=f"th{i}")


@pytest.fixture()
def bat_loi_goi(monkeypatch):
    """Chặn lời gọi nhà cung cấp và ghi lại tham số đã truyền xuống."""
    import app.tools.email_tools as et

    ghi: dict = {}

    def gia_lap(provider, token, **kw):
        ghi.update(kw)
        ghi["provider"] = provider
        return [_fake_email(0), _fake_email(1)], None

    monkeypatch.setattr(et.mail, "list_messages", gia_lap)
    return ghi


def _ctx(tier: str) -> RequestContext:
    return RequestContext(user_id="qa", access_token="tok", tier=tier)


# ── Cửa sổ PHẢI tới nơi ở các tool quét nội dung sẵn có ─────────────────────
@pytest.mark.parametrize("tier", ["free", "pro", "max"])
def test_phan_loai_truyen_dung_cua_so_cua_goi(bat_loi_goi, tier):
    import app.tools.email_tools as et

    asyncio.run(et.categorize_emails(CategorizeEmailsInput(limit=10), _ctx(tier)))
    assert bat_loi_goi.get("scan_after") == cutoff_iso(tier), (
        f"Gói {tier}: cửa sổ quét không tới được lệnh gọi hộp thư"
    )


@pytest.mark.parametrize("tier", ["free", "pro", "max"])
def test_tim_theo_nghia_truyen_dung_cua_so_cua_goi(bat_loi_goi, tier, monkeypatch):
    import app.core.embeddings as emb
    import app.tools.email_tools as et

    monkeypatch.setattr(emb, "embed_query", lambda q: [1.0, 0.0])
    monkeypatch.setattr(emb, "embed_texts", lambda docs: [[1.0, 0.0] for _ in docs])

    asyncio.run(et.semantic_search(SemanticSearchInput(query="tiền nong", limit=2), _ctx(tier)))
    assert bat_loi_goi.get("scan_after") == cutoff_iso(tier)


def test_goi_cao_hon_quet_nguoc_xa_hon(bat_loi_goi):
    """Nâng gói phải thấy được thư CŨ hơn — mốc cắt của gói cao phải SỚM hơn."""
    import app.tools.email_tools as et

    moc = {}
    for tier in ("free", "pro", "max"):
        asyncio.run(et.categorize_emails(CategorizeEmailsInput(limit=5), _ctx(tier)))
        moc[tier] = bat_loi_goi["scan_after"]
    assert moc["max"] < moc["pro"] < moc["free"]


def test_tier_la_thi_siet_ve_muc_hep_nhat(bat_loi_goi):
    """Ngữ cảnh mang tier rác không được vô tình mở toang phạm vi."""
    import app.tools.email_tools as et

    asyncio.run(et.categorize_emails(CategorizeEmailsInput(limit=5), _ctx("goi-ma")))
    assert bat_loi_goi["scan_after"] == cutoff_iso("free")


# ── NFR-SCO-03: tìm theo TỪ KHOÁ phải MIỄN TRỪ ──────────────────────────────
def test_tim_theo_tu_khoa_khong_bi_gioi_han(bat_loi_goi):
    """Giới hạn NFR-08 là giới hạn cho AI, không phải cho người dùng.

    Người dùng gõ từ khoá đi tìm thư năm ngoái của chính mình thì phải tìm thấy.
    Áp cửa sổ vào đây là biến một quy định về chi phí AI thành một lỗi mất dữ liệu.
    """
    import app.tools.email_tools as et

    asyncio.run(et.search_emails(SearchEmailsInput(query="hợp đồng", limit=10), _ctx("free")))
    assert bat_loi_goi.get("scan_after") is None, (
        "search_emails bị áp cửa sổ quét — trái NFR-SCO-03, người dùng mất quyền tìm thư cũ"
    )


# ── Báo cho người dùng khi không có gì trong phạm vi (FR-02.7) ──────────────
def test_khong_co_thu_trong_pham_vi_thi_noi_ro_ly_do(monkeypatch):
    """Trả 'hộp thư trống' cho người có 2000 thư là báo sai. Phải nói rõ là do gói."""
    import app.tools.email_tools as et

    monkeypatch.setattr(et.mail, "list_messages", lambda provider, token, **kw: ([], None))
    out = asyncio.run(et.semantic_search(SemanticSearchInput(query="tiền nong"), _ctx("free")))

    assert out.success is True
    assert "90 ngày" in out.message, "Không nói rõ cửa sổ của gói"
    assert "từ khoá" in out.message, "Không chỉ đường gỡ (thư cũ vẫn tìm được bằng từ khoá)"
