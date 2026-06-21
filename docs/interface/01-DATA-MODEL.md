# 01 — Data Model (ngôn ngữ chung)

> Mọi kiểu dữ liệu FE đang dùng, là **hợp đồng dữ liệu** giữa các bên. Trích trực tiếp từ code (`src/data/*`, `src/lib/*`). BE phải trả/nhận **đúng tên trường và kiểu** này (hoặc thống nhất đổi tại đây).

Nguồn gốc trong FE:
- `src/data/emails.ts` — `Email`, `Category`, `Priority`, `Attachment`
- `src/data/categories.ts` — bảng màu + nhãn category
- `src/auth/auth-context.tsx` — `User`
- `src/lib/agent.ts` — `AgentReply`, `PlanOp`, `AutopilotStep`, `AutopilotAction`
- `src/lib/search.ts` — `NLResult`
- `src/components/layout/autopilot-widget.tsx` — `AutopilotResult`

---

## 1. Email (thực thể trung tâm)

```ts
type Category = 'moss' | 'sea' | 'sun' | 'cherry' | 'sky' | 'terra' | 'wine'
type Priority = 'action' | 'waiting' | 'fyi'        // do AI Triage gán (UC015)
type Attachment = { name: string; size: string }    // size là chuỗi hiển thị, vd "248 KB"

type Email = {
  id: string
  sender: string            // tên hiển thị, vd "Giáo vụ HCMUS"
  senderEmail: string       // vd "giaovu@fit.hcmus.edu.vn"
  senderInitial: string     // 1 ký tự cho avatar, vd "G"
  to: string                // người nhận (hiển thị), vd "Anh Quân <quanpta.meoarc@gmail.com>"
  subject: string
  preview: string           // 1 dòng tóm tắt thô (snippet Gmail)
  body: string[]            // các đoạn văn; mỗi phần tử = 1 <p>, có thể chứa "\n"
  time: string              // nhãn ngắn cột list, vd "08:42" / "Hôm qua" / "T4"
  date: string              // nhãn đầy đủ ở detail, vd "Hôm nay, 08:42"
  unread: boolean
  starred: boolean
  category: Category        // quyết định MÀU + nhãn mặc định
  label?: string            // nhãn hiển thị, vd "Học tập" (xem §6)
  attachments?: Attachment[]
  priority?: Priority       // AI Triage; nếu thiếu, coi như 'fyi'
  tldr?: string             // tóm tắt 1 dòng do AI quét (UC008) — dùng ở card & smart card
  folder?: 'inbox' | 'sent' | 'drafts' | 'archive' | 'trash'  // thiếu = 'inbox'
}
```

### Lưu ý cho BE (mapping Gmail)
- `id` ↔ Gmail message id (hoặc thread id — thống nhất 1 mức; FE coi mỗi item là 1 thư).
- `preview` ↔ `snippet`. `body[]` ↔ phần text đã tách đoạn (BE tách HTML→text, cắt đoạn).
- `unread`/`starred` ↔ label `UNREAD`/`STARRED`. `folder` ↔ `INBOX`/`SENT`/`DRAFT`/`TRASH` + khái niệm archive (không có label INBOX).
- `time`/`date` **nên** do BE trả ISO 8601 ở field riêng (vd `receivedAt`) và để FE tự format; hiện FE đang nhận chuỗi sẵn — xem [02 §Emails](02-API-CONTRACT.md) cho field chuẩn hoá **(ĐỀ XUẤT)**.
- `priority` và `tldr` là **sản phẩm của AI** (Triage/Summarize). BE có thể trả rỗng lúc đầu rồi cập nhật dần (async enrichment).

### Ví dụ JSON (1 email thật từ seed)
```json
{
  "id": "1",
  "sender": "Giáo vụ HCMUS",
  "senderEmail": "giaovu@fit.hcmus.edu.vn",
  "senderInitial": "G",
  "to": "Anh Quân <quanpta.meoarc@gmail.com>",
  "subject": "Nhắc nộp báo cáo SRS — Nhóm 7",
  "preview": "Các nhóm vui lòng nộp bản SRS hoàn chỉnh trước 23:59 thứ Sáu...",
  "body": ["Chào các em,", "Các nhóm vui lòng nộp bản SRS hoàn chỉnh ...", "Trân trọng,\nPhòng Giáo vụ"],
  "time": "08:42",
  "date": "Hôm nay, 08:42",
  "unread": true,
  "starred": true,
  "category": "moss",
  "label": "Học tập",
  "priority": "action",
  "tldr": "Hạn nộp SRS hoàn chỉnh: 23:59 thứ Sáu, đặt tên Nhom07_SRS_v1.pdf.",
  "attachments": [{ "name": "Mau_SRS_Intro2SE.docx", "size": "248 KB" }]
}
```

## 2. User (UC001/002)

```ts
type User = { name: string; email: string; initial: string }
```

## 3. AgentReply — phản hồi của agent quyết định canvas render gì

> **Quan trọng nhất cho LLM/BE.** Endpoint chat (UC007) phải trả về **một** object thuộc union này. FE switch theo `kind` để render. Chi tiết hành vi ở [03-AGENT-SPEC](03-AGENT-SPEC.md).

```ts
type AgentReply =
  | { kind: 'text'; text: string }                                  // trả lời thường / hỏi lại
  | { kind: 'done'; text: string }                                  // thông báo đã xong (sau khi thực thi)
  | { kind: 'result'; title: string; intro: string; lines: string[] } // kết quả dạng danh sách (UC008)
  | { kind: 'plan';   intro: string; steps: string[]; warn?: string; confirmLabel: string; op: PlanOp } // UC006 — cần duyệt
  | { kind: 'draft';  intro: string; to: string; subject: string; body: string }  // UC010 — soạn thư, cần duyệt gửi
  | { kind: 'brief';  intro: string; title: string; when: string; deadline?: string;
      attendees: { name: string; initial: string }[]; actions: string[]; points: string[] }  // UC016
  | { kind: 'triage'; intro: string; title: string;
      groups: { level: 'high' | 'normal'; label: string;
                items: { sender: string; initial: string; subject: string; suggest: string }[] }[] }  // UC015
  | { kind: 'digest'; intro: string; title: string;
      stats: { label: string; value: number }[];
      breakdown: { label: string; count: number }[]; highlights: string[] }  // UC014
  | { kind: 'categorize'; intro: string; title: string;
      items: { id: string; sender: string; subject: string; category: Category; label: string }[] }  // UC009
  | { kind: 'autopilot'; intro: string; title: string; plan: AutopilotStep[] }  // UC017
```

Bảng tra nhanh:

| `kind` | UC | Read-only? | Cần user duyệt? | Render thành |
|---|---|---|---|---|
| `text` | 007 | ✓ | – | bong bóng chat |
| `done` | – | – | – | thẻ "đã xong" (sau thực thi) |
| `result` | 008 | ✓ | – | card danh sách gạch đầu dòng |
| `plan` | 006 | – | **✓** (đặc biệt khi có `warn`) | thẻ kế hoạch + Approve/Reject |
| `draft` | 010 | – | **✓ trước khi gửi** | thẻ nháp (Gửi/Sửa/Viết lại/Huỷ) |
| `brief` | 016 | ✓ | – | bento Meeting Brief |
| `triage` | 015 | ✓ | – | bento nhóm ưu tiên |
| `digest` | 014 | ✓ | – | bento số liệu |
| `categorize` | 009 | – | **✓ (user chỉnh rồi áp dụng)** | checklist nhãn |
| `autopilot` | 017 | hỗn hợp | **✓ cho bước rủi ro + áp dụng** | widget tự lái |

### Ví dụ JSON

`plan` (xoá hàng loạt — có cảnh báo):
```json
{
  "kind": "plan",
  "intro": "Mình tìm thấy 1 thư khớp yêu cầu. Đây là kế hoạch đề xuất:",
  "steps": ["Quét hộp thư & xác định 1 thư khớp: Promo Shopee", "Chuyển 1 thư vào thùng rác", "Cập nhật hộp thư & ghi nhật ký"],
  "warn": "Xoá hàng loạt không thể hoàn tác — cần bạn xác nhận trước khi thực thi.",
  "confirmLabel": "Xoá 1 thư",
  "op": { "type": "delete", "ids": ["t1"] }
}
```

`draft`:
```json
{ "kind": "draft", "intro": "Mình đã soạn một bản nháp trả lời Giáo vụ HCMUS:",
  "to": "Giáo vụ HCMUS <giaovu@fit.hcmus.edu.vn>", "subject": "Re: Nhắc nộp báo cáo SRS — Nhóm 7",
  "body": "Dạ em chào Giáo vụ HCMUS,\n\nEm đã nhận được email và sẽ phản hồi sớm ạ.\n\nTrân trọng,\nAnh Quân" }
```

## 4. PlanOp — thao tác mà một `plan` sẽ thực thi sau khi Approve

```ts
type PlanOp =
  | { type: 'archive';  ids: string[] }
  | { type: 'delete';   ids: string[] }
  | { type: 'markRead'; ids: string[]; read: boolean }
  | { type: 'label';    ids: string[]; category: Category; label: string }
  | { type: 'autoLabel'; items: { id: string; category: Category; label: string }[] }
```

Sau khi user Approve, FE gọi `EmailActions` tương ứng (xem [02 §Actions](02-API-CONTRACT.md)) rồi đẩy 1 `AgentReply` kind `done`.

## 5. Autopilot (UC017)

```ts
type AutopilotAction = 'archive' | 'markRead' | 'flag' | 'reply' | 'keep'

type AutopilotStep = {
  id: string; sender: string; initial: string; subject: string
  tldr: string; category: Category; label: string
  action: AutopilotAction      // quyết định của agent cho thư này
  reason: string               // lý do ngắn (glass-box), vd "Bản tin định kỳ → lưu trữ cho gọn"
  risky: boolean               // true = không hoàn tác (gửi) → phải user duyệt
}

// Kết quả widget gửi về để áp dụng thật (sau khi user bấm "Áp dụng vào hộp thư")
type AutopilotResult = {
  archive: string[]; markRead: string[]; flag: string[]
  counts: { archive: number; markRead: number; flag: number; replied: number; kept: number }
}
```

Logic ra quyết định tham chiếu (`decideAutopilot` trong `agent.ts`) — BE/LLM có thể nâng cấp nhưng giữ tinh thần:

| Điều kiện thư | action | risky |
|---|---|---|
| `priority='action'` + người gửi là người thật | `reply` | ✓ |
| `priority='action'` + bot (noreply/notifications) | `flag` | – |
| `category='terra'` hoặc `label='Bản tin'` | `archive` | – |
| `priority='waiting'` | `keep` | – |
| `category='sky'` hoặc `label='Deploy'` | `archive` | – |
| `priority='fyi'` | `markRead` | – |
| còn lại | `keep` | – |

## 6. Category — bảng màu & nhãn (nguồn duy nhất)

`src/data/categories.ts` là **nguồn màu duy nhất**. BE chỉ cần trả `category` (khoá) + tuỳ chọn `label`; màu do FE quyết.

| key | label mặc định (`CATEGORY_OPTIONS`) | ý nghĩa gợi ý |
|---|---|---|
| `moss` | Học tập | trường lớp, giáo vụ, SRS |
| `sea` | Dev | github, code, PR |
| `sun` | Hệ thống | cloud, api, hạn mức |
| `cherry` | Cá nhân | bạn bè, đồng đội |
| `sky` | Deploy | vercel, build |
| `terra` | Bản tin | newsletter, quảng cáo |
| `wine` | Khẩn | (mức ưu tiên cao) |

## 7. NLResult — kết quả "hiểu" truy vấn ngôn ngữ tự nhiên (UC005)

```ts
type NLResult = {
  unread?: boolean
  starred?: boolean
  attachment?: boolean
  text: string          // phần chữ còn lại để tìm theo nội dung
  criteria: string[]    // các tiêu chí đã hiểu, để hiển thị (vd ["Chưa đọc", "Có đính kèm"])
}
```

BE semantic search nên trả về **kết quả lọc** + (tuỳ chọn) `criteria` đã hiểu để FE hiển thị "Đã hiểu: …". Xem [02 §Search](02-API-CONTRACT.md).
