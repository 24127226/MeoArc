"""Giai đoạn 3 — CỔNG TIỀN. Phần đáng giá nhất, và phần phải khắt khe nhất.

Câu hỏi thật mà tầng này trả lời: **làm sao để một mô hình ngôn ngữ không tự ý tiêu tiền
của bạn.** Mọi phép kiểm ở đây mô phỏng một kiểu hỏng CỤ THỂ đã từng xảy ra với các hệ
thống thanh toán thật: bấm hai lần, mạng đứt giữa chừng, hai tab cùng mở, tiến trình chết
đúng lúc gọi API, và một vòng lặp hỏng biến thành mười đơn.
"""

from __future__ import annotations

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.audit import AuditLog
from app.models.dat_cho import DANG_XU_LY, THANH_CONG, THAT_BAI, DonDatCho
from app.models.user import User
from app.services import cong_tien as ct


@pytest.fixture
def db():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng)()
    s.add(User(id=1, email="a@b.c", name="A", initial="A"))
    s.commit()
    yield s
    s.close()


CHI_TIET = {"tu": "SGN", "den": "DAD", "ngay": "16/09/2026", "ma": "VN123"}


def _tao(db, tien=1_500_000, chi_tiet=None):
    return ct.tao_du_dinh(
        db, user_id=1, loai="chuyen_bay", mo_ta="SGN→DAD 16/09",
        so_tien_vnd=tien, chi_tiet=chi_tiet or CHI_TIET,
    )


def _no(msg):
    """Hàm `chay` luôn ném lỗi — viết thành hàm cho dễ đọc hơn lambda-throw."""
    def f():
        raise RuntimeError(msg)
    return f


# ── LỚP 1: HAI CHÌA KHOÁ ─────────────────────────────────────────────────────

def test_KHONG_duyet_thi_KHONG_thuc_thi(db):
    """Agent chỉ tạo được dự định. Đây là lớp chặn "mô hình hiểu sai ý rồi tự đặt"."""
    don = _tao(db)
    with pytest.raises(ct.CongTienTuChoi):
        ct.thuc_thi(db, don=don, nguoi_duyet="", chay=lambda: {"ma_dat": "X"})
    assert don.trang_thai == DANG_XU_LY


def test_tao_du_dinh_KHONG_goi_ra_ngoai():
    """Tạo dự định phải là thao tác thuần cục bộ. Nếu nó lỡ gọi nhà cung cấp thì
    "hai chìa khoá" chỉ còn một, và cả lớp bảo vệ đầu tiên sập."""
    import inspect
    src = inspect.getsource(ct.tao_du_dinh)
    for cam in ("httpx", "requests", "chay(", "nha_cung_cap"):
        assert cam not in src, f"tạo dự định không được {cam}"


# ── LỚP 2: CHỐNG TRÙNG ───────────────────────────────────────────────────────

def test_bam_HAI_LAN_chi_ra_MOT_don(db):
    a, b = _tao(db), _tao(db)
    assert a.id == b.id
    assert db.query(DonDatCho).count() == 1


def test_khoa_sinh_tu_NOI_DUNG_khong_tu_thoi_diem():
    """Sinh từ thời điểm thì bấm hai lần cách nhau một giây ra hai khoá khác nhau, và
    ràng buộc UNIQUE thành vô nghĩa — đúng thứ nó sinh ra để chặn."""
    a = ct.khoa_chong_trung(1, "chuyen_bay", CHI_TIET)
    time.sleep(0.01)
    b = ct.khoa_chong_trung(1, "chuyen_bay", CHI_TIET)
    assert a == b


def test_thu_tu_truong_KHAC_NHAU_van_ra_cung_khoa():
    """Cùng một đơn mà thứ tự trường khác nhau phải ra cùng khoá, nếu không thì hai lần
    gửi cùng nội dung lại lọt qua."""
    a = ct.khoa_chong_trung(1, "chuyen_bay", {"tu": "SGN", "den": "DAD"})
    b = ct.khoa_chong_trung(1, "chuyen_bay", {"den": "DAD", "tu": "SGN"})
    assert a == b


def test_don_KHAC_NHAU_ra_khoa_KHAC_NHAU():
    a = ct.khoa_chong_trung(1, "chuyen_bay", CHI_TIET)
    b = ct.khoa_chong_trung(1, "chuyen_bay", {**CHI_TIET, "ngay": "17/09/2026"})
    c = ct.khoa_chong_trung(2, "chuyen_bay", CHI_TIET)   # người dùng khác
    assert len({a, b, c}) == 3


def test_rang_buoc_UNIQUE_o_tang_CSDL(db):
    """Kiểm "đã có đơn này chưa" bằng SELECT rồi INSERT là kinh điển của lỗi đua: hai
    yêu cầu vào cùng lúc thì cả hai đều thấy "chưa có". Chỉ UNIQUE của CSDL mới cắt
    được, vì nó là điểm tuần tự hoá duy nhất."""
    _tao(db)
    db.add(DonDatCho(
        user_id=1, khoa_chong_trung=ct.khoa_chong_trung(1, "chuyen_bay", CHI_TIET),
        loai="chuyen_bay", mo_ta="trùng", so_tien_vnd=1, chi_tiet={},
    ))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_thuc_thi_LAN_HAI_khong_goi_lai_nha_cung_cap(db):
    """Lớp chống trùng thứ hai: khoá UNIQUE chặn TẠO đơn trùng, nhánh này chặn THỰC THI
    trùng trên cùng một đơn. Gọi nhà cung cấp hai lần là hai vé."""
    don = _tao(db)
    so_lan = []

    def chay():
        so_lan.append(1)
        return {"ma_dat": "ABC"}

    ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=chay)
    ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=chay)
    assert len(so_lan) == 1


# ── LỚP 3: GHI NHẬT KÝ TRƯỚC KHI GỌI ─────────────────────────────────────────

def test_ghi_nhat_ky_TRUOC_khi_goi_ra_ngoai(db):
    """Chỉ ghi SAU khi thành công thì tiến trình chết giữa lúc gọi API để lại khoảng
    mù: tiền có thể đã đi mà hệ thống không có bản ghi nào."""
    don = _tao(db)
    luc_dang_goi = {}

    def chay():
        luc_dang_goi["so_log"] = db.query(AuditLog).count()
        return {"ma_dat": "ABC"}

    ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=chay)
    assert luc_dang_goi["so_log"] >= 1, "phải có log 'bắt đầu' TRƯỚC khi gọi"


def test_TIEN_TRINH_CHET_giua_chung_KHONG_de_lai_don_thanh_cong(db):
    """PHÉP THỬ ĐẦU BẢNG của cả giai đoạn này.

    Mô phỏng tiến trình bị giết đúng lúc gọi nhà cung cấp. Đơn phải KẸT ở trạng thái
    nguy hiểm, KHÔNG được tự nhảy sang thành công, và lần chạy lại KHÔNG được đặt tiếp.

    Chọn thiết kế ở đây: thà để một đơn kẹt cho người xử tay, còn hơn tự động thử lại
    và mua hai vé."""
    don = _tao(db)

    def chay_roi_chet():
        raise KeyboardInterrupt("tiến trình bị giết")

    with pytest.raises(KeyboardInterrupt):
        ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=chay_roi_chet)

    db.expire_all()
    lai = db.query(DonDatCho).filter(DonDatCho.id == don.id).one()
    assert lai.trang_thai != THANH_CONG, "chết giữa chừng KHÔNG được thành 'thành công'"

    # Chạy lại: vẫn CÙNG một đơn, không sinh đơn thứ hai.
    b = _tao(db)
    assert b.id == don.id
    assert db.query(DonDatCho).count() == 1


def test_that_bai_duoc_ghi_lai_kem_ly_do(db):
    don = _tao(db)
    with pytest.raises(RuntimeError):
        ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=_no("hết chỗ"))
    db.expire_all()
    lai = db.query(DonDatCho).filter(DonDatCho.id == don.id).one()
    assert lai.trang_thai == THAT_BAI
    assert "hết chỗ" in lai.ket_qua["loi"]


def test_nhat_ky_hong_KHONG_lam_hong_giao_dich(db, monkeypatch):
    """Mất một dòng log tệ hơn nhiều nếu nó kéo theo mất cả đơn — nên `_ghi_nhat_ky`
    nuốt lỗi có chủ ý. Ở đây kiểm rằng giao dịch vẫn chạy tới nơi."""
    don = _tao(db)
    monkeypatch.setattr(ct, "_ghi_nhat_ky", lambda *a, **kw: None)
    ra = ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=lambda: {"ma_dat": "X"})
    assert ra.trang_thai == THANH_CONG


def test_ghi_du_ca_LOG_BAT_DAU_lan_LOG_KET_QUA(db):
    don = _tao(db)
    ct.thuc_thi(db, don=don, nguoi_duyet="quan", chay=lambda: {"ma_dat": "ABC"})
    hanh_dong = [a.action for a in db.query(AuditLog).all()]
    assert "dat_cho_bat_dau" in hanh_dong
    assert "dat_cho_thanh_cong" in hanh_dong


# ── LỚP 4: TRẦN CHI TIÊU ─────────────────────────────────────────────────────

def test_vuot_tran_MOI_LAN_thi_tu_choi(db):
    with pytest.raises(ct.CongTienTuChoi) as e:
        _tao(db, tien=ct.TRAN_MOI_LAN_VND + 1)
    assert "trần mỗi lần" in str(e.value)


def test_vuot_tran_MOI_NGAY_thi_tu_choi(db):
    """Trần ngày cộng dồn các đơn ĐÃ THÀNH CÔNG. Trần là thứ duy nhất chặn được lỗi mà
    ta CHƯA nghĩ ra — ví dụ một vòng lặp hỏng biến một câu hiểu sai thành mười vé."""
    for i in range(2):
        d = _tao(db, tien=4_000_000, chi_tiet={**CHI_TIET, "ma": f"V{i}"})
        ct.thuc_thi(db, don=d, nguoi_duyet="quan", chay=lambda: {"ma_dat": "X"})
    with pytest.raises(ct.CongTienTuChoi) as e:
        _tao(db, tien=4_000_000, chi_tiet={**CHI_TIET, "ma": "V9"})
    assert "trần ngày" in str(e.value)


@pytest.mark.parametrize("xau", [0, -1, -1_000_000])
def test_so_tien_khong_duong_thi_tu_choi(db, xau):
    with pytest.raises(ct.CongTienTuChoi):
        _tao(db, tien=xau)


def test_don_THAT_BAI_khong_tinh_vao_tran_ngay(db):
    """Đơn hỏng thì tiền không đi. Tính nó vào trần là tự khoá người dùng vì một lỗi
    của nhà cung cấp."""
    d = _tao(db, tien=4_000_000)
    with pytest.raises(RuntimeError):
        ct.thuc_thi(db, don=d, nguoi_duyet="quan", chay=_no("hết chỗ"))
    assert ct._da_tieu_hom_nay(db, 1) == 0


def test_tran_duoc_dat_THAP_co_chu_y():
    """Trần rộng tay thì không chặn được gì trong đúng tình huống nó sinh ra để chặn."""
    assert ct.TRAN_MOI_LAN_VND <= 5_000_000
    assert ct.TRAN_MOI_NGAY_VND <= 10_000_000
