# PA2 Design — phần còn phải sửa

> **Tóm tắt:** phần chữ §1.3 và §1.5 đã xong, không cần đụng nữa. Vấn đề nằm ở **4 cái hình**:
>
> | Hình | Ở mục | Tình trạng |
> | :---- | :---- | :---- |
> | Architecture (chi tiết) | §1.1 | Sai số thứ tự, sai một thuật ngữ khá nặng, danh sách tool/skill không khớp code |
> | Architecture (cây phân rã) | §1.1 | Lệch với hình trên nó |
> | Class Diagram | §1.2 | Lệch nhiều so với §1.3 và §1.5 — có 1 lỗi enum trùng giá trị |
> | Data Diagram | §1.4 | Vẫn là schema cũ, phải vẽ lại (có sẵn nguồn ở mục 4.5) |
> | Conceptual Model | §2 | Gần xong, còn 4 chỗ |
>
> Thứ tự ưu tiên nếu ít thời gian: **mục 3.1 → 4 → 2.1 → 5**.

---

## 0. Đã dò lại — không cần sửa gì nữa

Mình dò nguyên `Group 7_Design.docx` bản mới nhất. Phần chữ đã đúng hết:

| Kiểm tra | Kết quả |
| :---- | :---- |
| Đủ 25 bảng ở §1.5 | ✅ đủ |
| Số hiệu chạy liền `1.5.1` → `1.5.25`, không trùng, không nhảy cóc | ✅ đúng |
| Bảng `Tool` đã xoá khỏi §1.5 | ✅ đã xoá |
| §1.3.6 lớp `Tool` đã có câu giải thích vì sao không có bảng | ✅ có |
| camelCase sót lại (`mailboxScopeDays`, `aiTaskStatus`, `storage_ref`, `embedding_seq`, `email_seq`, `attachment_seq`) | ✅ sạch, 0 kết quả |
| `recipientAddress` trong §1.5 | ✅ chỉ còn 1 chỗ — trong **mô tả** của `Email_Draft_Recipient`, chỗ này đúng |
| `"draft"` ở §1.3.10 | ✅ đã đổi hết sang `pending` |
| Tham chiếu chéo `§1.5.23` ở §1.3.5 | ✅ đúng — `Confirmation_Request` đang ở 1.5.23 |
| Dấu `**` sót từ markdown | ✅ 0 kết quả |
| Cột mới: `token_expiry`, `sha256`, `storage_key`, `tokens_today`, `plan_catalog_id`, `vector(768)`, `source_attachment_id`, `call_seq` | ✅ có đủ |

Bạn đánh số §1.5 khác thứ tự mình đề nghị lúc đầu, nhưng **bản của bạn hợp lý hơn** (gom
`Connected_Account_Scope` lên ngay sau `Connected_Account`). Giữ nguyên. Từ đây mọi tham
chiếu theo dãy này:

```
1.5.1  User                  1.5.10 Email               1.5.19 Tool_call
1.5.2  User_Preference       1.5.11 Email_Recipient     1.5.20 Email_Draft
1.5.3  Connected_Account     1.5.12 Email_Label         1.5.21 Email_Draft_Recipient
1.5.4  Connected_Account_    1.5.13 Attachment          1.5.22 Plan_Catalog
       Scope                 1.5.14 Auditlog            1.5.23 Confirmation_Request
1.5.5  Gmail_Account         1.5.15 Embeddings          1.5.24 MCP_Credential
1.5.6  Outlook_Account       1.5.16 Tool_Call_Email     1.5.25 MCP_Credential_Scope
1.5.7  Subscription          1.5.17 Conversation
1.5.8  Notification          1.5.18 Message
1.5.9  Email_Thread
```

---

## 1. §1.1 Architecture Diagram — hình chi tiết (hình 1)

### 1.1 Nhảy mất số 2.3

Các khối trong Core System đang đánh: **2.1** Entry Points → **2.2** Agent Layer → **2.4**
Capability Layer → **2.5** Application Layer. Không có 2.3. Người chấm nhìn vào sẽ tưởng
thiếu một khối.

Đổi lại: `2.4 Capability Layer` → **2.3**, `2.5 Application Layer` → **2.4**.

### 1.2 "MCP Client Adapters" — chỗ này nên sửa nhất

Khối Integration Layer đang ghi *"MCP Client Adapters: Gmail Adapter, Outlook Adapter"*.

Gmail API và Microsoft Graph API là **REST API bình thường, không phải MCP server**. Không
có gì ở đó nói giao thức MCP cả, nên hai adapter này không phải "MCP client". Trong khi đó
MCP thật thì nằm ở bên trái — khối *Public MCP Server (for Agent)*, chỗ Claude Desktop nối
vào.

Ghi MCP ở cả hai chỗ nghĩa là MeoArc vừa là MCP server vừa là MCP client, mà code không hề
làm vậy. Thầy nào biết MCP sẽ hỏi ngay câu này khi bảo vệ.

Sửa nhãn thành: **`Provider Adapters`** (hoặc `Integration Adapters`). Bỏ chữ MCP đi.
Sửa cả ở hình 2 nữa — chỗ đó cũng ghi y hệt.

### 1.3 Gemini API đang nằm sau adapter hộp thư

Mũi tên đang là: `Integration Layer (Gmail Adapter, Outlook Adapter)` → `External Services
(Gmail API, Microsoft Graph API, Gemini API)`. Nhưng Gemini không được gọi qua adapter hộp
thư — nó được gọi từ **Agent Layer** (LLM Reasoning Loop), là chuyện hoàn toàn khác.

Chọn một trong hai cách:
- Kéo một mũi tên riêng từ **2.2 Agent Layer** thẳng sang `Gemini API`, hoặc
- Thêm `LLM Adapter` vào khối Integration Layer bên cạnh hai adapter kia.

### 1.4 Tool Registry — 8 tên trong hình, code có 9 tên khác

Hình đang liệt kê: Search Email Tool, Read Email Tool, Draft Email Tool, Send Email Tool,
Reply Email Tool, Semantic Search Tool, Extract Tasks Tool, Request Confirmation Tool.

Code thật (`app/tools/email_tools.py`) có đúng 9 tool:

```
search_emails       categorize_emails   semantic_search
get_email           list_labels         send_email
reply_email         apply_labels        bulk_action
```

Đối chiếu:

| Trong hình | Thực tế |
| :---- | :---- |
| Search Email Tool | ✅ = `search_emails` |
| Read Email Tool | ✅ = `get_email` (đổi tên cho khớp) |
| Send Email Tool | ✅ = `send_email` |
| Reply Email Tool | ✅ = `reply_email` |
| Semantic Search Tool | ✅ = `semantic_search` |
| Draft Email Tool | ❌ không có tool này |
| Extract Tasks Tool | ❌ không có tool này |
| Request Confirmation Tool | ❌ **không phải tool** — xác nhận là cái *registry tự áp* lên mọi tool thuộc nhóm `WRITE_DESTRUCTIVE`, không phải một tool để LLM gọi |
| *(thiếu)* | `categorize_emails`, `list_labels`, `apply_labels`, `bulk_action` |

Thay danh sách trong hình bằng đúng 9 tên trên. Nếu muốn gọn thì gom theo nhóm quyền —
cách này còn hay hơn vì nó cho thấy cơ chế chặn:

```
Tool Registry
  READ:               search_emails, get_email, list_labels,
                      semantic_search, categorize_emails
  WRITE_REVERSIBLE:   apply_labels
  WRITE_DESTRUCTIVE:  send_email, reply_email, bulk_action
                      (bắt buộc qua bước xác nhận của người dùng)
```

### 1.5 Skill Repository — cũng không khớp code

Hình đang ghi: Daily Summary, Inbox Cleanup, Draft Reply, Task Extraction, Email Writing
Guide, Gmail/Outlook Best Practices.

Code thật (`app/agent/skills/library/`) có 11 file, chia 4 nhóm:

```
domain/     academic_email, client_comms, job_application
provider/   gmail_quirks
workflows/  daily_digest, email_triage, meeting_prep
writing/    email_structure, tone_guide, language_vi, reply_etiquette
```

Ghi theo 4 nhóm này gọn hơn và đúng hơn. Quan trọng hơn: **hình 3 (class diagram) đang vẽ
`DailyDigestSkill`, `TriageSkill`, `MeetingPrepSkill`** — ba cái đó khớp thư mục `workflows/`,
tức là hình 3 đang đúng còn hình 1 đang bịa tên. Hai hình trong cùng tài liệu nói hai danh
sách khác nhau là chỗ dễ bị bắt.

### 1.6 Hai chữ nhỏ

- Khối PostgreSQL ghi `OAuth Account` → đổi thành **`Connected Account`** cho khớp §1.5.3
  và hình §2. (Xem thêm mục 3.1 — cùng một cái tên này sai ở cả 3 hình.)
- `- ect...` trong Application Layer → **`- etc.`**

---

## 2. §1.1 Architecture Diagram — cây phân rã (hình 2)

### 2.1 Lệch với hình 1: thiếu một service

Application Layer trong **hình 1** liệt kê 7 mục:
Authentication, Conversation, Email, Notification, Audit Log, Confirmation, **Attachment
Processing**.

Trong **hình 2** chỉ có 6 — thiếu **Attachment Processing Service**.

Hai hình cùng mô tả một hệ thống, đặt cạnh nhau trong cùng mục §1.1, mà danh sách khác
nhau. Thêm `Attachment Processing Service` vào hình 2.

### 2.2 Kéo theo từ hình 1

Ba chỗ sau sửa ở hình 1 thì phải sửa luôn ở hình 2:
- `MCP Client Adapters` → `Provider Adapters` (mục 1.2)
- Danh sách Capability Layer nếu có ghi tên tool/skill (mục 1.4, 1.5)
- Gemini API nối từ đâu (mục 1.3)

### 2.3 Nhãn "Persistent Layer"

Nhãn này đang trùm lên cả PostgreSQL **và** Redis Cache. Redis là bộ nhớ đệm — mất dữ liệu
trong Redis thì hệ thống vẫn chạy, mất PostgreSQL thì không. Gọi chung là "Persistent" hơi
sai. Đổi thành **`Data Layer`**, hoặc tách nhãn: PostgreSQL = *Persistent*, Redis = *Cache*.

Chỗ này nhỏ, không sửa cũng không sao.

---

## 3. §1.2 Class Diagram (hình 3) — chỗ lệch nhiều nhất

### 3.1 PHẢI SỬA — đang mâu thuẫn với chính tài liệu

**a) `OAuthAccount` phải đổi thành `ConnectedAccount`**

§1.5.3 gọi là `Connected_Account`. Hình §2 gọi là `CONNECTED_ACCOUNT`. Chỉ hình class này
còn gọi `OAuthAccount`. Đổi cả tên lớp cha.

Tiện thể: lớp con đang ghi **`OutLookAccount`** (chữ L hoa giữa từ) → **`OutlookAccount`**.
Lớp `GmailAccount` bên cạnh viết đúng nên nhìn vào thấy ngay hai kiểu.

*(Cùng cái tên này còn sai ở hình 1 — xem mục 1.6.)*

**b) Enum `EmailCategory` có `Personal` hai lần**

Hình đang liệt kê: `Spam, School, Career, System, SocialNetwork, Personal, Personal`.

Giá trị `Personal` xuất hiện **hai lần** — enum không thể có hai giá trị trùng tên, đây là
lỗi thật chứ không phải chuyện thẩm mỹ.

Taxonomy thật trong code (`app/core/labeling.py`) có đúng 7 nhãn:

| Code | Nhãn hiển thị | Tên enum nên dùng |
| :---- | :---- | :---- |
| `hoc_tap` | Học tập | `School` ✅ đã có |
| `cong_viec` | Công việc | `Career` ✅ đã có |
| `he_thong` | Cập nhật & Hệ thống | `System` ✅ đã có |
| `ca_nhan` | Cá nhân | `Personal` ✅ đã có |
| `mang_xh` | Mạng xã hội | `SocialNetwork` ✅ đã có |
| `mua_sam` | Mua sắm & Ưu đãi | `Shopping` ❌ **thiếu** |
| `tai_chinh` | Tài chính | `Finance` ❌ **thiếu** |

Còn `Spam` thì **code không có nhãn này**.

→ Sửa: bỏ `Spam`, bỏ `Personal` thừa, thêm `Shopping` và `Finance`. Enum thành đúng 7:

```
School, Career, System, Personal, SocialNetwork, Shopping, Finance
```

**c) `EmailDraft.recipientAddress` → `recipients`**

Phần chữ §1.3.10 đã sửa rồi (giờ là `recipients`, kiểu nhiều người nhận, có to/cc/bcc),
§1.5.21 cũng đã có bảng `Email_Draft_Recipient`. Chỉ còn hình này giữ `recipientAddress`.
Tức là §1.2 và §1.3 trong cùng một tài liệu đang nói ngược nhau.

Đổi `+string recipientAddress` → `+string[] recipients`.

**d) `Attachment.storageRef` → `storageKey`, và thiếu `sha256`**

§1.5.13 đã đổi tên cột thành `storage_key` và thêm `sha256 CHAR(64) NOT NULL`. Hình còn
`storageRef` và không có `sha256`.

**e) `Email.recipient` (số ít) → `recipients`**

§1.5.11 có bảng `Email_Recipient` vì một email có nhiều người nhận. Hình đang để
`+string recipient` số ít. Đổi thành `+string[] recipients`.

Tiện thể: hình ghi `externalMessageId`, §1.5.10 ghi `provider_message_id`. Chọn một tên
rồi dùng thống nhất (mình nghiêng về `providerMessageId` vì cả tài liệu đang dùng tiền tố
`provider_*`: `provider_thread_id`, `provider_attachment_id`, `provider_user_id`).

### 3.2 NÊN SỬA — thiếu thuộc tính so với §1.5

Mấy chỗ này không mâu thuẫn, chỉ là hình vẽ ít hơn bảng. Nhưng nếu người chấm dò chéo
§1.2 với §1.5 thì sẽ thấy trống.

| Lớp | Đang thiếu | Ở §1.5 |
| :---- | :---- | :---- |
| `User` | `role` | 1.5.1 |
| `Subscription` | `amount`, `currency`, `tokensToday`, `tokensMonth` | 1.5.7 |
| `Notification` | đang là `read` → đổi thành `isRead` | 1.5.8 |
| `Conversation` | `isPinned` | 1.5.17 |
| `Message` | `messageSeq`, `tokenUsage` | 1.5.18 |
| `ToolCall` | `callSeq` | 1.5.19 |
| `AuditLog` | `endpoint`, `httpStatus` | 1.5.14 |
| `GmailAccount` | `watchExpiration`, `lastSyncedAt` | 1.5.5 |
| `OutlookAccount` | `watchExpiration`, `lastSyncedAt` | 1.5.6 |

Thêm một quan hệ còn thiếu: §1.5.9 có `email_thread.account_id FK NOT NULL`, tức là mỗi
luồng thư thuộc về một tài khoản đã kết nối. Trên hình `EmailThread` chỉ nối với `Email`,
không nối lên `ConnectedAccount`. Thêm liên kết **`ConnectedAccount 1 —— n EmailThread`**.

### 3.3 Thiếu lớp — cân nhắc thêm 2, còn 2 thì tuỳ

Bốn bảng trong §1.5 không có lớp tương ứng trên hình:

**Nên thêm** — vì hai cái này chính là điểm khác biệt của MeoArc, thiếu thì hình không kể
được câu chuyện:

- **`PlanCatalog`** (§1.5.22) — `Subscription.planCatalogId` trỏ tới nó. Đang có FK mà
  không có lớp thì quan hệ treo lơ lửng.
- **`MCPCredential`** (§1.5.24) — đây là đường vào của agent ngoài. §1.5.19 nói rõ một
  `tool_call` đến từ **đúng một trong hai** đường: `message_id` (chat trong app) hoặc
  `mcp_credential_id` (MCP). Hình hiện chỉ vẽ đường thứ nhất (`Message 1 → n ToolCall`).
  Thêm `MCPCredential 1 → n ToolCall` là hình mới nói đủ. Mà đây đúng là chỗ hình 1 đang
  khoe khối *Public MCP Server*, nên hai hình đang không ăn khớp nhau.

**Tuỳ** — lớp không nhất thiết phải ánh xạ 1-1 với bảng, nên thiếu cũng có thể biện luận được:

- `Embeddings` (§1.5.15) — hiện đang thể hiện gián tiếp qua `Email.getVectorEmbedding(): vector`.
  Nếu muốn đủ thì thêm lớp, còn không thì thôi.
- `UserPreference` (§1.5.2) — hình đang để `theme` và `preferredLanguage` nằm thẳng trong
  `User` cùng `updatePreferences()`. §1.5 tách ra bảng riêng. Ở mức lớp thì gộp vào `User`
  vẫn hợp lý, nhưng nếu bị hỏi thì phải giải thích được là "tách bảng vì lý do lưu trữ, ở
  mức thiết kế lớp vẫn là một khái niệm".

### 3.4 Một chỗ vụn

Lớp `Tool` vẫn nằm trên hình — **đúng, giữ nguyên**, §1.3.6 đã có câu giải thích nó không
được lưu xuống database. Nếu muốn rõ hơn thì thêm stereotype `<<not persisted>>` phía trên
tên lớp. Không bắt buộc.

---

## 4. §1.4 Data Diagram (hình 4) — phải vẽ lại

### 4.1 Vấn đề

Hình này **chưa được cập nhật lần nào** — vẫn là schema cũ 18 bảng, trong khi §1.5 ngay
bên dưới đã là 25 bảng. Hai mục cạnh nhau trong cùng tài liệu đang mô tả hai database khác
nhau.

### 4.2 Phải bỏ khỏi hình (3 thứ)

| Bỏ | Vì sao |
| :---- | :---- |
| Nguyên bảng `TOOL` | Đã xoá khỏi §1.5 |
| Cột `TOOLCALL.tool_id` (FK sang TOOL) | Đi theo bảng vừa xoá. §1.5.19 chỉ còn `tool_name` |
| Cột `EMAIL.email_seq` | Đã bỏ, không còn trong §1.5.10 |

### 4.3 Phải thêm vào hình (8 bảng)

| Bảng | Ở §1.5 | Vai trò |
| :---- | :---- | :---- |
| `PLAN_CATALOG` | 1.5.22 | Bảng giá các gói |
| `USER_PREFERENCE` | 1.5.2 | Tách `theme` / `language` ra khỏi USER |
| `CONNECTED_ACCOUNT_SCOPE` | 1.5.4 | Thay cột `scopes string[]` |
| `EMAIL_RECIPIENT` | 1.5.11 | Thay cột `recipients string[]` |
| `EMAIL_LABEL` | 1.5.12 | Thay cột `provider_labels string[]` |
| `EMAIL_DRAFT_RECIPIENT` | 1.5.21 | Thay cột `recipientAddress` |
| `MCP_CREDENTIAL` | 1.5.24 | Đường vào của agent ngoài |
| `MCP_CREDENTIAL_SCOPE` | 1.5.25 | Quyền của credential đó |

5 bảng ở giữa **thay thế** các cột kiểu mảng đang có, không phải thêm vào bên cạnh. Sửa
xong thì cột `string_array` phải biến mất, nếu không là lưu trùng ở hai nơi.

### 4.4 Phải đổi tên (camelCase → snake_case)

| Bảng | Đang là | Sửa thành |
| :---- | :---- | :---- |
| EMAIL | `receivedAt` | `received_at` |
| EMAIL | `bodySnippet` | `body_snippet` |
| EMAIL | `bodyText` | `body_text` |
| EMAIL | `isRead` | `is_read` |
| EMAIL | `aiCategory` | `ai_category` |
| EMAIL | `aiPriority` | `ai_priority` |
| EMAIL | `aiTaskStatus` | `ai_task_status` |
| TOOLCALL | `toolName` | `tool_name` |
| CONNECTED_ACCOUNT | `accessToken` | `access_token` |
| CONNECTED_ACCOUNT | `refreshToken` | `refresh_token` |
| SUBSCRIPTION | `mailboxScopeDays` | `mailbox_scope_days` |
| AUDITLOG | `actorType` | `actor_type` |
| EMAILDRAFT | `recipientAddress` | (xoá — thành bảng `EMAIL_DRAFT_RECIPIENT`) |

### 4.5 Cách nhanh nhất: dán nguồn này vào dbdiagram.io

Sửa tay 25 bảng thì lâu và dễ sót. Nguồn dưới đây mình sinh thẳng từ §1.5 bản mới nhất
của bạn nên khớp 100%.

**Làm thế nào:** vào `dbdiagram.io` → *New Diagram* → xoá hết ô bên trái → dán khối dưới
đây vào → hình tự sinh bên phải → *Export* → *PNG* (hoặc PDF) → chèn vào §1.4.

```dbml
Table user {
  user_id     uuid      [pk]
  username    varchar   [not null]
  email       varchar   [unique, not null]
  role        varchar   [not null, default: 'user']
  created_at  timestamp [not null]
}

Table user_preference {
  user_id            uuid      [pk, ref: - user.user_id]
  language           varchar   [not null, default: 'vi']
  display_name       varchar
  theme              varchar   [default: 'system']
  tone_preference    varchar
  signature_note     text
  custom_instruction text
  updated_at         timestamp [not null]
}

Table connected_account {
  account_id       uuid        [pk]
  user_id          uuid        [not null, ref: > user.user_id]
  provider         varchar     [not null, note: 'google | microsoft']
  provider_user_id varchar     [not null]
  email_address    varchar     [not null]
  status           varchar     [not null, note: 'active | revoked | error']
  access_token     text        [note: 'encrypted']
  refresh_token    text        [null, note: 'encrypted']
  token_expiry     timestamptz [null]
  created_at       timestamptz [not null]
  updated_at       timestamptz [not null]

  indexes {
    (provider, provider_user_id) [unique]
  }
}

Table connected_account_scope {
  account_id uuid    [pk, ref: > connected_account.account_id]
  scope      varchar [pk]
}

Table gmail_account {
  account_id       uuid        [pk, ref: - connected_account.account_id]
  history_id       varchar     [null]
  watch_expiration timestamptz [null]
  last_synced_at   timestamptz [null]
}

Table outlook_account {
  account_id       uuid        [pk, ref: - connected_account.account_id]
  delta_link       text        [null]
  watch_expiration timestamptz [null]
  last_synced_at   timestamptz [null]
}

Table plan_catalog {
  plan_catalog_id    uuid            [pk]
  tier               varchar         [not null]
  price              "numeric(12,2)" [not null]
  currency           "char(3)"       [not null, default: 'VND']
  mailbox_scope_days integer         [not null]
  effective_from     timestamptz     [not null]
  effective_to       timestamptz     [null]
  created_by         uuid            [null, ref: > user.user_id]
  created_at         timestamptz     [not null]
}

Table subscription {
  subscription_id    uuid            [pk]
  user_id            uuid            [not null, ref: > user.user_id]
  tier               varchar         [not null]
  mailbox_scope_days integer         [not null]
  amount             "numeric(12,2)" [not null]
  currency           "char(3)"       [not null, default: 'VND']
  plan_catalog_id    uuid            [null, ref: > plan_catalog.plan_catalog_id]
  start_date         timestamptz     [not null]
  end_date           timestamptz     [null]
  day_key            varchar         [not null]
  tokens_today       integer         [not null, default: 0]
  month_key          varchar         [not null]
  tokens_month       integer         [not null, default: 0]
  created_at         timestamptz     [not null]
  updated_at         timestamptz     [not null]
}

Table notification {
  notification_id uuid        [pk]
  user_id         uuid        [ref: > user.user_id]
  type            varchar     [not null]
  message         varchar     [not null]
  is_read         boolean     [default: false]
  created_at      timestamptz [not null]
  updated_at      timestamptz [not null]
}

Table email_thread {
  thread_id          uuid      [pk]
  account_id         uuid      [not null, ref: > connected_account.account_id]
  subject            varchar
  provider_thread_id varchar   [not null]
  created_at         timestamp [not null]
}

Table email {
  email_id            uuid        [pk]
  thread_id           uuid        [not null, ref: > email_thread.thread_id]
  provider_message_id varchar     [not null]
  sender              varchar     [not null]
  subject             varchar
  body_snippet        varchar
  body_text           text
  is_read             boolean     [default: false]
  ai_category         varchar
  ai_priority         varchar
  ai_task_status      varchar
  has_attachment      boolean     [default: false]
  received_at         timestamp   [not null]
  created_at          timestamp   [not null]
  updated_at          timestamptz [not null]
}

Table email_recipient {
  email_id          uuid    [pk, ref: > email.email_id]
  recipient_address varchar [pk]
}

Table email_label {
  email_id uuid    [pk, ref: > email.email_id]
  label    varchar [pk]
}

Table attachment {
  email_id               uuid       [pk, ref: > email.email_id]
  provider_attachment_id varchar    [pk]
  filename               varchar    [not null]
  size_bytes             bigint     [null]
  type                   varchar    [null]
  storage_key            text       [not null]
  sha256                 "char(64)" [not null]
  extracted_text         text       [null]
}

Table embeddings {
  embedding_id         uuid          [pk]
  email_id             uuid          [not null, ref: > email.email_id]
  source_attachment_id varchar       [null]
  chunk_type           varchar       [not null]
  chunk_index          integer       [not null]
  chunk_text           text          [null]
  vector               "vector(768)" [not null]
  dimension            integer       [not null]
  model_name           varchar       [not null]

  indexes {
    (email_id, chunk_index) [unique]
  }
}

Table conversation {
  conversation_id uuid      [pk]
  user_id         uuid      [ref: > user.user_id]
  title           varchar
  is_pinned       boolean   [default: false]
  created_at      timestamp [not null]
  updated_at      timestamp [not null]
}

Table message {
  message_id      uuid      [pk]
  conversation_id uuid      [ref: > conversation.conversation_id]
  role            varchar   [not null, note: 'user | assistant | system']
  content         text      [not null]
  message_seq     integer
  token_usage     json
  created_at      timestamp [not null]
}

Table mcp_credential {
  mcp_credential_id uuid        [pk]
  user_id           uuid        [not null, ref: > user.user_id]
  encrypted_secret  text        [not null, unique]
  status            varchar     [not null]
  created_at        timestamptz [not null]
  expires_at        timestamptz [null]
}

Table mcp_credential_scope {
  mcp_credential_id uuid    [pk, ref: > mcp_credential.mcp_credential_id]
  scope             varchar [pk]
}

Table tool_call {
  toolcall_id       uuid        [pk]
  message_id        uuid        [null, ref: > message.message_id]
  mcp_credential_id uuid        [null, ref: > mcp_credential.mcp_credential_id]
  tool_name         varchar     [not null]
  status            varchar     [not null, note: 'pending | running | awaiting_confirmation | success | failed']
  input             jsonb       [not null]
  output            jsonb       [null]
  token_usage       integer     [null]
  call_seq          integer     [null]
  created_at        timestamptz [not null]
}

Table tool_call_email {
  toolcall_id uuid      [pk, ref: > tool_call.toolcall_id]
  email_id    uuid      [pk, ref: > email.email_id]
  created_at  timestamp [not null]
}

Table confirmation_request {
  tool_call_id uuid        [pk, ref: - tool_call.toolcall_id]
  action       varchar     [not null]
  description  text        [not null]
  status       varchar     [not null, default: 'pending']
  created_at   timestamptz [not null]
  updated_at   timestamptz [not null]
}

Table auditlog {
  log_id       uuid      [pk]
  user_id      uuid      [not null, ref: > user.user_id]
  tool_call_id uuid      [not null, unique, ref: - tool_call.toolcall_id]
  action       varchar   [not null]
  actor_type   varchar
  endpoint     varchar
  http_status  integer
  details      json
  created_at   timestamp [not null]
}

Table email_draft {
  message_id        uuid        [pk, ref: > message.message_id]
  draft_seq         integer     [pk]
  account_id        uuid        [not null, ref: > connected_account.account_id]
  reply_to_email_id uuid        [null, ref: > email.email_id]
  subject           varchar     [null]
  body              text        [null]
  status            varchar     [not null, note: 'pending | sent | discarded']
  created_at        timestamptz [not null]
  updated_at        timestamptz [not null]
}

Table email_draft_recipient {
  message_id        uuid    [pk]
  draft_seq         integer [pk]
  recipient_address varchar [pk]
  recipient_type    varchar [not null, note: 'to | cc | bcc']
}

// Khoá ngoại ghép — dbdiagram không viết được trong phần [ ] nên để riêng ở đây
Ref: email_draft_recipient.(message_id, draft_seq) > email_draft.(message_id, draft_seq)
Ref: embeddings.(email_id, source_attachment_id) > attachment.(email_id, provider_attachment_id)
```

**Hai chỗ cần biết khi dán:**

- `user` là từ khoá của PostgreSQL. dbdiagram vẫn vẽ được, nhưng khi viết SQL thật phải để
  trong nháy kép `"user"`. Không ảnh hưởng gì tới hình.
- `vector(768)` là kiểu của extension pgvector, dbdiagram không hiểu nên mình để trong nháy
  kép cho nó nhận là chuỗi. Hình vẫn hiện đúng chữ `vector(768)`.

---

## 5. §2 Conceptual Model (hình 5) — còn 4 chỗ

Hình này bạn đã sửa gần xong. Mình đối chiếu thì **6 thứ đã fix**: `SUBCRIBES` → `SUBSCRIBES`,
thêm quan hệ `LOGS` giữa AUDIT_LOG và TOOL_CALL, thêm `token_expiry` vào CONNECTED_ACCOUNT,
EMBEDDINGS bỏ `embedding_type`/`embedding_seq` chỉ còn `chunk_index`, EMAIL thêm `is_read` +
`updated_at`, CONFIRMATION_REQUEST bỏ thuộc tính `tool_call_id` thừa.

Còn 4 chỗ:

| # | Đang là | Sửa thành | Ghi chú |
| :---- | :---- | :---- | :---- |
| 1 | `PLAN_CATELOG` | `PLAN_CATALOG` | Sai chính tả. Khoá của chính nó ghi đúng là `plan_catalog_id`, nên trong cùng một ô đang có hai cách viết |
| 2 | `create_at` (PLAN_CATALOG) | `created_at` | Thiếu chữ `d`. Mọi bảng khác đều `created_at` |
| 3 | `recepients` (EMAIL) | `recipients` | Thiếu chữ `i`. EMAIL_DRAFT ngay bên cạnh ghi đúng `recipients` |
| 4 | TOOL_CALL: `tool_call_id`, `tool_name`, `status`, `input`, `output`, `token_usage`, `call_seq` | Thêm `created_at` | §1.5.19 có cột này và nó `NOT NULL` |

**Một chỗ dễ hiểu nhầm — đừng sửa:** thuộc tính `recipients` trên EMAIL vẽ bằng oval hai
viền (đa trị) là **đúng** cho sơ đồ khái niệm. Tới §1.4/§1.5 nó mới phải tách thành bảng
`EMAIL_RECIPIENT`. Hai hình ở hai mức trừu tượng khác nhau nên khác nhau là bình thường.
Chỉ sửa chính tả, đừng xoá cái oval.

---

## 6. Còn 5 đoạn hướng dẫn của template chưa xoá

Đoạn trong ngoặc vuông là chỉ dẫn của thầy, nộp bài phải bỏ. Ctrl+F theo chữ đầu, xoá cả
đoạn kể cả hai dấu ngoặc:

| Ở mục | Bắt đầu bằng |
| :---- | :---- |
| §2 Conceptual Model | `[Present a diagram illustrating the semantic entities…` |
| §1.4 Data Diagram | `[Draw the data diagram of the system…` |
| §1.5 Data Specification | `[If using a Database Management System (DBMS)…` (ngay dưới còn một đoạn nữa bắt đầu `[If using XML/JSON…` — xoá cả hai) |
| §1.6 Screen Diagram | `[Draw a screen diagram illustrating the relationships…` |
| §1.7 Screen Specifications | `[Students should select and present the specifications…` |

---

## 7. Ba chỗ vụn trong §1.5, sửa cũng được không sửa cũng không sai

1. Cột **Key/Constraint** ở §1.5.16 và §1.5.23 ghi `FK(TOOLCALL)`, tên bảng thật là
   `TOOL_CALL`. Đổi cho khớp — 3 chỗ.
2. §1.5.14 tên bảng `Auditlog`, các bảng khác đều có gạch dưới (`Email_Thread`, `Tool_call`).
   Đổi thành `Audit_Log` nếu muốn đồng nhất.
3. §1.5.16 ghi `Tool_Call_Email` (C hoa), §1.5.19 ghi `Tool_call` (c thường). Chọn một kiểu.

---

## 8. Đối chiếu với template gốc — chỗ nào được đụng, chỗ nào không

Template của thầy chỉ quy định **phải có hình gì**, không quy định **trong hình có gì**.
Nên gần như toàn bộ mục 1–7 ở trên là sửa nội dung bên trong, không đụng tới khung template.
Chỉ có ba điều cần biết:

### 8.1 ⛔ Chỗ nhìn như lỗi nhưng ĐỪNG sửa

Mục lục tài liệu đang là:

```
3  Architectural Design          4  Data Design            5  User Interface and UX Design
     1.1 Architecture Diagram         1.4 Data Diagram          1.6 Screen Diagram
     1.2 Class Diagram                1.5 Data Specification    1.7 Screen Specifications
     1.3 Class Specifications
```

Nhìn thì vô lý — sao trong mục **3** lại chứa mục **1.1**? Nhưng **đây là cách template gốc
của thầy đánh số**, mục con chạy liên tục 1.1 → 1.7 bất kể nằm dưới mục lớn nào. Đừng
"sửa" thành 3.1 / 3.2 / 4.1 / 4.2. Sửa là đang sửa template, và mọi tham chiếu chéo trong
bài (`§1.5.23`, `§1.3.10`…) hỏng theo hàng loạt.

**Chỗ dễ nhầm liên quan:** mục 1.1 ở trên bảo đổi `2.4 Capability Layer` → `2.3`. Đó là số
**in bên trong tấm ảnh kiến trúc**, không phải số mục của báo cáo. Heading §1.1 và §1.2
trong Word giữ nguyên, không đụng gì.

### 8.2 ⚠️ Mục duy nhất tạo thêm việc: 3.3 (thêm lớp vào §1.2)

§1.3 hiện đặc tả đúng **10 lớp**: User, Conversation, Message, ToolCall, ConfirmationRequest,
Tool, Skill, TriageSkill, Email, EmailDraft. Trong khi hình §1.2 vẽ khoảng 20 lớp.

Khoảng cách này **đã có sẵn từ trước**, không phải do đề xuất của mình. Nhưng nếu thêm
`PlanCatalog` và `MCPCredential` vào hình thì khoảng cách rộng thêm, nên xử lý luôn cho gọn.
Hai cách, chọn một:

- **Rẻ hơn (khuyên dùng):** thêm một câu vào đầu §1.3, kiểu:
  > *This section specifies the classes that carry the core behaviour of the system. The
  > remaining classes in the diagram are data holders whose structure is fully described in
  > the data specification (§1.5).*

  Cách này hợp lệ vì template ở §1.7 cũng cho phép "select and present a few of the most
  important screens" — cùng tinh thần chọn lọc.

- **Đầy đủ hơn:** viết thêm §1.3.11 `PlanCatalog` và §1.3.12 `MCPCredential`. Tốn thời gian
  hơn nhưng bịt hẳn câu hỏi.

Nếu không muốn làm cả hai thì **bỏ luôn mục 3.3**, giữ hình §1.2 như cũ. Mục 3.1 và 3.2 mới
là phần bắt buộc — chúng sửa mâu thuẫn nội bộ, còn 3.3 chỉ là cho đầy đủ.

### 8.3 ✅ Hai chỗ tưởng nghịch mà không nghịch

- **Xoá 5 đoạn ngoặc vuông (mục 6)** — đây là *làm đúng template hơn*, không phải nghịch.
  Mấy đoạn đó là chỉ dẫn cho sinh viên, bản nộp không được để lại.
- **Vẽ §1.4 bằng dbdiagram.io (mục 4.5)** — template không chỉ định công cụ cho §1.4, chỉ
  ghi *"Draw the data diagram of the system"*. Riêng §2 có nhắc MySQL Workbench /
  PowerDesigner, nhưng nguyên văn là *"can be created using"* — gợi ý chứ không bắt buộc.

  *Liên quan:* hình §2 hiện tại vẽ theo ký hiệu Chen (hình thoi, oval) chứ không phải EER
  của Workbench. Không sai, và thực ra còn đúng tinh thần "conceptual" hơn. Nếu bị hỏi thì
  trả lời: §2 là mức khái niệm thuần (Chen), §1.4 là mức quan hệ — hai mức khác nhau nên
  hai hình khác nhau, không phải vẽ trùng.

> *Lưu ý về căn cứ:* mình chỉ đọc được bản đã điền, không có file template trắng. Kết luận
> "template không quy định gì cho §1.1–§1.3" là suy ra từ chỗ 6 đoạn hướng dẫn còn lại đều
> thuộc §2, §1.4, §1.5, §1.6, §1.7 — không đoạn nào thuộc ba mục kia. Nếu bạn còn giữ file
> template gốc thì kiểm lại cho chắc.

---

## 9. Bảng kiểm sau khi làm xong

**Hình §1.1 (cả hai)**
- [ ] Số khối trong Core System chạy liền 2.1 → 2.4, không nhảy
- [ ] Không còn chữ `MCP` trong khối Integration Layer (đã đổi thành `Provider Adapters`)
- [ ] Gemini API nối từ Agent Layer, không nối từ adapter hộp thư
- [ ] Tool Registry ghi đúng 9 tên tool có thật
- [ ] Skill Repository ghi 4 nhóm `domain / provider / workflows / writing`
- [ ] `OAuth Account` → `Connected Account` trong khối PostgreSQL
- [ ] `ect...` → `etc.`
- [ ] Hai hình có **cùng** danh sách Application Layer (7 mục, có Attachment Processing)

**Hình §1.2 Class Diagram**
- [ ] Không còn chữ `OAuthAccount` (đã thành `ConnectedAccount`)
- [ ] `OutLookAccount` → `OutlookAccount`
- [ ] Enum `EmailCategory` có đúng 7 giá trị, **không giá trị nào trùng**, không còn `Spam`,
      đã có `Shopping` và `Finance`
- [ ] `EmailDraft` không còn `recipientAddress`
- [ ] `Attachment` có `storageKey` và `sha256`
- [ ] `Email.recipient` → `recipients`
- [ ] Có lớp `PlanCatalog` và `MCPCredential`, và `MCPCredential` có nối tới `ToolCall`
- [ ] Có liên kết `ConnectedAccount` → `EmailThread`

**Hình §1.4 Data Diagram**
- [ ] Đếm số bảng trên hình → **25**
- [ ] Không còn bảng `TOOL`
- [ ] Không còn cột nào kiểu `string_array` / `string[]`
- [ ] Không còn `receivedAt`, `aiCategory`, `accessToken`, `mailboxScopeDays`…
- [ ] Có đủ 8 bảng mới ở mục 4.3
- [ ] Tên 25 bảng khớp dãy §1.5.1 → §1.5.25 ở mục 0

**Hình §2 Conceptual Model**
- [ ] Tìm `CATELOG` → không còn
- [ ] Tìm `create_at` → không còn
- [ ] Tìm `recepients` → không còn
- [ ] TOOL_CALL có `created_at`

**Văn bản**
- [ ] Tìm `[Present`, `[Draw`, `[If using`, `[Students` → 0 kết quả
