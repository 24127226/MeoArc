# Triển khai MeoArc lên môi trường thật

> Viết sau khi dò code ngày 20/08. **Nền tảng đã sẵn sàng hơn bạn nghĩ** — Dockerfile,
> docker-compose, healthcheck, `uv.lock` khoá phiên bản, secrets để ngoài image đều đã có
> và viết tốt. Thứ thiếu là **cấu hình cho môi trường khác localhost**, và hai chỗ đó mình
> đã sửa xong trong code.

---

## I. Hai lỗi đã sửa — vì sao chúng nguy hiểm

Cả hai đều thuộc loại **hỏng âm thầm**: deploy thành công, log sạch, mở web lên thấy giao
diện, đăng nhập Google xong chuyển hướng đúng — rồi mọi thứ đứng im.

### 1. CORS ghi cứng `localhost`

`app/api/app.py` khai đúng hai origin `localhost:5173` và `localhost:5180`. Deploy lên
Vercel thì FE nằm ở `https://…vercel.app` — **trình duyệt chặn sạch mọi lệnh gọi API**,
mà backend hoàn toàn khoẻ mạnh, log không có gì bất thường.

→ Đã đổi thành đọc từ biến `CORS_ORIGINS`, giữ nguyên mặc định localhost cho máy dev.

### 2. Cookie phiên `SameSite=Lax` — đây mới là chỗ khó lần nhất

FE trên Vercel, BE trên Render là **hai site khác nhau**. Cookie `SameSite=Lax`
**không được trình duyệt gửi kèm** trong request khác site. Hệ quả:

> Đăng nhập Google → thành công → chuyển về app → **mọi lệnh gọi tiếp theo trả 401.**

Nhìn từ ngoài giống hệt lỗi xác thực, nên người ta thường đi sửa OAuth, sửa token, sửa
session — trong khi nguyên nhân là một thuộc tính cookie. Rất nhiều đồ án chết ở đúng đây.

→ Đã thêm biến `COOKIE_CROSS_SITE`. Bật lên thì cookie thành `SameSite=None; Secure`.
Máy dev không đổi gì.

**Kiểm nhanh sau khi sửa:**
```bash
cd src/backend && .venv/Scripts/python.exe -c "from app.core.config import settings; print(settings.cookie_kw, settings.allowed_origins)"
```
Toàn bộ 222 phép thử vẫn xanh sau khi sửa.

---

## II. Chọn nền tảng

PA2 §1.1 đã ghi **"React (Vercel)"** trong sơ đồ kiến trúc — nên dùng Vercel cho FE là
đúng cam kết trong tài liệu, không phải chọn tuỳ hứng.

| Thành phần | Nơi triển khai | Ghi chú |
| :---- | :---- | :---- |
| Frontend | **Vercel** | Miễn phí, khớp sơ đồ PA2, HTTPS sẵn |
| Backend | **Render** (Web Service, Docker) | Miễn phí, đọc thẳng `Dockerfile` đã có |
| PostgreSQL | **Render PostgreSQL** | Miễn phí, cùng nhà nên nối nội bộ |
| Redis | *bỏ qua* | `kv.py` tự lùi về bộ nhớ trong. Chỉ cần khi chạy nhiều worker |
| MCP server | *không triển khai được* | Chạy qua stdio trên máy người dùng — đúng bản chất, `docker-compose.yml` đã ghi chú |

---

## III. Trình tự — làm đúng thứ tự này

Thứ tự quan trọng: backend phải có URL trước thì frontend mới biết trỏ vào đâu, rồi mới
quay lại khai origin cho backend.

### Bước 1+2 · Dựng database và backend bằng một lần bấm

Repo đã có sẵn **`render.yaml`** ở thư mục gốc, nên không phải tạo tay từng thứ.

**Render → New → Blueprint → chọn repo này.** Render đọc file đó và dựng luôn cả PostgreSQL
lẫn Web Service, kèm healthcheck trỏ `/health`.

Render sẽ **hỏi bạn điền** những biến bí mật (đó là các dòng `sync: false` — chúng cố ý
không nằm trong repo):

| Biến | Lấy ở đâu |
| :---- | :---- |
| `GOOGLE_CLIENT_ID` · `GOOGLE_CLIENT_SECRET` | `.env` máy bạn |
| `GOOGLE_REDIRECT_URI` | `https://<backend>.onrender.com/auth/google/callback` |
| `AI_API_KEY` | khoá Gemini |
| `TOKEN_ENCRYPTION_KEY` | ⚠️ **chép đúng khoá đang có trong `.env`** — đổi khoá là mọi token đã lưu thành rác, người dùng phải đăng nhập lại hết |
| `CORS_ORIGINS` · `FRONTEND_URL` | để trống, điền ở bước 4 |

`DATABASE_URL` thì Render **tự nối**, không phải chép tay. Chuỗi nó phát ra thiếu tên driver
(`postgresql://` thay vì `postgresql+psycopg://`) — nhưng mình đã sửa code để tự chuẩn hoá,
nên dán thẳng vào là chạy. *(Trước đây đây là một trong những chỗ hay chết nhất.)*

Xong thì mở `https://<backend>.onrender.com/health` — phải ra `{"status":"ok","db":"up"}`.
**Chưa ra thì đừng đi tiếp.**

> **Về `AUTO_CREATE_TABLES`:** đúng chuẩn thì đặt `false` và chạy `alembic upgrade head`.
> Nhưng cho một bản demo chấm điểm, để `true` **an toàn hơn** — nó đảm bảo bảng luôn tồn
> tại kể cả khi bước di trú bị quên. Đánh đổi: schema có thể lệch với migration. Với đồ án
> thì rủi ro "không có bảng nào" đáng sợ hơn nhiều.

### Bước 3 · Đăng ký lại địa chỉ OAuth ⚠️

**Đây là bước hay bị quên nhất, và quên là không đăng nhập được.**

Vào **Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID**, thêm
vào **Authorized redirect URIs**:

```
https://<backend>.onrender.com/auth/google/callback
```

🔴 **Và kiểm ngay chỗ này: OAuth consent screen đang ở chế độ nào?**

Nếu app còn ở **Testing**, chỉ những tài khoản nằm trong danh sách *Test users* mới đăng
nhập được. **Thầy dùng Gmail của thầy để thử là bị chặn ngay**, hiện màn hình "Access
blocked" — và nhìn y hệt như sản phẩm hỏng.

Hai cách xử lý:
- **Thêm email của thầy vào Test users** — nhanh, nhưng phải biết trước email.
- **Publish app** — ai cũng đăng nhập được, nhưng Google hiện màn hình cảnh báo
  "chưa xác minh", người dùng phải bấm *Advanced → Go to MeoArc*.

Cách an toàn nhất cho buổi chấm: **làm cả hai** — publish, và vẫn thêm email thầy vào
test users. Rồi **tự đăng nhập thử bằng một tài khoản Google khác** để chắc chắn.

### Bước 4 · Deploy frontend lên Vercel

**Import repo** → **Root Directory** = `src/frontend`. Vercel tự nhận Vite.

Biến môi trường: `VITE_API_BASE_URL` = `https://<backend>.onrender.com`

Deploy xong, copy URL Vercel rồi **quay lại Render** sửa hai biến:

```
CORS_ORIGINS = https://<ten>.vercel.app
FRONTEND_URL = https://<ten>.vercel.app
```

Render sẽ tự khởi động lại. **Bỏ qua bước này là FE không gọi được API nào.**

### Bước 5 · Thử end-to-end

- [ ] `https://<backend>.onrender.com/health` → `{"status":"ok","db":"up"}`
- [ ] Mở FE trên Vercel, giao diện hiện đủ
- [ ] Bấm **Đăng nhập với Google** → về được app
- [ ] Sau khi đăng nhập, **danh sách thư hiện ra** ← *bước quan trọng nhất, nó chứng minh
      cookie đi qua được giữa hai tên miền*
- [ ] Mở DevTools → Application → Cookies: cookie `meoarc_session` phải có
      `SameSite=None` và `Secure` ✓
- [ ] Thử một lệnh chat với trợ lý

---

## IV. ⚠️ Ba cái bẫy trong ngày chấm

### 1. Render bản miễn phí **ngủ sau 15 phút không ai dùng**

Request đầu tiên đánh thức máy chủ mất **khoảng 50 giây**. Thầy mở link, thấy trang trắng
gần một phút — kết luận là hỏng.

**Xử lý:** trước buổi chấm **15 phút**, tự mở `/health` một lần để đánh thức. Nếu nộp link
để thầy tự chấm sau, đặt một cron ping mỗi 10 phút (dùng cron-job.org miễn phí), hoặc ghi
thẳng vào bài một câu: *"Máy chủ dùng gói miễn phí nên lần truy cập đầu có thể mất ~50 giây
để khởi động."* Nói trước thì đó là thông tin; để thầy tự phát hiện thì đó là lỗi.

### 2. Hạn ngạch Gemini

Gói miễn phí có trần theo phút và theo ngày. Thầy chấm cùng lúc với cả nhóm đang thử là
dễ hết. Nhóm đã có sẵn ngắt mạch nên hệ thống không sập — nhưng trợ lý sẽ báo bận.

### 3. Bí mật trong `.env` **không được đẩy lên GitHub**

`src/backend/.gitignore` đã chặn `.env` ✓ (mình kiểm rồi). Khi khai lên Render thì **gõ
tay vào ô Environment**, đừng commit file nào chứa khoá.

---

## V. Còn thiếu gì để "chuẩn" hơn

Không bắt buộc cho đồ án, ghi lại để biết:

- ~~**Chưa có CI/CD.**~~ ✅ **Đã thêm** `.github/workflows/test.yml` — chạy `pytest` và dựng
  frontend mỗi lần đẩy code lên `main` hoặc `integration`. Nó có giá trị kép: hỏng thì biết
  ngay, và kết quả nằm trên máy chủ GitHub có dấu thời gian — **bằng chứng kiểm thử mạnh
  hơn ảnh chụp màn hình**, vì không nhóm nào tự dựng ra được. Đẩy code lên là workflow chạy;
  chụp trang kết quả đó dán vào Phụ lục A thì đáng tin hơn mọi ảnh khác trong bài.
- **`WEB_CONCURRENCY` để 1.** Muốn chạy nhiều worker thì **bắt buộc** có Redis, nếu không
  mỗi worker giữ bộ đếm rate-limit riêng. `docker-compose.yml` đã ghi chú rõ điều này.
- **Chưa có tên miền riêng.** Dùng URL mặc định của Vercel/Render là đủ.

---

## VI. Ước lượng thời gian

| Việc | Thời gian |
| :---- | :---- |
| Dựng Postgres + deploy backend trên Render | 20 phút |
| Đăng ký lại OAuth + xử lý consent screen | 15 phút |
| Deploy frontend Vercel + nối CORS | 10 phút |
| Thử end-to-end, sửa vặt | 20 phút |
| **Tổng** | **~1 tiếng** nếu suôn sẻ |

Chỗ ăn thời gian nhất luôn là **OAuth consent screen** — làm bước đó trước, đừng để cuối.
