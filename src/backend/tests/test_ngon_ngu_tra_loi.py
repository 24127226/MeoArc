"""NÚT "English" PHẢI THẬT SỰ LÀM GÌ ĐÓ.

Cột `language` có trong bảng `user_preference` từ đầu, nhưng `to_prompt_context()`
KHÔNG HỀ ĐỌC nó — nên nút "English" ở màn Cài đặt là một nút chết: bấm xong không có
gì đổi. Cùng loại lỗi với ô tick ở bảng phân loại: một nút hứa một việc rồi không làm
thì tệ hơn không có nút, vì nó dạy người dùng rằng các nút khác cũng có thể vô nghĩa.
"""

from __future__ import annotations

import pytest

from app.models.user_preference import UserPreference


def _pref(**kw) -> UserPreference:
    return UserPreference(user_id=1, **kw)


def test_tieng_viet_KHONG_them_dong_nao():
    """Mặc định thì im lặng. Nhét một khối prompt thừa vừa tốn token vừa làm loãng
    những dòng thật sự cần — và system prompt đã tự nói tiếng Việt sẵn rồi."""
    assert _pref(language="vi").to_prompt_context() == ""


def test_tieng_anh_SINH_menh_lenh_ro_rang():
    ra = _pref(language="en").to_prompt_context()
    assert "TIẾNG ANH" in ra
    # Phải phủ được cả trường hợp người dùng gõ tiếng Việt nhưng muốn đọc tiếng Anh —
    # nếu không, mô hình sẽ bám theo ngôn ngữ câu hỏi và nút này lại thành vô nghĩa.
    assert "kể cả khi họ hỏi bằng tiếng Việt" in ra


def test_KHONG_bao_mo_hinh_dich_noi_dung_thu():
    """Ranh giới quan trọng: dịch LỜI CỦA TRỢ LÝ, KHÔNG dịch thư gốc.

    Dịch tiêu đề và nội dung thư là bịa dữ liệu — người dùng đối chiếu với Gmail sẽ
    thấy hai thứ khác nhau và không biết cái nào thật."""
    ra = _pref(language="en").to_prompt_context()
    assert "Giữ nguyên tiêu đề và nội dung thư gốc" in ra


def test_dong_ngon_ngu_dung_DAU_TIEN():
    """System prompt mở đầu bằng "nói TIẾNG VIỆT chỉn chu". Khối sở thích được nhét
    vào CUỐI prompt nên lời ở đây thắng — nhưng để nó lẫn giữa các dòng khác thì mô
    hình dễ đọc ra một gợi ý nhỏ thay vì một mệnh lệnh."""
    ra = _pref(language="en", display_name="Quân",
               custom_instruction="đừng dùng từ trân trọng").to_prompt_context()
    dong = [d for d in ra.splitlines() if d.strip().startswith("-")]
    assert dong and "NGÔN NGỮ" in dong[0]


@pytest.mark.parametrize("gt", [None, "", "vi"])
def test_gia_tri_rong_coi_nhu_tieng_viet(gt):
    """Bản ghi cũ có thể chưa có `language`. Thiếu giá trị mà đổi sang tiếng Anh thì
    người dùng tự dưng thấy trợ lý nói tiếng Anh mà không hiểu vì sao."""
    ra = _pref(language=gt).to_prompt_context() if gt is not None else _pref().to_prompt_context()
    assert "TIẾNG ANH" not in ra
