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

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_session
from app.models.session import AuthSession
from app.services import dat_cho

router = APIRouter(prefix="/tra-cuu", tags=["tra-cuu"])


def _phai_dang_nhap(session: AuthSession = Depends(get_current_session)) -> AuthSession:
    """Hai endpoint TỐN HẠN MỨC NHÀ CUNG CẤP phải yêu cầu đăng nhập.

    Gói AeroDataBox miễn phí tính theo lượt gọi, và MỖI lần tìm chuyến bay tốn 2 lượt.
    Để mở thì bất kỳ ai biết URL cũng đốt được hạn mức tháng của nhóm — không lấy được
    gì của người dùng, nhưng làm tính năng CHẾT đúng lúc cần nhất.

    `/trang-thai` và `/san-bay` VẪN MỞ có chủ ý: chúng chỉ trả siêu dữ liệu (đang dùng
    nguồn nào, danh sách sân bay), không gọi ra ngoài, không chạm dữ liệu ai. Giữ mở để
    còn kiểm tra được cấu hình bản deploy từ bên ngoài mà không phải đăng nhập."""
    return session


def _doc_ngay(s: str) -> datetime:
    """Đọc 'dd/mm/yyyy'. Sai định dạng thì BÁO LỖI chứ không đoán — đoán nhầm ngày
    bay là loại nhầm người dùng chỉ phát hiện ở sân bay."""
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y")
    except ValueError:
        raise HTTPException(400, f"Ngày '{s}' phải theo dạng dd/mm/yyyy")


def _khung_gio(gio: int) -> str:
    """Gộp giờ khởi hành thành 4 khung. Người ta chọn chuyến theo "sáng hay chiều",
    không theo từng giờ một — cho 24 ô lọc là bắt họ đọc nhiều hơn cần thiết."""
    if gio < 6:
        return "dem_khuya"
    if gio < 12:
        return "sang"
    if gio < 18:
        return "chieu"
    return "toi"


_TEN_KHUNG = {"dem_khuya": "Đêm/sáng sớm (00–06)", "sang": "Sáng (06–12)",
              "chieu": "Chiều (12–18)", "toi": "Tối (18–24)"}


def _bo_loc_co_the_dung(ds: list[dict]) -> dict:
    """Liệt kê các GIÁ TRỊ LỌC CÓ THẬT trong kết quả, kèm số chuyến mỗi giá trị.

    ── VÌ SAO SINH TỪ DỮ LIỆU, KHÔNG GÕ CỨNG DANH SÁCH ──
    Gõ cứng thì giao diện hiện "Bamboo Airways" cho một chặng không hãng nào bay, người
    dùng bấm vào rồi nhận danh sách rỗng và tưởng hỏng. Sinh từ dữ liệu thì mỗi ô lọc
    đều đảm bảo ra ít nhất một chuyến, và con số bên cạnh cho biết trước sẽ còn bao nhiêu.

    Lọc chạy ở GIAO DIỆN chứ không gọi lại máy chủ: cả ngày bay đã tải về rồi, lọc lại
    là việc của trình duyệt. Gọi lại vừa chậm vừa tốn hạn mức nhà cung cấp (gói miễn phí
    tính từng lượt), mà không biết thêm điều gì.
    """
    def dem(lay) -> list[dict]:
        d: dict[str, int] = {}
        for c in ds:
            v = (lay(c) or "").strip()
            if v:
                d[v] = d.get(v, 0) + 1
        return [{"gia_tri": k, "so_chuyen": n} for k, n in sorted(d.items(), key=lambda x: (-x[1], x[0]))]

    khung: dict[str, int] = {}
    for c in ds:
        try:
            g = int(str(c.get("khoi_hanh", ""))[11:13])
        except ValueError:
            continue
        k = _khung_gio(g)
        khung[k] = khung.get(k, 0) + 1

    return {
        "hang": dem(lambda c: c.get("hang")),
        "may_bay": dem(lambda c: c.get("may_bay")),
        "nha_ga": dem(lambda c: c.get("nha_ga")),
        "trang_thai": dem(lambda c: c.get("trang_thai")),
        "khung_gio": [
            {"gia_tri": k, "ten": _TEN_KHUNG[k], "so_chuyen": khung[k]}
            for k in ("dem_khuya", "sang", "chieu", "toi") if khung.get(k)
        ],
    }


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


def _ma_hoac_loi(gia_tri: str, nhan: str) -> str:
    """Đổi tên thành phố sang mã sân bay, hoặc BÁO LỖI kèm cách sửa.

    Trước đây tham số bị ép đúng 3 ký tự, tức là người dùng PHẢI tự biết "Nội Bài là
    HAN" — họ phải mở Google tra mã rồi mới quay lại gõ, nên công cụ chưa tiết kiệm
    được gì. Nay nhận cả tên thành phố.

    Không tra ra thì DỪNG kèm gợi ý, không đoán: đoán nhầm là gửi người ta tới sai đầu
    đất nước và họ chỉ phát hiện ở sân bay."""
    ma = dat_cho.ma_san_bay(gia_tri)
    if not ma:
        vd = ", ".join(f"{g['ten']} ({g['ma']})" for g in dat_cho.goi_y_san_bay(4))
        raise HTTPException(
            400, f"Không nhận ra {nhan} '{gia_tri}'. Gõ tên thành phố hoặc mã sân bay — ví dụ: {vd}."
        )
    return ma


@router.get("/san-bay")
def danh_sach_san_bay():
    """Danh sách sân bay để giao diện gợi ý — người dùng CHỌN chứ không phải nhớ mã."""
    return {
        "ket_qua": [
            {"ma": ma, "ten": tens[0], "cach_goi": list(tens)}
            for ma, tens in sorted(dat_cho.SAN_BAY.items())
        ],
        "pho_bien": dat_cho.goi_y_san_bay(10),
    }


@router.get("/chuyen-bay")
def tim_chuyen_bay(
    tu: str = Query(..., min_length=2, description="Tên thành phố hoặc mã sân bay, vd 'Hà Nội' hay HAN"),
    den: str = Query(..., min_length=2, description="Tên thành phố hoặc mã sân bay, vd 'Đà Nẵng' hay DAD"),
    ngay: str = Query(..., description="Ngày bay dd/mm/yyyy"),
    # Trần nâng từ 10 lên 100: cả ngày bay đã được tải về rồi (2 lượt gọi nhà cung cấp,
    # xem _CUA_SO), nên cắt còn 5 chuyến là VỨT ĐI dữ liệu đã trả tiền để lấy — mà
    # người dùng lại cần đủ chuyến thì bộ lọc mới có ý nghĩa.
    so_ket_qua: int = Query(30, ge=1, le=100),
    _=Depends(_phai_dang_nhap),
):
    """TRA CỨU chuyến bay. Không giữ chỗ, không đặt, không thanh toán."""
    ncc = dat_cho.lay_nha_cung_cap()
    d = _doc_ngay(ngay).date()
    ma_tu, ma_den = _ma_hoac_loi(tu, "điểm đi"), _ma_hoac_loi(den, "điểm đến")
    if ma_tu == ma_den:
        raise HTTPException(400, "Điểm đi và điểm đến đang là cùng một sân bay.")
    try:
        ds = ncc.tim_chuyen_bay(ma_tu, ma_den, d, so_ket_qua)
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
    ket_qua = [c.to_dict() for c in ds]
    # Kèm CÁC GIÁ TRỊ LỌC CÓ THẬT trong đúng kết quả này — giao diện dựng ô lọc từ
    # đó, nên không bao giờ có ô lọc bấm vào ra danh sách rỗng.
    return {**_vo_nguon(ket_qua, ncc), "bo_loc": _bo_loc_co_the_dung(ket_qua)}


@router.get("/khach-san")
def tim_khach_san(
    thanh_pho: str = Query(..., min_length=2, description="Tên thành phố, vd Đà Nẵng"),
    nhan_phong: str = Query(..., description="dd/mm/yyyy"),
    tra_phong: str = Query(..., description="dd/mm/yyyy"),
    so_ket_qua: int = Query(5, ge=1, le=10),
    _=Depends(_phai_dang_nhap),
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
