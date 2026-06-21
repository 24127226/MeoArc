# 04 — MCP Tools (UC012)

> **Actor:** `External AI Agent` (Claude Desktop / Codex). Kết nối qua **MCP server**, gọi **trực tiếp** các tool trong phạm vi quyền user đã cấp — **không** qua tầng ngôn ngữ tự nhiên của UC007.
>
> Nguồn trong FE: `src/components/layout/settings-dialog.tsx` (tab MCP) công bố endpoint, token, scope và danh sách tool. Tài liệu này biến danh sách đó thành đặc tả tool + schema để BE hiện thực.

## 1. Kết nối (hiển thị ở Settings → MCP)
- **Endpoint:** `https://mcp.meoarc.dev/sse` (SSE transport).
- **Auth:** access token dạng `mcp_sk_...` (cấp/thu hồi phía MeoArc).
- **Trạng thái:** FE hiển thị "đã kết nối · N client đang hoạt động".

## 2. Phạm vi quyền (scopes)
Khớp 3 scope hiển thị trong settings (và scope OAuth Gmail tương ứng):

| Scope | Cho phép | Gmail scope |
|---|---|---|
| `read` | Đọc thư (search, summarize, extract) | `gmail.readonly` |
| `modify` | Quản lý: label / archive / read / important / bulk | `gmail.modify` |
| `send` | Soạn & gửi / trả lời | `gmail.send` |

Tool yêu cầu scope vượt quá quyền đã cấp → trả lỗi `403 FORBIDDEN_SCOPE`.

## 3. Danh sách tool (7 tool — khớp `MCP_TOOLS` trong FE)

> Schema dạng JSON Schema rút gọn. Kiểu dữ liệu tham chiếu [01-DATA-MODEL](01-DATA-MODEL.md). Tool **mutating** (`send_email`, `reply_email`, `bulk_manage`) phải tôn trọng human-in-the-loop của UC012: trả về *bản xem trước cần xác nhận* hoặc yêu cầu cờ `confirm:true` rõ ràng (xem §4).

### 3.1 `search_emails` — scope `read`
Tìm thư theo tiêu chí hoặc ngôn ngữ tự nhiên.
```json
{
  "input": {
    "query": "string (NL hoặc từ khoá)",
    "folder": "inbox|sent|drafts|archive|trash|starred (optional)",
    "unread": "boolean (optional)", "starred": "boolean (optional)",
    "attachment": "boolean (optional)", "limit": "number (optional)"
  },
  "output": { "items": "Email[]", "criteria": "string[]" }
}
```

### 3.2 `summarize` — scope `read`
Tóm tắt 1 hoặc nhiều thư (read-only).
```json
{ "input": { "ids": "string[]  // hoặc 'query' để tự chọn" },
  "output": { "summary": "string", "perEmail": "{ id, tldr }[]" } }
```

### 3.3 `draft_reply` — scope `read` (chỉ soạn, chưa gửi)
Sinh bản nháp trả lời cho 1 thư.
```json
{ "input": { "emailId": "string", "instruction": "string (optional, vd 'ngắn gọn, trang trọng')" },
  "output": { "to": "string", "subject": "string", "body": "string" } }
```

### 3.4 `send_email` — scope `send` ⚠️ mutating
Gửi thư mới.
```json
{ "input": { "to": "string", "cc": "string[]?", "bcc": "string[]?",
             "subject": "string", "body": "string",
             "attachments": "{name,size}[]?", "confirm": "boolean" },
  "output": { "ok": true, "messageId": "string" } }
```

### 3.5 `reply_email` — scope `send` ⚠️ mutating
Trả lời 1 thư (giữ thread).
```json
{ "input": { "emailId": "string", "body": "string", "confirm": "boolean" },
  "output": { "ok": true, "messageId": "string" } }
```

### 3.6 `bulk_manage` — scope `modify` ⚠️ mutating (có thể không hoàn tác)
Thao tác hàng loạt: tương ứng `PlanOp` ([01 §4](01-DATA-MODEL.md)).
```json
{ "input": {
    "op": "archive|delete|markRead|label",
    "ids": "string[]",
    "read": "boolean (khi op=markRead)",
    "category": "Category (khi op=label)", "label": "string (khi op=label)",
    "confirm": "boolean"
  },
  "output": { "ok": true, "affected": "number" } }
```

### 3.7 `extract_tasks` — scope `read`
Trích việc cần làm / deadline từ thư (phục vụ Triage/Brief).
```json
{ "input": { "ids": "string[]  // hoặc 'query'" },
  "output": { "tasks": "{ emailId, title, deadline?, priority }[]" } }
```

## 4. Human-in-the-loop cho MCP
External agent vẫn phải tôn trọng cơ chế không hoàn tác:
- Tool mutating (`send_email`, `reply_email`, `bulk_manage` với `delete`) **chỉ thực thi khi `confirm:true`**. Nếu `confirm` thiếu/false → trả `422 CONFIRMATION_REQUIRED` kèm bản xem trước (preview) để client hỏi user.
- Ghi log mọi hành động (audit) — đồng nhất với "ghi nhật ký" trong plan của UC006/UC007.

## 5. Lưu ý kiến trúc
- MCP tool nên là **lớp mỏng** bọc **cùng service** mà REST API (`02`) và agent (`03`) dùng — tránh lệch hành vi giữa 3 lối vào (web UI, agent NL, MCP).
- Tên tool giữ đúng như FE công bố để tài liệu/UX nhất quán: `search_emails`, `summarize`, `draft_reply`, `send_email`, `reply_email`, `bulk_manage`, `extract_tasks`.
