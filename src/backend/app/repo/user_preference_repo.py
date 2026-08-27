# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/user_preference_repo.py — đọc/ghi sở thích người dùng     ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference


def get_or_create(db: Session, user_id: int) -> UserPreference:
    """Lấy sở thích; chưa có thì tạo bản mặc định.

    Tạo-khi-cần thay vì tạo lúc đăng ký: người dùng cũ (đăng ký trước khi có tính năng
    này) vẫn dùng được ngay, khỏi phải chạy script vá dữ liệu.
    """
    pref = db.get(UserPreference, user_id)
    if pref is None:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def update(db: Session, user_id: int, fields: dict) -> tuple[UserPreference, list[str]]:
    """Cập nhật rồi trả về (bản ghi, danh sách trường đã đổi)."""
    pref = get_or_create(db, user_id)
    da_doi = pref.update(fields)
    if da_doi:
        db.commit()
        db.refresh(pref)
    return pref, da_doi


def prompt_context(db: Session, user_id: int | None) -> str:
    """Đoạn ngữ cảnh để nhét vào system prompt của agent.

    Nuốt mọi lỗi và trả chuỗi rỗng: sở thích là thứ LÀM TỐT HƠN, không phải thứ agent
    cần để chạy. Một lỗi đọc bảng này mà làm hỏng cả cuộc trò chuyện là đánh đổi sai.
    """
    if user_id is None:
        return ""
    try:
        return get_or_create(db, user_id).to_prompt_context()
    except Exception:
        return ""
