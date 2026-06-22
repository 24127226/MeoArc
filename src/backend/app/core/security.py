# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/security.py — tiện ích BẢO MẬT (tầng core/)              ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Sinh "token phiên": một chuỗi NGẪU NHIÊN khó đoán, dùng làm chìa   ║
# ║ khoá nhận diện phiên đăng nhập.                                    ║
# ╚══════════════════════════════════════════════════════════════════╝

import secrets


def generate_token() -> str:
    # Dùng `secrets` (KHÔNG dùng `random` thường) vì secrets sinh số ngẫu nhiên
    # an toàn cho mục đích bảo mật — kẻ xấu không đoán được token tiếp theo.
    # token_urlsafe(32) ≈ 256 bit ngẫu nhiên, ký tự an toàn để bỏ vào URL/cookie.
    return secrets.token_urlsafe(32)
