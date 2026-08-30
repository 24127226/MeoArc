# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/dat_cho_routes.py — TRA CỨU CHUYẾN BAY & PHÒNG (HTTP)      ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Endpoint tra cứu gọi THẲNG, không đi qua mô hình ngôn ngữ.

── VÌ SAO CÓ ĐƯỜNG NÀY, TRONG KHI ĐÃ CÓ TOOL CHO AGENT ──
Hai lý do, và cả hai đều là chuyện trình bày chứ không phải kỹ thuật:

1. KHÔNG PHỤ THUỘC HẠN MỨC. Hạn mức Gemini free là 20 lượt/ngày cho mỗi model. Một
   buổi bảo vệ mà phần quan trọng nhất chết vì hết lượt thì không có cách nào cứu
   tại chỗ. Đường này không gọi mô hình lần nào.

2. TÁCH BẠCH ĐIỀU ĐANG CHỨNG MINH. Khi người xem hỏi "cái này có thật không", câu
   trả lời phải là dữ liệu, không phải một đoạn văn do mô hình viết ra. Ở đây kết
   quả đi thẳng từ nhà cung cấp về giao diện — không có chỗ nào cho mô hình diễn
   đạt lại, nên cũng không có chỗ nào để nghi ngờ.

── MỌI PHẢN HỒI ĐỀU TỰ KHAI NGUỒN ──
Trường `nguon` ("amadeus" | "mo_phong") và `la_that` đi kèm mọi kết quả, cùng thời
điểm truy vấn. Giao diện dán nhãn đó lên thẻ. Một bảng giá mô phỏng trông y hệt giá
thật là thứ nguy hiểm nhất ở đây — người xem phải phân biệt được bằng mắt, không
phải bằng lời hứa.

CHỈ TRA CỨU. Không endpoint nào ở đây đặt chỗ hay thanh toán.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.services import dat_cho

router = APIRouter(prefix="/tra-cuu", tags=["tra-cuu"])


def _doc_ngay(s: str) -> datetime:
    """Đọc 'dd/mm/yyyy'. Sai định dạng thì BÁO LỖI chứ không đoán — đoán nhầm ngày
    bay là loại nhầm người dùng chỉ phát hiện ở sân bay."""
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y")
    except ValueError:
        raise HTTPException(400, f"Ngày '{s}' phải theo dạng dd/mm/yyyy")


def _vo_nguon(du_lieu: list[dict], ncc) -> dict:
    """Bọc kết quả kèm KHAI BÁO NGUỒN. Đây là phần khiến bản demo đáng tin.

    Nhãn lấy TỪ CHÍNH nhà cung cấp, không suy ra bằng cách so tên ở đây. Bản trước viết
    `ten == "amadeus"` nên khi thêm nguồn thứ ba (AeroDataBox) nó lặng lẽ bị xếp vào
    "mô phỏng" — dữ liệu thật bị dán nhãn giả, và không có gì báo lỗi. Nhãn thuộc về
    nơi biết sự thật về nguồn, tức là chính lớp nhà cung cấp.
    """
    return {
        "nguon": getattr(ncc, "ten", "mo_phong"),
        "la_that": getattr(ncc, "la_that", False),
        "nhan": getattr(ncc, "nhan", "MÔ PHỎNG · không phải giá thật"),
        "thoi_diem": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "so_ket_qua": len(du_lieu),
        "ket_qua": du_lieu,
    }


@router.get("/trang-thai")
def trang_thai():
    """Đang dùng nhà cung cấp nào. Giao diện gọi lúc mở khung để biết dán nhãn gì.

    Không trả về khoá, chỉ trả về CÓ hay KHÔNG — khoá không bao giờ được rời máy chủ."""
    ncc = dat_cho.lay_nha_cung_cap()
    that = getattr(ncc, "la_that", False)
    return {
        "nguon": getattr(ncc, "ten", "mo_phong"),
        "la_that": that,
        "nhan": getattr(ncc, "nhan", "MÔ PHỎNG · không phải giá thật"),
        # Nguồn thật vẫn có thể thiếu giá (AeroDataBox không bán vé). Giao diện cần biết
        # điều này TRƯỚC khi vẽ bảng, để dựng sẵn cột giá dạng gạch ngang thay vì đợi
        # kết quả về rồi mới phát hiện thiếu và nhảy bố cục.
        "co_gia": getattr(ncc, "ten", "") != "aerodatabox",
        "huong_dan": None if that else (
            "Chưa cấu hình AERODATABOX_KEY (hoặc AMADEUS_KEY/SECRET) trong .env "
            "nên đang dùng số mô phỏng."
        ),
    }


@router.get("/chuyen-bay")
def tim_chuyen_bay(
    tu: str = Query(..., min_length=3, max_length=3, description="Mã sân bay đi, vd SGN"),
    den: str = Query(..., min_length=3, max_length=3, description="Mã sân bay đến, vd DAD"),
    ngay: str = Query(..., description="Ngày bay dd/mm/yyyy"),
    so_ket_qua: int = Query(5, ge=1, le=10),
):
    """TRA CỨU chuyến bay. Không giữ chỗ, không đặt, không thanh toán."""
    ncc = dat_cho.lay_nha_cung_cap()
    d = _doc_ngay(ngay).date()
    try:
        ds = ncc.tim_chuyen_bay(tu.upper(), den.upper(), d, so_ket_qua)
    except RuntimeError as exc:
        # Lỗi nhà cung cấp đã được DIỄN GIẢI SẴN thành câu người dùng làm được gì đó
        # (vd chạm trần tốc độ → chờ vài giây). Giữ nguyên, đừng bọc thêm tên lớp
        # ngoại lệ vào: "RuntimeError: ..." không giúp ai cả.
        # 503 chứ không 502: dịch vụ vẫn sống, chỉ tạm thời chưa phục vụ được.
        raise HTTPException(503, str(exc))
    except Exception as exc:
        # Lỗi CHƯA diễn giải: nói THẲNG cả tên lớp. Nuốt thành "có lỗi xảy ra" thì lúc
        # trình bày mà hỏng, không ai biết đường sửa trong ba mươi giây.
        raise HTTPException(502, f"{type(exc).__name__}: {str(exc)[:200]}")
    return _vo_nguon([c.to_dict() for c in ds], ncc)


@router.get("/khach-san")
def tim_khach_san(
    thanh_pho: str = Query(..., min_length=2, description="Tên thành phố, vd Đà Nẵng"),
    nhan_phong: str = Query(..., description="dd/mm/yyyy"),
    tra_phong: str = Query(..., description="dd/mm/yyyy"),
    so_ket_qua: int = Query(5, ge=1, le=10),
):
    """TRA CỨU khách sạn. Không giữ chỗ, không đặt, không thanh toán."""
    ncc = dat_cho.lay_nha_cung_cap()
    nhan, tra = _doc_ngay(nhan_phong).date(), _doc_ngay(tra_phong).date()
    if tra <= nhan:
        raise HTTPException(400, "Ngày trả phòng phải sau ngày nhận phòng")
    try:
        ds = ncc.tim_khach_san(thanh_pho, nhan, tra, so_ket_qua)
    except ValueError as exc:
        # Không tra ra mã thành phố là lỗi ĐẦU VÀO của người dùng, không phải lỗi
        # nhà cung cấp — trả 400 kèm đúng lý do để họ sửa được, thay vì 502 khó hiểu.
        raise HTTPException(400, str(exc))
    except NotImplementedError:
        # Nguồn đang dùng chỉ có dữ liệu bay (AeroDataBox). LUI VỀ MÔ PHỎNG cho khách
        # sạn, và quan trọng hơn: bọc kết quả bằng CHÍNH nguồn mô phỏng đó, nên nhãn
        # trả về là "MÔ PHỎNG". Nếu vẫn bọc bằng `ncc` thì phòng bịa sẽ đội nhãn
        # "LỊCH BAY THẬT" — đúng kiểu lỗi mà cả tệp này sinh ra để tránh.
        ncc = dat_cho.NhaCungCapMoPhong()
        ds = ncc.tim_khach_san(thanh_pho, nhan, tra, so_ket_qua)
    except Exception as exc:
        raise HTTPException(502, f"{type(exc).__name__}: {str(exc)[:200]}")
    return _vo_nguon([k.to_dict() for k in ds], ncc)
