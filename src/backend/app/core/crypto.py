# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/crypto.py — MÃ HOÁ TOKEN khi lưu DB (NFR-Security)        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Vấn đề: bảng sessions lưu google_access_token/refresh_token dạng    ║
# ║ VĂN BẢN THÔ → ai đọc được DB là chiếm được hộp thư nạn nhân.        ║
# ║ Giải pháp: mã hoá đối xứng Fernet (AES-128-CBC + HMAC) trước khi    ║
# ║ ghi, tự giải mã khi đọc — NHỜ 1 lớp TypeDecorator của SQLAlchemy    ║
# ║ nên MỌI nơi đọc/ghi token KHÔNG phải đổi gì.                        ║
# ║                                                                    ║
# ║ AN TOÀN KHI TRIỂN KHAI:                                            ║
# ║  • CHƯA đặt TOKEN_ENCRYPTION_KEY → giữ nguyên plaintext (y như cũ). ║
# ║  • Token cũ (không có tiền tố 'enc:') vẫn đọc được → tương thích    ║
# ║    ngược, không phá phiên đăng nhập đang có.                        ║
# ║  • Sinh khoá: python -c "from cryptography.fernet import Fernet;    ║
# ║    print(Fernet.generate_key().decode())" → dán vào .env.           ║
# ╚══════════════════════════════════════════════════════════════════╝

from sqlalchemy import String, TypeDecorator
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

_PREFIX = "enc:"   # đánh dấu chuỗi ĐÃ mã hoá (để phân biệt token cũ plaintext)
_fernet: Fernet | None = None


def _get_fernet() -> Fernet | None:
    """Dựng Fernet từ khoá trong .env (1 lần). Chưa có khoá → None = tắt mã hoá."""
    global _fernet
    if _fernet is None and settings.token_encryption_key:
        _fernet = Fernet(settings.token_encryption_key.encode())
    return _fernet


def encrypt_token(plain: str | None) -> str | None:
    """Mã hoá trước khi GHI. Chưa cấu hình khoá → trả nguyên (tương thích ngược)."""
    if not plain:
        return plain
    f = _get_fernet()
    if f is None:
        return plain
    return _PREFIX + f.encrypt(plain.encode()).decode()


def decrypt_token(stored: str | None) -> str | None:
    """Giải mã khi ĐỌC. Chuỗi không có tiền tố = token cũ plaintext → trả nguyên."""
    if not stored or not stored.startswith(_PREFIX):
        return stored
    f = _get_fernet()
    if f is None:
        return stored  # có ciphertext nhưng mất khoá → trả nguyên (gọi Gmail sẽ lỗi → user login lại)
    try:
        return f.decrypt(stored[len(_PREFIX):].encode()).decode()
    except InvalidToken:
        return stored


class EncryptedStr(TypeDecorator):
    """Cột chuỗi TỰ mã hoá lúc ghi / TỰ giải mã lúc đọc. Kiểu DB vẫn là VARCHAR nên
    KHÔNG cần migrate schema. Dùng ở models/session.py cho 2 cột token."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):   # Python → DB (ghi)
        return encrypt_token(value)

    def process_result_value(self, value, dialect):  # DB → Python (đọc)
        return decrypt_token(value)
