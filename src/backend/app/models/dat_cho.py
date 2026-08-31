# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/dat_cho.py — BẢNG 'don_dat_cho' (Giai đoạn 3)           ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Mỗi lần định đặt vé/phòng là MỘT dòng ở đây, ghi TRƯỚC khi gọi ra   ║
# ║ ngoài. Cột `khoa_chong_trung` là ràng buộc DUY NHẤT ở tầng CSDL —   ║
# ║ đó là thứ khiến bấm hai lần, mạng đứt giữa chừng, hay thử lại vẫn   ║
# ║ chỉ ra MỘT đơn.                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Đơn đặt chỗ — bản ghi để chống trùng và để truy vết.

── VÌ SAO GHI TRƯỚC KHI LÀM ──
Nếu chỉ ghi sau khi nhà cung cấp trả về thành công, thì tiến trình chết giữa lúc gọi API
sẽ để lại một khoảng mù: tiền có thể đã đi mà hệ thống không có bản ghi nào. Lần chạy
lại sẽ đặt lần thứ hai.

Ghi TRƯỚC với trạng thái `dang_xu_ly` thì lần chạy lại nhìn thấy bản ghi đó và dừng lại
hỏi, thay vì đặt tiếp. Thà kẹt một đơn phải xử tay còn hơn hai vé đã trả tiền.

── VÌ SAO RÀNG BUỘC Ở TẦNG CSDL, KHÔNG PHẢI Ở TẦNG MÃ ──
Kiểm "đã có đơn này chưa" bằng một câu SELECT rồi mới INSERT là kinh điển của lỗi đua:
hai yêu cầu vào cùng lúc thì cả hai đều thấy "chưa có". Chỉ ràng buộc UNIQUE của CSDL
mới cắt được, vì nó là điểm tuần tự hoá duy nhất.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Trạng thái đơn. `dang_xu_ly` là trạng thái NGUY HIỂM: đã ghi nhận ý định nhưng chưa
# biết nhà cung cấp đã nhận hay chưa. Đơn kẹt ở đây phải do người xử, không được để
# máy tự quyết.
DANG_XU_LY = "dang_xu_ly"
THANH_CONG = "thanh_cong"
THAT_BAI = "that_bai"


class DonDatCho(Base):
    __tablename__ = "don_dat_cho"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # KHOÁ CHỐNG TRÙNG — ràng buộc UNIQUE ở tầng CSDL.
    #
    # Sinh từ NỘI DUNG đơn (ai, loại gì, chặng nào, ngày nào, mã lựa chọn nào), không
    # phải từ thời điểm hay số ngẫu nhiên. Sinh từ thời điểm thì bấm hai lần cách nhau
    # một giây ra hai khoá khác nhau và ràng buộc này thành vô nghĩa.
    khoa_chong_trung: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    loai: Mapped[str] = mapped_column(String(16))          # 'chuyen_bay' | 'khach_san'
    mo_ta: Mapped[str] = mapped_column(String)             # câu người đọc hiểu
    so_tien_vnd: Mapped[int] = mapped_column(Integer, default=0)
    trang_thai: Mapped[str] = mapped_column(String(16), default=DANG_XU_LY, index=True)

    # Toàn bộ tham số đã gửi đi và kết quả nhận về — để đối chiếu khi có tranh chấp.
    chi_tiet: Mapped[dict] = mapped_column(JSON, default=dict)
    ket_qua: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Ai đã duyệt. Rỗng nghĩa là CHƯA AI DUYỆT — và khi đó không được phép thực thi.
    nguoi_duyet: Mapped[str] = mapped_column(String, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
