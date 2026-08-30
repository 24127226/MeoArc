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
    """
    return "https://www.google.com/search?q=" + quote_plus(
        f"{so_hieu} {ngay.strftime('%d/%m/%Y')}"
    )


def lien_ket_ban_do(ten: str, thanh_pho: str) -> str:
    """Mở khách sạn trên Google Maps. Dùng dạng `search` — không cần khoá API."""
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

    def to_dict(self) -> dict:
        so_dem = max(1, (self.tra_phong - self.nhan_phong).days)
        return {
            "ma": self.ma, "ten": self.ten, "thanh_pho": self.thanh_pho,
            "nhan_phong": self.nhan_phong.strftime("%d/%m/%Y"),
            "tra_phong": self.tra_phong.strftime("%d/%m/%Y"),
            "so_dem": so_dem,
            "gia_moi_dem_vnd": self.gia_moi_dem_vnd,
            "tong_vnd": self.gia_moi_dem_vnd * so_dem,
            "so_sao": self.so_sao, "cach_trung_tam_km": self.cach_trung_tam_km,
            "huy_mien_phi": self.huy_mien_phi, "nguon": self.nguon,
            "lien_ket": lien_ket_ban_do(self.ten, self.thanh_pho),
        }


# ── Nhà cung cấp MÔ PHỎNG ────────────────────────────────────────────────────

_HANG_BAY = [("VN", "Vietnam Airlines"), ("VJ", "Vietjet Air"), ("QH", "Bamboo Airways")]
_TEN_KHACH_SAN = ["Riverside", "Central Plaza", "Bay View", "Old Quarter Inn", "Sunrise"]


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
        ra: list[KhachSan] = []
        for i in range(so_ket_qua):
            hat = f"{thanh_pho}{nhan.isoformat()}{tra.isoformat()}{i}"
            ra.append(KhachSan(
                ma=f"KS{self._so(hat + 'k', 1000, 9999)}",
                ten=f"{_TEN_KHACH_SAN[i % len(_TEN_KHACH_SAN)]} {thanh_pho}",
                thanh_pho=thanh_pho, nhan_phong=nhan, tra_phong=tra,
                gia_moi_dem_vnd=self._so(hat + "g", 450_000, 2_400_000) // 10_000 * 10_000,
                so_sao=round(3 + self._so(hat + "s", 0, 20) / 10, 1),
                cach_trung_tam_km=round(self._so(hat + "c", 1, 60) / 10, 1),
                huy_mien_phi=(i != 2),
                nguon=self.ten,
            ))
        ra.sort(key=lambda k: k.gia_moi_dem_vnd)
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
            ra.append(ChuyenBay(
                ma=so_hieu,
                hang=hang.get("name") or ten_hang(hang.get("iata") or ""),
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
