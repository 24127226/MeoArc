# Đối chiếu 3 hình (§1.1 và §1.2) — với code và với docx

> File này trả lời đúng một câu hỏi: **ba tấm hình đó khác code chỗ nào, khác bảng trong
> docx chỗ nào.** Phần "phải sửa gì trên hình" nằm ở file [GUI-BAN-SUA-DESIGN.md](GUI-BAN-SUA-DESIGN.md).

## Cách đọc — ba loại lệch khác nhau

PA2 là tài liệu **thiết kế**. Code đi sau thiết kế là chuyện bình thường và không phải lỗi.
Nên phải tách ba loại, đừng gộp:

| Ký hiệu | Nghĩa | Xử lý |
| :---- | :---- | :---- |
| 🔴 | Hình mâu thuẫn với **chính docx** | **Phải sửa.** Hai chỗ trong cùng tài liệu nói ngược nhau |
| 🔵 | Hình nói có thứ **không tồn tại ở đâu cả** | **Phải sửa.** Đây là bịa |
| 🟡 | Hình/docx tả thứ **code chưa build** | Chấp nhận được — đó là thiết kế đích. Nhưng phải biết để không hứa nhầm khi demo |

---

# A. Hai hình §1.1 (kiến trúc) — so với CODE

## A1. Phần khớp — 17/20 khối có thật trong code

Đây là tin tốt: bộ xương kiến trúc vẽ đúng.

| Khối trong hình | Chỗ tương ứng trong code |
| :---- | :---- |
| React (Vercel) | `src/frontend/` (React 19 + Vite) |
| FastAPI | `app/api/app.py` |
| — Authentication API | `app/api/auth.py` → `/google/start`, `/google/callback`, `/outlook/start`, `/outlook/callback`, `/logout`, `/revoke` |
| — Chat API | `/agent/chat`, `/agent/conversations`, `/agent/plan/execute`, `/agent/autopilot/apply` (7 route) |
| — Email API | `/emails/*` (14 route) |
| — Notification API | `/notifications/*` (4 route) |
| Public MCP Server | `app/mcp/server.py` |
| Input Guardrails | `app/agent/guardrails/input_guardrail.py` |
| Output Guardrails | `app/agent/guardrails/output_guardrail.py` |
| Memory Manager | `app/agent/memory/memory_manager.py` |
| Skill Loader | `app/agent/skills/skill_loader.py` |
| LLM Reasoning Loop | `app/agent/graph.py` + `nodes/agent_node.py` + `nodes/tool_node.py` |
| Skill Repository | `app/agent/skills/library/` (11 file .md) |
| Tool Registry | `app/tools/registry.py` (9 tool) |
| PostgreSQL Database | `app/core/db.py` |
| Redis Cache (Cache / Queue / Rate limit) | `app/core/kv.py`, `limits.py`, `maintenance.py` |
| Gmail API | `app/services/gmail_service.py` |
| Microsoft Graph API | `app/services/outlook_service.py` |
| Gemini API | `app/core/llm.py` |

## A2. Phần không khớp

### 🔵 A2.1 — Tool Registry: 3 tool trong hình không tồn tại

Code có đúng 9 tool (`app/tools/email_tools.py`):

```
search_emails   categorize_emails   semantic_search   get_email   list_labels
send_email      reply_email         apply_labels      bulk_action
```

| Trong hình | Thực tế |
| :---- | :---- |
| Search Email Tool | ✅ `search_emails` |
| Read Email Tool | ✅ `get_email` |
| Send Email Tool | ✅ `send_email` |
| Reply Email Tool | ✅ `reply_email` |
| Semantic Search Tool | ✅ `semantic_search` |
| **Draft Email Tool** | 🔵 không có |
| **Extract Tasks Tool** | 🔵 không có |
| **Request Confirmation Tool** | 🔵 không có — và **không thể có**: xác nhận là cơ chế registry tự áp lên nhóm `WRITE_DESTRUCTIVE`, không phải một tool để LLM gọi |
| *(hình thiếu)* | `categorize_emails`, `list_labels`, `apply_labels`, `bulk_action` |

### 🔵 A2.2 — Skill Repository: 6 tên trong hình đều là tên bịa

Code có 11 file, chia 4 nhóm (`app/agent/skills/library/`):

```
domain/     academic_email    client_comms    job_application
provider/   gmail_quirks
workflows/  daily_digest      email_triage    meeting_prep
writing/    email_structure   tone_guide      language_vi     reply_etiquette
```

Không tên nào trong hình (Daily Summary, Inbox Cleanup, Draft Reply, Task Extraction,
Email Writing Guide, Gmail/Outlook Best Practices) trùng khớp. Gần nhất là Daily Summary ≈
`daily_digest`, Inbox Cleanup ≈ `email_triage`.

**Đáng chú ý:** hình 3 (class diagram) vẽ `DailyDigestSkill`, `TriageSkill`, `MeetingPrepSkill`
— ba cái này **khớp đúng** thư mục `workflows/`. Tức là hình 3 đúng, hình 1 sai, và hai
hình đang tự mâu thuẫn với nhau.

### 🔵 A2.3 — "MCP Client Adapters" không tồn tại

Code không có MCP client nào. Gmail và Outlook được gọi bằng REST thường
(`gmail_service.py`, `outlook_service.py`). MCP chỉ có một chiều: MeoArc **là** MCP server
(`app/mcp/server.py`) cho Claude Desktop nối vào.

### 🟡 A2.4 — Application Layer: 4/7 "service" nằm ở tầng khác

| Trong hình | Trong code |
| :---- | :---- |
| Authentication Service | ✅ `services/auth_service.py` + `auth_service_ms.py` |
| Email Service | ✅ `services/email_service.py` |
| Conversation Service | 🟡 không có file service — logic ở `repo/conversation_repo.py` |
| Notification Service | 🟡 `repo/notification_repo.py` |
| Audit Log Service | 🟡 `repo/audit_repo.py` |
| Confirmation Service | 🟡 `repo/confirmation_repo.py` |
| Attachment Processing Service | 🟡 gần nhất là `services/upload_store.py` |

Chỗ này **không cần sửa hình**. Hình kiến trúc mô tả tầng logic, không buộc map 1-1 với tên
thư mục. Tầng đó có thật, chỉ là một nửa nằm trong `repo/`.

### 🟡 A2.5 — Hai khối có thật trong code nhưng hình không vẽ

- **`services/sync_service.py`** — đồng bộ hộp thư (Gmail history_id / Graph delta_link,
  Pub/Sub push, incremental sync). Đây là một khối chức năng lớn và độc lập, thiếu hẳn
  trên hình. Nên thêm `Mailbox Sync Service` vào Application Layer.
- **`core/embeddings.py`** — sinh vector cho semantic search. Hình có ghi "Embeddings"
  trong ô PostgreSQL nhưng không có khối nào sinh ra chúng. Nên thêm `Embedding Service`.

Ngoài ra code còn có `breaker.py` (ngắt mạch), `retry.py`, `crypto.py` (mã hoá token),
`scope.py` (giới hạn cửa sổ quét). Mấy cái này là hạ tầng ngang, không nhất thiết phải lên
hình kiến trúc mức này.

### 🟡 A2.6 — Gemini nối sai đường

Hình: `Integration Layer (Gmail/Outlook Adapter)` → `Gemini API`.
Code: `app/core/llm.py` được gọi từ `agent/nodes/agent_node.py`, **không** đi qua adapter
hộp thư. Kéo mũi tên từ Agent Layer sang.

---

# B. Hình 3 (§1.2 class diagram) — so với CODE

Code hiện có **14 model** (`app/models/`). Hình vẽ khoảng 20 lớp. Đây là bảng đối chiếu đầy đủ.

## B1. Lớp trên hình đã có model tương ứng (8)

| Lớp trên hình | Model trong code | Khác biệt |
| :---- | :---- | :---- |
| `User` | `User` (`user.py`) | Code: `id, email, name, initial, created_at`. 🟡 chưa có `theme`, `preferredLanguage`, `role` |
| `OAuthAccount` | `ConnectedAccount` | 🔴 **khác tên** — xem mục D |
| `GmailAccount` | `GmailAccount` | ✅ khớp, code còn nhiều hơn hình (`watch_expiration`, `last_synced_at`) |
| `OutLookAccount` | `OutlookAccount` | ✅ có `delta_link`, `last_synced_at`. 🟡 code **chưa có** `watch_expiration` (Graph push chưa build) |
| `Subscription` | `Subscription` | Code có `is_active`, `day_key/tokens_today`, `month_key/tokens_month`. 🟡 code **chưa có** `startDate`/`endDate` |
| `Notification` | `Notification` | ✅ cột code tên `read` — trùng hình, nhưng lệch docx (xem D3) |
| `Conversation` | `Conversation` | Code: cột tên `pinned` (hình/docx ghi `isPinned`/`is_pinned`) |
| `ConfirmationRequest` | `ConfirmationRequest` | Có `approve()`/`reject()` ✅. Nhưng quan hệ khác hẳn — xem B4 |
| `Email` | `StoredEmail` (`email_store.py`) | Khác tên. Code có nhiều cột hơn hẳn (`ai_tldr`, `starred`, `folder`, `sender_initial`…) |
| `AuditLog` | `AuditLog` | Quan hệ khác — xem B4 |

## B2. 🟡 Lớp trên hình mà code CHƯA có bảng (7) — đây là thiết kế đích

| Lớp | Code hiện đang làm gì thay thế |
| :---- | :---- |
| `Message` | Lưu dạng JSON trong `Conversation.agent_messages` / `display_messages`, chưa tách bảng |
| `ToolCall` | Chưa có bảng. Lời gọi tool ghi vào `AuditLog.tool_name` |
| `EmailDraft` | Chưa có bảng |
| `EmailThread` | Chưa có bảng — `StoredEmail.thread_id` chỉ là chuỗi |
| `Attachment` | Chưa có bảng — `StoredEmail.attachments_json` |
| `Tool` | ✅ **đúng như thiết kế** — §1.3.6 đã nói rõ không lưu xuống DB |
| `Skill` + 3 lớp con | Không phải class Python — là file `.md` trong `library/`, do `skill_loader` nạp. 🟡 Vẽ thành lớp UML thì hơi khác thực tế, nhưng ở mức thiết kế chấp nhận được |

Bảy dòng này **không phải lỗi tài liệu**. Chỉ cần biết: nếu demo mà thầy hỏi "cho xem bảng
`message`" thì hiện chưa có.

## B3. 🟡 Có trong code nhưng KHÔNG có trên hình và cũng không có trong §1.5

Ba bảng này đang chạy thật mà thiết kế không nhắc tới chỗ nào:

| Model | Việc nó làm | Vấn đề |
| :---- | :---- | :---- |
| `AuthSession` (`session.py`) | Phiên đăng nhập: `token`, `user_id`, `expires_at`, + token Google | **§1.5 không có bảng nào cho phiên đăng nhập.** Thiết kế hiện không trả lời được câu "đăng nhập xong lưu ở đâu" |
| `SessionProvider` | Phiên này đăng nhập bằng nhà cung cấp nào | Đi kèm cái trên |
| `MailboxSync` (`email_store.py`) | `history_id`, `delta_link`, `watch_expiration`, `last_synced_at` | **Trùng chức năng** với `GmailAccount` + `OutlookAccount` mới thêm. Hai chỗ cùng giữ một loại dữ liệu → sẽ lệch nhau |

`AuthSession` là chỗ đáng xử lý nhất: hoặc thêm bảng `Session` vào §1.5, hoặc viết một câu
nói rõ phiên đăng nhập là JWT không lưu trạng thái. Hiện tại thiết kế đang bỏ trống.

## B4. 🟡 Ba chỗ code đi khác hướng đã chốt trong thiết kế

Đây là phần đáng chú ý nhất — không phải "code chưa làm", mà là "code đã làm **theo cách khác**".

**1. `ConfirmationRequest` nối vào Conversation, không nối vào ToolCall**

- Thiết kế (§1.5.23 + hình 3): khoá chính **là** `tool_call_id`, vừa PK vừa FK. Cách này
  cấm được về mặt cấu trúc chuyện một tool call có hai phiếu xác nhận.
- Code: `id` riêng + `user_id` + `conversation_id`, không có `tool_call_id`.

**2. `AuditLog` cũng vậy**

- Thiết kế (§1.5.14): `tool_call_id UUID NOT NULL UNIQUE`.
- Code: `conversation_id` + `tool_name` + `affected_email_ids` + `status`.

Nhân tiện — code có cột **`status`** (ghi thành công/thất bại) mà **§1.5.14 không có**.
Cột này có ý nghĩa thật. Nên thêm vào §1.5.14.

**3. `Subscription` trong code không có `start_date` / `end_date`**

Cả hình lẫn §1.5.7 đều có hai cột này; code chỉ có `is_active`. Nếu để nguyên thì lúc demo
không trả lời được "gói này hết hạn khi nào".

---

# C. Hai hình §1.1 — so với BẢNG trong docx

§1.1 gần như không đụng tới bảng, nên chỉ có hai chỗ:

| # | Trong hình | Trong docx | |
| :---- | :---- | :---- | :---- |
| 1 | Ô PostgreSQL ghi `OAuth Account` | §1.5.3 `Connected_Account`, hình §2 `CONNECTED_ACCOUNT` | 🔴 |
| 2 | Ô PostgreSQL ghi `User, Conversation, OAuth Account, Audit log, Embeddings, …` | §1.5 có 25 bảng | ✅ có dấu `…` nên không sai |

Một chỗ **nhất quán tốt**, nên giữ: hình 1 có khối *Public MCP Server (for Agent)*, và §1.5.24
có bảng `MCP_Credential` — hai chỗ khớp nhau. Đây cũng là lý do nên thêm lớp `MCPCredential`
vào hình 3, vì hiện chỉ có hình 3 là không kể câu chuyện MCP.

---

# D. Hình 3 (§1.2) — so với BẢNG trong docx

## 🔴 D1. Bốn chỗ mâu thuẫn thẳng với docx — phải sửa

| # | Hình đang ghi | Docx ghi | |
| :---- | :---- | :---- | :---- |
| 1 | `OAuthAccount` | `Connected_Account` (§1.5.3) — và hình §2 cũng vậy | Một thực thể mang hai tên ở ba hình |
| 2 | `EmailDraft.recipientAddress` | §1.3.10 đã đổi thành `recipients`, §1.5.21 có bảng `Email_Draft_Recipient` | **§1.2 và §1.3 nói ngược nhau trong cùng tài liệu** |
| 3 | `Attachment.storageRef` | §1.5.13 `storage_key`, và có thêm `sha256` | Hình thiếu `sha256` |
| 4 | `Email.recipient` (số ít) | §1.5.11 có bảng `Email_Recipient` (nhiều người nhận) | |

## 🔴 D2. Enum `EmailCategory` — lỗi nặng nhất

Hình liệt kê: `Spam, School, Career, System, SocialNetwork, Personal, Personal`

`Personal` **xuất hiện hai lần**. Enum không thể có hai giá trị trùng tên — đây là lỗi thật,
không phải thẩm mỹ.

Đối chiếu code (`app/core/labeling.py`) có đúng 7 nhãn:

| Code | Nhãn hiển thị | Trên hình |
| :---- | :---- | :---- |
| `hoc_tap` | Học tập | ✅ `School` |
| `cong_viec` | Công việc | ✅ `Career` |
| `he_thong` | Cập nhật & Hệ thống | ✅ `System` |
| `ca_nhan` | Cá nhân | ✅ `Personal` |
| `mang_xh` | Mạng xã hội | ✅ `SocialNetwork` |
| `mua_sam` | Mua sắm & Ưu đãi | 🔵 **thiếu** → thêm `Shopping` |
| `tai_chinh` | Tài chính | 🔵 **thiếu** → thêm `Finance` |
| — | *(không tồn tại)* | 🔵 `Spam` → **xoá** |

Sửa thành: `School, Career, System, Personal, SocialNetwork, Shopping, Finance`

## D3. Một chỗ ngược lại — docx mới là chỗ lệch

`Notification`: hình ghi `read`, **code cũng ghi `read`**, chỉ có §1.5.8 ghi `is_read`.
Tức là 2 chọi 1, và chỗ lệch là docx.

Dù vậy vẫn nên thống nhất về **`is_read`**, vì `Email` đã dùng `is_read` ở cả code lẫn docx —
để `read` thì riêng `Notification` lạc loài. Đổi thì tốn một migration nhỏ. Ưu tiên thấp.

## D4. Thiếu thuộc tính so với §1.5 (không mâu thuẫn, chỉ thiếu)

| Lớp | Thiếu | §1.5 |
| :---- | :---- | :---- |
| `User` | `role` | 1.5.1 |
| `Subscription` | `amount`, `currency`, `tokensToday`, `tokensMonth` | 1.5.7 |
| `Conversation` | `isPinned` | 1.5.17 |
| `Message` | `messageSeq`, `tokenUsage` | 1.5.18 |
| `ToolCall` | `callSeq` | 1.5.19 |
| `AuditLog` | `endpoint`, `httpStatus` | 1.5.14 |
| `GmailAccount` / `OutlookAccount` | `watchExpiration`, `lastSyncedAt` | 1.5.5 / 1.5.6 |
| *(quan hệ)* | `ConnectedAccount 1 — n EmailThread` | 1.5.9 có `account_id FK NOT NULL` |

## D5. Bốn bảng trong §1.5 không có lớp trên hình

`PlanCatalog` (1.5.22) · `MCPCredential` (1.5.24) · `Embeddings` (1.5.15) · `UserPreference` (1.5.2)

Hai cái đầu nên thêm — lý do đã nói ở mục C và ở
[GUI-BAN-SUA-DESIGN.md](GUI-BAN-SUA-DESIGN.md) mục 3.3. Hai cái sau tuỳ.

Chiều ngược lại thì sạch: **cả 10 lớp được đặc tả ở §1.3 đều có mặt trên hình 3** — không
lớp nào bị bỏ sót.

---

# E. Tóm lại — phải sửa gì trên hình

Chỉ 🔴 và 🔵 mới bắt buộc. 🟡 là chuyện code, không đụng tới tài liệu.

**Hình 1 (§1.1 chi tiết)** — 5 chỗ
1. 🔵 Tool Registry: thay bằng 9 tên tool có thật (A2.1)
2. 🔵 Skill Repository: thay bằng 4 nhóm có thật (A2.2)
3. 🔵 `MCP Client Adapters` → `Provider Adapters` (A2.3)
4. 🔴 `OAuth Account` → `Connected Account` (C1)
5. 🟡→nên thêm: `Mailbox Sync Service`, `Embedding Service`; kéo Gemini về Agent Layer (A2.5, A2.6)

**Hình 2 (§1.1 cây phân rã)** — kéo theo hình 1, cộng thêm mục thiếu `Attachment Processing Service`

**Hình 3 (§1.2 class)** — 6 chỗ
1. 🔴 `OAuthAccount` → `ConnectedAccount`, `OutLookAccount` → `OutlookAccount`
2. 🔴 Enum `EmailCategory`: bỏ `Spam` + `Personal` trùng, thêm `Shopping` + `Finance`
3. 🔴 `EmailDraft.recipientAddress` → `recipients`
4. 🔴 `Attachment.storageRef` → `storageKey`, thêm `sha256`
5. 🔴 `Email.recipient` → `recipients`
6. Thêm thuộc tính thiếu (D4) + hai lớp `PlanCatalog`, `MCPCredential` (D5)

**Cần sửa trong §1.5 (docx), không phải trên hình:**
- §1.5.14 `Auditlog` thêm cột **`status`** — code có, ghi thành công/thất bại (B4)
- Quyết định chỗ lưu phiên đăng nhập: thêm bảng `Session`, hoặc ghi rõ dùng JWT (B3)
