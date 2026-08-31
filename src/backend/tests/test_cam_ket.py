"""Bộ trích cam kết (bản backend) chạy qua BỘ CA DÙNG CHUNG.

Cùng file `src/shared/ca-cam-ket.json` mà bản TS ở frontend cũng phải chạy qua. Hai bản
cài đặt cùng một logic thì chắc chắn lệch nhau theo thời gian; một dòng chú thích "nhớ
sửa cả hai bên" không phải ràng buộc — nó chỉ là lời nhắc mà người ta quên. File ca
kiểm thử chung MỚI là ràng buộc.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.core import cam_ket as ck

# parents: tests → backend → src. Bộ ca nằm ở src/shared/, ngang hàng với backend.
CA = json.loads(
    (Path(__file__).resolve().parents[2] / "shared" / "ca-cam-ket.json")
    .read_text(encoding="utf-8")
)
MOC = datetime.fromisoformat(CA["moc"])


def _iso(d: datetime | None) -> str | None:
    return d.strftime("%Y-%m-%dT%H:%M") if d else None


# ── doc_han ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("c", CA["doc_han"], ids=[c["ten"] for c in CA["doc_han"]])
def test_doc_han(c):
    ra = ck.doc_han(c["van"], MOC)
    if c["han"] is None:
        assert ra is None, f"đáng lẽ không đọc ra mốc nào, lại ra {ra}"
        return
    assert ra is not None, "không đọc ra mốc nào"
    assert _iso(ra[0]) == c["han"]
    assert ra[1] is c["suy_ra"], (
        "sai cờ 'suy ra'. Cờ này quyết định giao diện HỎI hay tự khẳng định — "
        "khẳng định một phỏng đoán là cách nhanh nhất làm người dùng mất tin."
    )


# ── doc_khoang ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("c", CA["doc_khoang"], ids=[c["ten"] for c in CA["doc_khoang"]])
def test_doc_khoang(c):
    ra = ck.doc_khoang(c["van"], MOC)
    if c["han"] is None:
        assert ra is None
        return
    assert ra is not None
    assert _iso(ra[0]) == c["bat_dau"]
    assert _iso(ra[1]) == c["han"]


# ── trich_cam_ket: nhận đúng thứ đáng nhận ───────────────────────────────────

@pytest.mark.parametrize("c", CA["trich"], ids=[c["ten"] for c in CA["trich"]])
def test_trich(c):
    thu = {
        "id": "1", "subject": c["subject"], "body": c["body"],
        "priority": c["priority"], "sender": "Ai đó", "folder": "inbox",
    }
    ra = ck.trich_cam_ket([thu], MOC)
    assert (len(ra) == 1) is c["nhan"], (
        f"{'phải nhận' if c['nhan'] else 'phải BỎ QUA'} thư này"
    )
    if c["nhan"] and "khoang_ro_rang" in c:
        assert ra[0].khoang_ro_rang is c["khoang_ro_rang"]


# ── Những chỗ chỉ backend mới có ─────────────────────────────────────────────

def test_thu_da_gui_thanh_viec_CHO_HOI_AM():
    """Thư đã gửi = đang chờ người ta trả lời. Vẫn là việc phải theo dõi, và là loại
    hay bị quên nhất — nên nhận KHÔNG cần dấu hiệu ngày giờ."""
    ra = ck.trich_cam_ket([{
        "id": "s1", "subject": "Hỏi về học phí", "body": ["Em xin hỏi…"],
        "folder": "sent", "to": "giaovu@hcmus.edu.vn", "sender": "Tôi",
    }], MOC)
    assert len(ra) == 1
    assert ra[0].trang_thai == "dang_doi"
    assert ra[0].han is None
    assert ra[0].nguoi_cho == "giaovu@hcmus.edu.vn"


def test_muc_uu_tien_TACH_KHOI_muc_rui_ro():
    """Hai thang phải cho kết quả KHÁC NHAU trên cùng một việc, nếu không thì việc
    tách chúng ra là vô nghĩa. Việc High còn 2 ngày: rủi ro vẫn 1 (hỏng thì làm lại
    được), nhưng ưu tiên là 3 (phải làm ngay)."""
    han = MOC.replace(day=31)                      # 31/8, còn 2 ngày
    assert ck.muc_rui_ro("High", han, MOC) == 1
    assert ck.muc_uu_tien("High", han, MOC) == 3


def test_phut_moi_ngay_CHIA_DEU_khong_nhan_ban():
    """Việc 6 tiếng trải 3 ngày phải là 2 tiếng/ngày, không phải 6 tiếng mỗi ngày.
    Cộng thẳng thì ngày nào cũng 'quá tải', mà cảnh báo luôn bật thì hết là cảnh báo."""
    c = ck.CamKet(
        id="x", noi_dung="", han=datetime(2026, 9, 10), bat_dau=datetime(2026, 9, 8),
        han_suy_ra=False, trang_thai="chua_lam", nguoi_cho="", email_id="1",
        do_tin_cay=0.9, uoc_luong_phut=360, muc_rui_ro=1, muc_uu_tien=1,
    )
    assert ck.phut_moi_ngay(c) == pytest.approx(120.0)


def test_ap_luc_tinh_theo_KHOANG_LAM_khong_theo_ngay_han():
    """Việc hạn ngày 10 nhưng bắt đầu ngày 8 phải làm ngày 8 và 9 CÓ TẢI. Chỉ đếm
    ngày hạn thì hai ngày đó hiện ra rỗng — đúng cái ảo giác tính năng này sinh ra
    để phá."""
    moc = datetime(2026, 9, 8, 9, 0)
    c = ck.CamKet(
        id="x", noi_dung="", han=datetime(2026, 9, 10, 23, 59),
        bat_dau=datetime(2026, 9, 8), han_suy_ra=False, trang_thai="chua_lam",
        nguoi_cho="", email_id="1", do_tin_cay=0.9, uoc_luong_phut=360,
        muc_rui_ro=1, muc_uu_tien=1,
    )
    ra = ck.ap_luc_theo_ngay([c], 4, moc)
    assert ra[0]["so_viec"] == 1, "ngày bắt đầu phải có tải"
    assert ra[1]["so_viec"] == 1, "ngày giữa phải có tải"
    assert ra[2]["so_viec"] == 1, "ngày hạn phải có tải"
    assert ra[3]["so_viec"] == 0, "ngày sau hạn thì hết"


def test_viec_XONG_khong_tinh_vao_ap_luc():
    c = ck.CamKet(
        id="x", noi_dung="", han=datetime(2026, 9, 8, 12, 0), bat_dau=None,
        han_suy_ra=False, trang_thai="xong", nguoi_cho="", email_id="1",
        do_tin_cay=0.9, uoc_luong_phut=120, muc_rui_ro=1, muc_uu_tien=1,
    )
    ra = ck.ap_luc_theo_ngay([c], 2, datetime(2026, 9, 8, 9, 0))
    assert ra[0]["so_viec"] == 0


def test_tran_ngay_RO_RANG_rong_hon_tran_SUY_RA():
    """Khoảng thư nói thẳng không phải phỏng đoán, nên được trải dài hơn hẳn. Chặn nó
    ở 14 ngày như khoảng suy ra là tự bóp méo dữ liệu thật."""
    assert ck.TRAN_NGAY_RO_RANG > ck.TRAN_NGAY_SUY_RA
