# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/cam_ket.py — TRÍCH CAM KẾT TỪ THƯ (bản backend)           ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Đọc thư ra danh sách VIỆC PHẢI LÀM, cho agent dùng được.

── VÌ SAO PHẢI CÓ Ở BACKEND ──
Bộ trích này vốn CHỈ tồn tại ở `src/frontend/src/lib/cam-ket.ts`, chạy trong trình
duyệt. Nghĩa là agent hoàn toàn MÙ trước lịch trình: hỏi "tuần sau deadline nào nặng
nhất" thì nó chỉ có thể đọc lại thư từ đầu và đoán. Đo thật ngày 29/08/2026: grep cả
`app/tools/` ra 0 công cụ nào liên quan cam kết.

Đó là một nghịch lý đáng nói: phần đặc sắc nhất của MeoArc — biến hộp thư thành lịch
trình — lại là phần AI không chạm tới được.

── VÌ SAO LÀM BẰNG LUẬT, KHÔNG GỌI MÔ HÌNH ──
Trích cam kết phải chạy trên MỌI thư, không chỉ khi người dùng hỏi. Gọi mô hình cho
mọi thư thì hạn mức cạn trong vài giờ — mà hạn mức Gemini free chỉ có 20 lượt/ngày cho
model chính (đã đo). Lọc bằng luật rẻ tiền trước, phần khó mới đưa cho mô hình.

── GIỚI HẠN, NÓI THẲNG ──
Bộ luật này KHÔNG hiểu ngôn ngữ. Nó đọc được "trước 23:59 ngày 30/8" và "hạn chót thứ
Sáu", nhưng bó tay với "nộp sau khi thầy duyệt đề cương". Mọi cam kết vì thế mang
`do_tin_cay`, và dưới ngưỡng thì giao diện phải HỎI chứ không tự khẳng định — một hạn
nộp bị đọc sai ngày còn tệ hơn hẳn không có hạn nào.

── GIỮ ĐỒNG BỘ VỚI BẢN TS ──
Hai bản tồn tại vì hai đích: bản TS chạy ở chế độ mock (không có backend), bản này là
NGUỒN SỰ THẬT cho agent và cho bản chạy thật. Chống lệch bằng bộ ca kiểm thử dùng
CHUNG: `src/shared/ca-cam-ket.json` — cả hai bản đều phải chạy qua nó.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

# ── Nhận diện ────────────────────────────────────────────────────────────────

# Động từ báo hiệu một NGHĨA VỤ. Chỉ có ngày tháng thì chưa đủ: "hẹn gặp lại bạn
# tháng sau" có ngày nhưng không phải việc phải làm.
DONG_TU_CAM_KET = re.compile(
    r"(nộp|gửi|hoàn thành|hoàn tất|phản hồi|trả lời|xác nhận|đăng ký|thanh toán"
    r"|đóng|bảo vệ|trình bày|báo cáo|deadline|hạn chót|hạn cuối|due)",
    re.IGNORECASE,
)

DAU_HIEU_THOI_GIAN = re.compile(
    r"(\d{1,2}\s*[/-]\s*\d{1,2}(\s*[/-]\s*\d{2,4})?"
    r"|\d{1,2}\s*(giờ|h|:)\s*\d{0,2}"
    r"|ngày\s+\d{1,2}"
    r"|thứ\s*(hai|ba|tư|năm|sáu|bảy)|chủ\s*nhật"
    r"|hôm\s*nay|ngày\s*mai|tuần\s*(này|sau|tới)"
    r"|trong\s+vòng\s+\d+\s*ngày)",
    re.IGNORECASE,
)

NGAY_TUYET_DOI = re.compile(
    r"(\d{1,2})\s*[/-]\s*(\d{1,2})(?:\s*[/-]\s*(\d{2,4}))?"
    r"(?:[^\d]{0,12}?(\d{1,2})\s*[:h]\s*(\d{2})?)?"
)

TRONG_VONG = re.compile(r"trong\s+vòng\s+(\d+)\s*ngày(\s*làm\s*việc)?", re.IGNORECASE)

# Khoảng ngày NÓI THẲNG: "từ ngày 7/9 đến ngày 25/9". Đây là thứ duy nhất cho ra
# được một đợt kéo dài nhiều tuần — `tinh_bat_dau` suy từ ước lượng thời lượng thì
# nhiều nhất chỉ ra 3 ngày.
KHOANG_NGAY = re.compile(
    r"từ\s+(?:ngày\s+)?(\d{1,2})\s*[/-]\s*(\d{1,2})(?:\s*[/-]\s*(\d{2,4}))?"
    r"\s*(?:đến|tới|-|–)\s*(?:hết\s+)?(?:ngày\s+)?"
    r"(\d{1,2})\s*[/-]\s*(\d{1,2})(?:\s*[/-]\s*(\d{2,4}))?",
    re.IGNORECASE,
)

# Dạng nói PHỔ BIẾN NHẤT trong thư tiếng Việt — "trước 23:59 thứ Sáu tuần này" — và
# cũng là dạng Google Calendar bỏ qua hoàn toàn.
THU_TRONG_TUAN = re.compile(
    r"(thứ\s*(hai|ba|tư|tv|năm|sáu|bảy)|chủ\s*nhật)(\s*(tuần)\s*(này|sau|tới))?",
    re.IGNORECASE,
)
NGAY_TUONG_DOI = re.compile(r"(hôm\s*nay|ngày\s*mai|ngày\s*kia|cuối\s*tuần)", re.IGNORECASE)
GIO_RIENG = re.compile(r"(\d{1,2})\s*(?::|h|giờ)\s*(\d{2})?", re.IGNORECASE)

# Thứ Hai = 0 theo `weekday()` của Python. Bảng này dùng quy ước Chủ nhật = 6 để
# khớp cách nói tiếng Việt ("thứ Hai" là đầu tuần).
_SO_THU = {"hai": 0, "ba": 1, "tư": 2, "tv": 2, "năm": 3, "sáu": 4, "bảy": 5}

TRAN_MOI_NGAY = 6 * 60          # trần một ngày làm việc, tính bằng phút
_GIO_MOI_NGAY_THUC_TE = 180     # trần để suy ngày bắt đầu — thấp hơn trần ngày
TRAN_NGAY_SUY_RA = 14
TRAN_NGAY_RO_RANG = 70


@dataclass
class CamKet:
    id: str
    noi_dung: str
    han: datetime | None
    bat_dau: datetime | None
    han_suy_ra: bool
    trang_thai: str          # 'chua_lam' | 'dang_doi' | 'xong'
    nguoi_cho: str
    email_id: str
    do_tin_cay: float
    uoc_luong_phut: int
    muc_rui_ro: int
    muc_uu_tien: int
    khoang_ro_rang: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "noi_dung": self.noi_dung,
            "han": self.han.isoformat() if self.han else None,
            "bat_dau": self.bat_dau.isoformat() if self.bat_dau else None,
            "han_suy_ra": self.han_suy_ra,
            "trang_thai": self.trang_thai,
            "nguoi_cho": self.nguoi_cho,
            "email_id": self.email_id,
            "do_tin_cay": self.do_tin_cay,
            "uoc_luong_phut": self.uoc_luong_phut,
            "muc_rui_ro": self.muc_rui_ro,
            "muc_uu_tien": self.muc_uu_tien,
            "khoang_ro_rang": self.khoang_ro_rang,
        }


# ── Đọc mốc thời gian ────────────────────────────────────────────────────────

def cong_ngay(tu: datetime, so_ngay: int, chi_ngay_lam_viec: bool) -> datetime:
    """Cộng N ngày, BỎ QUA thứ Bảy và Chủ nhật khi đề bài nói 'ngày làm việc'.
    Đúng loại chi tiết mà một bộ lọc ẩu bỏ qua rồi cho ra hạn sai hai ngày."""
    d = tu
    con = so_ngay
    while con > 0:
        d = d + timedelta(days=1)
        if chi_ngay_lam_viec and d.weekday() >= 5:
            continue
        con -= 1
    return d


def _thu_gan_nhat(moc: datetime, dich: int, tuan_sau: bool) -> datetime:
    """Ngày gần nhất TỪ `moc` trở đi rơi vào thứ `dich` (0 = thứ Hai).
    Trùng chính hôm nay thì vẫn tính hôm nay — 'nộp trước 23:59 thứ Sáu' gửi vào
    sáng thứ Sáu nói về tối HÔM ĐÓ, không phải tuần sau."""
    cach = (dich - moc.weekday() + 7) % 7
    if tuan_sau:
        cach += 7
    return moc + timedelta(days=cach)


def doc_khoang(van: str, moc: datetime | None = None) -> tuple[datetime, datetime] | None:
    """Đọc khoảng ngày nói thẳng: 'từ 7/9 đến 25/9'. Trả None nếu không có."""
    moc = moc or datetime.now()
    m = KHOANG_NGAY.search(van)
    if not m:
        return None

    d1, t1 = int(m.group(1)), int(m.group(2))
    d2, t2 = int(m.group(4)), int(m.group(5))
    if not (1 <= d1 <= 31 and 1 <= t1 <= 12 and 1 <= d2 <= 31 and 1 <= t2 <= 12):
        return None

    def nam(raw: str | None) -> int:
        if not raw:
            return moc.year
        n = int(raw)
        return n + 2000 if n < 100 else n

    try:
        bat_dau = datetime(nam(m.group(3)), t1, d1, 0, 0)
        han = datetime(nam(m.group(6)), t2, d2, 23, 59)
    except ValueError:
        return None   # 31/2 chẳng hạn

    # Mốc cuối trước mốc đầu = đợt vắt qua năm mới ("từ 20/12 đến 5/1"). Không xử
    # lý thì ra khoảng ÂM và mọi phép tính phía sau hỏng lặng lẽ.
    if han < bat_dau:
        han = han.replace(year=han.year + 1)
    return bat_dau, han


def doc_han(van: str, moc: datetime | None = None) -> tuple[datetime, bool] | None:
    """Đọc mốc hạn trong một đoạn văn. Trả (hạn, có_phải_suy_ra) hoặc None."""
    moc = moc or datetime.now()

    tv = TRONG_VONG.search(van)
    if tv:
        return cong_ngay(moc, int(tv.group(1)), bool(tv.group(2))), True

    # Thứ trong tuần / ngày tương đối xét TRƯỚC ngày tuyệt đối: câu như "trước
    # 23:59 thứ Sáu" có số, nhưng số đó là GIỜ chứ không phải ngày tháng.
    gio_m = GIO_RIENG.search(van)
    gio_so = min(23, int(gio_m.group(1))) if gio_m else 23
    phut_so = int(gio_m.group(2)) if (gio_m and gio_m.group(2)) else (0 if gio_m else 59)

    td = NGAY_TUONG_DOI.search(van)
    if td:
        t = re.sub(r"\s+", "", td.group(1)).lower()
        d = moc
        if t.startswith("ngàymai"):
            d = moc + timedelta(days=1)
        elif t.startswith("ngàykia"):
            d = moc + timedelta(days=2)
        elif t.startswith("cuốituần"):
            d = moc + timedelta(days=(5 - moc.weekday()) % 7)
        return d.replace(hour=gio_so, minute=phut_so, second=0, microsecond=0), True

    tt = THU_TRONG_TUAN.search(van)
    if tt:
        ten = (tt.group(2) or "").lower()
        dich = 6 if "chủ" in tt.group(1).lower() else _SO_THU.get(ten, -1)
        if dich >= 0:
            tuan_sau = bool(tt.group(5) and re.search(r"sau|tới", tt.group(5), re.I))
            d = _thu_gan_nhat(moc, dich, tuan_sau)
            # Có giờ rõ ràng thì chắc hơn hẳn — "thứ Sáu" suông vẫn là suy ra.
            return d.replace(hour=gio_so, minute=phut_so, second=0, microsecond=0), not gio_m

    m = NGAY_TUYET_DOI.search(van)
    if m:
        ngay, thang = int(m.group(1)), int(m.group(2))
        if not (1 <= ngay <= 31 and 1 <= thang <= 12):
            return None
        nam = int(m.group(3)) if m.group(3) else moc.year
        if nam < 100:
            nam += 2000

        gio = int(m.group(4)) if m.group(4) else None
        phut = int(m.group(5)) if m.group(5) else (0 if m.group(4) else None)

        # GIỜ CÓ THỂ ĐỨNG TRƯỚC NGÀY. `NGAY_TUYET_DOI` chỉ bắt giờ đi SAU ("16/9
        # lúc 17:00"), trong khi tiếng Việt hay viết ngược — "trước 17:00 ngày
        # 16/9". Thiếu nhánh này thì giờ rơi về 23:59 và giao diện hiện một con số
        # MÂU THUẪN với chính câu chữ bên cạnh. Một hạn sai 7 tiếng tệ hơn hẳn
        # không có hạn: người dùng tin vào nó.
        if gio is None:
            truoc = van[max(0, m.start() - 20):m.start()]
            khop = list(GIO_RIENG.finditer(truoc))
            if khop:
                g = int(khop[-1].group(1))     # lần khớp CUỐI = gần ngày nhất
                if 0 <= g <= 23:
                    gio = g
                    phut = int(khop[-1].group(2)) if khop[-1].group(2) else 0

        if gio is None:
            gio, phut = 23, 59   # cuối ngày hạn: "trước ngày 16/9" thì hết ngày 16 vẫn kịp

        try:
            d = datetime(nam, thang, ngay, gio, phut or 0)
        except ValueError:
            return None
        # Không ghi năm mà ngày đã qua → hiểu là năm sau.
        if not m.group(3) and d < moc - timedelta(days=1):
            d = d.replace(year=nam + 1)
        return d, False

    return None


# ── Ước lượng & xếp hạng ─────────────────────────────────────────────────────

def uoc_luong(body: list[str], priority: str | None) -> int:
    so_chu = len(" ".join(body).strip().split())
    nen = 240 if so_chu > 400 else 120 if so_chu > 220 else 60 if so_chu > 90 else 30
    return nen * 2 if priority == "High" else nen


def tinh_bat_dau(han: datetime, phut: int) -> datetime | None:
    """Ngày nên BẮT ĐẦU, suy từ khối lượng. Chia cho trần THẤP HƠN trần ngày (3 giờ
    thay vì 6): không ai dồn cả ngày cho đúng một việc, và lấy trần thật thì lời
    khuyên 'bắt đầu từ hôm nay' tới muộn một ngày."""
    so_ngay = -(-phut // _GIO_MOI_NGAY_THUC_TE)   # ceil
    if so_ngay <= 1:
        return None
    return (han - timedelta(days=so_ngay - 1)).replace(hour=0, minute=0, second=0, microsecond=0)


def muc_rui_ro(priority: str | None, han: datetime | None, moc: datetime) -> int:
    """'Hỏng thì mất gì'. CỐ Ý giữ cấp 3 cực hiếm — nó dành cho lúc agent thật sự
    tiêu tiền (đặt vé, đặt phòng). Phát sớm thì tới lúc cần nó đã mất sức nặng."""
    if not han:
        return 1
    con_lai = (han - moc).total_seconds()
    if con_lai < 86400 and priority == "High":
        return 2
    if con_lai < 0:
        return 2
    return 1


def muc_uu_tien(priority: str | None, han: datetime | None, moc: datetime) -> int:
    """'Làm cái nào trước' — TRỤC KHÁC hẳn `muc_rui_ro`.

    Thang rủi ro giữ cấp 3 cực hiếm nên gần như mọi việc đều cấp 1 (đo trên bộ demo:
    13/13). Dùng nó để xếp thì mọi việc trông y hệt nhau. Thang này gộp mức ưu tiên
    do AI gán với khoảng cách tới hạn — một việc High còn hai tuần không gấp bằng
    một việc Medium đến hạn ngày mai."""
    if not han:
        return 1
    ngay_con_lai = (han - moc).total_seconds() / 86400
    cao = priority == "High"
    if ngay_con_lai < 0:
        return 3
    if cao and ngay_con_lai <= 3:
        return 3
    if cao or ngay_con_lai <= 2:
        return 2
    return 1


def _khoang_ngay(c: CamKet) -> tuple[datetime, datetime] | None:
    """Khoảng ngày việc thật sự chiếm, đã áp trần theo mức đáng tin."""
    if not c.han:
        return None
    tran = TRAN_NGAY_RO_RANG if c.khoang_ro_rang else TRAN_NGAY_SUY_RA
    cuoi = c.han.replace(hour=0, minute=0, second=0, microsecond=0)
    dau = (c.bat_dau or c.han).replace(hour=0, minute=0, second=0, microsecond=0)
    so_ngay = min(tran, max(1, (cuoi - dau).days + 1))
    return cuoi - timedelta(days=so_ngay - 1), cuoi


def phut_moi_ngay(c: CamKet) -> float:
    """Số phút việc này chiếm TRONG MỘT NGÀY, đã chia đều theo số ngày nó trải qua.
    Cộng thẳng `uoc_luong_phut` cho mọi ngày thì việc 6 tiếng trải 3 ngày thành 18
    tiếng, và ngày nào cũng 'quá tải' — cảnh báo luôn bật thì hết là cảnh báo."""
    k = _khoang_ngay(c)
    if not k:
        return 0.0
    so_ngay = (k[1] - k[0]).days + 1
    return c.uoc_luong_phut / max(1, so_ngay)


# ── Trích ────────────────────────────────────────────────────────────────────

def trich_cam_ket(emails: list, moc: datetime | None = None) -> list[CamKet]:
    """Trích cam kết từ danh sách thư.

    Chỉ nhận thư THẬT SỰ có dấu hiệu nghĩa vụ — cần CẢ động từ cam kết LẪN mốc thời
    gian. Thà bỏ sót còn hơn nhồi rác vào danh sách việc: một danh sách đầy thứ
    không phải việc thì người dùng thôi mở nó, và lúc đó nó vô dụng hoàn toàn.

    `emails` nhận object có thuộc tính hoặc dict — để dùng được cả với schema Email
    của API lẫn dữ liệu thô.
    """
    moc = moc or datetime.now()
    ra: list[CamKet] = []

    for e in emails:
        g = (lambda k, m=e: getattr(m, k, None) if not isinstance(m, dict) else m.get(k))
        subject = g("subject") or ""
        body = g("body") or []
        if isinstance(body, str):
            body = [body]
        folder = g("folder") or "inbox"
        eid = str(g("id") or "")
        sender = g("sender") or "ai đó"
        priority = g("priority")
        status = g("status")
        tldr = g("tldr")

        # Thư ĐÃ GỬI = đang chờ người ta hồi âm. Vẫn là việc phải theo dõi, và là
        # loại hay bị quên nhất. Không cần dấu hiệu ngày giờ.
        if folder == "sent":
            ra.append(CamKet(
                id=f"ck-{eid}", noi_dung=f"Chờ hồi âm: {subject}",
                han=None, bat_dau=None, han_suy_ra=False, trang_thai="dang_doi",
                nguoi_cho=g("to") or "người nhận", email_id=eid,
                do_tin_cay=0.9, uoc_luong_phut=0, muc_rui_ro=1, muc_uu_tien=1,
            ))
            continue

        van = f"{subject} {' '.join(body)}"
        if not DONG_TU_CAM_KET.search(van) or not DAU_HIEU_THOI_GIAN.search(van):
            continue

        # Khoảng nói thẳng ĐƯỢC ƯU TIÊN hơn hạn đơn lẻ: nó cho cả hạn LẪN ngày bắt
        # đầu THẬT, chính xác hơn hẳn ngày bắt đầu suy từ ước lượng thời lượng.
        khoang = doc_khoang(van, moc)
        doc = (khoang[1], False) if khoang else doc_han(van, moc)
        han = doc[0] if doc else None
        suy_ra = doc[1] if doc else False

        # Đọc được hạn tuyệt đối thì chắc; suy ra thì kém chắc hơn; có dấu hiệu mà
        # không đọc nổi mốc thì thấp — và giao diện sẽ HỎI thay vì tự khẳng định.
        do_tin_cay = 0.45 if not doc else (0.7 if suy_ra else 0.88)
        phut = uoc_luong(body, priority)

        ra.append(CamKet(
            id=f"ck-{eid}",
            noi_dung=tldr if (tldr and len(tldr) > 8) else subject,
            han=han,
            bat_dau=khoang[0] if khoang else (tinh_bat_dau(han, phut) if han else None),
            han_suy_ra=suy_ra,
            trang_thai="xong" if status == "Done" else "dang_doi" if status == "Waiting" else "chua_lam",
            nguoi_cho=sender,
            email_id=eid,
            do_tin_cay=do_tin_cay,
            uoc_luong_phut=phut,
            muc_rui_ro=muc_rui_ro(priority, han, moc),
            muc_uu_tien=muc_uu_tien(priority, han, moc),
            khoang_ro_rang=bool(khoang),
        ))

    return ra


def ap_luc_theo_ngay(ds: list[CamKet], so_ngay: int = 7,
                     moc: datetime | None = None) -> list[dict]:
    """Tải mỗi ngày trong `so_ngay` ngày tới.

    Tính theo KHOẢNG LÀM chứ không theo ngày hạn: một việc 8 tiếng hạn thứ Sáu làm
    cho thứ Tư và thứ Năm hiện ra RỖNG nếu chỉ đếm ngày hạn — đúng cái ảo giác mà
    cả tính năng này sinh ra để phá."""
    moc = moc or datetime.now()
    ra = []
    for i in range(so_ngay):
        d = (moc + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        het = d + timedelta(days=1)
        trong = []
        for c in ds:
            if not c.han or c.trang_thai == "xong":
                continue
            k = _khoang_ngay(c)
            if k and k[0] < het and k[1] >= d:
                trong.append(c)
        ra.append({
            "ngay": d.date().isoformat(),
            "phut": round(sum(phut_moi_ngay(c) for c in trong)),
            "so_viec": len(trong),
            "qua_tai": sum(phut_moi_ngay(c) for c in trong) > TRAN_MOI_NGAY,
        })
    return ra


# ══════════════════════════════════════════════════════════════════════════════
# GIAI ĐOẠN 1 — NHẬN RA Ý ĐỊNH ĐI LẠI
#
# Từ cam kết đã trích, nhận ra cái nào NGỤ Ý PHẢI DI CHUYỂN. Chỉ ĐỀ XUẤT, không
# đặt gì cả, không gọi API ngoài nào.
#
# Chỗ dễ sai nhất là nhận nhầm họp trực tuyến thành phải bay. Một đề xuất "cần bay
# đi Đà Nẵng" cho một buổi họp Zoom không chỉ vô ích — nó làm người dùng thôi tin
# vào mọi đề xuất sau đó. Nên danh sách chặn trực tuyến được xét TRƯỚC, và thắng.
# ══════════════════════════════════════════════════════════════════════════════

# Thành phố nhận diện được, kèm mã sân bay để giai đoạn sau tra chuyến bay.
# Cố ý NGẮN: nhận nhầm một địa danh còn tệ hơn bỏ sót nó, vì bỏ sót thì người dùng
# tự làm như cũ, còn nhận nhầm thì họ phải đi sửa hậu quả.
THANH_PHO: dict[str, str] = {
    "hà nội": "HAN", "hanoi": "HAN",
    "đà nẵng": "DAD", "da nang": "DAD",
    "hồ chí minh": "SGN", "tp.hcm": "SGN", "tphcm": "SGN", "sài gòn": "SGN",
    "hải phòng": "HPH", "huế": "HUI", "nha trang": "CXR", "cam ranh": "CXR",
    "đà lạt": "DLI", "cần thơ": "VCA", "phú quốc": "PQC", "quy nhơn": "UIH",
    "vinh": "VII", "buôn ma thuột": "BMV", "pleiku": "PXU", "côn đảo": "VCS",
}

# Dấu hiệu buổi đó diễn ra TRỰC TUYẾN → KHÔNG phải đi đâu cả.
TRUC_TUYEN = re.compile(
    r"(trực\s*tuyến|online|zoom|google\s*meet|ms\s*teams|microsoft\s*teams"
    r"|link\s*họp|đường\s*link|webinar|từ\s*xa|remote)",
    re.IGNORECASE,
)

# Động từ ngụ ý PHẢI CÓ MẶT. Khác hẳn động từ cam kết chung: "nộp báo cáo" thì nộp
# online được, còn "bảo vệ đồ án" thì phải đến.
DONG_TU_CO_MAT = re.compile(
    r"(bảo\s*vệ|trình\s*bày|thuyết\s*trình|tham\s*dự|có\s*mặt|dự\s*(lễ|hội|thi)"
    r"|phỏng\s*vấn|gặp\s*mặt|hội\s*thảo|chung\s*kết|khai\s*mạc|lễ\s*trao)",
    re.IGNORECASE,
)

# Nơi người dùng thường trú — điểm khởi hành mặc định.
NOI_O_MAC_DINH = "SGN"


@dataclass
class YDinhDiLai:
    """Một cam kết ngụ ý phải di chuyển. Đây là ĐỀ XUẤT, chưa phải đặt chỗ."""
    cam_ket_id: str
    email_id: str
    noi_dung: str
    thanh_pho: str
    ma_san_bay: str
    tu_san_bay: str
    han: datetime | None
    #  Đề xuất bay TRƯỚC buổi đó bao lâu, tính bằng ngày.
    nen_den_truoc_ngay: int
    do_tin_cay: float
    ly_do: str = ""

    def to_dict(self) -> dict:
        return {
            "cam_ket_id": self.cam_ket_id,
            "email_id": self.email_id,
            "noi_dung": self.noi_dung,
            "thanh_pho": self.thanh_pho,
            "ma_san_bay": self.ma_san_bay,
            "tu_san_bay": self.tu_san_bay,
            "han": self.han.strftime("%d/%m/%Y %H:%M") if self.han else None,
            "nen_den_truoc_ngay": self.nen_den_truoc_ngay,
            "do_tin_cay": round(self.do_tin_cay, 2),
            "ly_do": self.ly_do,
        }


def doc_thanh_pho(van: str, tru_ma: str = NOI_O_MAC_DINH) -> tuple[str, str] | None:
    """Tìm thành phố ĐÍCH trong đoạn văn. Trả (tên, mã sân bay) hoặc None.

    Bỏ qua thành phố trùng với nơi ở: một buổi họp "tại TP.HCM" với người đang ở
    TP.HCM thì không phải chuyến đi."""
    thap = van.lower()
    tim_thay: list[tuple[int, str, str]] = []
    for ten, ma in THANH_PHO.items():
        vi_tri = thap.find(ten)
        if vi_tri >= 0 and ma != tru_ma:
            tim_thay.append((vi_tri, ten, ma))
    if not tim_thay:
        return None
    # Lấy cái xuất hiện SỚM NHẤT: thư thường nêu nơi diễn ra trước, rồi mới nhắc
    # các địa danh phụ (nơi gửi, chi nhánh…) ở phần cuối.
    tim_thay.sort()
    _, ten, ma = tim_thay[0]
    return ten, ma


def suy_y_dinh_di_lai(
    ds: list[CamKet],
    van_theo_email: dict[str, str],
    tu_san_bay: str = NOI_O_MAC_DINH,
) -> list[YDinhDiLai]:
    """Lọc ra những cam kết ngụ ý phải di chuyển.

    `van_theo_email` là bản đồ email_id → toàn văn thư, vì `CamKet` chỉ giữ một câu
    tóm tắt còn địa điểm thường nằm trong thân thư.

    BỐN điều kiện, thiếu một là bỏ:
      1. có hạn (không biết ngày thì không đề xuất chuyến bay được)
      2. có thành phố đích khác nơi ở
      3. KHÔNG có dấu hiệu trực tuyến
      4. có động từ ngụ ý phải có mặt
    """
    ra: list[YDinhDiLai] = []
    for c in ds:
        if not c.han or c.trang_thai == "xong":
            continue
        van = van_theo_email.get(c.email_id, "") or c.noi_dung

        # Xét TRỰC TUYẾN trước và cho nó thắng. Nhận nhầm một buổi Zoom thành chuyến
        # bay không chỉ vô ích — nó làm người dùng thôi tin vào mọi đề xuất sau đó.
        if TRUC_TUYEN.search(van):
            continue
        if not DONG_TU_CO_MAT.search(van):
            continue
        tp = doc_thanh_pho(van, tu_san_bay)
        if not tp:
            continue

        ten, ma = tp
        # Buổi sáng (trước 12h) thì nên tới từ hôm trước — bay sáng cùng ngày là
        # đặt cược vào việc không có chuyến nào trễ.
        truoc = 1 if c.han.hour < 12 else 0
        ra.append(YDinhDiLai(
            cam_ket_id=c.id, email_id=c.email_id, noi_dung=c.noi_dung,
            thanh_pho=ten.title(), ma_san_bay=ma, tu_san_bay=tu_san_bay,
            han=c.han, nen_den_truoc_ngay=truoc,
            # Độ tin cậy KHÔNG BAO GIỜ cao hơn độ tin cậy của chính cái hạn: suy ra
            # một chuyến bay từ một cái hạn đoán mò thì cả hai đều đoán mò.
            do_tin_cay=min(c.do_tin_cay, 0.85),
            ly_do=f"{'Buổi sáng' if truoc else 'Buổi chiều'} tại {ten.title()}",
        ))
    return ra
