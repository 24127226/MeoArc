# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/config.py — CẤU HÌNH (tầng core/)                         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: gom mọi "thiết lập có thể đổi" (khoá Google, URL...) vào  ║
# ║ MỘT chỗ, đọc từ file .env.                                         ║
# ║ QUY CHUẨN VÀNG: KHÔNG hardcode bí mật (client secret) trong code —  ║
# ║   vì code đẩy lên Git là lộ. Bí mật để trong .env (KHÔNG commit).   ║
# ║ pydantic-settings: tự đọc .env + kiểm kiểu; thiếu/sai báo ngay khi  ║
# ║   khởi động (fail fast) thay vì chạy giữa chừng mới lỗi.            ║
# ╚══════════════════════════════════════════════════════════════════╝

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Đọc biến từ file .env; biến lạ trong .env thì bỏ qua (extra="ignore").
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── Google OAuth (lấy từ Google Cloud Console — xem hướng dẫn) ──
    # Tên biến field map với biến .env không phân biệt hoa/thường:
    #   google_client_id  ← GOOGLE_CLIENT_ID
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # ── Database ──
    # Nhóm CHỐT dùng PostgreSQL → đặt DATABASE_URL trong .env, vd:
    #   postgresql+psycopg://USER:PASSWORD@localhost:5432/meoarc
    # ("+psycopg" = dùng driver psycopg v3). Để TRỐNG (không set trong .env) thì
    # tự lùi về SQLite file cho máy chưa cài Postgres vẫn chạy được ngay khi học.
    database_url: str = "sqlite:///./meoarc.db"

    # ── Khác ──
    frontend_url: str = "http://localhost:5173"  # để redirect FE về sau khi đăng nhập
    session_ttl_hours: int = 24                  # phiên sống bao lâu trước khi hết hạn


# Tạo MỘT instance dùng chung toàn app: `from app.core.config import settings`.
settings = Settings()
