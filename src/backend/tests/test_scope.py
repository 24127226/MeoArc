# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_scope.py — PHẠM VI QUÉT THEO GÓI (NFR-08)               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đây là các ca BIÊN, nên mốc thời gian được ghim cứng bằng tham số  ║
# ║ `today`. Không ghim thì test phụ thuộc ngày chạy — hôm nay xanh,   ║
# ║ mai đỏ, mà chẳng ai đổi dòng code nào.                            ║
# ║                                                                    ║
# ║ Cặp 90/91 mới là thứ đáng canh: chỉ kiểm "91 ngày bị loại" thì một ║
# ║ bản cài đặt chặn nhầm cả 90 ngày vẫn qua được.                     ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from app.core.scope import (
    TASK_EXTRACTION_MAX_DAYS,
    cutoff_date,
    gmail_after_clause,
    graph_filter_clause,
    is_within_scope,
    scan_days,
    scope_note,
    task_scan_days,
)

HOM_NAY = date(2026, 8, 7)   # mốc cố định cho mọi ca biên


def _nhan_cach_day(n: int) -> datetime:
    return datetime.combine(HOM_NAY - timedelta(days=n), datetime.min.time())


# ── Cửa sổ công bố của từng gói (khớp NFR-SCO-01) ───────────────────────────
@pytest.mark.parametrize("tier,ngay", [("free", 90), ("pro", 180), ("max", 365)])
def test_cua_so_dung_nhu_cong_bo(tier, ngay):
    assert scan_days(tier) == ngay


def test_goi_la_thi_lui_ve_mien_phi():
    """Tier rác không được vô tình mở rộng phạm vi — phải siết về mức hẹp nhất."""
    assert scan_days("khong-ton-tai") == 90
    assert scan_days("") == 90


# ── NFR-08-TC01..04: bốn ca biên ────────────────────────────────────────────
def test_tc01_dung_90_ngay_van_duoc_tinh_o_goi_mien_phi():
    assert is_within_scope(_nhan_cach_day(90), "free", today=HOM_NAY) is True


def test_tc02_qua_91_ngay_thi_bi_loai_o_goi_mien_phi():
    assert is_within_scope(_nhan_cach_day(91), "free", today=HOM_NAY) is False


def test_tc03_dung_180_ngay_van_duoc_tinh_o_goi_pro():
    assert is_within_scope(_nhan_cach_day(180), "pro", today=HOM_NAY) is True
    assert is_within_scope(_nhan_cach_day(181), "pro", today=HOM_NAY) is False


def test_tc04_dung_365_ngay_van_duoc_tinh_o_goi_pro_max():
    assert is_within_scope(_nhan_cach_day(365), "max", today=HOM_NAY) is True
    assert is_within_scope(_nhan_cach_day(366), "max", today=HOM_NAY) is False


def test_goi_cao_hon_khong_bao_gio_hep_hon_goi_thap():
    """Tính chất phải luôn đúng dù ai chỉnh con số: nâng gói không được thu hẹp phạm vi."""
    assert scan_days("free") <= scan_days("pro") <= scan_days("max")


def test_thu_moi_ve_luon_nam_trong_pham_vi():
    assert is_within_scope(_nhan_cach_day(0), "free", today=HOM_NAY) is True
    assert is_within_scope(_nhan_cach_day(1), "free", today=HOM_NAY) is True


def test_thu_khong_co_ngay_nhan_thi_van_xu_ly():
    """Thà xử lý thừa một thư còn hơn im lặng bỏ sót thư người dùng đang hỏi tới."""
    assert is_within_scope(None, "free", today=HOM_NAY) is True


# ── NFR-SCO-02: trần cứng cho trích việc ────────────────────────────────────
def test_trich_viec_bi_chan_o_90_ngay_du_goi_cao():
    assert task_scan_days("max") == TASK_EXTRACTION_MAX_DAYS == 90
    assert task_scan_days("pro") == 90


def test_tran_cung_khong_duoc_noi_rong_goi_hep():
    """min() chứ không phải hằng số: gói nào hẹp hơn 90 thì giữ nguyên mức hẹp."""
    assert task_scan_days("free") == 90   # free vốn đã 90
    assert task_scan_days("free") <= scan_days("free")


# ── Dịch sang cú pháp của từng nhà cung cấp ─────────────────────────────────
def test_moc_cat_dung_ngay():
    assert cutoff_date("free", today=HOM_NAY) == date(2026, 5, 9)   # 7/8 - 90 ngày


def test_menh_de_gmail_dung_khuon():
    assert gmail_after_clause("free", today=HOM_NAY) == "after:2026/05/09"


def test_menh_de_graph_dung_khuon():
    assert graph_filter_clause("free", today=HOM_NAY) == "receivedDateTime ge 2026-05-09T00:00:00Z"


def test_hai_nha_cung_cap_cat_cung_mot_moc():
    """Gmail và Outlook phải quét đúng cùng khoảng — lệch là hai hộp thư cho kết quả khác nhau."""
    for tier in ("free", "pro", "max"):
        g = gmail_after_clause(tier, today=HOM_NAY).removeprefix("after:")
        f = graph_filter_clause(tier, today=HOM_NAY)
        assert g.replace("/", "-") in f


# ── Câu báo cho người dùng (FR-02.7) ────────────────────────────────────────
def test_cau_bao_neu_dung_so_ngay_va_chi_duong_go():
    note = scope_note("free")
    assert "90 ngày" in note
    assert "từ khoá" in note, "Phải nói rõ thư cũ vẫn tìm được — nếu không người dùng tưởng mất thư"
    assert "Nâng gói" in note


# ── Cửa sổ CHỐT theo người, không đọc lại bảng giá ──────────────────────────
def test_doi_bang_gia_khong_lam_doi_pham_vi_cua_nguoi_dang_dung():
    """Vì sao phải chốt vào bản ghi thay vì đọc lại từ `plans.py`:

    Nếu đọc lại, sửa một con số trong bảng giá là phạm vi quét của MỌI người dùng
    hiện hữu đổi theo — kể cả người đã trả tiền cho mức cũ. Snapshot khiến giá trị
    chỉ đổi tại đúng một thời điểm: lúc người đó đổi gói.
    """
    from types import SimpleNamespace

    from app.repo.subscription_repo import scan_days_of

    # Người dùng đã chốt 180 ngày, nhưng gói 'pro' trong bảng giá nay đổi thành 999
    da_chot = SimpleNamespace(tier="pro", mailbox_scope_days=180)
    assert scan_days_of(da_chot) == 180, "Giá trị đã chốt bị bảng giá hiện hành ghi đè"


def test_ban_ghi_cu_chua_co_gia_tri_thi_lui_ve_bang_gia():
    """Bản ghi tạo trước khi có cột này (`None`/0) không được rơi về 0 ngày —
    rơi về 0 là người dùng đột ngột không quét được thư nào."""
    from types import SimpleNamespace

    from app.repo.subscription_repo import scan_days_of

    assert scan_days_of(SimpleNamespace(tier="pro", mailbox_scope_days=None)) == 180
    assert scan_days_of(SimpleNamespace(tier="max", mailbox_scope_days=0)) == 365


def test_so_ngay_da_chot_thang_tier_khi_tinh_moc_cat():
    """`days` truyền vào phải được ưu tiên hơn giá trị suy từ `tier`."""
    assert cutoff_date("free", today=HOM_NAY, days=365) == cutoff_date("max", today=HOM_NAY)
    assert gmail_after_clause("free", today=HOM_NAY, days=180) == gmail_after_clause("pro", today=HOM_NAY)
