"""Ảnh đại diện người gửi — lấy biểu tượng nhận diện của tổ chức gửi thư.

── VÌ SAO PHẢI ĐI QUA BACKEND, KHÔNG GỌI THẲNG TỪ TRÌNH DUYỆT ──
Cách nhanh nhất là để trình duyệt trỏ thẳng `<img src="google.com/s2/favicons?domain=...">`.
Nhưng làm thế thì MỖI lần hiển thị hộp thư, trình duyệt gửi cho Google (hoặc
Gravatar) danh sách tên miền — tức là danh sách người đang liên hệ với người
dùng. Đó là rò rỉ dữ liệu quan hệ, và nó xảy ra âm thầm sau mỗi lần cuộn.

Đi qua backend thì bên thứ ba chỉ thấy MÁY CHỦ của mình hỏi, không thấy người
dùng nào đang hỏi, và không ghép được thành hồ sơ. Đổi lại phải tự lo cache —
đáng, vì đây là thứ gọi liên tục.

── VÌ SAO KHÔNG LẤY ẢNH GOOGLE CỦA CÁ NHÂN ──
Đã cân nhắc và không làm, vì ba lý do xếp theo mức nghiêm trọng:
  1. Gmail API KHÔNG trả ảnh đại diện người gửi. Muốn có phải dùng People API.
  2. People API chỉ trả ảnh của người NẰM TRONG DANH BẠ người dùng, nên phần lớn
     người gửi vẫn không có ảnh — công sức bỏ ra không đổi lấy được bao nhiêu.
  3. Nó đòi thêm quyền OAuth (`contacts.readonly`). Xin thêm quyền đọc toàn bộ
     danh bạ chỉ để hiển thị ảnh tròn là cái giá quá đắt, và trái với điều sản
     phẩm này đang hứa với người dùng ở trang giới thiệu — xin ít quyền nhất có
     thể. Nếu vẫn muốn, đây là một quyết định sản phẩm, không phải kỹ thuật.

Nên: tổ chức thì lấy biểu tượng tên miền (github.com, vercel.com, hcmus.edu.vn…),
cá nhân dùng hộp thư phổ thông thì giữ chữ cái đầu — chữ cái không phải giải pháp
tạm, nó là câu trả lời đúng khi không có gì thật để hiển thị.
"""

from __future__ import annotations

import logging
import time

import httpx
from fastapi import APIRouter, HTTPException, Response, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/avatars", tags=["avatars"])

# Hộp thư phổ thông: tên miền ở đây là của NHÀ CUNG CẤP, không phải của người gửi.
# Lấy biểu tượng gmail.com cho một cá nhân dùng Gmail thì mọi cá nhân đều đeo
# chung một logo Gmail — vô nghĩa và còn tệ hơn chữ cái đầu.
HOP_THU_PHO_THONG = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "yahoo.com.vn", "icloud.com", "me.com", "proton.me",
    "protonmail.com", "zoho.com", "aol.com", "mail.com", "gmx.com",
}

# Cache trong tiến trình: {ten_mien: (bytes, kieu_noi_dung, het_han)}
# Không dùng Redis/DB vì đây là dữ liệu rẻ, thay được, và mất cũng không sao —
# thêm một phụ thuộc hạ tầng cho việc này là không tương xứng.
_CACHE: dict[str, tuple[bytes, str, float]] = {}
_TTL = 60 * 60 * 24 * 7  # 7 ngày: logo công ty gần như không đổi
_TOI_DA = 500  # chặn cache phình vô hạn khi gặp hộp thư nhiều tên miền lạ


def _don_ten_mien(raw: str) -> str | None:
    """Chuẩn hoá và CHẶN đầu vào độc. Đây là tham số do người dùng đưa vào rồi
    dùng để gọi mạng ra ngoài — nếu không chặn thì thành SSRF: kẻ tấn công đưa
    `169.254.169.254` (endpoint metadata của máy ảo) và máy chủ tự đi lấy hộ."""
    d = (raw or "").strip().lower().lstrip("@")
    if not d or len(d) > 253:
        return None
    # Chỉ cho phép tên miền thật: chữ, số, dấu chấm, gạch nối, và PHẢI có dấu chấm.
    if not all(c.isalnum() or c in ".-" for c in d):
        return None
    if "." not in d or d.startswith(".") or d.endswith("."):
        return None
    # Chặn tên nội bộ và địa chỉ IP dạng số
    if d in {"localhost"} or d.endswith(".local") or d.endswith(".internal"):
        return None
    if all(p.isdigit() for p in d.split(".")):
        return None
    if d in HOP_THU_PHO_THONG:
        return None
    return d


@router.get("/{ten_mien}")
async def bieu_tuong_ten_mien(ten_mien: str) -> Response:
    """Trả biểu tượng nhận diện của một tên miền, có cache."""
    d = _don_ten_mien(ten_mien)
    if d is None:
        # 404 chứ không phải lỗi: "không có biểu tượng cho tên miền này" là một
        # câu trả lời hợp lệ, và frontend đã có sẵn đường lùi về chữ cái đầu.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không có biểu tượng cho tên miền này.")

    gio = time.time()
    hit = _CACHE.get(d)
    if hit and hit[2] > gio:
        return Response(content=hit[0], media_type=hit[1],
                        headers={"Cache-Control": "public, max-age=604800"})

    url = f"https://www.google.com/s2/favicons?domain={d}&sz=64"
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            r = await client.get(url)
        # Google trả một ảnh "quả cầu" mặc định cho tên miền không có favicon.
        # Ảnh đó rất nhỏ; lấy nó về thì mọi tên miền lạ đều đeo chung một quả cầu,
        # trong khi chữ cái đầu còn phân biệt được. Nên coi ảnh quá nhỏ là "không có".
        if r.status_code != 200 or len(r.content) < 120:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy biểu tượng.")
        kieu = r.headers.get("content-type", "image/png").split(";")[0]
        if not kieu.startswith("image/"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Phản hồi không phải ảnh.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.info("Không lấy được biểu tượng cho %s: %s", d, exc)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không lấy được biểu tượng.") from exc

    if len(_CACHE) >= _TOI_DA:
        _CACHE.clear()  # đơn giản hơn LRU, và mất cache ở đây không tốn gì
    _CACHE[d] = (r.content, kieu, gio + _TTL)
    return Response(content=r.content, media_type=kieu,
                    headers={"Cache-Control": "public, max-age=604800"})
