# 05 — Ma trận truy vết Use Case (không sót)

> Bảng đối chiếu **UC ↔ component FE ↔ dữ liệu ↔ API/Tool ↔ trạng thái mock ↔ việc BE cần làm**. Dùng làm checklist nghiệm thu để các bên đảm bảo *đủ và đồng bộ*.

## 1. Ma trận đầy đủ

| UC | Tên | Component FE | Dữ liệu chính | API / Tool | Mock hiện tại | BE cần làm | HITL* |
|---|---|---|---|---|---|---|---|
| 001 | Authenticate with Google | `pages/login.tsx`, `auth/auth-context.tsx` | `User` | `GET /auth/google/start`+`/callback`, `GET /me` | `DEMO_USER`, delay giả | OAuth 2.0 thật, tạo phiên | – |
| 002 | Logout & Revoke | `layout/account-menu.tsx` | `User` | `POST /auth/logout`, `/auth/revoke` | xoá localStorage | Revoke token Google thật | ✓ (xác nhận revoke) |
| 003 | View Email List | `layout/email-list.tsx` | `Email[]` | `GET /emails?folder=` | `src/data/emails.ts` | Liệt kê từ Gmail | – |
| 004 | View Email Details | `layout/email-detail.tsx` | `Email`, `Attachment` | `GET /emails/{id}`, `/read`, `/attachments/{name}` | data tĩnh, `aiSummary` mock | Lấy body/đính kèm, set read | – |
| 005 | Search & Filter | `layout/email-list.tsx`, `lib/search.ts` | `NLResult`, `Email[]` | `GET /emails?q=&nl=` | `interpretNL` (chỉ unread/starred/attachment) | **Semantic search** thật | – |
| 006 | Manage Emails | `email-list.tsx`, `label-dialog.tsx`, `email-detail.tsx` | `PlanOp`, `EmailActions` | `POST /emails/actions/*` | `EmailActions` in-memory | Thực thi Gmail (label/archive/delete/read/star) | ✓ (delete & bulk) |
| 007 | NL mailbox **(trung tâm)** | `layout/chat-panel.tsx`, `lib/agent.ts` | `AgentReply` | `POST /agent/chat` (SSE) | `interpretCommand` rule-based | **LLM controller** (Gemini) | ✓ (theo từng skill) |
| 008 | Summarize | chat `result` + `email-detail` smart card | `AgentReply.result` | `/agent/chat` | suy từ `body`/`tldr` | LLM tóm tắt thật | – |
| 009 | Categorize | `CategorizeWidget` (chat-panel) | `AgentReply.categorize` | `/agent/chat` → `/emails/actions/label` | nhãn từ `category` | LLM phân loại; áp nhãn thật | ✓ (user chỉnh rồi áp) |
| 010 | Compose & Send | `compose-dialog.tsx`, `DraftCard` | `AgentReply.draft` | `/agent/chat` → `POST /emails/send` | dialog không gửi thật | Gửi Gmail + đính kèm | ✓ (xác nhận gửi) |
| 011 | Conversation History | `chat-panel.tsx` (drawer) | `Session` | `GET/POST/PATCH/DELETE /sessions` | in-memory `initSessions` | Lưu/đọc phiên server | ✓ (xác nhận xoá phiên) |
| 012 | MCP Client Access | `settings-dialog.tsx` (tab MCP) | tool schema ([04](04-MCP-TOOLS.md)) | MCP server `…/sse` | danh sách tĩnh | **MCP server + 7 tool** | ✓ (tool mutating) |
| 013 | Manage Settings | `settings-dialog.tsx`, `theme-provider.tsx` | `{lang, theme}` | `GET/PUT /settings` | `localStorage` | (tuỳ chọn) đồng bộ server | – |
| 014 | Daily Digest | `DigestWidget` | `AgentReply.digest` | `/agent/chat` | đếm từ data | LLM tổng hợp theo khoảng thời gian | – |
| 015 | Triage Inbox | `TriageWidget` + badge ở list | `AgentReply.triage`, `Priority` | `/agent/chat` | từ field `priority` | LLM gán ưu tiên + gợi ý | – |
| 016 | Meeting Brief | `BriefWidget` + contextActions ở detail | `AgentReply.brief` | `/agent/chat` | brief tĩnh | LLM phân tích thread | – |
| 017 | **Inbox Autopilot** | `autopilot-widget.tsx` | `AutopilotStep`, `AutopilotResult` | `/agent/chat` → `/agent/autopilot/apply` | `decideAutopilot` rule-based | LLM ra quyết định/lý do; batch thực thi | ✓ (bước rủi ro + áp dụng) |

\* **HITL = Human-in-the-loop**: hành động cần user xác nhận trước khi BE thực thi.

## 2. Checklist nghiệm thu cho Backend

**Nền tảng**
- [ ] OAuth Google (UC001) + revoke (UC002), quản lý phiên/token.
- [ ] Service email dùng chung cho REST + Agent + MCP (tránh lệch hành vi).
- [ ] Chuẩn lỗi thống nhất ([02 §Quy ước](02-API-CONTRACT.md)).

**Dữ liệu & thao tác**
- [ ] `GET /emails` đủ tham số folder/category/unread/starred/attachment/q/nl (UC003/005).
- [ ] `GET /emails/{id}` + đánh dấu đọc + tải đính kèm (UC004).
- [ ] Actions: read/important/label/archive/delete theo lô id (UC006), tách archive vs delete.
- [ ] Gửi thư + đính kèm (UC010).

**Agent / LLM**
- [ ] `POST /agent/chat` (SSE) trả đúng `AgentReply` cho mọi `kind` ([01 §3](01-DATA-MODEL.md)).
- [ ] Đủ skill: summarize/triage/digest/brief/categorize/draft/autopilot/manage.
- [ ] Tôn trọng human-in-the-loop: **không tự gửi/xoá/bulk khi chưa Approve**.
- [ ] Guardrails: mơ hồ → hỏi lại; rỗng → báo nhẹ; clamp scope.

**MCP (UC012)**
- [ ] Server SSE + auth token + scope read/modify/send.
- [ ] 7 tool đúng tên + schema ([04](04-MCP-TOOLS.md)); tool mutating yêu cầu `confirm`.

**Khác**
- [ ] Lịch sử phiên (UC011) — nếu cần "tiếp tục phiên".
- [ ] Settings đồng bộ (UC013) — tuỳ chọn.

## 3. Phân vai gợi ý

| Bên | Trách nhiệm |
|---|---|
| **FE (đã xong)** | Toàn bộ UI/UX 16 UC + UC017, định nghĩa contract (bộ docs này). Việc còn lại: thêm **API adapter** thay các hàm mock. |
| **BE core** | Auth, email service, REST API ([02](02-API-CONTRACT.md)). |
| **BE/LLM** | Agent controller + skills ([03](03-AGENT-SPEC.md)). |
| **BE/MCP** | MCP server + tools ([04](04-MCP-TOOLS.md)). |
| **QA** | Dùng ma trận này + checklist để kiểm thử từng UC, đặc biệt các luồng HITL. |

## 4. Điểm dễ sai (đọc kỹ)
1. **`removeEmails` gộp archive + delete** ở FE — BE phải tách (hệ quả Gmail khác nhau).
2. **`priority`/`tldr` là sản phẩm AI** — không phải field gốc của Gmail; BE sinh ra (có thể async).
3. **`category` là khoá màu**, không phải nhãn Gmail; `label` là chuỗi hiển thị. Màu do FE quyết ([01 §6](01-DATA-MODEL.md)).
4. **Autopilot chỉ quét `folder='inbox'`**; bước `risky` (reply) phải chờ duyệt, không tự gửi.
5. **Mọi lối vào (web/agent/MCP) phải share service** để 3 nơi không cho kết quả khác nhau.
6. **Thời gian**: nên trả ISO 8601 + để FE format, thay vì chuỗi `"Hôm nay, 08:42"` cứng.
