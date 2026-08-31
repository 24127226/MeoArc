# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/cong_tien.py — CỔNG TIỀN (Giai đoạn 3)                ║
# ╚══════════════════════════════════════════════════════════════════╝
"""Chỗ duy nhất trong MeoArc được phép thực thi một việc TIÊU TIỀN.

Đây là phần đáng giá nhất của cả lộ trình về mặt kỹ thuật, vì nó trả lời câu hỏi thật:
**làm sao để một mô hình ngôn ngữ không tự ý tiêu tiền của bạn.**

── BỐN LỚP, MỖI LỚP CHẶN MỘT KIỂU HỎNG KHÁC NHAU ──

1. HAI CHÌA KHOÁ. Agent chỉ tạo được DỰ ĐỊNH; thực thi cần `nguoi_duyet` không rỗng.
   Chặn: mô hình hiểu sai ý rồi tự đặt.

2. KHOÁ CHỐNG TRÙNG, ràng buộc UNIQUE ở tầng CSDL. Chặn: bấm hai lần, mạng đứt rồi thử
   lại, hai tab cùng mở. Kiểm bằng SELECT rồi INSERT là kinh điển của lỗi đua — hai
   yêu cầu vào cùng lúc thì cả hai đều thấy "chưa có".

3. GHI NHẬT KÝ TRƯỚC KHI GỌI RA NGOÀI. Chặn: tiến trình chết giữa lúc gọi API để lại
   khoảng mù — tiền đã đi mà không có bản ghi nào, và lần chạy lại đặt lần thứ hai.

4. TRẦN CHI TIÊU mỗi lần và mỗi ngày. Chặn: một vòng lặp hỏng hoặc một câu hiểu sai
   biến thành mười vé. Trần là thứ duy nhất chặn được lỗi mà ta CHƯA nghĩ ra.

── ĐIỀU TỆ NHẤT CÓ THỂ XẢY RA, VÀ TA CHỌN GÌ ──
Không có thiết kế nào loại bỏ hoàn toàn rủi ro tiến trình chết đúng lúc nhà cung cấp
đã nhận lệnh. Chọn ở đây là: thà để một đơn KẸT ở `dang_xu_ly` cho người xử tay, còn
hơn tự động thử lại và mua hai vé. Máy không được tự quyết ở trạng thái đó.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.dat_cho import DANG_XU_LY, THANH_CONG, THAT_BAI, DonDatCho

# Trần chi tiêu. Con số cố ý THẤP: đây là đồ án, và một trần rộng tay thì không chặn
# được gì trong đúng tình huống nó sinh ra để chặn.
TRAN_MOI_LAN_VND = 5_000_000
TRAN_MOI_NGAY_VND = 10_000_000


class CongTienTuChoi(Exception):
    """Cổng từ chối thực thi. Mang theo lý do để hiện thẳng cho người dùng."""


def khoa_chong_trung(user_id: int, loai: str, chi_tiet: dict) -> str:
    """Sinh khoá từ NỘI DUNG đơn, không phải từ thời điểm.

    Sinh từ thời điểm hay số ngẫu nhiên thì bấm hai lần cách nhau một giây ra hai khoá
    khác nhau, và ràng buộc UNIQUE thành vô nghĩa — đúng thứ nó sinh ra để chặn.

    Sắp xếp khoá trước khi băm: cùng một đơn mà thứ tự trường khác nhau phải ra cùng
    một khoá, nếu không thì hai lần gửi cùng nội dung lại lọt qua.
    """
    phan = "|".join(f"{k}={chi_tiet[k]}" for k in sorted(chi_tiet))
    return hashlib.sha256(f"{user_id}|{loai}|{phan}".encode("utf-8")).hexdigest()[:48]


def _da_tieu_hom_nay(db: Session, user_id: int) -> int:
    """Tổng tiền đã đặt THÀNH CÔNG trong 24 giờ qua."""
    tu = datetime.now(timezone.utc) - timedelta(days=1)
    tong = (
        db.query(func.coalesce(func.sum(DonDatCho.so_tien_vnd), 0))
        .filter(
            DonDatCho.user_id == user_id,
            DonDatCho.trang_thai == THANH_CONG,
            DonDatCho.created_at >= tu,
        )
        .scalar()
    )
    return int(tong or 0)


def kiem_tra_tran(db: Session, user_id: int, so_tien: int) -> None:
    """Ném `CongTienTuChoi` nếu vượt trần. Gọi TRƯỚC khi tạo đơn."""
    if so_tien <= 0:
        raise CongTienTuChoi("Số tiền phải lớn hơn 0.")
    if so_tien > TRAN_MOI_LAN_VND:
        raise CongTienTuChoi(
            f"Đơn {so_tien:,} đ vượt trần mỗi lần ({TRAN_MOI_LAN_VND:,} đ). "
            "Việc này phải đặt tay, MeoArc không tự làm."
        )
    da = _da_tieu_hom_nay(db, user_id)
    if da + so_tien > TRAN_MOI_NGAY_VND:
        raise CongTienTuChoi(
            f"Hôm nay đã đặt {da:,} đ; thêm {so_tien:,} đ nữa là vượt trần ngày "
            f"({TRAN_MOI_NGAY_VND:,} đ)."
        )


def tao_du_dinh(
    db: Session, *, user_id: int, loai: str, mo_ta: str,
    so_tien_vnd: int, chi_tiet: dict,
) -> DonDatCho:
    """Ghi DỰ ĐỊNH đặt chỗ. CHƯA gọi ra ngoài, CHƯA tiêu đồng nào.

    Đơn đã tồn tại (cùng khoá) thì TRẢ LẠI đơn cũ chứ không tạo mới — đó chính là cơ chế
    chống trùng, và nó phải hoạt động cả khi hai yêu cầu vào đúng cùng lúc.
    """
    kiem_tra_tran(db, user_id, so_tien_vnd)
    khoa = khoa_chong_trung(user_id, loai, chi_tiet)

    cu = db.query(DonDatCho).filter(DonDatCho.khoa_chong_trung == khoa).one_or_none()
    if cu:
        return cu

    don = DonDatCho(
        user_id=user_id, khoa_chong_trung=khoa, loai=loai, mo_ta=mo_ta,
        so_tien_vnd=so_tien_vnd, trang_thai=DANG_XU_LY, chi_tiet=chi_tiet,
    )
    db.add(don)
    try:
        db.commit()
    except IntegrityError:
        # Một yêu cầu khác vừa chèn cùng khoá giữa lúc ta kiểm và ta chèn. Đây KHÔNG
        # phải lỗi — đây đúng là lúc ràng buộc UNIQUE làm việc của nó. Lùi lại và
        # dùng đơn của yêu cầu kia.
        db.rollback()
        return db.query(DonDatCho).filter(DonDatCho.khoa_chong_trung == khoa).one()
    db.refresh(don)
    return don


def thuc_thi(
    db: Session, *, don: DonDatCho, nguoi_duyet: str, chay,
) -> DonDatCho:
    """Thực thi đơn ĐÃ ĐƯỢC DUYỆT. `chay()` là hàm gọi ra nhà cung cấp.

    Thứ tự ở đây quan trọng hơn nội dung:
      1. chặn nếu chưa có người duyệt
      2. chặn nếu đơn đã xong (chống trùng ở tầng thực thi)
      3. GHI NHẬT KÝ trước khi gọi
      4. gọi
      5. ghi nhật ký kết quả
    """
    if not nguoi_duyet:
        raise CongTienTuChoi("Đơn chưa có người duyệt. MeoArc không tự thực thi.")

    if don.trang_thai == THANH_CONG:
        # Đã đặt rồi thì trả lại kết quả cũ, KHÔNG đặt lần nữa. Đây là lớp chống trùng
        # thứ hai: khoá UNIQUE chặn tạo đơn trùng, nhánh này chặn thực thi trùng trên
        # cùng một đơn.
        return don

    _ghi_nhat_ky(db, don, "dat_cho_bat_dau", "success",
                 {"so_tien_vnd": don.so_tien_vnd, "nguoi_duyet": nguoi_duyet})

    try:
        ket_qua = chay()
    except Exception as e:
        don.trang_thai = THAT_BAI
        don.ket_qua = {"loi": str(e)[:500]}
        db.commit()
        _ghi_nhat_ky(db, don, "dat_cho_that_bai", "failed", {"loi": str(e)[:200]})
        raise

    don.trang_thai = THANH_CONG
    don.ket_qua = ket_qua
    don.nguoi_duyet = nguoi_duyet
    db.commit()
    db.refresh(don)
    _ghi_nhat_ky(db, don, "dat_cho_thanh_cong", "success", {"ket_qua": ket_qua})
    return don


def _ghi_nhat_ky(db: Session, don: DonDatCho, hanh_dong: str,
                 trang_thai: str, them: dict) -> None:
    """Ghi vào `audit_logs`. Nuốt lỗi có chủ ý: nhật ký hỏng KHÔNG được làm hỏng chính
    giao dịch — mất một dòng log tệ hơn nhiều nếu nó kéo theo mất cả đơn."""
    try:
        db.add(AuditLog(
            user_id=don.user_id, action=hanh_dong, tool_name="dat_cho",
            actor_type="agent", affected_email_ids=[], status=trang_thai,
            details={"don_id": don.id, "khoa": don.khoa_chong_trung,
                     "mo_ta": don.mo_ta, **them},
        ))
        db.commit()
    except Exception:
        db.rollback()
