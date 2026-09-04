"""THẺ TRẢ LỜI PHẢI ĐỔI THEO NGÔN NGỮ NGƯỜI DÙNG.

Dịch mỗi frontend thì bấm "English" xong khung thành tiếng Anh, nhưng thẻ trả lời vẫn
"Đây là những việc bạn đang mắc:" và nhãn vẫn "Học tập". Chữ Anh bao quanh chữ Việt
LỘ HƠN HẲN so với để nguyên cả cụm tiếng Việt — dịch nửa vời làm mọi thứ tệ hơn.

Ranh giới quan trọng nhất được khoá ở đây: **dịch NHÃN, không dịch DỮ LIỆU**. Tên
người gửi và tiêu đề thư phải đi qua nguyên xi. Dịch chúng là bịa dữ liệu — người dùng
đối chiếu với Gmail sẽ thấy hai thứ khác nhau và không biết cái nào thật.
"""

from __future__ import annotations

import json
import types

import pytest

from app.api.app import _digest_card, _lich_trinh_card, _triage_card
from app.core.ngon_ngu import dich, dich_gia_tri

_NGUOI = types.SimpleNamespace(type="human", content="hỏi gì đó")


def _tool(ten: str, data):
    return types.SimpleNamespace(type="tool", name=ten, content=json.dumps({"data": data}))


# ── Lớp dịch ─────────────────────────────────────────────────────────────────

def test_thieu_khoa_tra_ve_CHINH_KHOA():
    """Một thẻ hiện ra "the.khong.co" là lỗi nhìn thấy ngay và sửa được; một thẻ
    trống thì trông như hệ thống hỏng và không ai đoán ra thiếu gì."""
    assert dich("the.khong.co", "en") == "the.khong.co"


def test_dien_hong_KHONG_nem_loi():
    """Sai tên biến thay thế thì trả chuỗi chưa điền. Một dòng dẫn có dấu ngoặc nhọn
    là xấu; một ngoại lệ ở đây làm hỏng cả lượt chat — đắt hơn nhiều."""
    assert "{n}" in dich("the.lich.tieude_viec", "en", sai_ten=1)


def test_ngon_ngu_la_khong_biet_thi_ve_tieng_viet():
    assert dich("the.lich.dan_viec", "fr") == dich("the.lich.dan_viec", "vi")


def test_DU_LIEU_THAT_di_qua_nguyen_xi():
    """Ranh giới quan trọng nhất của cả tệp này."""
    for that in ("Thư từ thầy Sơn", "Giáo vụ HCMUS", "Nộp báo cáo trước 18/9"):
        assert dich_gia_tri(that, "en") == that


def test_nhan_CHUAN_thi_duoc_dich():
    assert dich_gia_tri("Học tập", "en") == "Study"
    assert dich_gia_tri("Học tập", "vi") == "Học tập"


# ── Thẻ đổi theo ngôn ngữ ────────────────────────────────────────────────────

def test_the_lich_trinh_doi_theo_ngon_ngu():
    msgs = [_NGUOI, _tool("liet_ke_cam_ket", [
        {"noi_dung": "Nộp báo cáo", "email_id": "m1", "muc_uu_tien": 2}])]
    assert "đang mắc" in _lich_trinh_card(msgs, "vi")["intro"]
    assert "currently owe" in _lich_trinh_card(msgs, "en")["intro"]


def test_the_lich_trinh_GIU_NGUYEN_noi_dung_viec():
    """Nội dung việc lấy từ tiêu đề thư — là DỮ LIỆU, không được dịch."""
    msgs = [_NGUOI, _tool("liet_ke_cam_ket", [
        {"noi_dung": "Nộp báo cáo Testing PA3", "email_id": "m1"}])]
    assert _lich_trinh_card(msgs, "en")["viec"][0]["noi_dung"] == "Nộp báo cáo Testing PA3"


def test_the_digest_doi_ca_tieu_de_lan_nhan_o_so_lieu():
    msgs = [_NGUOI, _tool("tom_tat_ngay", {
        "tong": 5, "chua_doc": 3, "can_xu_ly": 2,
        "theo_nhan": [{"label": "Học tập", "count": 4}], "noi_bat": [], "thu": []})]
    en = _digest_card(msgs, "en")
    assert "Mailbox summary" in en["title"]
    assert en["stats"][0]["label"] == "Total"
    assert en["breakdown"][0]["label"] == "Study"
    vi = _digest_card(msgs, "vi")
    assert "Tóm tắt hộp thư" in vi["title"] and vi["breakdown"][0]["label"] == "Học tập"


def test_the_triage_doi_ca_nhom_lan_goi_y():
    msgs = [_NGUOI, _tool("phan_loai_uu_tien", {"tong": 2, "nhom": [
        {"level": "high", "label": "Ưu tiên cao", "items": [
            {"id": "m1", "sender": "Giáo vụ HCMUS", "initial": "G",
             "subject": "Nộp báo cáo", "suggest": "Cần bạn xử lý"}]}]})]
    en = _triage_card(msgs, "en")
    assert en["groups"][0]["label"] == "High priority"
    assert en["groups"][0]["items"][0]["suggest"] == "Needs your action"
    # DỮ LIỆU giữ nguyên
    assert en["groups"][0]["items"][0]["sender"] == "Giáo vụ HCMUS"
    assert en["groups"][0]["items"][0]["subject"] == "Nộp báo cáo"


@pytest.mark.parametrize("dung", [_digest_card, _triage_card, _lich_trinh_card])
def test_mac_dinh_van_la_tieng_viet(dung):
    """Không truyền ngôn ngữ thì phải y hệt trước khi có tính năng này — mọi nơi gọi
    cũ (test, kịch bản kiểm) không được đổi hành vi."""
    import inspect
    assert inspect.signature(dung).parameters["ngon"].default == "vi"
