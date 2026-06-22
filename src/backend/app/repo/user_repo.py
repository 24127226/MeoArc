# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/user_repo.py — TRUY VẤN bảng users (tầng repo/ = thủ kho) ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ QUY CHUẨN: mỗi hàm NHẬN `db: Session` từ ngoài (không tự mở).       ║
# ║ Vì sao: nơi gọi (route) kiểm soát "ca làm việc" + giao dịch, và     ║
# ║ khi test có thể đưa vào một DB giả. Repo chỉ lo "lấy/cất".          ║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    # select(User).where(...) = "SELECT * FROM users WHERE email = ?" viết kiểu Python.
    # db.scalar(...) = lấy 1 đối tượng (hoặc None nếu không có).
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, email: str, name: str, initial: str) -> User:
    user = User(email=email, name=name, initial=initial)
    db.add(user)      # bỏ vào "giỏ" (chưa ghi xuống đĩa)
    db.commit()       # CHỐT giao dịch → ghi thật xuống file DB
    db.refresh(user)  # đọc lại để lấy 'id' DB vừa tự sinh
    return user


def get_or_create_user(db: Session, email: str, name: str, initial: str) -> User:
    # Mẫu KINH ĐIỂN khi đăng nhập: đã có user thì dùng lại, chưa có thì tạo mới.
    return get_user_by_email(db, email) or create_user(db, email, name, initial)


def list_users(db: Session) -> list[User]:
    # db.scalars(...).all() = lấy NHIỀU dòng.
    return list(db.scalars(select(User)).all())
