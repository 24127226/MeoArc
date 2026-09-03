"""THẺ LỊCH TRÌNH — dữ liệu có cấu trúc KHÔNG được rơi thành văn xuôi.

Ba tool `liet_ke_cam_ket`, `ap_luc_lich_trinh`, `de_xuat_di_lai` trước đây không có
thẻ nào nên rơi hết vào nhánh `kind:"text"`, tức là mô hình kể lại bằng lời. Đo được
trên bản triển khai 03/09/2026:

  • "tuần này lịch trình tôi thế nào?" → trả về ĐÚNG MỘT câu hỏi ngược ("Bạn có muốn
    mình xem chi tiết thư nào không?"), không liệt kê nổi một việc.
  • "tuần này tôi có bị quá tải không?" → một đoạn văn bốn dòng, người đọc phải tự dò.
  • "cần đi công tác việc nào không?" → cũng văn xuôi.

Văn xuôi thì mỗi lần một khác, không bấm được, và không mở được lá thư gốc.
"""

from __future__ import annotations

import json
import types

from app.api.app import _lich_trinh_card


def _tool(ten: str, data):
    """Giả một ToolMessage đúng hình dạng mà `_tim_tool` đọc."""
    return types.SimpleNamespace(type="tool", name=ten,
                                 content=json.dumps({"data": data}))


_NGUOI = types.SimpleNamespace(type="human", content="tuần này tôi thế nào?")


def test_khong_goi_tool_lich_trinh_thi_KHONG_dung_the():
    """Không được cướp những lượt chat chẳng liên quan."""
    assert _lich_trinh_card([_NGUOI]) is None
    assert _lich_trinh_card([_NGUOI, _tool("search_emails", [{"id": "1"}])]) is None


def test_liet_ke_cam_ket_thanh_danh_sach_viec():
    card = _lich_trinh_card([_NGUOI, _tool("liet_ke_cam_ket", [
        {"noi_dung": "Nộp báo cáo", "han": "18/09/2026 23:59", "email_id": "m1",
         "tieu_de": "Nhắc nộp báo cáo", "nguoi_gui": "Giáo vụ", "muc_uu_tien": 3},
    ])])
    assert card is not None
    assert card["kind"] == "lichtrinh"
    assert len(card["viec"]) == 1
    v = card["viec"][0]
    assert v["noi_dung"] == "Nộp báo cáo"
    # ID + TIÊU ĐỀ phải đi kèm, nếu không giao diện vẽ ra một cái nút không có chữ và
    # người dùng phải bấm mới biết mình sắp mở gì.
    assert v["email_id"] == "m1" and v["tieu_de"] == "Nhắc nộp báo cáo"


def test_ap_luc_thanh_bang_ngay_va_noi_ro_ngay_nang_nhat():
    """Người dùng hỏi "có quá tải không" cần MỘT câu trả lời và MỘT chỗ để nhìn, chứ
    không phải bốn dòng văn để tự dò ra ngày nào bận."""
    card = _lich_trinh_card([_NGUOI, _tool("ap_luc_lich_trinh", [
        {"ngay": "2026-09-03", "phut": 120, "so_viec": 4, "qua_tai": False,
         "viec": [{"noi_dung": "Xác nhận danh sách", "email_id": "m2",
                   "muc_uu_tien": 3, "han": "03/09 16:00"}]},
        {"ngay": "2026-09-04", "phut": 30, "so_viec": 1, "qua_tai": False, "viec": []},
    ])])
    assert card is not None
    assert len(card["ngay"]) == 2
    assert "2026-09-03" in card["intro"], "phải chỉ thẳng ngày nặng nhất"
    # Việc gom từ bảng ngày → danh sách không được rỗng, nếu không thẻ chỉ có mấy cái
    # cột mà không nói được là việc gì.
    assert any(v["noi_dung"] == "Xác nhận danh sách" for v in card["viec"])
    assert any(v["email_id"] == "m2" for v in card["viec"])


def test_de_xuat_di_lai_thanh_the_kem_noi_den():
    card = _lich_trinh_card([_NGUOI, _tool("de_xuat_di_lai", [
        {"noi_dung": "Hội thảo sinh viên", "han": "20/09/2026 08:00",
         "thanh_pho": "Hà Nội", "ma_san_bay": "HAN", "tu_san_bay": "SGN",
         "email_id": "m3"},
    ])])
    assert card is not None
    v = card["viec"][0]
    assert v["noi"] == "Hà Nội" and v["ma_san_bay"] == "HAN"
    assert v["email_id"] == "m3"


def test_cam_ket_THANG_khi_co_ca_hai():
    """Hỏi "tuần này tôi có gì" mà agent gọi cả hai tool thì danh sách việc CHI TIẾT
    phải thắng bảng gom từ áp lực — nó có thêm người chờ và tiêu đề thư."""
    card = _lich_trinh_card([
        _NGUOI,
        _tool("ap_luc_lich_trinh", [{"ngay": "2026-09-03", "phut": 60, "so_viec": 1,
                                     "qua_tai": False, "viec": [
                                         {"noi_dung": "Từ bảng ngày", "email_id": "z"}]}]),
        _tool("liet_ke_cam_ket", [{"noi_dung": "Từ cam kết", "email_id": "m9",
                                   "nguoi_cho": "Thầy A", "muc_uu_tien": 2}]),
    ])
    assert card is not None
    assert [v["noi_dung"] for v in card["viec"]] == ["Từ cam kết"]
    assert card["viec"][0]["nguoi_cho"] == "Thầy A"
    # Vẫn giữ bảng ngày để vẽ dải áp lực — hai phần bổ sung nhau, không loại nhau.
    assert len(card["ngay"]) == 1


def test_khong_co_viec_nao_thi_van_dung_the_neu_co_bang_ngay():
    """Tuần rảnh vẫn phải trả lời "bạn rảnh" bằng một cái thẻ, chứ không im lặng rơi
    về văn xuôi — người dùng cần thấy CÁI GÌ ĐÓ xác nhận là đã tính."""
    card = _lich_trinh_card([_NGUOI, _tool("ap_luc_lich_trinh", [
        {"ngay": "2026-09-03", "phut": 0, "so_viec": 0, "qua_tai": False, "viec": []},
    ])])
    assert card is not None
    assert card["viec"] == []
    assert len(card["ngay"]) == 1
