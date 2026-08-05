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

    # ── Microsoft OAuth (Outlook — đa provider). Đăng ký app ở Azure AD (Entra):
    #   ms_client_id ← MS_CLIENT_ID, ms_client_secret ← MS_CLIENT_SECRET.
    #   ms_tenant="common" = cho phép cả tài khoản cá nhân + tổ chức đăng nhập.
    #   ĐỂ TRỐNG ms_client_id = tắt nút Outlook (app chỉ chạy Google như cũ).
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_redirect_uri: str = "http://localhost:8000/auth/outlook/callback"
    ms_tenant: str = "common"

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

    # ── NFR-Scalability: TRẦN TÀI NGUYÊN khi nhiều người dùng cùng lúc ──
    # read_rate_limit_per_min ← READ_RATE_LIMIT_PER_MIN : trần lượt ĐỌC thư mỗi người
    #   mỗi phút. Rộng tay hơn agent (đọc rẻ hơn gọi mô hình) nhưng vẫn phải có trần:
    #   một tab bị kẹt vòng lặp cũng đủ làm nghẽn hạn ngạch Gmail của cả hệ thống.
    read_rate_limit_per_min: int = 90
    # max_provider_concurrency ← MAX_PROVIDER_CONCURRENCY : tổng số lệnh gọi Gmail/Graph
    #   được phép chạy song song TRONG CẢ TIẾN TRÌNH. Mỗi request dựng danh sách bắn 8
    #   lệnh; không có trần thì 50 người vào cùng lúc = 400 kết nối → nhà cung cấp trả 429.
    max_provider_concurrency: int = 32
    # max_llm_concurrency ← MAX_LLM_CONCURRENCY : số lượt gọi mô hình chạy song song.
    #   LLM chậm và đắt nhất, lại có hạn ngạch riêng → trần chặt hơn nhiều.
    max_llm_concurrency: int = 6
    # web_thread_pool ← WEB_THREAD_POOL : số luồng cho các route đồng bộ. FastAPI mặc
    #   định 40; route của mình chờ I/O lâu (Gmail ~2.5s) nên cần rộng hơn.
    web_thread_pool: int = 96
    # web_concurrency ← WEB_CONCURRENCY : số tiến trình uvicorn đang chạy. Semaphore
    #   giới hạn lệnh gọi ra ngoài nằm TRONG từng tiến trình, nên chạy 4 worker mà
    #   giữ nguyên trần 32 thì thực tế thành 128 — vượt gấp 4 ý định. Khai báo số
    #   worker ở đây để app tự chia trần cho đúng.
    web_concurrency: int = 1

    # auto_create_tables ← AUTO_CREATE_TABLES : bật thì lúc khởi động app tự tạo bảng
    #   còn thiếu (tiện cho máy dev và cho test). Ở môi trường THẬT nên đặt false:
    #   cấu trúc database chỉ được đổi khi có người chạy `alembic upgrade`, không đổi
    #   lén lúc khởi động. Alembic mới là nguồn sự thật của schema.
    auto_create_tables: bool = True

    # sentry_dsn ← SENTRY_DSN : điền vào là lỗi được gửi kèm ngữ cảnh lên Sentry;
    #   để trống thì ghi log nội bộ như cũ (0 phụ thuộc, đúng kiểu cắm-rút của kv.py).
    #   Bộ lọc trong app/core/errors.py che mọi trường có thể chứa nội dung thư.
    sentry_dsn: str = ""
    # app_env ← APP_ENV : nhãn môi trường ('development'/'staging'/'production'),
    #   gắn vào báo cáo lỗi để phân biệt lỗi máy dev với lỗi người dùng thật gặp.
    app_env: str = "development"

    # ── Dọn dữ liệu cũ (data retention) — cùng tinh thần "trần + TTL" ở NFR.md ──
    # Ba bảng chỉ thêm không bớt: sessions, audit_logs, notifications.
    # maintenance_interval_min ← MAINTENANCE_INTERVAL_MIN : chu kỳ chạy dọn (phút).
    #   Đặt 0 để TẮT hẳn việc dọn tự động.
    maintenance_interval_min: int = 60
    # audit_retention_days ← AUDIT_RETENTION_DAYS : giữ nhật ký thao tác bao nhiêu ngày.
    #   Nhật ký là bằng chứng human-in-the-loop → mặc định giữ khá lâu.
    audit_retention_days: int = 180
    # notification_retention_days ← NOTIFICATION_RETENTION_DAYS : chỉ xoá thông báo
    #   ĐÃ ĐỌC và cũ hơn ngần này ngày; chưa đọc thì giữ nguyên dù cũ tới đâu.
    notification_retention_days: int = 30

    # redis_url ← REDIS_URL : đặt (vd redis://localhost:6379/0) → cache + rate-limit chạy
    #   trên Redis (chia sẻ được giữa nhiều worker khi scale). ĐỂ TRỐNG = in-memory như cũ.
    redis_url: str = ""

    # ── EMAIL STORE-OF-RECORD (đọc-từ-DB, chống rate-limit) ──
    # mailbox_store_enabled ← MAILBOX_STORE_ENABLED : BẬT thì /emails và /emails/{id} đọc
    #   thẳng từ DB đã đồng bộ (không gọi Gmail lúc user mở web). ĐỂ TẮT (mặc định) = giữ
    #   nguyên luồng live cũ — an toàn tuyệt đối cho demo, bật khi đã chạy /sync/run.
    mailbox_store_enabled: bool = False
    #   mailbox_sync_page ← MAILBOX_SYNC_PAGE : số thư/thư-mục kéo về mỗi lần initial sync.
    mailbox_sync_page: int = 40
    #   gmail_pubsub_topic ← GMAIL_PUBSUB_TOPIC : 'projects/<proj>/topics/<topic>'. Đặt để
    #   gọi được gmail.watch() (bật Push). Để trống = chỉ đồng bộ thủ công/định kỳ (/sync/run).
    gmail_pubsub_topic: str = ""
    #   gmail_pubsub_pull_subscription ← GMAIL_PUBSUB_PULL_SUBSCRIPTION :
    #   'projects/<proj>/subscriptions/<sub>'. Dùng cho worker KÉO (app/workers/pubsub_puller.py)
    #   — nhận Gmail Push KHÔNG cần URL public/ngrok. Để trống = không chạy worker pull.
    gmail_pubsub_pull_subscription: str = ""
    #   pubsub_verify_token ← PUBSUB_VERIFY_TOKEN : token ?token=... bảo vệ webhook /gmail/push
    #   (khớp với token cấu hình trong Pub/Sub push subscription). Để trống = không kiểm.
    pubsub_verify_token: str = ""

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
