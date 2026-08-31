# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/dat_cho_gia_lap.py — ĐẶT CHỖ MÔ PHỎNG (Giai đoạn 3)   ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Đặt chỗ GIẢ LẬP — để cổng tiền có một thứ để gác.

── VÌ SAO TÁCH RIÊNG KHỎI `dat_cho.py` ──
`dat_cho.py` là tầng TRA CỨU, và nó có một phép kiểm quét cả module để chắc rằng không
hàm nào ở đó đặt chỗ hay thanh toán. Phép kiểm đó đã bắt được chính lần sửa này: tôi
nhét `dat_cho_mo_phong` vào đấy và test đỏ ngay — đúng thứ nó sinh ra để chặn.

Không nới phép kiểm, mà tách module. Ranh giới "tầng tra cứu không có đường nào dẫn tới
đặt chỗ" là một bảo đảm đáng giữ, và giữ nó bằng cấu trúc thư mục thì rõ hơn giữ bằng
lời hứa.

── ĐÂY KHÔNG PHẢI ĐẶT THẬT ──
Không có vé, không có phòng, không đồng nào chuyển. Mọi kết quả mang `mo_phong: True`
và mã bắt đầu bằng "MP-". Một xác nhận đặt chỗ trông y như thật mà thực ra là giả là
thứ nguy hiểm nhất ở đây — người dùng có thể ra sân bay với nó.
"""

from __future__ import annotations

import hashlib

from app.core.config import settings


def dat_cho_mo_phong(loai: str, chi_tiet: dict) -> dict:
    """Trả một 'xác nhận' mô phỏng, tất định theo nội dung đơn.

    Tất định để demo lặp lại được và test không chớp nháy — cùng một đơn luôn ra cùng
    một mã."""
    hat = f"{loai}|" + "|".join(f"{k}={chi_tiet[k]}" for k in sorted(chi_tiet))
    ma = hashlib.sha1(hat.encode("utf-8")).hexdigest()[:8].upper()
    return {
        "ma_dat_cho": f"MP-{ma}",
        "loai": loai,
        "mo_phong": True,
        "canh_bao": "ĐÂY LÀ ĐẶT CHỖ MÔ PHỎNG. Không có vé, không có phòng, không có "
                    "khoản tiền nào được thanh toán.",
        "chi_tiet": chi_tiet,
    }


def co_nha_cung_cap_that() -> bool:
    """Có cấu hình nhà cung cấp thật không.

    Dùng để TỪ CHỐI chạy mô phỏng khi có khoá thật: phần đặt qua Amadeus chưa nối, và
    chạy giả lập trong lúc hệ thống đang cấu hình cho môi trường thật là kiểu nhầm tệ
    nhất — người vận hành tưởng đã đặt xong."""
    return bool(getattr(settings, "amadeus_key", "") and getattr(settings, "amadeus_secret", ""))
