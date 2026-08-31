# Hướng dẫn chụp ảnh minh chứng cho §3.2 Testing

> **Đọc 30 giây trước khi làm.**
>
> §3.2 có **40 test case**. Nhưng không phải cái nào cũng chụp được bằng trình duyệt:
>
> | | Số ca | Chụp bằng gì |
> | :---- | :----: | :---- |
> | Phần 1 | **11** | Swagger UI ở `/docs` |
> | Phần 2 | **29** | Terminal chạy `pytest` |
>
> **Bốn ca ở Phần 1 kỳ vọng KHÔNG phải 200.** Chụp được 200 ở mấy ca đó nghĩa là test
> **trượt**, không phải đạt. Mình có đánh dấu 🔴 rõ ở từng dòng — đọc kỹ cột "Kỳ vọng".
>
> Đừng cố chụp 200 OK cho cả 40 ca. Ví dụ HITL-TC03 khẳng định "hành động chỉ đọc **không**
> sinh phiếu xác nhận" — ảnh 200 OK không nói được gì về chuyện đó, dán vào là người chấm
> thấy ngay bằng chứng không khớp với câu khẳng định.

---

# CHUẨN BỊ (làm một lần, ~5 phút)

### Bước 1. Bật backend

```bash
cd src/backend
./.venv/Scripts/python.exe -m uvicorn app.api.app:app --port 8000
```

Để cửa sổ này chạy suốt, đừng tắt.

### Bước 2. Đăng nhập để lấy phiên

Mở trình duyệt vào:

```
http://localhost:8000/auth/google/start
```

Đăng nhập Google như bình thường. Xong nó sẽ chuyển hướng về app.

⚠️ **Phải dùng `localhost`, không dùng `127.0.0.1`.** Cookie phiên tên `meoarc_session` gắn
theo tên host — đăng nhập ở `localhost` mà mở `127.0.0.1` thì trình duyệt không gửi cookie
và bạn nhận 401 ở mọi endpoint.

### Bước 3. Mở Swagger **trong cùng trình duyệt đó**

```
http://localhost:8000/docs
```

### Bước 4. Kiểm tra phiên có hiệu lực chưa

Tìm dòng `GET /me` → bấm **Try it out** → **Execute**.

- Ra `200` kèm email của bạn → xong, làm tiếp Phần 1.
- Ra `401` → cookie chưa có. Quay lại Bước 2, và kiểm lại là đang ở `localhost` chứ không
  phải `127.0.0.1`.

---

# QUY ƯỚC CHỤP ẢNH

Mỗi ảnh **bắt buộc** thấy đủ bốn thứ, nếu không thì ảnh không chứng minh được gì:

1. **Thanh địa chỉ** — chứng minh đang ở `localhost:8000/docs`, không phải ảnh trên mạng
2. **Tên endpoint** — dòng `POST /emails/actions/delete` chẳng hạn
3. **Ô `Code`** trong khung *Server response* — con số 200 / 422 / 429 nằm ở đây
4. **Khung `Response body`** hoặc `Response headers` — tuỳ ca, cột "Chụp gì" ghi rõ

Cách chụp: `Win + Shift + S` → chọn vùng → dán vào Paint → lưu PNG.

**Tên file:** `TC-<mã>-<mô tả ngắn>.png`
Ví dụ: `TC-SEC-TC06-owasp-headers.png`, `TC-TOOL-TC01-limit-5000.png`

Lưu hết vào `docs/test/screenshots/`.

---

# PHẦN 1 — 11 ảnh từ Swagger

## Nhóm A — 4 ca kỳ vọng 200 (bình thường)

### A1 · SEC-TC06 — Header bảo mật OWASP (§3.2.16)

| | |
| :---- | :---- |
| Endpoint | `GET /health` |
| Nhập gì | Không nhập gì. Bấm **Try it out** → **Execute** |
| Kỳ vọng | `Code 200` |
| **Chụp gì** | ⚠️ Chụp khung **Response headers**, KHÔNG phải Response body |

Trong Response headers phải thấy đủ ba dòng này:

```
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
```

Ba header đó **chính là** bằng chứng. Body không liên quan gì ở ca này.

### A2 · NFR-TC01 — `/health` báo đúng trạng thái database (§3.2.29)

| | |
| :---- | :---- |
| Endpoint | `GET /health` |
| Nhập gì | Không có |
| Kỳ vọng | `Code 200` |
| **Chụp gì** | Response **body** — phải thấy trạng thái kết nối database |

### A3 · NFR-TC02 — Độ trễ p95 dưới 3 giây (§3.2.30)

| | |
| :---- | :---- |
| Endpoint | `GET /metrics` |
| Nhập gì | Không có |
| Kỳ vọng | `Code 200` |
| **Chụp gì** | Response body — tìm khối `latency_ms` có `p50`, `p95`, `p99` |

💡 Chạy vài chục request trước cho có số liệu, đừng chụp lúc `p95: 0`. Cách nhanh: bấm
Execute trên `GET /emails` chừng 20 lần rồi mới mở `/metrics`.

### A4 · SCOPE-TC01…08 — Cửa sổ quét theo gói (§3.2.39)

| | |
| :---- | :---- |
| Endpoint | `GET /subscription` |
| Nhập gì | Không có |
| Kỳ vọng | `Code 200` |
| **Chụp gì** | Body — trường số ngày quét phải khớp gói hiện tại (Free 90 · Pro 180 · Pro Max 365) |

---

## Nhóm B — 🔴 4 ca kỳ vọng KHÔNG phải 200

**Đọc kỹ nhóm này.** Ở đây mã lỗi mới là bằng chứng đạt. Chụp được 200 là test trượt.

### B1 · 🔴 TOOL-TC01 — `limit` ngoài khoảng 1–50 bị chặn (§3.2.27)

| | |
| :---- | :---- |
| Endpoint | `GET /emails` |
| Nhập gì | Ô `limit` gõ **`5000`**. Các ô khác để trống |
| Kỳ vọng | 🔴 **`Code 422`** — không phải 200 |
| **Chụp gì** | Ô Code hiện `422` + body báo lỗi validation |

Hệ thống khai `limit` tối đa 50 ngay ở chữ ký hàm, nên FastAPI chặn trước khi vào xử lý.
Nếu ra 200 thì trần đã hỏng.

### B2 · 🔴 TOOL-TC01b — Từ khoá quá dài bị chặn

| | |
| :---- | :---- |
| Endpoint | `GET /emails` |
| Nhập gì | Ô `q` dán một chuỗi **dài hơn 200 ký tự** (gõ `a` rồi copy-paste cho dài ra) |
| Kỳ vọng | 🔴 **`Code 422`** |
| **Chụp gì** | Ô Code hiện `422` |

### B3 · 🔴 NFR-TC03 — Giới hạn tần suất (§3.2.31)

| | |
| :---- | :---- |
| Endpoint | `GET /emails` |
| Nhập gì | Để mặc định. **Bấm Execute liên tục thật nhanh** cho tới khi đổi mã |
| Kỳ vọng | 🔴 **`Code 429`** (Too Many Requests) |
| **Chụp gì** | Ô Code hiện `429` + body |

Bấm chừng 30–60 lần trong một phút. Nếu mãi không ra 429 thì ngưỡng đang đặt cao — hỏi
lại nhóm trước khi kết luận là lỗi.

### B4 · 🔴 NFR-TC04 — Tệp vượt trần bị từ chối (§3.2.32)

| | |
| :---- | :---- |
| Endpoint | `POST /uploads` |
| Nhập gì | Chọn một tệp **lớn hơn 2 MB** (ảnh chụp màn hình 4K, hoặc file PDF bất kỳ) |
| Kỳ vọng | 🔴 **`Code 413`** (Payload Too Large) |
| **Chụp gì** | Ô Code hiện `413` + body có câu *"Nội dung gửi lên quá lớn."* |

---

## Nhóm C — 3 ca: mã là 200 nhưng **bằng chứng nằm ở body**

Ba ca này chụp ô Code không đủ, vì ca đạt và ca trượt đều trả 200. Phải chụp **nội dung body**.

### C1 · HITL-TC01 — Hành động nguy hiểm sinh phiếu duyệt thay vì thực thi (§3.2.1)

| | |
| :---- | :---- |
| Endpoint | `POST /emails/actions/delete` |
| Nhập gì | Body JSON: `{"ids": ["<id một thư thật>"]}` |
| Lấy id ở đâu | Chạy `GET /emails` trước, copy một `id` trong kết quả |
| Kỳ vọng | `Code 200`, **nhưng body phải cho thấy có phiếu chờ duyệt, thư CHƯA bị xoá** |
| **Chụp gì** | Toàn bộ body |

Sau khi chụp, mở Gmail kiểm tra thư đó **vẫn còn trong hộp thư**. Nếu thư bị xoá luôn thì
cổng xác nhận không hoạt động — báo lại nhóm ngay, đừng chụp ảnh rồi cho qua.

### C2 · HITL-TC02 — Duyệt xong thì hành động mới thật sự chạy (§3.2.2)

| | |
| :---- | :---- |
| Endpoint | `POST /confirmations/{req_id}/approve` |
| Nhập gì | Ô `req_id` dán id phiếu lấy từ bước C1 (hoặc chạy `GET /confirmations` để lấy) |
| Kỳ vọng | `Code 200` + body báo đã thực thi |
| **Chụp gì** | Body |

Chụp xong mở Gmail xác nhận thư **giờ mới** vào thùng rác. Nếu chụp được cả hai trạng thái
trước/sau thì càng tốt — đó là bằng chứng mạnh nhất cho cả mục HITL.

### C3 · HITL-TC05 — 🔴 Thao tác hàng loạt vượt trần bị từ chối (§3.2.5)

| | |
| :---- | :---- |
| Endpoint | `POST /emails/actions/delete` |
| Nhập gì | Body có **rất nhiều id** — dán khoảng 200 id giả: `{"ids": ["a1","a2", … ]}` |
| Kỳ vọng | 🔴 **4xx** (400 hoặc 422) |
| **Chụp gì** | Ô Code + body |

---

# PHẦN 2 — 29 ca còn lại: chụp terminal `pytest`

Những ca này kiểm chuyện bên trong hệ thống — agent chọn tool nào, guardrail có chặn không,
dữ liệu người này có lọt sang người kia không. **Không có mã HTTP nào chứng minh được**, nên
bằng chứng đúng là output của bộ test.

Mở terminal mới (giữ nguyên cửa sổ uvicorn đang chạy):

```bash
cd src/backend
```

Rồi chạy lần lượt 8 lệnh dưới đây, mỗi lệnh chụp một ảnh terminal:

| # | Lệnh | Phủ test case nào |
| :---- | :---- | :---- |
| P1 | `./.venv/Scripts/python.exe -m pytest -v tests/test_confirmation.py tests/test_confirmation_api.py` | HITL-TC03, TC04 (§3.2.3–3.2.4) |
| P2 | `./.venv/Scripts/python.exe -m pytest -v tests/test_agent_offline.py` | UC007-TC01→TC08 (§3.2.6–3.2.13) |
| P3 | `./.venv/Scripts/python.exe -m pytest -v tests/test_isolation.py` | SEC-TC01…04 (§3.2.14) |
| P4 | `./.venv/Scripts/python.exe -m pytest -v tests/test_labeling.py tests/test_ai_labels.py` | UC009-TC01→TC09 (§3.2.17–3.2.22, §3.2.40) |
| P5 | `./.venv/Scripts/python.exe -m pytest -v tests/test_mcp.py tests/test_tool_schemas.py` | MCP-TC01, TC02 (§3.2.25–3.2.26) |
| P6 | `./.venv/Scripts/python.exe -m pytest -v tests/test_nfr.py tests/test_breaker.py tests/test_maintenance.py` | NFR-TC05, TC07 (§3.2.33, §3.2.35) |
| P7 | `./.venv/Scripts/python.exe -m pytest -v tests/test_migrations.py tests/test_uc011_api.py tests/test_mailbox_sync.py` | NFR-TC06, TC08, AUTH-TC03 (§3.2.23, §3.2.34, §3.2.36) |
| P8 | `./.venv/Scripts/python.exe -m pytest -v tests/test_semantic.py tests/test_scope.py tests/test_scope_tools.py` | SEM-TC01…06, SCOPE-TC01…08 (§3.2.38–3.2.39) |

**Chụp gì:** cả cửa sổ terminal, phải thấy **dòng lệnh** ở trên và **dòng tổng kết** ở dưới
(`N passed`). `-v` in ra từng tên test kèm `PASSED`, mà tên test nói rõ nó kiểm gì — đó chính
là thứ người chấm cần đọc.

**Tên file:** `PYTEST-P1-hitl.png`, `PYTEST-P2-agent.png`, …

### Một ảnh tổng kết nữa

```bash
./.venv/Scripts/python.exe -m pytest -q
```

Kỳ vọng: **`215 passed, 21 skipped`**. Đặt tên `PYTEST-TONG-KET.png`. Ảnh này để ở đầu
Phụ lục A.

### Ba ca không chụp được bằng cả hai cách

| Test case | Vì sao | Làm gì |
| :---- | :---- | :---- |
| §3.2.15 SEC-TC05 — không lưu mật khẩu dạng chữ thường | Phải mở database xem cột `access_token` | Bỏ qua, hoặc chụp màn hình DB nếu có công cụ |
| §3.2.24 AUTH-TC01/02/04/05 | Tài liệu đã ghi rõ **chưa chạy** | Không chụp. Đừng bịa ảnh cho ca chưa chạy |
| §3.2.37 NFR-TC09 — tương thích trình duyệt | Cần mở app trên Chrome/Edge/Firefox | Chụp giao diện app trên 3 trình duyệt, không liên quan Swagger |

---

# BẢNG KIỂM CUỐI

**Phần 1 — Swagger (11 ảnh)**
- [ ] A1 `SEC-TC06` — 200, chụp **Response headers** có đủ 3 dòng
- [ ] A2 `NFR-TC01` — 200, body có trạng thái DB
- [ ] A3 `NFR-TC02` — 200, body có `p50/p95/p99` khác 0
- [ ] A4 `SCOPE` — 200, số ngày quét khớp gói
- [ ] B1 `TOOL-TC01` — 🔴 **422**
- [ ] B2 `TOOL-TC01b` — 🔴 **422**
- [ ] B3 `NFR-TC03` — 🔴 **429**
- [ ] B4 `NFR-TC04` — 🔴 **413**
- [ ] C1 `HITL-TC01` — 200 + body có phiếu chờ duyệt + Gmail thư vẫn còn
- [ ] C2 `HITL-TC02` — 200 + Gmail thư giờ mới vào thùng rác
- [ ] C3 `HITL-TC05` — 🔴 **4xx**

**Phần 2 — pytest (9 ảnh)**
- [ ] P1 → P8, mỗi ảnh thấy dòng lệnh và dòng `N passed`
- [ ] `PYTEST-TONG-KET.png` hiện `215 passed, 21 skipped`

**Kiểm lại toàn bộ**
- [ ] Mọi ảnh Swagger đều thấy thanh địa chỉ `localhost:8000/docs`
- [ ] Bốn ảnh 🔴 **không** hiện 200 — nếu hiện 200 là test trượt, báo nhóm chứ đừng dán vào
- [ ] Tên file đúng quy ước, để hết trong `docs/test/screenshots/`

---

**Có gì không khớp thì đừng tự sửa cho vừa** — báo lại nhóm. Ảnh minh chứng sai còn tệ hơn
thiếu ảnh, vì nó thành lỗi trung thực chứ không còn là lỗi thiếu sót.
