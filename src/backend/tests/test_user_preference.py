# ╔══════════════════════════════════════════════════════════════════╗
# ║ tests/test_user_preference.py — sở thích cá nhân (PA2 §1.5.2)      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Tính năng này có hai kiểu hỏng âm thầm rất dễ mắc:                 ║
# ║  • Cập nhật MỘT trường mà xoá sạch các trường khác — người dùng    ║
# ║    đổi giọng văn xong mất luôn chữ ký, không ai báo gì.            ║
# ║  • Sở thích không tới được prompt — mọi thứ vẫn chạy, thư vẫn gửi, ║
# ║    chỉ là giọng văn chẳng bao giờ đổi. Không có lỗi nào để lần.    ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user_preference import DEFAULT_TONE, TONES, UserPreference
from app.repo import user_preference_repo as repo


@pytest.fixture()
def db():
    from app.core.db import Base
    import app.models.user             # noqa: F401
    import app.models.user_preference  # noqa: F401

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng)()
    from app.models.user import User
    s.add(User(id=1, email="u1@x.vn", name="U1", initial="U"))
    s.commit()
    return s


# ── Tạo khi cần ─────────────────────────────────────────────────────────────
def test_nguoi_dung_cu_chua_co_ban_ghi_van_dung_duoc(db):
    """Tính năng thêm sau, nên phần lớn người dùng chưa có dòng nào trong bảng.
    Phải tự tạo bản mặc định thay vì nổ."""
    pref = repo.get_or_create(db, user_id=1)
    assert pref.user_id == 1
    assert pref.language == "vi"
    assert pref.tone_preference == DEFAULT_TONE


def test_goi_hai_lan_khong_tao_hai_ban_ghi(db):
    a = repo.get_or_create(db, 1)
    b = repo.get_or_create(db, 1)
    assert a is b or a.user_id == b.user_id
    assert db.query(UserPreference).count() == 1


# ── Cập nhật có chọn lọc ────────────────────────────────────────────────────
def test_sua_mot_truong_khong_lam_mat_truong_khac(db):
    """Đây là lỗi mất dữ liệu âm thầm: đổi giọng văn xong mất luôn chữ ký."""
    repo.update(db, 1, {"signature_note": "Quân\nNhóm 7 — HCMUS"})
    repo.update(db, 1, {"tone_preference": "formal"})

    pref = repo.get_or_create(db, 1)
    assert pref.tone_preference == "formal"
    assert pref.signature_note == "Quân\nNhóm 7 — HCMUS", "Chữ ký bị xoá khi đổi giọng văn"


def test_chi_bao_nhung_truong_that_su_doi(db):
    repo.update(db, 1, {"display_name": "Quân"})
    _pref, da_doi = repo.update(db, 1, {"display_name": "Quân"})   # ghi lại y hệt
    assert da_doi == [], "Ghi đè cùng giá trị mà vẫn báo là đã đổi"


def test_khong_cho_sua_truong_ngoai_danh_sach_trang(db):
    """Nhận bừa cả dict thì một payload kèm user_id sẽ đổi luôn chủ bản ghi."""
    pref = repo.get_or_create(db, 1)
    pref.update({"user_id": 999, "display_name": "Quân"})
    assert pref.user_id == 1, "Khoá chính bị sửa qua đường cập nhật sở thích"


def test_ba_truong_bat_buoc_khong_bi_xoa_rong(db):
    """language/theme/tone không được để rỗng — rỗng thì prompt và giao diện đều hỏng."""
    pref = repo.get_or_create(db, 1)
    pref.update({"language": "   ", "theme": "", "tone_preference": None})
    assert pref.language == "vi" and pref.theme == "system"
    assert pref.tone_preference == DEFAULT_TONE


# ── Kết tinh thành prompt ───────────────────────────────────────────────────
def test_chua_dat_gi_thi_khong_nhet_gi_vao_prompt(db):
    """Nhét khối rỗng vào prompt vừa tốn token vừa dạy mô hình rằng phần này
    thường trống — khiến nó coi nhẹ cả những lần có nội dung thật."""
    assert repo.prompt_context(db, 1) == ""


def test_giong_van_mac_dinh_khong_can_noi_lai(db):
    """Prompt gốc đã mô tả giọng mặc định rồi. Nhắc lại là thừa."""
    repo.update(db, 1, {"tone_preference": DEFAULT_TONE})
    assert repo.prompt_context(db, 1) == ""


def test_so_thich_that_su_di_vao_prompt(db):
    repo.update(db, 1, {
        "display_name": "Anh Quân",
        "tone_preference": "formal",
        "signature_note": "Phạm Trần Anh Quân\nNhóm 7",
        "custom_instruction": "Đừng dùng từ 'trân trọng'.",
    })
    ctx = repo.prompt_context(db, 1)

    assert "Anh Quân" in ctx
    assert TONES["formal"].split(",")[0] in ctx
    assert "Nhóm 7" in ctx
    assert "trân trọng" in ctx


def test_chua_dang_nhap_thi_tra_rong_chu_khong_no(db):
    assert repo.prompt_context(db, None) == ""


def test_loi_doc_bang_khong_duoc_lam_hong_luot_chat(db, monkeypatch):
    """Sở thích là thứ LÀM TỐT HƠN, không phải thứ agent cần để chạy. Một lỗi ở đây
    mà làm sập cuộc trò chuyện là đánh đổi sai."""
    def no(*a, **k):
        raise RuntimeError("database đứt")
    monkeypatch.setattr(repo, "get_or_create", no)

    assert repo.prompt_context(db, 1) == ""


# ── Nối vào agent ───────────────────────────────────────────────────────────
def test_agent_that_su_doc_user_context():
    """Không có phép thử này thì mọi thứ ở trên vẫn xanh trong khi sở thích chẳng
    bao giờ tới được mô hình — hỏng âm thầm đúng nghĩa."""
    import inspect
    import app.agent.nodes.agent_node as an

    src = inspect.getsource(an.agent_node if hasattr(an, "agent_node") else an)
    assert "user_context" in src, "agent_node không đọc user_context → sở thích vô dụng"
