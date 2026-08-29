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
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.core.config import settings


# ── Kiểu dữ liệu ─────────────────────────────────────────────────────────────

@dataclass
class ChuyenBay:
    ma: str
    hang: str
    tu: str
    den: str
    khoi_hanh: datetime
    ha_canh: datetime
    gia_vnd: int
    so_diem_dung: int
    hoan_duoc: bool
    nguon: str

    def to_dict(self) -> dict:
        return {
            "ma": self.ma, "hang": self.hang, "tu": self.tu, "den": self.den,
            "khoi_hanh": self.khoi_hanh.strftime("%d/%m/%Y %H:%M"),
            "ha_canh": self.ha_canh.strftime("%d/%m/%Y %H:%M"),
            "gia_vnd": self.gia_vnd, "so_diem_dung": self.so_diem_dung,
            "hoan_duoc": self.hoan_duoc, "nguon": self.nguon,
        }


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

    ten = "mo_phong"

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
                hang=dau["carrierCode"],
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
            ))
        return ra

    def tim_khach_san(self, thanh_pho: str, nhan: date, tra: date,
                      so_ket_qua: int = 3) -> list[KhachSan]:
        # Endpoint khách sạn của Amadeus cần thêm bước tra mã thành phố và có hạn mức
        # riêng. Chưa làm — trả rỗng và nói thẳng, hơn là lặng lẽ đưa số mô phỏng ra
        # dưới nhãn "amadeus".
        raise NotImplementedError(
            "Tra cứu khách sạn qua Amadeus chưa nối. Dùng nhà cung cấp mô phỏng."
        )


# ── Chọn nhà cung cấp ────────────────────────────────────────────────────────

def lay_nha_cung_cap():
    """Có khoá Amadeus thì dùng thật, không thì mô phỏng.

    Mặc định về mô phỏng chứ không báo lỗi: thiếu khoá là trạng thái BÌNH THƯỜNG khi
    trình bày hay khi chạy test, và bắt cả tính năng chết vì thiếu một khoá không bắt
    buộc là tự làm khó mình.
    """
    khoa = getattr(settings, "amadeus_key", "")
    bi_mat = getattr(settings, "amadeus_secret", "")
    if khoa and bi_mat:
        return NhaCungCapAmadeus(khoa, bi_mat)
    return NhaCungCapMoPhong()

