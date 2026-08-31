# ╔══════════════════════════════════════════════════════════════════╗
# ║ backend/Dockerfile — đóng gói FastAPI + agent (phần QA/DevOps)     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Image gốc của uv (kèm sẵn CPython 3.13) → cài deps từ uv.lock      ║
# ║ (KHÓA phiên bản = build lặp lại được, đúng chuẩn CI/CD).           ║
# ║ Build:  docker build -t meoarc-backend ./backend                   ║
# ║ (Thường không build lẻ — dùng docker-compose ở gốc repo.)          ║
# ╚══════════════════════════════════════════════════════════════════╝

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Biên dịch bytecode lúc build (khởi động nhanh hơn) + copy thay vì hardlink (an toàn trong Docker)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Cài THƯ VIỆN trước, code sau — đổi code không phải cài lại deps (tận dụng layer cache)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy code (những gì bị loại nằm ở .dockerignore — đặc biệt KHÔNG copy .env vào image)
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

# Chạy uvicorn TRỰC TIẾP (không qua main.py vì main.py bật reload=True — chỉ hợp khi dev)
CMD ["uv", "run", "uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
