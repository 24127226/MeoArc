# MeoArc — Frontend

Giao diện web của **MeoArc** (Email Intelligence Platform quản lý Gmail bằng LLM agent) — Đồ án Intro2SE, HCMUS, Nhóm 7.

Đây là **bản mockup frontend** (React + Vite), dùng **dữ liệu giả lập sẵn** nên **chạy được ngay, KHÔNG cần backend, KHÔNG cần tài khoản Google**.

---

## 1. Cần cài sẵn trên máy

- **Node.js phiên bản 20 trở lên** (khuyến nghị 20 LTS hoặc 22). Tải tại <https://nodejs.org>.
  Kiểm tra sau khi cài:
  ```bash
  node -v   # phải ra v20.x trở lên
  npm -v
  ```
- Có sẵn **npm** (đi kèm Node) — không cần cài thêm gì.

> Nếu `node -v` báo phiên bản thấp hơn 20, hãy gỡ và cài lại bản mới, nếu không Vite sẽ báo lỗi khi chạy.

---

## 2. Tải code về & chạy (3 bước)

Sau khi `git clone` repo về, mở terminal và làm đúng các bước sau:

```bash
# Bước 1: vào đúng thư mục frontend (QUAN TRỌNG — không chạy ở thư mục gốc repo)
cd src/frontend

# Bước 2: cài thư viện (chỉ làm 1 lần, lần đầu; chờ vài phút)
npm install

# Bước 3: chạy server phát triển
npm run dev
```

Sau bước 3, terminal sẽ hiện một dòng dạng:

```
  ➜  Local:   http://localhost:5173/
```

→ **Mở trình duyệt vào địa chỉ đó** (thường là <http://localhost:5173>) là thấy app.

Muốn dừng server: bấm `Ctrl + C` trong terminal.

---

## 3. Các lệnh khác

| Lệnh | Tác dụng |
|------|----------|
| `npm run dev`     | Chạy chế độ phát triển (có hot-reload) |
| `npm run build`   | Build bản production ra thư mục `dist/` |
| `npm run preview` | Xem thử bản đã build |
| `npm run lint`    | Kiểm tra lỗi code (ESLint) |

---

## 4. Lỗi thường gặp

- **`npm : command not found` / `'npm' is not recognized`**: chưa cài Node.js, xem lại mục 1.
- **Lỗi nhắc tới phiên bản Node khi `npm run dev`**: Node của bạn quá cũ, cài lại bản 20+.
- **Cổng 5173 đang bận**: Vite sẽ tự nhảy sang 5174... — cứ mở đúng địa chỉ nó in ra trong terminal.
- **Trắng trang / lỗi import**: chạy sai thư mục. Hãy chắc bạn đang ở `src/frontend` rồi mới `npm run dev`.

---

## 5. Trải nghiệm thử

App mô phỏng đủ 16 use case của MeoArc với dữ liệu giả. Một số thứ đáng thử:

- **3 cột**: thanh điều hướng trái · danh sách email giữa · trợ lý AI / chi tiết thư bên phải.
- **Trợ lý ngôn ngữ tự nhiên**: gõ yêu cầu vào ô chat bên phải (vd: *"tóm tắt các email chưa đọc"*, *"soạn trả lời sếp"*).
- **Phím tắt**: `/` tìm kiếm · `c` soạn thư · `j` / `k` duyệt thư · `Enter` mở thư · `Esc` bỏ chọn.
- **Command Palette**: nhấn `Ctrl + K` (hoặc `⌘ + K`) để gõ lệnh nhanh / đổi giao diện.
- **Voice Mode**: nút micro ở ô chat — nói tiếng Việt, mèo MeoArc phản hồi (cần trình duyệt Chrome/Edge cho phép micro).
- **Đổi giao diện sáng/tối** trong phần Cài đặt.

---

## 6. Công nghệ

React 19 · Vite · TypeScript · Tailwind CSS v4 · shadcn-style UI · lucide-react · react-router-dom.

Frontend Lead: **Phạm Trần Anh Quân**.
