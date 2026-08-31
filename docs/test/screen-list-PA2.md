# PA2 §1.6 — Screen list (dán ngay dưới Screen Diagram)

> Đoạn mở đầu + hai bảng dưới đây thay cho việc phải viết 7 đặc tả mới.
> Sơ đồ vẽ đủ 14 màn hình; bảng này mô tả ngắn tất cả; §1.7 chỉ đặc tả sâu nhóm chính.
> Nhờ vậy sơ đồ và danh sách khớp nhau, không còn hộp nào "vẽ mà không tả".

---

The screen diagram above shows every surface the user can reach. The table below describes each
one briefly. The **primary screens** are specified in full in §1.7; the **secondary surfaces** are
transient panels, dialogs and overlays rendered above the Main Workspace, and the descriptions
here are their specification.

## Primary screens — full specification in §1.7

| # | Screen | Description |
| :---- | :---- | :---- |
| 1 | **Landing Page** | Public marketing page and the first screen an unauthenticated visitor sees. Presents the value proposition, an overview of the assistant's capabilities, the seven email categories, the subscription plans and their AI processing time windows, and the sign-in call to action. |
| 2 | **Login & Connect Account** (UC001) | Authentication screen. Starts the Google or Microsoft OAuth 2.0 flow and, on success, provisions the user record and an encrypted session, then opens the Main Workspace. On error or cancellation it stays in place and shows a plain-language message. |
| 3 | **Main Workspace** (UC003) | The authenticated shell, laid out in three columns: a navigation rail of folders on the left, the email list in the centre, and a right panel that hosts either the AI chat canvas or an email detail view. Every other screen is reached from here. |
| 4 | **Chat Canvas / AI Panel** (UC007–UC016) | Default state of the right panel. The user issues requests in natural language and the assistant replies either with text or with an interactive card — a result list, a daily digest, a triage report, a meeting brief, a categorisation table, or an email draft. |
| 5 | **Confirmation Prompt** (UC006, UC010) | An embedded card that appears inside the chat canvas whenever the agent proposes an irreversible action such as sending, deleting, or a bulk operation. It states what will happen and on which emails. Nothing is executed until the user approves; rejecting discards the proposal without side effects. |
| 6 | **Settings Panel** (UC013) | Preferences and account management: display language, light/dark theme, connected mail accounts and their revocation, current subscription tier, and MCP access for external agents. |
| 7 | **Conversation History** (UC011) | A drawer listing previous conversations with the assistant. The user can rename, pin, delete, or resume any of them; resuming restores the conversation into the chat canvas. |

## Secondary surfaces — described here

| # | Surface | Description |
| :---- | :---- | :---- |
| 8 | **Email Detail** (UC004) | Renders the full content of a selected email in the right panel — sender, subject, body, attachments and the AI summary. Opening an email marks it as read. From here the user can reply, which opens the Compose Dialog. |
| 9 | **Compose Dialog** (UC010) | Editor for writing a new email or replying to an existing thread, with recipient, subject, body and attachments. Reached from the workspace toolbar, from Email Detail, or from a draft the assistant has prepared. |
| 10 | **Command Palette** (overlay) | Keyboard-driven launcher opened with Ctrl/Cmd + K. Lets the user switch folders and trigger frequent actions without leaving the keyboard. |
| 11 | **Notification Center** | Panel listing system alerts and completion summaries of agent actions, opened from the bell icon, which carries an unread counter. |
| 12 | **Activity / Audit Log** | Chronological record of every action performed on the mailbox — whether by the user, by the agent, or by an external MCP client — including the tool used, the emails affected, and whether it succeeded or failed. Reached from the Notification Center. |
| 13 | **Onboarding** (overlay) | Shown once on first sign-in. Introduces the three-column layout, the natural-language assistant, voice input, and the keyboard shortcuts. |
| 14 | **Voice Mode** (overlay) | Speech input surface: the user dictates a request and the assistant reads its reply aloud. |

---

## ⚠️ Sửa kèm cho khớp tên

Sơ đồ và §1.7 hiện gọi khác nhau ở bốn chỗ. Chọn **cột bên phải** (tên trong sơ đồ) và sửa
tiêu đề §1.7 theo, vì bảng trên đã dùng bộ tên đó:

| §1.7 hiện ghi | Sửa thành |
| :---- | :---- |
| Screen "Main screen (Chat + Dynamic Canvas)" | Screen **"Main Workspace"** |
| Screen "Confirmation Dialog (Human-in-the-loop)" | Screen **"Confirmation Prompt (Human-in-the-loop)"** |
| Screen "Conversation History List" | Screen **"Conversation History"** |
| Screen "Email List" | **Bỏ mục này** — Email List là cột giữa của Main Workspace, đã tả trong mục Main Workspace. Sơ đồ cũng không vẽ nó thành hộp riêng. |

Sau khi sửa, §1.7 gồm đúng **7 mục**, khớp một-một với bảng "Primary screens":

```
1.7.1  Landing Page
1.7.2  Login & Connect Account
1.7.3  Main Workspace
1.7.4  Chat Canvas / AI Panel
1.7.5  Confirmation Prompt (Human-in-the-loop)
1.7.6  Settings Panel
1.7.7  Conversation History
```

> Mục **Chat Canvas / AI Panel** là mục duy nhất phải viết mới (§1.7.4). Nội dung có thể tách ra
> từ đoạn "Main screen (Chat + Dynamic Canvas)" cũ — đoạn đó đang tả gộp cả bố cục ba cột lẫn
> hành vi trợ lý, giờ tách đôi: phần bố cục về Main Workspace, phần trợ lý về Chat Canvas.
