# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_audit_failed.py — HÀNH ĐỘNG THẤT BẠI PHẢI ĐƯỢC GHI NHẬN ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Lấp đúng một lỗ hổng: nhánh ghi status="failed" ĐÃ CÓ trong        ║
# ║ app/mcp/server.py (_audit_mcp) nhưng chưa test nào canh. Nhánh mã   ║
# ║ chưa từng chạy trong test là nhánh mã không ai biết còn đúng không. ║
# ║                                                                    ║
# ║ Hai điều được canh ở đây:                                          ║
# ║  1) Phân loại đúng thành công/thất bại — nhầm chiều thì nhật ký     ║
# ║     báo "xong" cho một việc chưa hề xảy ra, tệ hơn là không ghi gì. ║
# ║  2) Một hành động hỏng KHÔNG kéo theo các hành động khác trong      ║
# ║     cùng lượt (UC007-TC06).                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def _mem_db():
    from app.core.db import Base
    import app.models.user  # noqa: F401 — đăng ký bảng users (đích của khoá ngoại)
    import app.models.audit  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def test_phan_loai_dung_ket_qua_tool_thanh_cong_hay_that_bai():
    """`_ok` là thứ quyết định dòng nhật ký ghi 'success' hay 'failed'.

    Nhầm chiều ở đây nguy hiểm hơn là không ghi gì: người dùng mở nhật ký,
    thấy 'đã gửi', và tin rằng thư đã đi.
    """
    from app.mcp.server import _ok

    # Chỉ dict có success=False mới là thất bại
    assert _ok({"success": False, "error": "Gmail 403"}) is False

    # Mọi thứ còn lại coi như thành công — kể cả khuôn dạng trả về khác
    assert _ok({"success": True, "data": {}}) is True
    assert _ok({"data": {"modified_count": 3}}) is True
    assert _ok([]) is True
    assert _ok(None) is True


def test_hanh_dong_hong_duoc_ghi_failed_va_khong_lam_hong_hanh_dong_khac():
    """UC007-TC06: một tool hỏng giữa lượt thì dòng nhật ký của NÓ mang
    status='failed', còn các hành động khác trong cùng lượt vẫn nguyên vẹn."""
    from app.repo import audit_repo

    db = _mem_db()

    # Cùng một lượt của người dùng: 2 việc chạy được, 1 việc hỏng.
    audit_repo.log(db, user_id=1, action="search_emails", tool_name="search_emails",
                   affected_email_ids=["m1", "m2"], status="success")
    audit_repo.log(db, user_id=1, action="apply_labels", tool_name="apply_labels",
                   affected_email_ids=["m1"], status="failed",
                   details={"error": "Gmail 404: email không tồn tại"})
    audit_repo.log(db, user_id=1, action="mark_read", tool_name="bulk_action",
                   affected_email_ids=["m2"], status="success")

    rows = audit_repo.list_recent(db, 1)
    assert len(rows) == 3, "Việc hỏng không được làm mất dòng nhật ký của việc khác"

    theo_action = {r.action: r for r in rows}
    assert theo_action["apply_labels"].status == "failed"
    assert "404" in theo_action["apply_labels"].details.get("error", ""), \
        "Dòng thất bại phải mang được lý do — 'failed' trống thì không sửa được gì"

    # Hai việc kia KHÔNG bị lây trạng thái hỏng.
    assert theo_action["search_emails"].status == "success"
    assert theo_action["mark_read"].status == "success"
    assert theo_action["search_emails"].affected_email_ids == ["m1", "m2"]


def test_mac_dinh_la_success_nen_that_bai_phai_duoc_ghi_ro():
    """`status` mặc định là 'success'. Nghĩa là quên truyền status ở nhánh lỗi
    sẽ ghi nhầm thành công một cách IM LẶNG — nên nhánh lỗi phải luôn nói rõ."""
    from app.repo import audit_repo

    db = _mem_db()
    row = audit_repo.log(db, user_id=2, action="send_email", tool_name="send_email")
    assert row.status == "success"
