"""THÂN THƯ DO LLM SOẠN PHẢI XUỐNG DÒNG THẬT, KHÔNG ĐƯỢC HIỆN RA CHỮ "\\n".

Người dùng báo: trợ lý soạn thư gửi đi, thư tới nơi KHÔNG xuống dòng mà hiện ra hai
ký tự `\\` và `n` giữa câu. Truy lại thì đường đi hoàn toàn đối xứng (`json.dumps`
rồi `json.loads`), không có chỗ nào escape hai lần — nên nguồn là chính MÔ HÌNH viết
ra chuỗi thoát thay vì ký tự xuống dòng. Đó là thói quen rất quen của LLM khi phải
đặt một chuỗi NHIỀU DÒNG vào trong một tham số JSON.

Không sửa được bằng cách dặn thêm trong prompt: dặn thì đỡ, nhưng vẫn lọt, và mỗi
lần lọt là một bức thư đã gửi đi cho người thật — không rút lại được.

RANH GIỚI CỦA PHÉP SỬA (chính là phần đáng test nhất):

  • Chỉ chữa khi thân thư KHÔNG có lấy một dấu xuống dòng thật nào. Đó đúng là dấu
    vân tay của lỗi: mô hình dùng chuỗi thoát THAY CHO xuống dòng, nên không thể có
    cả hai. Còn khi đã có xuống dòng thật thì mọi `\\n` còn lại nhiều khả năng là
    chữ người ta cố ý viết — đụng vào là tự bịa nội dung.

  • Vì thế `C:\\nam-2026\\bao-cao.docx` trong một bức thư CÓ xuống dòng vẫn nguyên vẹn.
    Bức thư một dòng duy nhất chứa đường dẫn đó thì vẫn bị cắt — đó là cái giá đã
    biết trước và chấp nhận: thư một dòng lại chứa đường dẫn Windows bắt đầu bằng
    chữ 'n' là hiếm hơn hẳn so với việc mô hình viết `\\n`, mà hậu quả thì nhẹ hơn
    (một chỗ xuống dòng thừa) so với cả bức thư dính liền một khối.

  • Chỉ áp cho chữ do MÔ HÌNH viết. Người dùng tự gõ trong khung soạn thư đi đường
    khác (`/emails/send`) và KHÔNG bị đụng tới: họ gõ gì thì gửi đúng thứ đó.
"""

from __future__ import annotations

import pytest

from app.tools.schemas import ReplyEmailInput, SendEmailInput
from app.core.van_ban import sua_xuong_dong


# ── Chính lỗi người dùng gặp ─────────────────────────────────────────────────

def test_than_thu_toan_chuoi_thoat_thi_thanh_xuong_dong_that():
    goc = "Dạ em chào thầy,\\n\\nEm gửi thầy báo cáo ạ.\\n\\nTrân trọng,\\nQuân"
    ra = sua_xuong_dong(goc)
    assert "\\n" not in ra
    assert ra.count("\n") == 5
    assert ra.startswith("Dạ em chào thầy,\n\nEm gửi")


def test_di_qua_ca_schema_send_email():
    """Chặn ở schema thì phủ CẢ LangGraph LẪN MCP — cả hai đều đi qua registry."""
    inp = SendEmailInput(to=["a@b.c"], subject="Báo cáo", body="Dòng 1\\nDòng 2")
    assert inp.body == "Dòng 1\nDòng 2"


def test_di_qua_ca_schema_reply_email():
    inp = ReplyEmailInput(email_id="m1", instructions="Chào anh,\\n\\nEm đồng ý ạ.")
    assert inp.instructions == "Chào anh,\n\nEm đồng ý ạ."


def test_cheo_nguoc_DA_THOAT_thi_giu_nguyen():
    """`\\\\n` là dấu chéo ngược ĐÃ ĐƯỢC THOÁT — người viết thật sự muốn nói tới ký tự
    chéo ngược, không phải xuống dòng. Đây là chỗ bản dùng chung CỐ Ý khác với bản
    đầu tôi viết: đổi nó đi là sửa một cái sai thành một cái sai khác, mà lần này
    người dùng không ngờ tới."""
    assert sua_xuong_dong("A\\\\nB") == "A\\\\nB"


def test_xuong_dong_kieu_windows():
    assert sua_xuong_dong("A\\r\\nB") == "A\r\nB"


def test_tab_chi_duoc_go_KHI_da_chac_chan_la_chuoi_thoat():
    """`\\t` một mình KHÔNG đủ để kết luận. Dấu vân tay của lỗi là `\\n`/`\\r`: cả thân
    thư nằm trên một dòng vì mô hình viết chuỗi thoát thay cho xuống dòng. Có dấu đó
    rồi thì `\\t` đi cùng cũng là chuỗi thoát; không có nó thì một chuỗi chỉ chứa `\\t`
    là mơ hồ, và để nguyên là lựa chọn ít hại hơn."""
    assert sua_xuong_dong("Cột 1\\tCột 2") == "Cột 1\\tCột 2"
    assert sua_xuong_dong("Bảng:\\nCột 1\\tCột 2") == "Bảng:\nCột 1\tCột 2"


# ── Ranh giới: KHÔNG được đụng vào ───────────────────────────────────────────

def test_da_co_xuong_dong_that_thi_KHONG_dung_vao():
    """Có xuống dòng thật nghĩa là mô hình biết xuống dòng — `\\n` còn lại là chữ thật."""
    goc = "Xem thư mục:\nC:\\new\\bao-cao.docx\nCảm ơn anh."
    assert sua_xuong_dong(goc) == goc


def test_khong_co_chuoi_thoat_thi_tra_ve_nguyen_xi():
    goc = "Chào anh, em xác nhận tham dự ạ."
    assert sua_xuong_dong(goc) is goc or sua_xuong_dong(goc) == goc


def test_dau_cheo_nguoc_khong_di_kem_chu_n_thi_giu_nguyen():
    """Chỉ gỡ chuỗi thoát xuống dòng. Mọi dấu chéo ngược khác giữ nguyên."""
    goc = "Đường dẫn D:\\tai-lieu\\bao-cao.docx nhé anh."
    assert sua_xuong_dong(goc) == goc


@pytest.mark.parametrize("rong", ["", "   "])
def test_chuoi_rong_khong_gay_loi(rong):
    assert sua_xuong_dong(rong) == rong


def test_khong_phai_chuoi_thi_tra_ve_nguyen_xi():
    """Validator chạy ở mode='before' nên có thể nhận kiểu lạ — không được ném lỗi
    ở đây, để Pydantic báo lỗi kiểu bằng thông điệp của chính nó."""
    assert sua_xuong_dong(None) is None
    assert sua_xuong_dong(12) == 12


def test_nguoi_dung_tu_go_KHONG_di_qua_lop_nay():
    """Chốt bằng chữ: schema này chỉ dành cho tool của agent. Đường soạn thư của
    người dùng (`/emails/send` → `SendReq`) là model KHÁC, và phải giữ nguyên như thế."""
    from app.api.app import SendReq
    assert not hasattr(SendReq, "__pydantic_decorators__") or all(
        "sua_xuong_dong" not in str(getattr(d, "func", ""))
        for d in SendReq.__pydantic_decorators__.field_validators.values()
    )
