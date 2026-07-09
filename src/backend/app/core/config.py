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

    # ── LLM cho AGENT (Pha 3 — tích hợp não develop) ──
    # `core/llm.py` đọc 4 field này để dựng client LLM (qua langchain init_chat_model).
    #   • ai_api_key          ← AI_API_KEY        : KHOÁ Gemini (lấy free ở aistudio.google.com).
    #                            ĐỂ TRỐNG = chưa cấu hình → /agent/chat tự lùi về câu trả lời mẫu
    #                            (app KHÔNG sập, vẫn chạy mọi tính năng khác).
    #   • model_name          ← MODEL_NAME        : tên model, mặc định gemini-2.0-flash (nhanh, rẻ).
    #   • model_provider      ← MODEL_PROVIDER    : nhà cung cấp; "google_genai" cho Gemini.
    #   • local_model_base_url← LOCAL_MODEL_BASE_URL : nếu chạy model LOCAL (Ollama…) thay vì cloud.
    ai_api_key: str = ""
    model_name: str = "gemini-2.0-flash"
    model_provider: str = "google_genai"
    local_model_base_url: str = ""
    #   • agent_temperature ← AGENT_TEMPERATURE : độ "ngẫu hứng" của LLM (0..1).
    #     Mặc định 0 = bám tool-call/định dạng chặt nhất (đặc biệt cần cho Groq/Llama,
    #     tránh lỗi 400 tool_use_failed). Tăng lên (vd 0.3) nếu muốn văn phong tự nhiên hơn.
    agent_temperature: float = 0.0

    # ── Observability: LangSmith tracing (đúng proposal — opt-in, tắt mặc định) ──
    # langsmith_api_key ← LANGSMITH_API_KEY : điền key (free ở smith.langchain.com) là BẬT
    #   tracing toàn bộ vòng agent (LangGraph tự instrument) → xem trace từng bước gọi tool
    #   trên UI LangSmith. ĐỂ TRỐNG = tắt (dữ liệu email không rời máy — mặc định an toàn).
    langsmith_api_key: str = ""
    langsmith_project: str = "meoarc"

    # ── NFR: ngưỡng bảo vệ tài nguyên (chỉnh được qua .env, có mặc định hợp lý) ──
    # agent_rate_limit_per_min ← AGENT_RATE_LIMIT_PER_MIN : số lượt /agent/chat tối đa
    #   MỖI NGƯỜI mỗi phút. Chặn spam vô ý/cố ý làm cạn quota Gemini của cả nhóm.
    # upload_max_mb ← UPLOAD_MAX_MB : trần dung lượng 1 tệp đính kèm (đọc vào RAM).
    agent_rate_limit_per_min: int = 8
    upload_max_mb: int = 15

    # redis_url ← REDIS_URL : đặt (vd redis://localhost:6379/0) → cache + rate-limit chạy
    #   trên Redis (chia sẻ được giữa nhiều worker khi scale). ĐỂ TRỐNG = in-memory như cũ.
    redis_url: str = ""

    # ── Bảo mật: mã hoá token Gmail khi lưu DB (NFR-Security) ──
    # token_encryption_key ← TOKEN_ENCRYPTION_KEY : khoá Fernet (base64 32 byte).
    #   ĐỂ TRỐNG = tắt (lưu plaintext như cũ). Sinh khoá:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    token_encryption_key: str = ""

    @property
    def agent_enabled(self) -> bool:
        """Agent có thể CHẠY THẬT không? (có key cloud HOẶC có model local).
        Dùng ở /agent/chat để quyết định gọi LLM hay trả câu mẫu (fallback)."""
        return bool(self.ai_api_key or self.local_model_base_url)


# Tạo MỘT instance dùng chung toàn app: `from app.core.config import settings`.
settings = Settings()
