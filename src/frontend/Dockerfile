# ╔══════════════════════════════════════════════════════════════════╗
# ║ frontend/Dockerfile — build React rồi phục vụ tĩnh bằng nginx      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ 2 tầng (multi-stage): tầng node CHỈ để build → image cuối chỉ còn  ║
# ║ nginx + file tĩnh (~50MB thay vì ~1GB kèm node_modules).           ║
# ║ LƯU Ý Vite: biến VITE_* bị "nướng" vào bundle LÚC BUILD → truyền    ║
# ║ qua build-arg, đổi API URL là phải build lại (đặc thù SPA).         ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── Tầng 1: build ──
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ── Tầng 2: serve ──
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
