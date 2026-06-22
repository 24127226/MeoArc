# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/schemas/user.py — KHUÔN dữ liệu User vào/ra API (tầng schemas/)║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ NHỚ: đây KHÁC models/user.py.                                      ║
# ║  • models/User  = cấu trúc BẢNG trong DB (bên trong kho).           ║
# ║  • schemas/User = hình dạng trao đổi với BÊN NGOÀI (API).           ║
# ║ Tách ra để: API giấu bớt cột nhạy cảm + shape API có thể khác bảng. ║
# ╚══════════════════════════════════════════════════════════════════╝

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Dữ liệu ĐI VÀO khi tạo user (client gửi lên)."""
    email: str
    name: str
    initial: str


class UserOut(BaseModel):
    """Dữ liệu TRẢ RA cho client. Cố tình KHÔNG có created_at hay cột nội bộ."""
    id: int
    email: str
    name: str
    initial: str

    # from_attributes=True → cho phép Pydantic đọc dữ liệu TỪ object ORM (model User),
    # nhờ vậy route trả thẳng đối tượng User, FastAPI tự "rót" sang UserOut.
    model_config = ConfigDict(from_attributes=True)
