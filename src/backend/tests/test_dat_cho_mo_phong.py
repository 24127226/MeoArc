"""Giai đoạn 3 nối đầu-cuối — đặt chỗ MÔ PHỎNG đi qua cổng xác nhận + cổng tiền.

Trước file này, cổng tiền là một tầng đã test nhưng KHÔNG CÓ GÌ DÙNG NÓ. Một cổng không
gác gì thì không chứng minh được điều gì, và cũng không demo được.

Điều được canh chặt nhất ở đây là TÍNH TRUNG THỰC. Đây không phải đặt thật: không có vé,
không có phòng, không đồng nào chuyển. Một xác nhận đặt chỗ trông y như thật mà thực ra
là giả là thứ nguy hiểm nhất trong cả tính năng — người dùng có thể ra sân bay với nó.
"""

from __future__ import annotations

import inspect

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.app import _confirm_card as _the_tu_tin_nhan
from app.core.db import Base
from app.models.dat_cho import DonDatCho, THANH_CONG
from app.models.user import User
from app.services import dat_cho
from app.services import dat_cho_gia_lap as gia_lap
from app.tools import email_tools as T
from app.tools.registry import ToolCategory, RequestContext, tool_registry
from app.tools.schemas import DatChoMoPhongInput

CTX = RequestContext(user_id="1", access_token="x", email_provider="gmail")


@pytest.fixture
def db_tam(monkeypatch):
    """CSDL trong bộ nhớ, thay cho SessionLocal mà tool tự mở."""
    # StaticPool: `sqlite://` trong bộ nhớ cấp MỘT CSDL RIÊNG cho mỗi kết nối, nên
    # mặc định thì luồng khác = CSDL rỗng. Tool chạy `cong_tien.thuc_thi` qua
    # `asyncio.to_thread`, tức luồng khác — không có dòng này thì bảng "biến mất"
    # giữa chừng và lỗi hiện ra là "no such table", rất dễ tưởng là lỗi di trú.
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    Lam = sessionmaker(bind=eng)
    s = Lam()
    s.add(User(id=1, email="a@b.c", name="A", initial="A"))
    s.commit()
    s.close()
    import app.core.db as mod_db
    monkeypatch.setattr(mod_db, "SessionLocal", Lam)
    return Lam


def _dau_vao(tien=1_200_000, ma="VN123", hoan=False):
    return DatChoMoPhongInput(
        loai="chuyen_bay", mo_ta="VN123 SGN→DAD 16/09 06:20, 1 khách",
        so_tien_vnd=tien, ma_lua_chon=ma, ngay="16/09/2026", hoan_duoc=hoan,
    )


# ── CỔNG XÁC NHẬN: tool phải bị CHẶN, không chạy thẳng ───────────────────────

def test_tool_la_WRITE_DESTRUCTIVE_nen_bi_chan():
    """Đây là cơ chế khiến agent KHÔNG tự đặt được. `requires_confirmation` suy ra từ
    category, và `tool_node` chặn tại chỗ — không tin vào việc mô hình tự kiềm chế."""
    s = tool_registry.get_spec("dat_cho_mo_phong")
    assert s.category is ToolCategory.WRITE_DESTRUCTIVE
    assert s.requires_confirmation is True


def test_the_du_dinh_dung_TAT_DINH_tu_args():
    """Thẻ phải dựng từ args, KHÔNG nhờ mô hình viết lại. Để mô hình diễn đạt lại thì
    thẻ và hành động có thể lệch nhau, và người dùng duyệt một thứ khác với thứ xảy ra."""
    import json
    from types import SimpleNamespace

    tin = [
        SimpleNamespace(type="human", content="đặt vé đó giúp mình"),
        SimpleNamespace(type="tool", name="dat_cho_mo_phong", content=json.dumps({
            "needs_confirmation": True, "action": "dat_cho_mo_phong",
            "args": {"loai": "chuyen_bay", "mo_ta": "VN123 SGN→DAD 16/09",
                     "so_tien_vnd": 1_200_000, "hoan_duoc": False},
        })),
    ]
    the = _the_tu_tin_nhan(tin)
    assert the is not None
    assert the["kind"] == "dudinh"
    assert the["buoc"][0]["tien"] == 1_200_000
    assert the["buoc"][0]["mo_ta"] == "VN123 SGN→DAD 16/09"
    assert the["_tool"] == "dat_cho_mo_phong"


def test_khong_hoan_duoc_thi_RUI_RO_CAP_3():
    """Cấp 3 = mất tiền thật. Thang rủi ro giữ cấp này cực hiếm suốt cả sản phẩm, và
    đây đúng là chỗ nó được dành sẵn cho."""
    import json
    from types import SimpleNamespace

    def the(hoan):
        return _the_tu_tin_nhan([
            SimpleNamespace(type="human", content="x"),
            SimpleNamespace(type="tool", name="dat_cho_mo_phong", content=json.dumps({
                "needs_confirmation": True, "args": {
                    "loai": "chuyen_bay", "mo_ta": "m", "so_tien_vnd": 1, "hoan_duoc": hoan},
            })),
        ])
    assert the(False)["buoc"][0]["mucRuiRo"] == 3
    assert the(True)["buoc"][0]["mucRuiRo"] == 2


def test_the_NOI_RO_day_la_mo_phong():
    """Nhãn mô phỏng phải nằm NGAY TRÊN THẺ DUYỆT, không chỉ trong log hay tài liệu.
    Đây là màn hình duy nhất người dùng chắc chắn đọc trước khi bấm."""
    import json
    from types import SimpleNamespace

    the = _the_tu_tin_nhan([
        SimpleNamespace(type="human", content="x"),
        SimpleNamespace(type="tool", name="dat_cho_mo_phong", content=json.dumps({
            "needs_confirmation": True,
            "args": {"loai": "chuyen_bay", "mo_ta": "m", "so_tien_vnd": 1},
        })),
    ])
    cd = the["cho_doan"].lower()
    assert "mô phỏng" in cd
    assert "không có khoản tiền" in cd, "phải nói rõ là không tiêu tiền"
    assert "không nhận được" in cd, "phải nói rõ là không có vé/phòng thật"


# ── CHẠY THẬT (sau khi duyệt) ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dat_thanh_cong_va_ghi_don(db_tam):
    ra = await T.dat_cho_mo_phong(_dau_vao(), CTX)
    assert ra.success is True
    assert ra.data["ma_dat_cho"].startswith("MP-"), "mã phải tự nhận là mô phỏng"
    assert ra.data["mo_phong"] is True
    assert "MÔ PHỎNG" in ra.message

    s = db_tam()
    don = s.query(DonDatCho).one()
    assert don.trang_thai == THANH_CONG
    assert don.nguoi_duyet == "user:1"
    s.close()


@pytest.mark.asyncio
async def test_dat_HAI_LAN_khong_ra_hai_don(db_tam):
    """Chống trùng đi xuyên qua cả tool, không chỉ ở tầng service."""
    a = await T.dat_cho_mo_phong(_dau_vao(), CTX)
    b = await T.dat_cho_mo_phong(_dau_vao(), CTX)
    assert a.data["don_id"] == b.data["don_id"]
    s = db_tam()
    assert s.query(DonDatCho).count() == 1
    s.close()


@pytest.mark.asyncio
async def test_vuot_tran_thi_TU_CHOI_kem_ly_do(db_tam):
    """Nuốt lỗi trần thành 'có lỗi xảy ra' thì người dùng không biết phải làm gì."""
    ra = await T.dat_cho_mo_phong(_dau_vao(tien=99_000_000), CTX)
    assert ra.success is False
    assert "trần" in ra.message


@pytest.mark.asyncio
async def test_CO_KHOA_THAT_thi_TU_CHOI_chay_mo_phong(db_tam, monkeypatch):
    """Có khoá Amadeus mà vẫn chạy mô phỏng là kiểu nhầm tệ nhất: người vận hành tưởng
    hệ thống đã đặt thật. Thà từ chối."""
    monkeypatch.setattr(dat_cho.settings, "amadeus_key", "k", raising=False)
    monkeypatch.setattr(dat_cho.settings, "amadeus_secret", "s", raising=False)
    ra = await T.dat_cho_mo_phong(_dau_vao(), CTX)
    assert ra.success is False
    assert "chưa nối" in ra.message


# ── TRUNG THỰC ───────────────────────────────────────────────────────────────

def test_ten_tool_TU_NO_da_noi_la_mo_phong():
    """Agent đọc danh sách tool. Tên mang chữ 'mo_phong' thì nó không thể vô tình trình
    bày đây như đặt thật."""
    assert "mo_phong" in "dat_cho_mo_phong"
    assert "MÔ PHỎNG" in (tool_registry.get_spec("dat_cho_mo_phong").description.upper())


def test_ket_qua_luon_mang_canh_bao():
    ra = gia_lap.dat_cho_mo_phong("chuyen_bay", {"ma": "VN1"})
    assert ra["mo_phong"] is True
    assert "MÔ PHỎNG" in ra["canh_bao"]
    assert ra["ma_dat_cho"].startswith("MP-")


def test_ma_dat_cho_TAT_DINH():
    a = gia_lap.dat_cho_mo_phong("chuyen_bay", {"ma": "VN1", "ngay": "16/09/2026"})
    b = gia_lap.dat_cho_mo_phong("chuyen_bay", {"ngay": "16/09/2026", "ma": "VN1"})
    assert a["ma_dat_cho"] == b["ma_dat_cho"]


def test_prompt_cam_noi_da_dat_xong():
    from app.agent.nodes import agent_node
    p = agent_node._SYSTEM_BASE
    assert "dat_cho_mo_phong" in p
    assert "KHÔNG nói 'đã đặt xong'" in p
    assert "ĐẶT MÔ PHỎNG" in p


def test_tool_KHONG_tu_thuc_thi_khi_chua_duyet():
    """Tool chỉ chạy qua endpoint /confirmations/{id}/approve, tức đã có người bấm.
    Ở đây khoá lại rằng nó truyền `nguoi_duyet` chứ không để rỗng — cổng tiền từ chối
    đơn không có người duyệt, và đó là lớp bảo vệ cuối cùng nếu cổng xác nhận bị lách."""
    src = inspect.getsource(T.dat_cho_mo_phong)
    assert "nguoi_duyet=" in src
    assert 'nguoi_duyet=""' not in src
