# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_ai_labels.py — BA TRỤC NHÃN AI (UC009, PA1 §4.2.9)     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Đặc tả chia nhãn AI thành ba trục: Category luôn có; Priority và   ║
# ║ Status chỉ có với thư mang tính công việc.                        ║
# ║                                                                    ║
# ║ Hai điều được canh chặt nhất ở đây:                                ║
# ║  1) Ba nhãn phải đi CÙNG một thao tác (PA2 §1.3.9). Gán lẻ được là ║
# ║     sớm muộn có thư mang Priority của lượt này, Status của lượt    ║
# ║     trước — người dùng thấy "High / Done" và không hiểu gì.        ║
# ║  2) Thư không phải việc phải để NULL, KHÔNG phải "Low"/"Done".     ║
# ║     None = đây không phải việc. Low = đã xét, việc nhẹ. Nhầm hai   ║
# ║     thứ đó là đổ cả hộp thư quảng cáo vào danh sách việc cần làm.  ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import pytest

from app.core.labeling import Priority, TaskStatus, analyze


def _thu(**kw):
    """Một bản ghi thư rỗng vừa đủ để thử applyAILabels (không cần database)."""
    from app.models.email_store import StoredEmail
    e = StoredEmail()
    for k, v in kw.items():
        setattr(e, k, v)
    return e


# ── UC009: applyAILabels cập nhật ĐỒNG THỜI cả ba trục ──────────────────────
def test_gan_ba_nhan_trong_mot_thao_tac():
    e = _thu()
    e.apply_ai_labels("moss", Priority.HIGH.value, TaskStatus.TODO.value, label="Học tập")

    assert e.ai_category == "moss"
    assert e.ai_priority == "High"
    assert e.ai_status == "Todo"
    assert e.ai_label == "Học tập"


def test_thieu_mot_trong_hai_thi_bo_ca_hai():
    """Không cho phép trạng thái nửa vời: có Priority mà không có Status, hoặc ngược lại.

    Nếu để lọt, giao diện sẽ hiện một thư "ưu tiên Cao" mà không nói được cao để làm gì.
    """
    e = _thu()
    e.apply_ai_labels("sea", Priority.HIGH.value, None)
    assert (e.ai_priority, e.ai_status) == (None, None)

    e2 = _thu()
    e2.apply_ai_labels("sea", None, TaskStatus.TODO.value)
    assert (e2.ai_priority, e2.ai_status) == (None, None)


def test_gan_lai_thi_thay_the_ca_cum_khong_de_sot_gia_tri_cu():
    """Lượt phân tích sau phải xoá sạch kết quả lượt trước, không trộn lẫn."""
    e = _thu()
    e.apply_ai_labels("moss", Priority.HIGH.value, TaskStatus.TODO.value)
    # Lượt sau kết luận: đây không phải việc nữa
    e.apply_ai_labels("terra", None, None)

    assert e.ai_category == "terra"
    assert e.ai_priority is None, "Priority của lượt trước còn sót lại"
    assert e.ai_status is None, "Status của lượt trước còn sót lại"


def test_khong_dung_apply_van_gan_duoc_nhung_do_la_duong_khong_nen_di():
    """Ghi chú thiết kế: các thuộc tính vẫn gán thẳng được (SQLAlchemy không chặn).
    Hàng rào nằm ở chỗ MỌI nơi sinh nhãn đều đi qua applyAILabels — test này chỉ
    ghi lại rằng sự ràng buộc là quy ước, không phải cưỡng chế ở tầng ORM."""
    e = _thu()
    e.ai_priority = "High"
    assert e.ai_status is None   # gán lẻ ⇒ đúng là sinh ra trạng thái nửa vời


# ── UC009: thư KHÔNG mang tính công việc phải giữ null cả hai trục ──────────
@pytest.mark.parametrize("sender,name,subject,snippet", [
    ("no-reply@shopee.vn", "Shopee", "Flash Sale 12.12", "vui lòng mua ngay kẻo lỡ"),
    ("notification@facebookmail.com", "Facebook", "Bạn có thông báo mới", "5 lượt thích"),
    ("ban.than@gmail.com", "Bạn thân", "Đi cà phê không?", "cuối tuần rảnh chứ"),
])
def test_thu_khong_phai_viec_giu_null_ca_priority_lan_status(sender, name, subject, snippet):
    r = analyze(sender, name, subject, snippet)
    assert r.task_like is False
    assert r.priority is None and r.status is None
    assert r.category is not None, "Category thì LUÔN phải có, dù không phải việc"


def test_quang_cao_co_chu_vui_long_van_khong_thanh_viec():
    """Ca gài bẫy: 'vui lòng' là dấu hiệu việc cần làm, nhưng thư Mua sắm thì không.
    Nhóm nhãn phải thắng từ khoá — nếu không, mỗi đợt sale là danh sách việc nổ tung."""
    r = analyze("no-reply@shopee.vn", "Shopee", "Flash Sale", "vui lòng xác nhận đơn ngay")
    assert r.task_like is False
    assert (r.priority, r.status) == (None, None)


# ── Thư MANG tính công việc thì phải có ĐỦ cả hai ───────────────────────────
@pytest.mark.parametrize("subject,snippet,mong_status", [
    ("Nhắc nộp báo cáo SRS", "hạn nộp thứ Sáu", TaskStatus.TODO),
    ("Đã gửi đề xuất", "đang chờ duyệt", TaskStatus.WAITING),
    ("Hợp đồng đã duyệt", "đã hoàn tất", TaskStatus.DONE),
])
def test_thu_cong_viec_co_du_ca_hai_truc(subject, snippet, mong_status):
    r = analyze("sep@company.com", "Sếp", subject, snippet)
    assert r.task_like is True
    assert r.status is mong_status
    assert r.priority is not None, "Đã là việc thì phải có độ ưu tiên"


def test_dau_hieu_gap_thi_day_len_uu_tien_cao():
    r = analyze("no-reply@vietcombank.com.vn", "VCB", "Nhắc thanh toán thẻ", "quá hạn")
    assert r.priority is Priority.HIGH


def test_viec_da_xong_thi_ha_uu_tien_xuong_thap():
    """Việc đã xong không được tranh chỗ với việc đang cần làm."""
    r = analyze("noreply@github.com", "GitHub", "PR merged", "đã hoàn tất")
    assert r.status is TaskStatus.DONE and r.priority is Priority.LOW


def test_khop_duoc_ca_tieu_de_khong_dau():
    """Tiêu đề tiếng Việt rất hay bị gõ không dấu — bỏ sót là mất nhãn cho cả một nhóm thư."""
    co_dau = analyze("giaovu@fit.hcmus.edu.vn", "Giáo vụ", "Nhắc nộp báo cáo", "hạn nộp thứ Sáu")
    khong_dau = analyze("giaovu@fit.hcmus.edu.vn", "Giao vu", "Nhac nop bao cao", "han nop thu Sau")
    assert (co_dau.priority, co_dau.status) == (khong_dau.priority, khong_dau.status)
    assert co_dau.task_like is khong_dau.task_like is True


# ── Từ vựng phải khớp ĐÚNG đặc tả (PA1 §4.2.9) ──────────────────────────────
def test_tu_vung_dung_nhu_dac_ta():
    """Chuỗi lưu xuống database phải đúng từ mà PA1 dùng — lệch là tài liệu và code
    nói hai thứ khác nhau, dù hành vi giống hệt."""
    assert [p.value for p in Priority] == ["High", "Medium", "Low"]
    assert [s.value for s in TaskStatus] == ["Todo", "Waiting", "Done"]
