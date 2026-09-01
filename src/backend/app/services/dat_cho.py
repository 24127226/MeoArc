# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/dat_cho.py — TRA CỨU CHUYẾN BAY & PHÒNG (Giai đoạn 2) ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Tra cứu chỗ ở và chuyến bay. CHỈ ĐỌC — không có đường nào dẫn tới thanh toán.

── HAI NHÀ CUNG CẤP, VÀ VÌ SAO ──
`NhaCungCapMoPhong` chạy được ngay, không cần khoá, kết quả TẤT ĐỊNH (cùng đầu vào ra
cùng đầu ra). Đây là thứ dùng để trình bày và để chạy test.

`NhaCungCapAmadeus` gọi API thật (môi trường test của Amadeus, miễn phí). Chỉ bật khi có
`AMADEUS_KEY` + `AMADEUS_SECRET` trong .env.

── NÓI RÕ ĐÂU LÀ SỐ GIẢ ──
Mọi kết quả mang trường `nguon`: "mo_phong" hay "amadeus". Giá mô phỏng KHÔNG BAO GIỜ
được trình bày như giá thật — một bảng giá bịa nhìn y như giá thật là thứ khiến người
dùng đưa ra quyết định tiền bạc dựa trên số không có thật. Giao diện phải hiện nhãn đó.

── RANH GIỚI GIAI ĐOẠN ──
Tệp này KHÔNG có hàm nào đặt chỗ, giữ chỗ, hay thanh toán. Đó là Giai đoạn 3, và nó phải
đi qua cổng xác nhận riêng. Có test quét mã nguồn để giữ ranh giới đó.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from urllib.parse import quote_plus

from app.core.config import settings


# ── TÊN HÃNG BAY ─────────────────────────────────────────────────────────────
# Amadeus trả về MÃ IATA hai ký tự ("VJ", "VN"), không trả tên. Hiện "VJ" cho người
# dùng là bắt họ tự tra. Bảng này phủ các hãng bay nội địa Việt Nam — đủ cho mọi
# chặng trong nước, và có nhánh lùi giữ nguyên mã cho hãng lạ.
TEN_HANG: dict[str, str] = {
    "VN": "Vietnam Airlines", "VJ": "Vietjet Air", "QH": "Bamboo Airways",
    "BL": "Pacific Airlines", "VU": "Vietravel Airlines",
    "TR": "Scoot", "SQ": "Singapore Airlines", "TG": "Thai Airways",
    "KE": "Korean Air", "OZ": "Asiana Airlines", "CX": "Cathay Pacific",
    "JL": "Japan Airlines", "NH": "ANA", "AK": "AirAsia", "MH": "Malaysia Airlines",
    "CI": "China Airlines", "BR": "EVA Air", "QR": "Qatar Airways", "EK": "Emirates",
}


# ── TÊN THÀNH PHỐ → MÃ SÂN BAY ───────────────────────────────────────────────
# Bắt người dùng tự biết "Nội Bài là HAN" là bắt họ làm việc của máy: họ phải mở
# Google tra mã, rồi mới quay lại gõ vào đây — tức công cụ chưa tiết kiệm được gì.
# Bảng phủ toàn bộ sân bay dân dụng Việt Nam + các điểm đến quốc tế phổ biến.
# Mỗi mã kèm NHIỀU CÁCH GỌI. PHẦN TỬ ĐẦU là TÊN HIỂN THỊ (có dấu, viết hoa đúng) —
# nó được đem ra gợi ý cho người dùng, nên không được là chuỗi không dấu dùng để so
# khớp nội bộ. Các phần tử sau chỉ để nhận dạng; `_bo_dau` chuẩn hoá hết khi dựng bảng
# tra ngược nên viết có dấu hay không đều khớp được.
SAN_BAY: dict[str, tuple[str, ...]] = {
    "SGN": ("TP HCM", "tphcm", "ho chi minh", "thanh pho ho chi minh", "sai gon",
            "saigon", "tan son nhat", "hcm"),
    "HAN": ("Hà Nội", "hanoi", "noi bai"),
    "DAD": ("Đà Nẵng", "danang"),
    "CXR": ("Nha Trang", "cam ranh", "khanh hoa"),
    "PQC": ("Phú Quốc", "kien giang"),
    "HPH": ("Hải Phòng", "cat bi"),
    "VCA": ("Cần Thơ", "tra noc"),
    "HUI": ("Huế", "phu bai", "thua thien hue"),
    "DLI": ("Đà Lạt", "dalat", "lien khuong", "lam dong"),
    "VII": ("Vinh", "nghe an"),
    "UIH": ("Quy Nhơn", "phu cat", "binh dinh"),
    "THD": ("Thanh Hoá", "tho xuan"),
    "BMV": ("Buôn Ma Thuột", "dak lak", "daklak"),
    "PXU": ("Pleiku", "gia lai"),
    "TBB": ("Tuy Hoà", "phu yen"),
    "VDO": ("Vân Đồn", "quang ninh", "ha long"),
    "VCL": ("Chu Lai", "tam ky", "quang nam"),
    "CAH": ("Cà Mau",),
    "VKG": ("Rạch Giá",),
    "DIN": ("Điện Biên", "dien bien phu"),
    "VDH": ("Đồng Hới", "quang binh"),
    "BKK": ("Bangkok", "thai lan", "suvarnabhumi"),
    "SIN": ("Singapore", "changi"),
    "KUL": ("Kuala Lumpur", "malaysia"),
    "HKG": ("Hong Kong", "hongkong"),
    "ICN": ("Seoul", "han quoc", "incheon"),
    "NRT": ("Tokyo", "narita", "nhat ban"),
    "TPE": ("Đài Bắc", "taipei", "dai loan"),
    "PVG": ("Thượng Hải", "shanghai"),
    "PEK": ("Bắc Kinh", "beijing"),
    "CDG": ("Paris", "phap"),
    "LHR": ("London", "anh"),
    "SYD": ("Sydney", "uc"),
    "MEL": ("Melbourne",),
    "LAX": ("Los Angeles", "la"),
    "SFO": ("San Francisco",),
    "DXB": ("Dubai",),
    "DOH": ("Doha", "qatar"),
}


def _bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp. "Đà Nẵng" và "da nang" phải ra cùng một chỗ —
    không ai gõ đúng dấu khi đang vội, và bắt gõ đúng dấu cũng là một rào cản."""
    import unicodedata
    s = (s or "").strip().lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


# Dựng sẵn bảng tra ngược một lần, thay vì quét lại mỗi lời gọi.
_TRA_NGUOC: dict[str, str] = {
    _bo_dau(ten): ma for ma, tens in SAN_BAY.items() for ten in tens
}


def ma_san_bay(text: str) -> str | None:
    """Đổi thứ người dùng gõ thành mã IATA. Trả None nếu không nhận ra.

    Nhận: mã sẵn ("HAN", "han"), tên thành phố ("Hà Nội", "ha noi"), tên sân bay
    ("Nội Bài"), và khớp một phần ("sân bay Đà Nẵng" → DAD).

    KHÔNG đoán bừa khi không chắc: trả None để tầng trên hỏi lại. Đoán nhầm thành phố
    là gửi người ta tới sai đầu đất nước, và họ chỉ phát hiện ở sân bay.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    # Đã là mã IATA thì dùng luôn — người biết mã không phải đi đường vòng.
    if len(raw) == 3 and raw.isalpha() and raw.upper() in SAN_BAY:
        return raw.upper()

    goi = _bo_dau(raw)
    if goi in _TRA_NGUOC:
        return _TRA_NGUOC[goi]

    # Khớp một phần: "sân bay đà nẵng", "bay đi Nha Trang". Chọn tên KHỚP DÀI NHẤT để
    # "tp hcm" không bị "hcm" giành mất, và tránh khớp bừa vào tên ngắn.
    ung_vien = [(ten, ma) for ten, ma in _TRA_NGUOC.items() if ten in goi]
    if ung_vien:
        return max(ung_vien, key=lambda x: len(x[0]))[1]
    return None


def goi_y_san_bay(so: int = 8) -> list[dict]:
    """Vài sân bay phổ biến để giao diện gợi ý sẵn — người dùng bấm chứ không phải gõ."""
    pho_bien = ["SGN", "HAN", "DAD", "CXR", "PQC", "HPH", "HUI", "DLI", "VCA", "UIH"]
    return [{"ma": m, "ten": SAN_BAY[m][0]} for m in pho_bien[:so]]


def ten_hang(ma: str) -> str:
    """Đổi mã IATA sang tên hãng. Không biết thì GIỮ NGUYÊN MÃ — bịa một cái tên
    còn tệ hơn hiện hai chữ cái, vì người dùng sẽ tin cái tên đó."""
    return TEN_HANG.get((ma or "").upper(), (ma or "").upper())


def lien_ket_chuyen_bay(tu: str, den: str, ngay: date) -> str:
    """Đường dẫn MỞ RA TRANG THẬT của chặng bay này trên Google Flights.

    ── VÌ SAO PHẢI CÓ ──
    Một bảng giá không bấm được thì người dùng vẫn phải tự mở tab khác và gõ lại từ
    đầu — tức là công cụ chưa tiết kiệm được gì. Bấm ra trang thật cũng là cách người
    xem TỰ KIỂM số liệu: giá trên màn hình khớp hay không khớp với thị trường, họ
    thấy ngay trong ba giây.

    ── VÌ SAO KHÔNG PHẢI LINK ĐẶT CỦA HÃNG ──
    Amadeus môi trường Test không trả về đường đặt chỗ, và dựng link đặt của từng
    hãng là đoán — đoán sai thì người dùng bấm vào một chặng khác với thứ họ vừa xem.
    Google Flights là trang TRA CỨU trung lập, dựng được từ đúng ba dữ kiện ta có
    chắc chắn: chặng đi, chặng đến, ngày."""
    q = f"Flights from {tu} to {den} on {ngay.isoformat()}"
    return "https://www.google.com/travel/flights?q=" + quote_plus(q)


def lien_ket_chi_tiet_chuyen_bay(so_hieu: str, ngay: date) -> str:
    """Mở THẺ CHI TIẾT của ĐÚNG chuyến bay này trên Google.

    ── KHÁC GÌ `lien_ket_chuyen_bay` ──
    Hàm kia dựng link theo CHẶNG (SGN→DAD ngày 15/9) — mở ra một bảng nhiều chuyến,
    người dùng vẫn phải tự dò lại chuyến mình vừa xem. Hàm này dựng theo SỐ HIỆU, nên
    bấm vào một dòng là ra đúng dòng đó: giờ khởi hành, nhà ga, cửa ra, loại máy bay,
    trạng thái đang bay hay chưa.

    Chỉ dựng được khi số hiệu là THẬT. Với nhà cung cấp mô phỏng thì số hiệu do hàm
    băm sinh ra, tra Google sẽ không ra gì — nên `to_dict` chỉ gắn link này khi nguồn
    tự khai là thật. Một đường dẫn dẫn tới trang trống còn tệ hơn không có đường dẫn:
    người dùng kết luận công cụ hỏng, chứ không kết luận dữ liệu là giả.

    ── GIỚI HẠN CÒN LẠI ──
    Google KHÔNG có đường dẫn công khai trỏ thẳng vào một chuyến bay cụ thể; ta chỉ gửi
    được một truy vấn tìm kiếm và để Google tự quyết có hiện thẻ chuyến bay hay không.
    Nên đôi khi nó hiện thẻ đúng chuyến, đôi khi ra danh sách kết quả. Cách tăng khả
    năng ra thẻ: TÁCH mã hãng khỏi số hiệu bằng dấu cách ("VN 106", không phải "VN106")
    — đó là dạng Google dùng để nhận diện số hiệu chuyến bay.
    """
    import re
    # "VN106" → "VN 106". Không khớp mẫu thì giữ nguyên, đừng cắt bừa.
    dep = re.sub(r"^([A-Z0-9]{2})(\d{1,4})$", r"\1 \2", so_hieu.upper())
    return "https://www.google.com/search?q=" + quote_plus(
        f"{dep} {ngay.strftime('%d/%m/%Y')}"
    )


# ── TOẠ ĐỘ TRUNG TÂM CÁC TỈNH/THÀNH ──────────────────────────────────────────
# Dùng để (a) sinh khách sạn mô phỏng ở ĐÚNG thành phố người dùng hỏi, và (b) nhúng
# bản đồ chỉ thẳng vào vị trí thay vì chỉ đưa một đường dẫn Google Maps.
#
# Toạ độ là THẬT (trung tâm hành chính). Tên khách sạn thì mô phỏng — và giao diện
# dán nhãn rõ. Ranh giới ở đây quan trọng: một khách sạn bịa đặt ở đúng toạ độ thành
# phố thì bản đồ vẫn nói thật về VỊ TRÍ, chỉ cái tên là không có thật.
TOA_DO_TP: dict[str, tuple[float, float, str]] = {
    "tp hcm": (10.7769, 106.7009, "TP Hồ Chí Minh"),
    "ha noi": (21.0278, 105.8342, "Hà Nội"),
    "da nang": (16.0544, 108.2022, "Đà Nẵng"),
    "hai phong": (20.8449, 106.6881, "Hải Phòng"),
    "can tho": (10.0452, 105.7469, "Cần Thơ"),
    "hue": (16.4637, 107.5909, "Huế"),
    "nha trang": (12.2388, 109.1967, "Nha Trang"),
    "da lat": (11.9404, 108.4583, "Đà Lạt"),
    "phu quoc": (10.2270, 103.9670, "Phú Quốc"),
    "vung tau": (10.3460, 107.0843, "Vũng Tàu"),
    "ha long": (20.9101, 107.1839, "Hạ Long"),
    "quy nhon": (13.7829, 109.2196, "Quy Nhơn"),
    "hoi an": (15.8801, 108.3380, "Hội An"),
    "sapa": (22.3364, 103.8438, "Sa Pa"),
    "phan thiet": (10.9280, 108.1020, "Phan Thiết"),
    "buon ma thuot": (12.6667, 108.0500, "Buôn Ma Thuột"),
    "pleiku": (13.9833, 108.0000, "Pleiku"),
    "vinh": (18.6790, 105.6813, "Vinh"),
    "thanh hoa": (19.8067, 105.7852, "Thanh Hoá"),
    "nam dinh": (20.4388, 106.1621, "Nam Định"),
    "thai nguyen": (21.5942, 105.8482, "Thái Nguyên"),
    "bac ninh": (21.1861, 106.0763, "Bắc Ninh"),
    "hai duong": (20.9373, 106.3145, "Hải Dương"),
    "ninh binh": (20.2506, 105.9745, "Ninh Bình"),
    "quang binh": (17.4689, 106.6223, "Đồng Hới"),
    "quang tri": (16.7500, 107.2000, "Quảng Trị"),
    "quang ngai": (15.1214, 108.8044, "Quảng Ngãi"),
    "tuy hoa": (13.0955, 109.3200, "Tuy Hoà"),
    "phan rang": (11.5642, 108.9887, "Phan Rang"),
    "bien hoa": (10.9447, 106.8243, "Biên Hoà"),
    "thu dau mot": (10.9804, 106.6519, "Thủ Dầu Một"),
    "my tho": (10.3600, 106.3600, "Mỹ Tho"),
    "long xuyen": (10.3860, 105.4350, "Long Xuyên"),
    "rach gia": (10.0125, 105.0808, "Rạch Giá"),
    "ca mau": (9.1769, 105.1524, "Cà Mau"),
    "soc trang": (9.6025, 105.9739, "Sóc Trăng"),
    "ben tre": (10.2415, 106.3759, "Bến Tre"),
    "tay ninh": (11.3100, 106.0983, "Tây Ninh"),
    "lang son": (21.8537, 106.7615, "Lạng Sơn"),
    "dien bien": (21.3860, 103.0230, "Điện Biên Phủ"),
    "ha giang": (22.8233, 104.9784, "Hà Giang"),
    "con dao": (8.6833, 106.6000, "Côn Đảo"),
    "cat ba": (20.7280, 107.0480, "Cát Bà"),
    "mui ne": (10.9330, 108.2870, "Mũi Né"),
}


def tra_toa_do(thanh_pho: str) -> tuple[float, float, str] | None:
    """Tên thành phố (có dấu hay không) → (vĩ độ, kinh độ, tên chuẩn)."""
    goi = _bo_dau(thanh_pho)
    if goi in TOA_DO_TP:
        return TOA_DO_TP[goi]
    # Khớp một phần: "khách sạn ở Đà Nẵng" → da nang. Chọn tên DÀI NHẤT khớp được để
    # "hue" không giành mất của một tên dài hơn có chứa nó.
    ung = [(k, v) for k, v in TOA_DO_TP.items() if k in goi]
    return max(ung, key=lambda x: len(x[0]))[1] if ung else None


def lien_ket_ban_do_nhung(vi_do: float, kinh_do: float) -> str:
    """Bản đồ NHÚNG THẲNG vào trang, có ghim vị trí — không cần khoá API.

    ── VÌ SAO OPENSTREETMAP CHỨ KHÔNG PHẢI GOOGLE MAPS ──
    Bản đồ nhúng của Google đòi khoá API và có hạn mức tính tiền. Thêm một khoá nữa
    vào .env là thêm một thứ có thể quên cấu hình rồi hỏng đúng lúc trình bày — mà
    nhóm đã vấp đúng chuyện đó với Gemini và Amadeus. OSM nhúng được không cần khoá,
    không hạn mức, nên nó luôn chạy.
    Nút "mở Google Maps" vẫn giữ cho ai muốn chỉ đường."""
    d = 0.008   # khung ~1.5km quanh điểm: đủ thấy phố xá, chưa mất bối cảnh khu vực
    bbox = f"{kinh_do - d},{vi_do - d},{kinh_do + d},{vi_do + d}"
    return ("https://www.openstreetmap.org/export/embed.html"
            f"?bbox={bbox}&layer=mapnik&marker={vi_do},{kinh_do}")


def lien_ket_ban_do(ten: str, thanh_pho: str,
                    nhan: date | None = None, tra: date | None = None) -> str:
    """Mở khách sạn trên Google, MANG THEO ngày nhận/trả phòng người dùng vừa nhập.

    ── VÌ SAO ĐEM NGÀY THEO ──
    Bản trước mở Google Maps trống ngày, nên người dùng sang tới nơi vẫn phải gõ lại
    đúng hai cái ngày họ vừa gõ ở đây. Mỗi lần bắt gõ lại một thứ vừa gõ là một lần
    công cụ tự nhận mình chỉ là cái nút mở tab mới.
    Có ngày thì Google Hotels mở ra ĐÚNG khoảng lưu trú đó, kèm giá THẬT của khoảng
    đó — tức là chỗ này vá luôn phần MeoArc không có: giá phòng thật.

    Thiếu ngày (gọi từ chỗ khác) thì lùi về Maps như cũ, không vỡ."""
    if nhan and tra:
        return ("https://www.google.com/travel/search?q="
                + quote_plus(f"{ten} {thanh_pho}")
                + f"&checkin={nhan.isoformat()}&checkout={tra.isoformat()}")
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{ten} {thanh_pho}")



# ── Kiểu dữ liệu ─────────────────────────────────────────────────────────────

@dataclass
class ChuyenBay:
    ma: str
    hang: str
    tu: str
    den: str
    khoi_hanh: datetime
    ha_canh: datetime
    gia_vnd: int          # 0 = KHÔNG CÓ DỮ LIỆU GIÁ (xem `co_gia` trong to_dict)
    so_diem_dung: int
    hoan_duoc: bool
    nguon: str
    # ── Dữ liệu chỉ nguồn THẬT mới có. Mặc định rỗng để nguồn mô phỏng không phải
    # bịa thêm: rỗng nghĩa là "không biết", và giao diện hiểu đúng như vậy.
    may_bay: str = ""
    nha_ga: str = ""
    trang_thai: str = ""
    la_that: bool = False

    def to_dict(self) -> dict:
        d = {
            "ma": self.ma, "hang": self.hang, "tu": self.tu, "den": self.den,
            "khoi_hanh": self.khoi_hanh.strftime("%d/%m/%Y %H:%M"),
            "ha_canh": self.ha_canh.strftime("%d/%m/%Y %H:%M"),
            "gia_vnd": self.gia_vnd, "so_diem_dung": self.so_diem_dung,
            "hoan_duoc": self.hoan_duoc, "nguon": self.nguon,
            # ── GIÁ LÀ TUỲ CHỌN ──
            # Nguồn lịch bay thật (AeroDataBox) KHÔNG bán vé nên không có giá. Trả 0 rồi
            # để giao diện tự đoán là "miễn phí" thì tệ hơn nhiều so với nói thẳng là
            # không biết — nên gửi kèm cờ này thay vì bắt giao diện suy ra từ số 0.
            "co_gia": self.gia_vnd > 0,
            "may_bay": self.may_bay, "nha_ga": self.nha_ga,
            "trang_thai": self.trang_thai, "la_that": self.la_that,
            # Bấm ra trang thật — vừa tiện, vừa là cách người xem tự kiểm số liệu.
            "lien_ket": lien_ket_chuyen_bay(self.tu, self.den, self.khoi_hanh.date()),
            "phut_bay": int((self.ha_canh - self.khoi_hanh).total_seconds() // 60),
        }
        # Link theo SỐ HIỆU chỉ có nghĩa khi số hiệu là thật — xem chú thích ở
        # `lien_ket_chi_tiet_chuyen_bay`.
        if self.la_that:
            d["lien_ket_chi_tiet"] = lien_ket_chi_tiet_chuyen_bay(
                self.ma, self.khoi_hanh.date()
            )
        return d


@dataclass
class KhachSan:
    ma: str
    ten: str
    thanh_pho: str
    nhan_phong: date
    tra_phong: date
    gia_moi_dem_vnd: int
    so_sao: float
    cach_trung_tam_km: float
    huy_mien_phi: bool
    nguon: str
    # Toạ độ THẬT của khu vực. 0,0 = không biết → giao diện không vẽ bản đồ, chứ
    # không vẽ một cái ghim ngoài khơi vịnh Guinea (đúng chỗ toạ độ 0,0 rơi vào).
    vi_do: float = 0.0
    kinh_do: float = 0.0
    # True = TÊN, HẠNG SAO và VỊ TRÍ là của một cơ sở CÓ THẬT; giá vẫn mô phỏng.
    # Tách riêng khỏi `nguon` vì hai điều đó khác nhau, và gộp lại thì hoặc phải gọi
    # cả bảng là "thật" (nói quá về giá — con số người dùng ra quyết định dựa vào),
    # hoặc phải gọi một khách sạn có thật là "bịa".
    ten_that: bool = False

    def to_dict(self) -> dict:
        so_dem = max(1, (self.tra_phong - self.nhan_phong).days)
        co_toa_do = bool(self.vi_do or self.kinh_do)
        return {
            "vi_do": self.vi_do, "kinh_do": self.kinh_do, "ten_that": self.ten_that,
            "ban_do_nhung": (lien_ket_ban_do_nhung(self.vi_do, self.kinh_do)
                             if co_toa_do else None),
            "ma": self.ma, "ten": self.ten, "thanh_pho": self.thanh_pho,
            "nhan_phong": self.nhan_phong.strftime("%d/%m/%Y"),
            "tra_phong": self.tra_phong.strftime("%d/%m/%Y"),
            "so_dem": so_dem,
            "gia_moi_dem_vnd": self.gia_moi_dem_vnd,
            "tong_vnd": self.gia_moi_dem_vnd * so_dem,
            "so_sao": self.so_sao, "cach_trung_tam_km": self.cach_trung_tam_km,
            "huy_mien_phi": self.huy_mien_phi, "nguon": self.nguon,
            # Mang theo ĐÚNG hai ngày người dùng vừa nhập — xem chú thích ở
            # `lien_ket_ban_do`. Google Hotels mở ra đúng khoảng đó kèm GIÁ THẬT,
            # tức là vá luôn phần MeoArc không có.
            "lien_ket": lien_ket_ban_do(self.ten, self.thanh_pho,
                                        self.nhan_phong, self.tra_phong),
        }


# ── Nhà cung cấp MÔ PHỎNG ────────────────────────────────────────────────────

_HANG_BAY = [("VN", "Vietnam Airlines"), ("VJ", "Vietjet Air"), ("QH", "Bamboo Airways")]
_TEN_KHACH_SAN = ["Riverside", "Central Plaza", "Bay View", "Old Quarter Inn", "Sunrise"]

# ── KHÁCH SẠN & RESORT CÓ THẬT ───────────────────────────────────────────────
# (tên, số sao, vĩ độ, kinh độ). Ưu tiên 4–5 sao vì đây là thứ hiện ra đầu tiên khi
# trình bày, và một danh sách nhà nghỉ 2 sao thì không nói lên điều gì về sản phẩm.
#
# ── RANH GIỚI: CÁI GÌ THẬT, CÁI GÌ KHÔNG ──
# THẬT: tên cơ sở, hạng sao, vị trí. Đây là thông tin công khai, kiểm chứng được —
#       người xem tra tên trên bản đồ là ra đúng chỗ.
# MÔ PHỎNG: GIÁ và tình trạng phòng. Không nguồn miễn phí nào cho giá phòng thật
#       (Booking/Agoda đều đòi hợp đồng đối tác), nên giá vẫn do hàm băm sinh ra.
# Vì vậy nhãn nguồn KHÔNG đổi thành "thật" — chỉ thêm cờ `ten_that` để giao diện nói
# chính xác: "tên & vị trí thật · giá mô phỏng". Nói gọn thành "dữ liệu thật" ở đây là
# nói quá, và giá mới là con số người dùng ra quyết định dựa vào.
#
# Toạ độ ~vài trăm mét là đủ cho bản đồ khu vực; hạng sao theo công bố phổ biến.
KHACH_SAN_THAT: dict[str, list[tuple[str, float, float, float]]] = {
    "tp hcm": [
        ("The Reverie Saigon", 5, 10.7723, 106.7047),
        ("Park Hyatt Saigon", 5, 10.7768, 106.7028),
        ("Caravelle Saigon", 5, 10.7768, 106.7031),
        ("Rex Hotel Saigon", 5, 10.7745, 106.7010),
        ("Hotel Continental Saigon", 4, 10.7765, 106.7020),
    ],
    "ha noi": [
        ("Sofitel Legend Metropole Hanoi", 5, 21.0245, 105.8570),
        ("Lotte Hotel Hanoi", 5, 21.0313, 105.8134),
        ("Meliá Hanoi", 5, 21.0258, 105.8437),
        ("Hotel de l'Opera Hanoi", 5, 21.0243, 105.8563),
        ("Hanoi La Siesta Premium", 4, 21.0345, 105.8500),
    ],
    "da nang": [
        ("InterContinental Danang Sun Peninsula Resort", 5, 16.1200, 108.3000),
        ("Furama Resort Danang", 5, 16.0430, 108.2470),
        ("Premier Village Danang Resort", 5, 16.0170, 108.2600),
        ("Novotel Danang Premier Han River", 5, 16.0720, 108.2240),
        ("Danang Golden Bay", 5, 16.0900, 108.2260),
    ],
    "nha trang": [
        ("InterContinental Nha Trang", 5, 12.2400, 109.1970),
        ("Sheraton Nha Trang Hotel & Spa", 5, 12.2430, 109.1960),
        ("Vinpearl Resort Nha Trang", 5, 12.2130, 109.2470),
        ("Amiana Resort Nha Trang", 5, 12.2900, 109.2200),
        ("Havana Nha Trang Hotel", 5, 12.2380, 109.1970),
    ],
    "da lat": [
        ("Dalat Palace Heritage Hotel", 5, 11.9400, 108.4400),
        ("Ana Mandara Villas Dalat Resort", 5, 11.9330, 108.4200),
        ("Dalat Edensee Lake Resort & Spa", 5, 11.8980, 108.4180),
        ("Swiss-Belresort Tuyen Lam", 5, 11.9000, 108.4300),
        ("Terracotta Hotel & Resort Dalat", 4, 11.9130, 108.4460),
    ],
    "phu quoc": [
        ("JW Marriott Phu Quoc Emerald Bay", 5, 10.0400, 104.0180),
        ("InterContinental Phu Quoc Long Beach", 5, 10.1500, 103.9600),
        ("Premier Village Phu Quoc Resort", 5, 10.0300, 104.0200),
        ("Vinpearl Resort & Spa Phu Quoc", 5, 10.3300, 103.8560),
        ("Salinda Resort Phu Quoc", 5, 10.1930, 103.9560),
    ],
    "hoi an": [
        ("Four Seasons Resort The Nam Hai", 5, 15.9330, 108.2900),
        ("Anantara Hoi An Resort", 5, 15.8800, 108.3350),
        ("La Siesta Hoi An Resort & Spa", 5, 15.8820, 108.3200),
        ("Allegro Hoi An", 4, 15.8830, 108.3260),
        ("Hoi An Silk Marina Resort", 4, 15.8790, 108.3250),
    ],
    "hue": [
        ("Azerai La Residence Hue", 5, 16.4620, 107.5860),
        ("Meliá Vinpearl Hue", 5, 16.4680, 107.5930),
        ("Indochine Palace", 5, 16.4600, 107.5960),
        ("Silk Path Grand Hue", 5, 16.4640, 107.5900),
        ("Pilgrimage Village Boutique Resort", 5, 16.4300, 107.5650),
    ],
    "ha long": [
        ("Vinpearl Resort & Spa Ha Long", 5, 20.9500, 107.0700),
        ("Wyndham Legend Halong", 5, 20.9530, 107.0790),
        ("FLC Grand Hotel Halong", 5, 20.9600, 107.0500),
        ("Muong Thanh Luxury Quang Ninh", 5, 20.9540, 107.0770),
        ("Novotel Ha Long Bay", 4, 20.9520, 107.0740),
    ],
    "vung tau": [
        ("Pullman Vung Tau", 5, 10.3460, 107.0850),
        ("The Imperial Hotel Vung Tau", 5, 10.3330, 107.0800),
        ("Marina Bay Vung Tau Resort", 5, 10.3200, 107.0900),
        ("Lan Rung Resort & Spa", 4, 10.3250, 107.0870),
        ("Malibu Hotel Vung Tau", 4, 10.3400, 107.0830),
    ],
    "sapa": [
        ("Hotel de la Coupole – MGallery", 5, 22.3340, 103.8420),
        ("Silk Path Grand Sapa Resort", 5, 22.3370, 103.8450),
        ("Pao's Sapa Leisure Hotel", 5, 22.3300, 103.8480),
        ("Victoria Sapa Resort & Spa", 4, 22.3390, 103.8410),
        ("Sapa Jade Hill Resort", 4, 22.3250, 103.8500),
    ],
    "quy nhon": [
        ("Anantara Quy Nhon Villas", 5, 13.7000, 109.2600),
        ("FLC Luxury Hotel Quy Nhon", 5, 13.8600, 109.2500),
        ("Muong Thanh Luxury Quy Nhon", 5, 13.7760, 109.2230),
        ("Avani Quy Nhon Resort", 4, 13.7300, 109.2300),
        ("Seagull Hotel Quy Nhon", 4, 13.7700, 109.2260),
    ],
    "mui ne": [
        ("Anantara Mui Ne Resort", 5, 10.9450, 108.2300),
        ("The Anam Mui Ne", 5, 10.9500, 108.2200),
        ("Sea Links Beach Hotel", 5, 10.9200, 108.2500),
        ("Victoria Phan Thiet Beach Resort", 4, 10.9370, 108.2350),
        ("Pandanus Resort Mui Ne", 4, 10.9600, 108.2100),
    ],
    "can tho": [
        ("Azerai Can Tho", 5, 10.0600, 105.7500),
        ("Vinpearl Hotel Can Tho", 5, 10.0330, 105.7860),
        ("Muong Thanh Luxury Can Tho", 5, 10.0400, 105.7800),
        ("Nam Bo Boutique Hotel", 4, 10.0340, 105.7880),
        ("Iris Hotel Can Tho", 4, 10.0350, 105.7830),
    ],
    "hai phong": [
        ("Vinpearl Hotel Imperia Hai Phong", 5, 20.8500, 106.6880),
        ("Pullman Hai Phong Grand", 5, 20.8560, 106.6820),
        ("Mercure Hai Phong", 4, 20.8480, 106.6900),
        ("Somerset Central TD Hai Phong", 4, 20.8530, 106.6860),
        ("Nam Cuong Hai Phong Hotel", 4, 20.8470, 106.6830),
    ],
}


def tra_khach_san_that(thanh_pho: str) -> list[tuple[str, float, float, float]]:
    """Danh sách cơ sở CÓ THẬT ở thành phố này, sắp SAO CAO TRƯỚC. Rỗng nếu chưa có."""
    goi = _bo_dau(thanh_pho)
    ds = KHACH_SAN_THAT.get(goi)
    if ds is None:
        ung = [(k, v) for k, v in KHACH_SAN_THAT.items() if k in goi]
        ds = max(ung, key=lambda x: len(x[0]))[1] if ung else []
    return sorted(ds, key=lambda x: -x[1])


class NhaCungCapMoPhong:
    """Kết quả TẤT ĐỊNH sinh từ hàm băm của tham số tìm kiếm.

    Tất định là có chủ ý: cùng một câu hỏi lúc nào cũng ra cùng một bảng, nên demo lặp
    lại được và test không bao giờ chớp nháy. Ngẫu nhiên thì mỗi lần chạy một khác, và
    lúc đó không ai phân biệt được "giá đổi" với "mã hỏng".
    """

    # ── NHÀ CUNG CẤP TỰ KHAI NHÃN ──
    # Trước đây tầng HTTP so chuỗi `ten == "amadeus"` để quyết định dán nhãn gì. Cách
    # đó chỉ đúng khi có ĐÚNG HAI nhà cung cấp: thêm cái thứ ba là mọi nguồn mới mặc
    # định bị xếp vào "mô phỏng" mà không ai báo lỗi. Để chính lớp nhà cung cấp khai
    # thì thêm nguồn = thêm một class, tầng trên không phải sửa và không thể sót.
    ten = "mo_phong"
    la_that = False
    nhan = "MÔ PHỎNG · không phải giá thật"

    @staticmethod
    def _so(hat: str, day: int, cao: int) -> int:
        h = int(hashlib.sha1(hat.encode("utf-8")).hexdigest()[:8], 16)
        return day + h % max(1, cao - day)

    def tim_chuyen_bay(self, tu: str, den: str, ngay: date, so_ket_qua: int = 3) -> list[ChuyenBay]:
        ra: list[ChuyenBay] = []
        for i in range(so_ket_qua):
            hat = f"{tu}{den}{ngay.isoformat()}{i}"
            ma_hang, ten_hang = _HANG_BAY[i % len(_HANG_BAY)]
            gio = self._so(hat + "h", 6, 21)
            phut = (self._so(hat + "m", 0, 60) // 5) * 5
            khoi = datetime(ngay.year, ngay.month, ngay.day, gio, phut)
            bay_phut = self._so(hat + "d", 70, 135)
            dung = 0 if i < 2 else 1
            ra.append(ChuyenBay(
                ma=f"{ma_hang}{self._so(hat + 'n', 100, 999)}",
                hang=ten_hang, tu=tu, den=den,
                khoi_hanh=khoi,
                ha_canh=khoi + timedelta(minutes=bay_phut + dung * 60),
                gia_vnd=self._so(hat + "g", 890_000, 3_200_000) // 10_000 * 10_000,
                so_diem_dung=dung,
                hoan_duoc=(i == 0),
                nguon=self.ten,
            ))
        ra.sort(key=lambda c: c.gia_vnd)
        return ra

    def tim_khach_san(self, thanh_pho: str, nhan: date, tra: date,
                      so_ket_qua: int = 3) -> list[KhachSan]:
        """Sinh khách sạn mô phỏng NHƯNG ĐẶT ĐÚNG THÀNH PHỐ người dùng hỏi.

        ── VÌ SAO GẮN TOẠ ĐỘ THẬT VÀO DỮ LIỆU BỊA ──
        Tên khách sạn là bịa, và nhãn nói rõ vậy. Nhưng VỊ TRÍ thì lấy toạ độ thật của
        thành phố, nên bản đồ nhúng chỉ đúng khu vực. Nếu để toạ độ bịa luôn thì bản
        đồ thành thứ vô nghĩa — tệ hơn không có bản đồ, vì nó trông như thông tin thật.

        Rải quanh trung tâm bằng chính hàm băm đã dùng cho giá: các ghim không chồng
        lên nhau, mà vẫn TẤT ĐỊNH — cùng câu hỏi luôn ra cùng bản đồ, nên demo lặp
        lại được và không ai nhầm "vị trí đổi" với "mã hỏng"."""
        toa_do = tra_toa_do(thanh_pho)
        lat, lon, ten_chuan = toa_do if toa_do else (0.0, 0.0, thanh_pho)
        co_so_that = tra_khach_san_that(thanh_pho)

        ra: list[KhachSan] = []
        for i in range(so_ket_qua):
            hat = f"{thanh_pho}{nhan.isoformat()}{tra.isoformat()}{i}"
            if i < len(co_so_that):
                # CƠ SỞ CÓ THẬT: tên, sao, vị trí đều thật. Chỉ GIÁ là mô phỏng.
                ten_ks, sao, v_do, k_do = co_so_that[i]
                that = True
                # Giá neo theo hạng sao — 5 sao mà ra 500k thì nhìn là biết số bịa, và
                # một con số vô lý làm người xem nghi ngờ cả những phần đang nói thật.
                day, cao = (2_200_000, 9_000_000) if sao >= 5 else (1_100_000, 3_500_000)
            else:
                # Chưa có dữ liệu thật cho thành phố này → tên mô phỏng quanh trung tâm.
                ten_ks = f"{_TEN_KHACH_SAN[i % len(_TEN_KHACH_SAN)]} {ten_chuan}"
                sao = round(3 + self._so(hat + "s", 0, 20) / 10, 1)
                that = False
                # Lệch tối đa ~1.2km quanh trung tâm (0.011 độ ≈ 1.2km).
                v_do = lat + (self._so(hat + "y", 0, 220) - 110) / 10000
                k_do = lon + (self._so(hat + "x", 0, 220) - 110) / 10000
                day, cao = 450_000, 2_400_000

            ra.append(KhachSan(
                ma=f"KS{self._so(hat + 'k', 1000, 9999)}",
                ten=ten_ks,
                thanh_pho=ten_chuan, nhan_phong=nhan, tra_phong=tra,
                gia_moi_dem_vnd=self._so(hat + "g", day, cao) // 10_000 * 10_000,
                so_sao=float(sao),
                cach_trung_tam_km=round(self._so(hat + "c", 1, 60) / 10, 1),
                huy_mien_phi=(i != 2),
                nguon=self.ten,
                vi_do=round(v_do, 6) if (that or toa_do) else 0.0,
                kinh_do=round(k_do, 6) if (that or toa_do) else 0.0,
                ten_that=that,
            ))
        # Sắp SAO CAO TRƯỚC (rồi giá) — đây là thứ hiện ra đầu tiên khi trình bày, và
        # một danh sách mở đầu bằng nhà nghỉ 3 sao thì không nói lên điều gì.
        ra.sort(key=lambda k: (-k.so_sao, k.gia_moi_dem_vnd))
        return ra


# ── Nhà cung cấp THẬT (Amadeus, môi trường test) ─────────────────────────────

class NhaCungCapAmadeus:
    """Gọi Amadeus Self-Service API (môi trường test — miễn phí, dữ liệu chuyến bay thật).

    CHỈ dùng các endpoint TRA CỨU. Amadeus có endpoint đặt chỗ, và tệp này cố ý KHÔNG
    chạm tới — đặt chỗ là Giai đoạn 3 và phải đi qua cổng xác nhận riêng.
    """

    ten = "amadeus"
    la_that = True
    nhan = "AMADEUS · dữ liệu thật"
    _GOC = "https://test.api.amadeus.com"

    def __init__(self, khoa: str, bi_mat: str):
        self.khoa, self.bi_mat = khoa, bi_mat
        self._token: str | None = None
        self._het_han: datetime = datetime.min

    def _lay_token(self) -> str:
        import httpx
        if self._token and datetime.now() < self._het_han:
            return self._token
        with httpx.Client(timeout=15) as c:
            r = c.post(
                f"{self._GOC}/v1/security/oauth2/token",
                data={"grant_type": "client_credentials",
                      "client_id": self.khoa, "client_secret": self.bi_mat},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            d = r.json()
        self._token = d["access_token"]
        # Trừ hao 60 giây: token hết hạn ĐÚNG lúc đang bay giữa đường thì lời gọi
        # hỏng bằng 401 khó hiểu thay vì tự lấy token mới.
        self._het_han = datetime.now() + timedelta(seconds=int(d.get("expires_in", 1799)) - 60)
        return self._token

    def tim_chuyen_bay(self, tu: str, den: str, ngay: date, so_ket_qua: int = 3) -> list[ChuyenBay]:
        import httpx
        with httpx.Client(timeout=25) as c:
            r = c.get(
                f"{self._GOC}/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {self._lay_token()}"},
                params={
                    "originLocationCode": tu, "destinationLocationCode": den,
                    "departureDate": ngay.isoformat(), "adults": 1,
                    "max": so_ket_qua, "currencyCode": "VND",
                },
            )
            r.raise_for_status()
            data = r.json().get("data", [])

        ra: list[ChuyenBay] = []
        for o in data[:so_ket_qua]:
            seg = o["itineraries"][0]["segments"]
            dau, cuoi = seg[0], seg[-1]
            ra.append(ChuyenBay(
                ma=f"{dau['carrierCode']}{dau['number']}",
                hang=ten_hang(dau["carrierCode"]),
                tu=dau["departure"]["iataCode"], den=cuoi["arrival"]["iataCode"],
                khoi_hanh=datetime.fromisoformat(dau["departure"]["at"]),
                ha_canh=datetime.fromisoformat(cuoi["arrival"]["at"]),
                gia_vnd=int(float(o["price"]["grandTotal"])),
                so_diem_dung=len(seg) - 1,
                # Amadeus không phơi chính sách hoàn ở endpoint tra cứu. KHÔNG ĐOÁN:
                # nói "hoàn được" mà thật ra không hoàn là dẫn người dùng tới một quyết
                # định tiền bạc dựa trên thông tin bịa.
                hoan_duoc=False,
                nguon=self.ten,
                la_that=True,
            ))
        return ra

    def _tra_ma_thanh_pho(self, ten: str) -> str | None:
        """Đổi tên thành phố sang mã IATA ("Hà Nội" → "HAN").

        Bắt người dùng tự biết mã là bắt họ làm việc của máy. Endpoint này cũng dùng
        cho ô gợi ý ở giao diện."""
        import httpx
        with httpx.Client(timeout=20) as c:
            r = c.get(
                f"{self._GOC}/v1/reference-data/locations",
                headers={"Authorization": f"Bearer {self._lay_token()}"},
                params={"keyword": ten, "subType": "CITY", "page[limit]": 1},
            )
            r.raise_for_status()
            d = r.json().get("data") or []
        return d[0].get("iataCode") if d else None

    def tim_khach_san(self, thanh_pho: str, nhan: date, tra: date,
                      so_ket_qua: int = 3) -> list[KhachSan]:
        """Tra cứu khách sạn thật qua Amadeus. Ba bước, vì Amadeus tách chúng ra:
        tên thành phố → mã IATA → danh sách khách sạn → giá theo ngày."""
        import httpx

        ma_tp = self._tra_ma_thanh_pho(thanh_pho)
        if not ma_tp:
            # Không tra ra mã thì DỪNG, không đoán. Đoán nhầm thành phố là trả về
            # khách sạn ở một nơi khác hẳn mà nhìn vẫn hợp lý.
            raise ValueError(f"Không tra được mã thành phố cho '{thanh_pho}'")

        tieu_de = {"Authorization": f"Bearer {self._lay_token()}"}
        with httpx.Client(timeout=30) as c:
            r = c.get(f"{self._GOC}/v1/reference-data/locations/hotels/by-city",
                      headers=tieu_de, params={"cityCode": ma_tp})
            r.raise_for_status()
            ds_ks = (r.json().get("data") or [])[: max(so_ket_qua * 4, 12)]
            if not ds_ks:
                return []

            r = c.get(
                f"{self._GOC}/v3/shopping/hotel-offers",
                headers=tieu_de,
                params={
                    "hotelIds": ",".join(h["hotelId"] for h in ds_ks),
                    "checkInDate": nhan.isoformat(),
                    "checkOutDate": tra.isoformat(),
                    "adults": 1, "currency": "VND", "bestRateOnly": "true",
                },
            )
            r.raise_for_status()
            data = r.json().get("data") or []

        ra: list[KhachSan] = []
        for o in data[:so_ket_qua]:
            ks = o.get("hotel") or {}
            gia_ds = o.get("offers") or []
            if not gia_ds:
                continue
            tong = float((gia_ds[0].get("price") or {}).get("total") or 0)
            so_dem = max(1, (tra - nhan).days)
            chinh_sach = (gia_ds[0].get("policies") or {}).get("cancellations") or []
            ra.append(KhachSan(
                ma=ks.get("hotelId", ""),
                ten=ks.get("name", "(không rõ tên)"),
                thanh_pho=thanh_pho,
                nhan_phong=nhan, tra_phong=tra,
                gia_moi_dem_vnd=int(tong / so_dem),
                # Amadeus KHÔNG trả số sao ở endpoint này. Để 0 và giao diện hiểu là
                # "không có dữ liệu" — bịa một con số cho đẹp là nói dối về chất lượng.
                so_sao=float(ks.get("rating") or 0),
                cach_trung_tam_km=0.0,
                huy_mien_phi=any(
                    str(x.get("type", "")).upper() == "FULL_STAY" or x.get("amount") in (None, "0")
                    for x in chinh_sach
                ),
                nguon=self.ten,
            ))
        return ra


# ── Nhà cung cấp THẬT (AeroDataBox qua RapidAPI) ─────────────────────────────

class NhaCungCapAeroDataBox:
    """Lịch bay THẬT: hãng thật, số hiệu thật, giờ thật, loại máy bay, nhà ga.

    ── VÌ SAO CHỌN NGUỒN NÀY, DÙ NÓ KHÔNG CÓ GIÁ ──
    Amadeus đã đóng đăng ký self-service. Trong các nguồn còn mở, có hai loại:
      (a) API ĐẶT VÉ (Duffel...): có giá, nhưng môi trường thử nghiệm trả chuyến bay
          BỊA — tài liệu của chính họ ghi "you won't see realistic schedules or prices",
          hãng test mang mã ZZ. Người xem tra số hiệu đó sẽ không ra gì.
      (b) API DỮ LIỆU BAY (nguồn này): không có giá, nhưng mọi chuyến đều CÓ THẬT
          và tra lại được từ bên ngoài.
    Chọn (b) vì thứ cần chứng minh ở đây là DỮ LIỆU THẬT, không phải luồng thanh toán —
    mà luồng thanh toán thì nhóm cố ý không làm (cần hợp đồng đại lý + PCI DSS).
    Một bảng giá bịa trông y như thật là thứ nguy hiểm nhất; thà thiếu cột giá.

    ── KHÔNG CÓ GIÁ THÌ LÀM GÌ ──
    `gia_vnd = 0` và `co_gia = False`. Giao diện hiện gạch ngang, kèm nút mở
    Google Flights cho ai cần giá. Bịa một con số cho bảng trông đầy đủ là nói dối
    về tiền — cùng lý do `so_sao=0` ở nhánh Amadeus phía trên.

    ── VÌ SAO PHẢI LỌC THỦ CÔNG ──
    Gói miễn phí không có endpoint tra theo CHẶNG. Chỉ có FIDS (bảng đi/đến của một
    sân bay). Nên ta lấy toàn bộ chuyến đi khỏi sân bay đi, rồi tự lọc theo sân bay
    đến. `withLeg=true` là bắt buộc — thiếu nó thì phản hồi không kèm đầu đến và
    không lọc được gì.
    """

    ten = "aerodatabox"
    la_that = True
    nhan = "LỊCH BAY THẬT · AeroDataBox · không có giá vé"
    _GOC = "https://aerodatabox.p.rapidapi.com"
    _MAY_CHU = "aerodatabox.p.rapidapi.com"

    # API chặn khoảng thời gian quá 12 tiếng, nên một ngày cần HAI lời gọi. Gói miễn
    # phí tính theo lượt nên con số này đáng biết: mỗi lần tìm = 2 lượt.
    _CUA_SO = (("T00:00", "T11:59"), ("T12:00", "T23:59"))

    # ── VÌ SAO PHẢI NGHỈ GIỮA HAI LỜI GỌI ──
    # Gói miễn phí giới hạn 1 REQUEST/GIÂY. Bắn hai cửa sổ liên tiếp thì lời gọi thứ
    # hai dính 429 và cả lượt tìm hỏng — dù hạn mức tháng còn nguyên. Lỗi này KHÔNG
    # xuất hiện khi chạy test (test giả lập httpx, không có đồng hồ thật) và cũng
    # không xuất hiện ở máy dev nếu chỉ thử một lần; nó chỉ lộ ra khi gọi thật.
    _NGHI_GIAY = 1.2          # nhỉnh hơn 1s để trừ hao sai lệch đồng hồ
    _LAN_THU_LAI = 2          # 429 vẫn có thể xảy ra do lượt gọi khác cùng khoá
    _CHO_KHI_429 = 2.5

    def __init__(self, khoa: str):
        self.khoa = khoa

    @staticmethod
    def _doc_gio(muc: dict | None) -> datetime | None:
        """Đọc DateTimeContract {"utc": ..., "local": ...}.

        Dùng giờ ĐỊA PHƯƠNG vì người dùng hỏi "chuyến 6h sáng" theo giờ sân bay, không
        theo UTC. AeroDataBox ngăn cách ngày và giờ bằng DẤU CÁCH ("2026-09-15 06:15+07:00")
        chứ không phải chữ T, nên `fromisoformat` thuần sẽ hỏng — phải đổi trước.
        Cắt tzinfo để đồng nhất với phần còn lại của hệ thống (toàn bộ dùng giờ ngây thơ).
        """
        if not muc:
            return None
        raw = (muc.get("local") or muc.get("utc") or "").strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace(" ", "T", 1)).replace(tzinfo=None)
        except ValueError:
            return None

    def tim_chuyen_bay(self, tu: str, den: str, ngay: date, so_ket_qua: int = 3) -> list[ChuyenBay]:
        import httpx

        tieu_de = {"x-rapidapi-key": self.khoa, "x-rapidapi-host": self._MAY_CHU}
        tham_so = {
            "direction": "Departure",
            "withLeg": "true",          # bắt buộc: thiếu nó thì không biết chuyến bay đi đâu
            "withCancelled": "false",
            "withCodeshared": "false",  # bỏ chuyến bán chung, tránh một chuyến hiện hai lần
            "withCargo": "false",
            "withPrivate": "false",
            "withLocation": "false",
        }

        tho: list[dict] = []
        with httpx.Client(timeout=25) as c:
            for i, (bat_dau, ket_thuc) in enumerate(self._CUA_SO):
                if i:
                    # Giãn cách để không vượt trần 1 request/giây của gói miễn phí.
                    time.sleep(self._NGHI_GIAY)

                duong_dan = (
                    f"{self._GOC}/flights/airports/iata/{tu}"
                    f"/{ngay.isoformat()}{bat_dau}/{ngay.isoformat()}{ket_thuc}"
                )
                for lan in range(self._LAN_THU_LAI):
                    r = c.get(duong_dan, headers=tieu_de, params=tham_so)
                    if r.status_code != 429:
                        break
                    # 429 = chạm trần TỐC ĐỘ, không phải hết hạn mức tháng. Chờ rồi thử
                    # lại thì qua. Ném lỗi ngay sẽ làm hỏng cả lượt tìm vì một giới hạn
                    # chỉ kéo dài một giây.
                    if lan < self._LAN_THU_LAI - 1:
                        time.sleep(self._CHO_KHI_429)

                if r.status_code == 429:
                    # Vẫn 429 sau khi thử lại: nói RÕ là chạm trần và cách xử lý, thay vì
                    # ném nguyên HTTPStatusError dài dòng mà người dùng không làm gì được.
                    raise RuntimeError(
                        "AeroDataBox đang chặn vì vượt giới hạn tốc độ (gói miễn phí cho "
                        "1 lượt/giây). Chờ vài giây rồi tìm lại."
                    )
                # 204 = sân bay không có chuyến nào trong khung giờ đó. Đó là CÂU TRẢ LỜI
                # hợp lệ, không phải lỗi — ném lỗi ở đây là báo hỏng cho một chuyến bay
                # đêm không tồn tại.
                if r.status_code == 204:
                    continue
                r.raise_for_status()
                tho.extend((r.json() or {}).get("departures") or [])

        ra: list[ChuyenBay] = []
        for o in tho:
            # ── KHÔNG LỌC BỚT CHO ĐẸP MẮT ──
            # Dữ liệu thật có mục lạ: đo được chặng SGN-DAD trả về "9G956 / 9G Rail",
            # nghe như tuyến nối bằng đường sắt dù nhà cung cấp vẫn gán loại máy bay.
            # ĐÃ CÂN NHẮC rồi bỏ phương án lọc theo tên ("Rail"/"Bus"): lọc theo chuỗi
            # là cách mong manh, bỏ nhầm một hãng thật thì người dùng mất chuyến bay
            # có thật mà không hề biết — hỏng âm thầm, tệ hơn hiện thừa một dòng lạ.
            # Ở đây hiện ĐÚNG thứ nhà cung cấp trả về, nhất quán với nguyên tắc của cả
            # tệp này: không chỉnh dữ liệu cho vừa mắt.
            di = o.get("departure") or o.get("movement") or {}
            toi = o.get("arrival") or {}
            if ((toi.get("airport") or {}).get("iata") or "").upper() != den.upper():
                continue

            gio_di = self._doc_gio(di.get("scheduledTime") or di.get("revisedTime"))
            gio_den = self._doc_gio(toi.get("scheduledTime") or toi.get("revisedTime"))
            if not gio_di or not gio_den:
                # Thiếu giờ thì BỎ chuyến đó, không đoán. Một dòng có giờ sai còn tệ hơn
                # một dòng vắng mặt: người dùng ra sân bay theo giờ sai.
                continue

            hang = o.get("airline") or {}
            so_hieu = (o.get("number") or "").replace(" ", "")
            # ── ƯU TIÊN BẢNG TÊN CỦA MÌNH, KHÔNG PHẢI TÊN CỦA NHÀ CUNG CẤP ──
            # Đo trên dữ liệu thật: AeroDataBox trả "Vietnam" cho VN và "VietJetAir"
            # cho VJ — viết tắt và sai chính tả thương hiệu. Bảng TEN_HANG phủ đủ các
            # hãng nội địa nên dùng nó trước; hãng lạ mới lấy tên nhà cung cấp; không
            # có gì thì giữ mã. Thứ tự này để không bao giờ hiện tên trống.
            ma_hang = (hang.get("iata") or "").upper()
            ra.append(ChuyenBay(
                ma=so_hieu,
                hang=TEN_HANG.get(ma_hang) or hang.get("name") or ma_hang,
                tu=tu.upper(), den=den.upper(),
                khoi_hanh=gio_di, ha_canh=gio_den,
                gia_vnd=0,          # nguồn này KHÔNG bán vé — xem chú thích đầu lớp
                so_diem_dung=0,     # FIDS chỉ trả chặng thẳng
                hoan_duoc=False,    # không có dữ liệu chính sách vé -> không khẳng định
                nguon=self.ten,
                may_bay=(o.get("aircraft") or {}).get("model") or "",
                nha_ga=di.get("terminal") or "",
                trang_thai=o.get("status") or "",
                la_that=True,
            ))

        ra.sort(key=lambda c: c.khoi_hanh)   # không có giá để sắp, nên sắp theo giờ bay
        return ra[:so_ket_qua]

    def tim_khach_san(self, thanh_pho: str, nhan: date, tra: date,
                      so_ket_qua: int = 3) -> list[KhachSan]:
        """Nguồn này CHỈ có dữ liệu hàng không.

        Ném lỗi rõ ràng thay vì trả danh sách rỗng: rỗng bị đọc thành "hết phòng", còn
        đây là "nguồn không có loại dữ liệu này". Tầng HTTP bắt lỗi này rồi lui về nguồn
        mô phỏng CÙNG VỚI nhãn mô phỏng — nên khách sạn không bao giờ bị dán nhãn thật.
        """
        raise NotImplementedError(
            "AeroDataBox chỉ cung cấp dữ liệu chuyến bay, không có khách sạn."
        )


# ── Chọn nhà cung cấp ────────────────────────────────────────────────────────

def lay_nha_cung_cap():
    """Chọn nguồn theo khoá đang có, ưu tiên nguồn THẬT.

    Thứ tự: Amadeus (thật, có giá) → AeroDataBox (thật, không giá) → mô phỏng.
    Amadeus đứng trước vì nếu có cả hai khoá thì nguồn có giá là nguồn đầy đủ hơn.
    Trên thực tế Amadeus đã đóng đăng ký self-service nên nhánh đó gần như không chạy
    nữa, nhưng giữ lại: xoá đi thì ai đã có khoá cũ sẽ mất tính năng mà không hiểu vì sao.

    Mặc định về mô phỏng chứ không báo lỗi: thiếu khoá là trạng thái BÌNH THƯỜNG khi
    trình bày hay khi chạy test, và bắt cả tính năng chết vì thiếu một khoá không bắt
    buộc là tự làm khó mình.
    """
    khoa = getattr(settings, "amadeus_key", "")
    bi_mat = getattr(settings, "amadeus_secret", "")
    if khoa and bi_mat:
        return NhaCungCapAmadeus(khoa, bi_mat)

    adb = getattr(settings, "aerodatabox_key", "")
    if adb:
        return NhaCungCapAeroDataBox(adb)

    return NhaCungCapMoPhong()
