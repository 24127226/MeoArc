# Cầu nối Gemini qua Cloudflare — gỡ chặn theo vùng

## Bệnh

Bản triển khai báo:

> 🌏 Google không phục vụ Gemini API cho khu vực mà máy chủ này đang đặt.

Google chặn `generativelanguage.googleapis.com` theo vị trí **máy chủ gọi**, không
phải vị trí trình duyệt. App Service đang ở Azure **East Asia**, thực địa là **Hong
Kong** — vùng Google không phục vụ. Vì thế cùng một khoá, cùng một dòng mã:

| Chạy ở đâu | Kết quả |
|---|---|
| Máy nhà (Việt Nam) | HTTP 200, agent trả lời bình thường |
| Azure East Asia (Hong Kong) | `FAILED_PRECONDITION — User location is not supported` |

Đây không phải lỗi khoá, không phải hết lượt, và **không sửa được bằng cách đăng
nhập lại hay đổi model**.

## Vì sao "bật Cloudflare" không tự khỏi

Đây là chỗ dễ mất thời gian nhất, nên nói rõ:

- Cloudflare **không có nút chọn vùng máy chủ**. Bật proxy (đám mây cam) chỉ đổi
  đường thư **đi vào** website của bạn — trong khi lời gọi Gemini là đường **đi ra**
  từ Azure. Bật hay tắt đều không đụng tới nó.
- Viết một **Worker thường** cũng chưa đủ. Worker chạy ở PoP **gần người gọi nhất**.
  Người gọi ở đây là Azure Hong Kong → Worker chạy ở PoP Hong Kong → lời gọi ra
  Google **vẫn đi ra từ Hong Kong**. Vẫn bị chặn, mà nhìn thì tưởng đã có proxy rồi.
- Và bạn **không muốn** trỏ tới máy chủ ở Hong Kong. Cần đi **ra khỏi** Hong Kong.

## Cách làm được

**Durable Object** có vị trí cố định. `locationHint` ghim nó vào một vùng, và mọi
lời gọi ra ngoài phát đi **từ vùng đó**.

```
MeoArc (Azure Hong Kong)
   └─ HTTPS ─▶ Worker  (chạy ở PoP Hong Kong — chỉ nhận rồi đẩy tiếp)
                 └─▶ Durable Object  (GHIM ở Bắc Mỹ)
                        └─▶ generativelanguage.googleapis.com
                             ▲ Google thấy lời gọi đến TỪ MỸ → phục vụ
```

Vùng Azure giữ nguyên → URL đăng nhập giữ nguyên → **không phải khai báo lại OAuth
redirect** với Google. Đây là lý do cách này rẻ hơn hai cách còn lại.

Đánh đổi: thêm một chặng mạng, khoảng **150–200ms**. Không đáng kể so với vài giây
một lượt sinh văn bản.

## Dựng — 5 bước

Cần Node.js. Không cần thẻ tín dụng: gói Workers miễn phí đủ dùng (100.000
lượt/ngày), và Durable Object đã mở cho gói miễn phí từ 2025.

**1. Đăng nhập Cloudflare**

```bash
npx wrangler login
```

**2. Triển khai**

```bash
cd infra/cf-gemini-proxy && npx wrangler deploy
```

Xong sẽ in ra một URL dạng `https://meoarc-gemini-proxy.<tên-bạn>.workers.dev`.
**Chép lại URL đó.**

**3. Kiểm tra Worker sống chưa** (thay `<URL>` bằng URL vừa chép)

```bash
curl https://meoarc-gemini-proxy.YOUR-SUBDOMAIN.workers.dev/__suckhoe
```

Phải thấy `{"ok":true,"vung":"wnam",...}`. Chưa thấy thì dừng ở đây, chưa đi tiếp.

Rồi kiểm tra **điều quan trọng nhất** — Durable Object có thật sự nằm ngoài Hong Kong
không (`locationHint` chỉ là *gợi ý* best-effort, không phải cam kết):

```bash
curl https://meoarc-gemini-proxy.YOUR-SUBDOMAIN.workers.dev/__vitri
```

Đọc ở khối **`ben_ngoai`**, không phải khối `cloudflare`. Khối `ben_ngoai` là một máy
chủ ngoài Cloudflare nói cho biết nó nhìn thấy lời gọi đến từ đâu — chính là thứ
Google nhìn thấy. `"country": "US"` là đạt.

Khối `cloudflare` chỉ để tham khảo và **dễ đọc nhầm**: trường `loc` ở đó thường báo
quốc gia của *người gọi gốc* chứ không phải nơi đối tượng đang chạy. Đo thật đã gặp
`colo: DEN` (Denver) mà `loc: VN` cùng lúc — nhìn khối đó một mình thì tưởng hỏng.
Trường đáng tin trong khối này là `colo` (mã sân bay): `DEN`/`SJC`/`LAX`/`SEA` là Bắc
Mỹ, `HKG` là hỏng.

Số đo thật ngày 29/08/2026: `colo: DEN`, và bên ngoài thấy `172.68.35.102 · Denver ·
Colorado · US`.

**4. Đặt bí mật dùng chung** (nên làm — nếu không, ai biết URL cũng mượn được hạn
mức Cloudflare của bạn; khoá Gemini thì không lộ vì proxy không giữ khoá)

```bash
cd infra/cf-gemini-proxy && npx wrangler secret put PROXY_SECRET
```

Nó sẽ hỏi giá trị — gõ một chuỗi ngẫu nhiên và **giữ lại để dùng ở bước 5**.

**5. Khai báo cho MeoArc.** Trên Azure Portal → App Service của bạn →
*Settings* → *Environment variables* → thêm hai biến rồi bấm **Apply** (app sẽ tự
khởi động lại):

| Tên | Giá trị |
|---|---|
| `AI_BASE_URL` | URL Worker ở bước 2, **không có gạch chéo cuối** |
| `AI_PROXY_SECRET` | chuỗi đã đặt ở bước 4 (bỏ qua nếu bỏ qua bước 4) |

Xong. Vào MeoArc chat thử một câu.

> Muốn thử ở máy nhà trước thì thêm đúng hai dòng đó vào `src/backend/.env` rồi khởi
> động lại `uvicorn` — sửa `.env` xong **phải restart**, đọc lại lúc nạp chứ không
> nóng.

## Đổi vùng ghim

Sửa `VUNG` trong `wrangler.toml`. Giá trị dùng được: `wnam` (Bắc Mỹ Tây, **mặc
định** — vùng chắc chắn được phục vụ và gần Hong Kong nhất), `enam`, `weur`, `eeur`,
`sam`.

**Đừng chọn `apac`** — nó bao gồm cả Hong Kong, tức là có xác suất rơi đúng vào vùng
đang bị chặn. Sửa xong mà lúc được lúc không là kiểu lỗi tệ nhất để đi tìm. Có test
chặn giá trị này (`tests/test_gemini_proxy.py`).

⚠️ `locationHint` **chỉ có tác dụng lúc tạo lần đầu**. Durable Object đã tạo rồi thì
nằm nguyên chỗ cũ. Đổi vùng phải đổi **luôn cái tên** trong `idFromName(...)` ở
`src/worker.js`, nếu không cấu hình mới bị lờ đi trong im lặng — file trông như đã
đổi mà hành vi thì không.

## Ba cách sửa, vì sao chọn cách này

| Cách | Được | Mất |
|---|---|---|
| **Proxy Cloudflare** (đang dùng) | Miễn phí; URL app không đổi; ~15 phút | Thêm ~150ms; thêm một thành phần phải trông |
| Dựng lại App Service ở Japan East / Korea Central / Southeast Asia | Sạch nhất, không thêm gì | Vùng App Service **không đổi tại chỗ được**, phải tạo mới → **URL đổi** → phải khai báo lại OAuth redirect với Google, đặt lại toàn bộ biến môi trường, dựng lại Pub/Sub. Rủi ro cao nếu sát hạn demo |
| Vertex AI (`MODEL_PROVIDER=google_vertexai`) | Chạy được ngay tại Hong Kong (chính sách vùng khác hẳn) | Phải có project GCP + **bật thanh toán** (thẻ tín dụng) + service account |

Nếu sau này dời App Service sang vùng được phục vụ, chỉ cần **xoá `AI_BASE_URL`** là
quay lại gọi thẳng Google — không phải sửa dòng mã nào.

## Khi hỏng thì xem gì

| Hiện tượng | Nguyên nhân hay gặp |
|---|---|
| `404` từ proxy | `AI_BASE_URL` có gạch chéo cuối (backend đã tự cắt, nhưng kiểm tra lại), hoặc URL sai |
| `401` từ proxy | `AI_PROXY_SECRET` không khớp `PROXY_SECRET` bên Worker |
| `401` từ Google | Khoá `AI_API_KEY` hỏng — đây là lỗi khoá thật, không phải proxy |
| Vẫn `FAILED_PRECONDITION` | Backend chưa đọc `AI_BASE_URL`: chưa restart, hoặc gõ sai tên biến. Xem log lúc khởi động — có dòng `Gemini đi qua proxy: …` là đã ăn |
| `wrangler deploy` đòi nâng gói | `wrangler.toml` phải dùng `new_sqlite_classes`, không phải `new_classes` |

Xem log Worker theo thời gian thực:

```bash
cd infra/cf-gemini-proxy && npx wrangler tail
```
