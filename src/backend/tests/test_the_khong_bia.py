"""BỘ TRÌNH BÀY KHÔNG ĐƯỢC TỰ BỊA MỘT LOẠI THẺ CÓ NGUỒN TẤT ĐỊNH.

── ĐO ĐƯỢC 03/09/2026 ──
Câu "tìm giúp mình các thư về học phí" chỉ gọi `search_emails`, nhưng bộ trình bày
(`PresentReply`) trả về `kind='triage'` — nên người dùng nhận một widget "xếp theo độ
ưu tiên" cho một câu hỏi TÌM KIẾM.

Nguy hiểm ở chỗ nó TRÔNG CHỈN CHU. Một thẻ vẽ đẹp nhưng sai loại còn khó phát hiện
hơn một lỗi lộ liễu, và người xem demo sẽ tin đó là thiết kế có chủ ý.

`digest` và `triage` đều có bộ dựng riêng đọc số liệu THẲNG từ tool. Mô hình chọn
chúng khi tool tương ứng không chạy nghĩa là nó đang vẽ một cái vỏ không có ruột.
"""

from __future__ import annotations

import json
import types

import pytest

from app.api.app import ha_the_bia


def _tool(ten: str, data):
    return types.SimpleNamespace(type="tool", name=ten, content=json.dumps({"data": data}))


_NGUOI = types.SimpleNamespace(type="human", content="tìm thư về học phí")


_ha_cap = ha_the_bia   # dùng THẲNG hàm của sản phẩm, không viết lại


def test_triage_bia_ra_thi_bi_ha_ve_result():
    """Đúng ca đã gặp: chỉ tìm kiếm, mà mô hình gắn nhãn triage."""
    ra = _ha_cap({"kind": "triage", "intro": "x"},
                 [_NGUOI, _tool("search_emails", [{"id": "1"}])])
    assert ra["kind"] == "result"


def test_digest_bia_ra_thi_bi_ha_ve_result():
    ra = _ha_cap({"kind": "digest", "intro": "x"},
                 [_NGUOI, _tool("search_emails", [{"id": "1"}])])
    assert ra["kind"] == "result"


def test_triage_CO_TOOL_that_thi_giu_nguyen():
    """Ranh giới: có tool đỡ thì thẻ hợp lệ, không được đụng vào."""
    ra = _ha_cap({"kind": "triage", "intro": "x"},
                 [_NGUOI, _tool("phan_loai_uu_tien", {"nhom": [], "tong": 0})])
    assert ra["kind"] == "triage"


def test_digest_CO_TOOL_that_thi_giu_nguyen():
    ra = _ha_cap({"kind": "digest", "intro": "x"},
                 [_NGUOI, _tool("tom_tat_ngay", {"tong": 5})])
    assert ra["kind"] == "digest"


@pytest.mark.parametrize("k", ["text", "result", "plan", "draft", "dilai", "lichtrinh"])
def test_cac_loai_the_KHAC_khong_bi_dung_toi(k):
    """Luật này CHỈ áp cho hai kiểu có bộ dựng tất định. Nới rộng ra là chặn nhầm
    những thẻ hoàn toàn hợp lệ do các nhánh khác dựng."""
    ra = _ha_cap({"kind": k, "intro": "x"}, [_NGUOI])
    assert ra["kind"] == k
