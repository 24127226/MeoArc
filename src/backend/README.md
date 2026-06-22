# MeoArc Backend — Sandbox học việc

Nơi học backend MeoArc từ con số 0 (FastAPI). Đây là **sân tập riêng**, không phải repo nhóm — cứ thử thoải mái.

## Nấc 0 — Làm cho server chạy được

### Cần gì
- Python 3.13 (máy bạn đã có ✅) và `uv` (cài bên dưới).

### Các bước (mở PowerShell)

```powershell
# 1) Cài uv (chỉ làm 1 lần) — trình quản lý môi trường/thư viện cho Python
python -m pip install uv

# 2) Vào thư mục dự án
cd D:\meoarc-backend

# 3) Chạy server. Lần đầu uv sẽ tự tạo môi trường ảo + cài fastapi/uvicorn (chờ chút)
uv run main.py
```

Khi thấy dòng `Uvicorn running on http://0.0.0.0:8000`, mở trình duyệt:

| Mở địa chỉ | Bạn sẽ thấy |
|---|---|
| <http://localhost:8000> | `{"message": "MeoArc backend đang chạy 🎉"}` |
| <http://localhost:8000/health> | `{"status": "ok"}` |
| <http://localhost:8000/docs> | **Swagger UI** — trang tài liệu API tự sinh, bấm "Try it out" để thử |

Dừng server: bấm `Ctrl + C` trong PowerShell.

### Cấu trúc thư mục (giống khung nhóm để sau dễ "bê" sang `src/backend`)
```
meoarc-backend/
├── pyproject.toml      # khai báo dự án + thư viện
├── main.py             # điểm khởi động (bật server)
└── app/
    └── api/
        └── app.py      # tạo ứng dụng + các route (cửa nhận request)
```

> Các nấc tiếp theo (list email giả → đăng nhập → Gmail thật) sẽ thêm `app/schemas`, `app/services`… — làm tới đâu giải thích tới đó.
