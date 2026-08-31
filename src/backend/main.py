# ╔══════════════════════════════════════════════════════════════════╗
# ║ main.py — ĐIỂM KHỞI ĐỘNG: dùng để "bật" server                     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: gọi uvicorn (động cơ) để chạy ứng dụng FastAPI.          ║
# ║ Chạy bằng: `uv run main.py`  →  mở http://localhost:8000           ║
# ╚══════════════════════════════════════════════════════════════════╝

# uvicorn là "server ASGI" — nó lắng nghe cổng mạng và chuyển request
# vào ứng dụng FastAPI của ta. (FastAPI tự nó không lắng nghe mạng.)
import uvicorn

# Đoạn `if __name__ == "__main__":` nghĩa là: chỉ chạy khối này KHI
# file được gọi trực tiếp (`uv run main.py`), không chạy khi bị import.
if __name__ == "__main__":
    uvicorn.run(
        "app.api.app:app",  # "đường_dẫn_module:tên_biến" — trỏ tới `app` trong app/api/app.py
        host="0.0.0.0",      # nghe trên mọi địa chỉ máy (localhost vẫn vào được)
        port=8000,           # cổng — mở trình duyệt ở http://localhost:8000
        reload=True,         # tự khởi động lại mỗi khi bạn sửa code (tiện lúc học)
    )
