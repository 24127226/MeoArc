# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_confirmation.py — HUMAN-IN-THE-LOOP CÓ TRẠNG THÁI      ║
# ║ (PA2 §1.3.5, FR-02.4)                                             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Trước đây việc duyệt chỉ tồn tại ở giao diện: nút bấm gọi thẳng    ║
# ║ lệnh gửi. Máy chủ không biết có "yêu cầu đang chờ duyệt" nào, nên  ║
# ║ bấm hai lần là GỬI HAI LẦN — và mở lại hội thoại cũ thì thẻ nháp   ║
# ║ lại bấm được nữa.                                                 ║
# ║                                                                    ║
# ║ Đây là lỗi không tự lộ: không ngoại lệ, không dòng log, chỉ có     ║
# ║ người nhận thấy hai lá thư giống nhau. Nên nó phải có test riêng.  ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.confirmation import APPROVED, PENDING, REJECTED
from app.repo import confirmation_repo as repo


def _mem_db():
    from app.core.db import Base
    import app.models.user       # noqa: F401 — bảng users là đích của khoá ngoại
    import app.models.confirmation  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def _yeu_cau(db, user_id=1, action="send_email"):
    return repo.create(
        db, user_id=user_id, action=action,
        description="Gửi thư tới thien@example.com?",
        args={"to": ["thien@example.com"], "subject": "Chào Thiên"},
    )


# ── Vòng đời cơ bản ─────────────────────────────────────────────────────────
def test_moi_yeu_cau_bat_dau_o_trang_thai_cho_duyet():
    db = _mem_db()
    r = _yeu_cau(db)
    assert r.status == PENDING and r.is_pending is True
    assert r.result is None, "Chưa duyệt thì không thể có kết quả"


def test_duyet_thi_chuyen_sang_approved():
    db = _mem_db()
    r = _yeu_cau(db)
    assert repo.approve(db, r) is True
    assert r.status == APPROVED


def test_tu_choi_thi_chuyen_sang_rejected():
    db = _mem_db()
    r = _yeu_cau(db)
    assert repo.reject(db, r) is True
    assert r.status == REJECTED


# ── ĐÂY LÀ CA QUAN TRỌNG NHẤT: bấm duyệt hai lần ────────────────────────────
def test_duyet_lan_hai_khong_duoc_thuc_thi_lai():
    """Lỗi gửi trùng. Người dùng bấm "Gửi" hai lần (mạng chậm, lỡ tay), hoặc mở lại
    hội thoại cũ rồi bấm vào đúng thẻ nháp đó — thư phải chỉ đi MỘT lần.

    Ràng buộc "chỉ gọi khi status = pending" của PA2 §1.3.5 chính là hàng rào:
    lần gọi thứ hai trả False, và nơi gọi dựa vào đó để KHÔNG chạy lại hành động.
    """
    db = _mem_db()
    r = _yeu_cau(db)

    lan_dau = repo.approve(db, r)
    lan_hai = repo.approve(db, r)

    assert lan_dau is True, "Lần duyệt đầu phải được thực thi"
    assert lan_hai is False, "Lần duyệt thứ hai KHÔNG được thực thi lại — thư sẽ đi hai lần"
    assert r.status == APPROVED


def test_dem_so_lan_thuc_thi_that_su(monkeypatch):
    """Đếm thẳng số lần hành động chạy, thay vì tin vào cờ trạng thái.

    Cờ đúng mà nơi gọi vẫn chạy hai lần thì test trên vẫn xanh — nên ở đây mô phỏng
    đúng cách endpoint dùng: chỉ chạy khi approve() trả True.
    """
    db = _mem_db()
    r = _yeu_cau(db)
    da_gui = {"n": 0}

    def bam_nut_gui():
        if repo.approve(db, r):
            da_gui["n"] += 1
            repo.save_result(db, r, {"sent": True, "lan": da_gui["n"]})
        return r.result

    kq1 = bam_nut_gui()
    kq2 = bam_nut_gui()
    kq3 = bam_nut_gui()

    assert da_gui["n"] == 1, f"Thư đã gửi {da_gui['n']} lần — phải đúng 1"
    assert kq1 == kq2 == kq3, "Lần bấm sau phải trả lại đúng kết quả cũ, không báo lỗi"


def test_tu_choi_roi_thi_khong_duyet_duoc_nua():
    """Đã từ chối thì hành động phải chết hẳn, không ai 'cứu' lại được."""
    db = _mem_db()
    r = _yeu_cau(db)
    assert repo.reject(db, r) is True
    assert repo.approve(db, r) is False
    assert r.status == REJECTED


def test_duyet_roi_thi_khong_tu_choi_duoc_nua():
    """Chiều ngược lại: thư đã gửi thì bấm Huỷ không rút lại được, và trạng thái
    không được nói dối rằng đã huỷ."""
    db = _mem_db()
    r = _yeu_cau(db)
    assert repo.approve(db, r) is True
    assert repo.reject(db, r) is False
    assert r.status == APPROVED


# ── Quyền sở hữu ────────────────────────────────────────────────────────────
def test_nguoi_khac_khong_duyet_ho_duoc():
    """Duyệt hộ được thì cổng human-in-the-loop mất sạch ý nghĩa — đoán một id là
    gửi thư thay người khác."""
    db = _mem_db()
    r = _yeu_cau(db, user_id=1)

    assert repo.get_owned(db, r.id, user_id=2) is None
    assert repo.get_owned(db, r.id, user_id=1) is not None
    assert r.status == PENDING, "Yêu cầu vẫn phải nguyên vẹn sau khi người lạ chạm vào"


def test_id_khong_ton_tai_tra_ve_none():
    db = _mem_db()
    assert repo.get_owned(db, "khong-co-that", user_id=1) is None


# ── Nội dung yêu cầu ────────────────────────────────────────────────────────
def test_tham_so_duoc_chot_luc_tao_yeu_cau():
    """Người dùng duyệt CÁI HỌ THẤY. Nếu tham số đọc lại lúc thực thi thì một lời
    gọi xen giữa có thể đổi người nhận sau khi người dùng đã bấm đồng ý."""
    db = _mem_db()
    r = _yeu_cau(db)
    repo.approve(db, r)
    assert r.args["to"] == ["thien@example.com"]
    assert r.args["subject"] == "Chào Thiên"


def test_mo_ta_la_cau_cho_nguoi_doc():
    """`action` là tên hàm, `description` mới là thứ người dùng đọc để quyết định."""
    db = _mem_db()
    r = _yeu_cau(db)
    assert r.action == "send_email"
    assert "thien@example.com" in r.description


def test_khuon_tra_ra_ngoai_khong_lo_noi_dung_thu():
    """`args` chứa tiêu đề và thân thư — không được phơi qua API."""
    db = _mem_db()
    r = _yeu_cau(db)
    d = repo.to_dict(r)
    assert d["status"] == PENDING and d["action"] == "send_email"
    assert "args" not in d, "Khuôn trả ra ngoài đang lộ nội dung thư"


def test_danh_sach_cho_duyet_chi_cua_minh_va_chi_con_pending():
    db = _mem_db()
    a1 = _yeu_cau(db, user_id=1)
    _yeu_cau(db, user_id=1, action="bulk_delete")
    _yeu_cau(db, user_id=2)                      # của người khác

    repo.approve(db, a1)                          # đã xử lý → rời danh sách chờ

    cho = repo.list_pending(db, user_id=1)
    assert len(cho) == 1
    assert cho[0].action == "bulk_delete"
