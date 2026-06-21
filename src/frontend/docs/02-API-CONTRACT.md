# 02 — API Contract (FE ↔ BE)

> Hợp đồng tích hợp REST + SSE. Mỗi endpoint ghi rõ: nó **thay cho chỗ mock nào trong FE**, request/response (tham chiếu [01-DATA-MODEL](01-DATA-MODEL.md)), UC liên quan.
>
> Đường dẫn/ý tưởng REST là **(ĐỀ XUẤT)** — BE chốt được, miễn giữ đúng *dữ liệu vào/ra* và *cơ chế xác nhận*. Base URL ví dụ: `/api/v1`.

## Quy ước chung
- **Auth:** mọi endpoint (trừ luồng login) cần `Authorization: Bearer <session_token>`.
- **Content-Type:** `application/json; charset=utf-8`. Stream agent dùng `text/event-stream`.
- **i18n:** `Accept-Language: vi | en` (UC013).
- **Lỗi (chuẩn hoá):**
  ```json
  { "error": { "code": "EMAIL_NOT_FOUND", "message": "Không tìm thấy thư", "details": {} } }
  ```
  Mã HTTP: 400 (input sai), 401 (chưa đăng nhập), 403 (thiếu scope), 404, 409 (xung đột), 422 (cần xác nhận/guardrail), 500.

---

## A. Auth (UC001, UC002) — thay `src/auth/auth-context.tsx`

| Method | Path | Mô tả | Response |
|---|---|---|---|
| `GET` | `/auth/google/start` | Bắt đầu OAuth 2.0, trả URL redirect Google | `{ "authUrl": "https://accounts.google.com/..." }` |
| `GET` | `/auth/google/callback?code=...` | Google gọi lại; BE đổi code → token, tạo phiên | set cookie / `{ token, user }` |
| `GET` | `/me` | Lấy user phiên hiện tại | `User` (xem [01 §2](01-DATA-MODEL.md)) |
| `POST` | `/auth/logout` | Đăng xuất phiên (UC002) | `204` |
| `POST` | `/auth/revoke` | **Thu hồi quyền Gmail** (gọi Google revoke token) + xoá phiên | `204` |

FE hiện mock: `loginWithGoogle()` set `DEMO_USER`, `logout()` xoá localStorage `meoarc-auth`. `account-menu.tsx` có 2 bước xác nhận trước khi revoke — BE chỉ cần endpoint, xác nhận do FE lo.

**Scope OAuth tối thiểu:** đọc (`gmail.readonly`), quản lý (`gmail.modify`), gửi (`gmail.send`). Khớp 3 scope hiển thị ở settings.

---

## B. Emails — đọc & tìm (UC003, UC004, UC005) — thay `src/data/emails.ts` + `src/lib/search.ts`

### `GET /emails`
Liệt kê thư theo thư mục + bộ lọc. Thay cho logic lọc trong `email-list.tsx`.

Query params:
| param | kiểu | ý nghĩa (khớp FE) |
|---|---|---|
| `folder` | `inbox\|sent\|drafts\|archive\|trash\|starred` | `starred` = thư gắn sao (trừ trash). Mặc định `inbox`. |
| `category` | `Category` | lọc theo nhãn màu (chip FE). |
| `unread` | bool | bộ lọc nhanh. |
| `starred` | bool | bộ lọc nhanh. |
| `attachment` | bool | chỉ thư có đính kèm. |
| `q` | string | tìm theo từ khoá (khớp **mọi token** trên sender/email/subject/preview/body/label — xem `matchText`). |
| `nl` | bool | nếu `true`, `q` là ngôn ngữ tự nhiên → BE tự rút tiêu chí (semantic, UC005). |
| `cursor`/`limit` | | phân trang **(ĐỀ XUẤT)**. |

Response:
```json
{
  "items": [ /* Email[] */ ],
  "nextCursor": null,
  "criteria": ["Chưa đọc", "Có đính kèm"]   // khi nl=true: tiêu chí BE đã hiểu (để FE hiện "Đã hiểu: …")
}
```

### `GET /emails/{id}` (UC004)
Trả 1 `Email` đầy đủ (`body`, `attachments`, `to`…).

### `POST /emails/{id}/read` (UC004)
Đánh dấu đã đọc khi mở thư. Body `{ "read": true }`. FE gọi khi `openEmail` (app-shell tự set `unread:false`).

### `GET /emails/{id}/attachments/{name}` (UC004)
Tải tệp đính kèm (nút Download ở `email-detail.tsx`). Trả file stream.

> **Semantic search (UC005):** khi `nl=true`, BE thay `interpretNL` (mock chỉ hiểu unread/starred/attachment) bằng hiểu ngữ nghĩa thật, nhưng **vẫn trả `items` + `criteria`** để FE hiển thị nhất quán.

---

## C. Actions — quản lý thư (UC006) — thay `EmailActions` (`src/lib/email-actions.ts`)

FE gom mọi thao tác vào interface `EmailActions` (nhận **mảng id** để dùng cho cả 1 thư lẫn hàng loạt):

```ts
type EmailActions = {
  markRead:     (ids: string[], read: boolean) => void
  setImportant: (ids: string[], value: boolean) => void
  applyLabel:   (ids: string[], category: Category, label: string) => void
  removeEmails: (ids: string[]) => void   // dùng cho CẢ archive lẫn delete
}
```

Hợp đồng REST tương ứng:

| Hành động FE | Method | Path | Body |
|---|---|---|---|
| `markRead` | `POST` | `/emails/actions/read` | `{ "ids": [...], "read": true }` |
| `setImportant` | `POST` | `/emails/actions/important` | `{ "ids": [...], "value": true }` |
| `applyLabel` | `POST` | `/emails/actions/label` | `{ "ids": [...], "category": "moss", "label": "Học tập" }` |
| archive | `POST` | `/emails/actions/archive` | `{ "ids": [...] }` |
| delete | `POST` | `/emails/actions/delete` | `{ "ids": [...] }` |

Response chuẩn: `{ "ok": true, "affected": <number> }`.

> ⚠️ **`delete` và bulk là không hoàn tác** → trong luồng agent phải qua `plan` + Approve (xem [03](03-AGENT-SPEC.md)). Khi gọi trực tiếp từ UI (nút Xoá), FE đã tự hiện dialog xác nhận; BE cứ thực thi khi nhận request.
> 💡 FE hiện gộp archive+delete vào `removeEmails` (đều biến mất khỏi list). BE nên tách 2 endpoint vì hệ quả Gmail khác nhau (archive = bỏ label INBOX; delete = chuyển TRASH).

---

## D. Compose & Send (UC010) — thay `compose-dialog.tsx`

| Method | Path | Mô tả | Body |
|---|---|---|---|
| `POST` | `/emails/send` | Gửi thư (sau khi user xác nhận ở dialog/draft card) | `{ to, cc?, bcc?, subject, body, attachments? }` |
| `POST` | `/emails/drafts` | Lưu nháp **(ĐỀ XUẤT)** | như trên |
| `POST` | `/uploads` | Upload tệp đính kèm, trả id để gắn vào `send` **(ĐỀ XUẤT)** | multipart |

FE compose có bước `compose → confirm → sent`. **Không gửi khi chưa qua bước confirm.**

---

## E. Agent chat — UC007 (trung tâm) — thay `interpretCommand` (`src/lib/agent.ts`)

### `POST /agent/chat` → **SSE stream**
Đầu vào lời người dùng, trả về `AgentReply`. Đây là endpoint quan trọng nhất.

Request:
```json
{ "sessionId": "s0", "message": "lưu trữ thư bản tin", "viaVoice": false }
```

Stream sự kiện (SSE `event:` / `data:`):
| event | data | ý nghĩa |
|---|---|---|
| `thinking` | `{}` | bật trạng thái "đang nghĩ" (FE hiện skeleton/mèo) |
| `reply` | `AgentReply` | phản hồi cuối cùng (1 object thuộc union [01 §3](01-DATA-MODEL.md)) |
| `error` | `{ code, message }` | lỗi |

> Có thể nâng cấp stream từng token cho `text`. Tối thiểu cần `thinking` → `reply`.

### Thực thi sau xác nhận (human-in-the-loop)
Khi `reply.kind = 'plan'`, FE hiện Approve/Reject. Khi Approve:

| Method | Path | Body | Khi nào |
|---|---|---|---|
| `POST` | `/agent/plan/execute` | `{ "op": PlanOp }` | user bấm Approve trên thẻ plan |

BE thực thi `op` (gọi cùng service như mục C) rồi trả `{ "ok": true, "done": "Đã lưu trữ 1 thư…" }` để FE đẩy `AgentReply` kind `done`.

> Hiện FE tự thực thi `op` qua `EmailActions` và tự sinh câu `done` (`approvePlan`/`execOp`/`doneText` trong `chat-panel.tsx`). BE thật chỉ cần đảm bảo `op` được thực thi đúng + trả câu tóm tắt.

### Các skill khác (đều là `POST /agent/chat`, khác `message`)
| Ý định | Ví dụ message | reply.kind | Thực thi sau đó |
|---|---|---|---|
| Tóm tắt (UC008) | "tóm tắt thư chưa đọc" | `result` | – (read-only) |
| Triage (UC015) | "triage hộp thư" | `triage` | – |
| Digest (UC014) | "digest hôm nay" | `digest` | – |
| Brief (UC016) | "brief cuộc họp" | `brief` | – |
| Phân loại (UC009) | "phân loại tự động toàn bộ" | `categorize` | user chỉnh → `POST /emails/actions/label` cho từng thư |
| Soạn/Trả lời (UC010) | "soạn trả lời giáo vụ" | `draft` | user duyệt → `POST /emails/send` |
| Autopilot (UC017) | "tự lái hộp thư" | `autopilot` | user áp dụng → batch actions (xem dưới) |

### Áp dụng Autopilot (UC017)
Khi user bấm "Áp dụng vào hộp thư", FE gửi `AutopilotResult`:
```
POST /agent/autopilot/apply
{ "archive": ["5","6"], "markRead": ["3"], "flag": ["2"] }
```
BE thực thi batch (archive/markRead/important) + (các `reply` đã được user duyệt sẽ gửi qua `/emails/send`). Trả `{ "ok": true }`.

---

## F. Conversation history (UC011) — hiện FE lưu in-memory (`chat-panel.tsx`)

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/sessions` | danh sách phiên `{ id, title, time, pinned, preview }[]` |
| `GET` | `/sessions/{id}` | đầy đủ messages của phiên |
| `POST` | `/sessions` | tạo phiên mới |
| `PATCH` | `/sessions/{id}` | đổi tên / ghim (`{ title?, pinned? }`) |
| `DELETE` | `/sessions/{id}` | xoá phiên (FE đã có xác nhận) |

**(ĐỀ XUẤT — toàn bộ mục F)**: nếu chưa làm kịp, FE vẫn chạy với lịch sử in-memory; nhưng để "tiếp tục phiên đã lưu" thật thì cần các endpoint này.

---

## G. Settings (UC013)
| Method | Path | Body |
|---|---|---|
| `GET` | `/settings` | `{ "lang": "vi", "theme": "light" }` |
| `PUT` | `/settings` | `{ "lang"?, "theme"? }` |

Hiện FE lưu cục bộ (`localStorage` `meoarc-lang`, theme provider). Đồng bộ server là **(ĐỀ XUẤT)**.

## H. MCP (UC012)
Không phải REST cho FE — xem [04-MCP-TOOLS](04-MCP-TOOLS.md). Settings hiển thị endpoint `https://mcp.meoarc.dev/sse`, access token, scopes, trạng thái kết nối.
