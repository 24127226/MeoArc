# PA2 §1.5 Data Specification — phần cần sửa để khớp schema v6

> Đối chiếu giữa PA2 §1.5 hiện tại (18 bảng) và schema v6 sau 4 vòng chốt.
> Tin tốt: PA2 đã có sẵn `Connected_Account`, `EmailThread`, `Attachment`, `Embeddings`,
> `EmailDraft`, `ConfirmationRequest` — nên đây là **bản vá**, không phải viết lại.

---

## 0. Cách dán để không vỡ font

Đây là chỗ dễ hỏng nhất, làm đúng từ đầu đỡ phải sửa lại cả tài liệu.

**Luôn dán bằng `Ctrl + Shift + V`** (Paste without formatting). Dán thường sẽ mang theo
font và cỡ chữ từ nguồn, tạo ra những đoạn lệch font nằm rải rác mà sau đó rất khó dò.
Dán không định dạng thì chữ tự nhận style của đoạn đang đứng.

**Bảng thì đừng dán chữ — hãy chèn bảng thật.** Với mỗi bảng bên dưới:
1. Insert → Table, chọn **5 cột** (Seq · Attribute · Data Type · Key/Constraint · Description)
2. Copy từng ô một, hoặc gõ tay nếu ít dòng

Dán nguyên khối markdown `| … | … |` vào Docs sẽ ra một cục chữ có dấu gạch đứng, không
thành bảng.

**Sau khi dán xong, tìm ba thứ này** (`Ctrl + F`):
- Dấu sao đôi `**` → phải **0 kết quả**. Lần trước có 8 dấu lọt vào PDF.
- Dấu gạch đứng `|` → chỉ được có trong bảng thật, không nằm giữa dòng văn.
- Dấu `→` và `—` → PA2 đang dùng được, nhưng nếu thấy ô vuông thì đổi thành `->` và `-`.

---

## 1. Tóm tắt: cần làm gì

| Việc | Số lượng | Mục |
| :---- | :---- | :---- |
| Thay nội dung bảng đã có | 12 bảng | 1.5.2, 1.5.3, 1.5.4, 1.5.5, 1.5.6, 1.5.8, 1.5.9, 1.5.10, 1.5.11, 1.5.15, 1.5.17, 1.5.18 |
| Thêm bảng mới | 8 bảng | chèn sau 1.5.18 |
| Xoá bảng | 1 bảng | 1.5.16 Tool |
| Sửa mục khác | 3 chỗ | §1.3.5, bảng tổng hợp Weak Entity, bảng tổng hợp Bảng phụ trợ |

Bốn bảng **không đổi gì**, khỏi đụng tới: 1.5.7 EmailThread · 1.5.12 Toolcall_Email ·
1.5.13 Conversation · 1.5.14 Message. Bảng 1.5.1 User cũng giữ nguyên.

Tổng sau khi sửa: **25 bảng**.

---

# PHẦN A — THAY nội dung bảng đã có

## A1. `1.5.2 Connected_Account`

**Đổi gì:** bỏ cột `scopes` (tách thành bảng riêng, xem B3) · thêm `token_expiry` ·
`refresh_token` cho phép rỗng · thêm ràng buộc duy nhất theo nhà cung cấp.

Mô tả giữ nguyên. Thay bảng bằng:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | account_id | UUID | PK | Unique identifier for the connection record |
| 2 | user_id | UUID | FK (USER), NOT NULL | Reference to the owner of the account |
| 3 | provider | string | NOT NULL | Service provider (`google`, `microsoft`) — discriminator for the subtypes |
| 4 | provider_user_id | string | NOT NULL, UNIQUE (provider, provider_user_id) | The unique user ID issued by the external service. The pair with `provider` prevents the same mailbox being connected twice, which would make every sync run twice |
| 5 | email_address | string | NOT NULL | Human-readable address of the connected mailbox; used for display, the From address, and routing push notifications to the right account |
| 6 | status | string | NOT NULL | `active`, `revoked`, `error`. Revoking changes the status instead of deleting the row, so existing audit records keep something to point at |
| 7 | access_token | text | Encrypted | Short-lived token for calling the provider API |
| 8 | refresh_token | text | Encrypted, NULL | Long-lived token used to obtain a new access token. Nullable because Google and Microsoft do not always return one on re-consent; NOT NULL would force storing an empty string and lose the distinction between "never had one" and "empty" |
| 9 | token_expiry | TIMESTAMPTZ | NULL | When `access_token` expires. Without it the system cannot know when to refresh and must call, take a 401, and only then refresh |
| 10 | created_at | TIMESTAMPTZ | NOT NULL | When the account was first connected |
| 11 | updated_at | TIMESTAMPTZ | NOT NULL | Last token refresh or status change |

---

## A2. `1.5.3 Gmail_Account` và `1.5.4 Outlook_Account`

**Đổi gì:** mỗi bảng con thêm 2 cột theo dõi đồng bộ.

Gmail_Account:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | account_id | UUID | PK, FK (CONNECTED_ACCOUNT) | Inherits the parent connection |
| 2 | history_id | string | NULL | Gmail change cursor for incremental sync |
| 3 | watch_expiration | TIMESTAMPTZ | NULL | Gmail push subscriptions expire after about 7 days. Without this the renewal deadline is unknown, and one day mail silently stops arriving with no error anywhere |
| 4 | last_synced_at | TIMESTAMPTZ | NULL | Last successful sync, also shown in the UI |

Outlook_Account:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | account_id | UUID | PK, FK (CONNECTED_ACCOUNT) | Inherits the parent connection |
| 2 | delta_link | text | NULL | Microsoft Graph delta query cursor |
| 3 | last_synced_at | TIMESTAMPTZ | NULL | Last successful sync |

---

## A3. `1.5.5 Subscription`

**Đổi gì:** mỗi dòng giờ là **một kỳ đăng ký** (giữ lịch sử) · thêm số tiền và đơn vị đã
chốt tại thời điểm giao dịch · thêm bộ đếm token · thêm ràng buộc chỉ một kỳ đang chạy.

Mô tả thay bằng:

> Each row is one billing period for one user. The full history is kept so that revenue can
> be reported by month and by tier.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | subscription_id | UUID | PK | Unique identifier for the subscription period |
| 2 | user_id | UUID | FK (USER), NOT NULL | The subscriber |
| 3 | tier | string | NOT NULL | `free`, `pro`, `pro_max` |
| 4 | mailbox_scope_days | integer | NOT NULL | Maximum days of mailbox history the AI may scan (NFR-SCO-01). Snapshotted from `plan_catalog` when the period starts, not read back from it: otherwise editing the price list would silently change the scope of every existing user, including ones who paid for the old value |
| 5 | amount | NUMERIC(12,2) | NOT NULL | Amount actually charged for this period, snapshotted at transaction time rather than joined from the current price list |
| 6 | currency | CHAR(3) | NOT NULL, DEFAULT `VND` | ISO 4217 code |
| 7 | plan_catalog_id | UUID | FK (PLAN_CATALOG), NULL | Traceability only — never used to recompute revenue |
| 8 | start_date | TIMESTAMPTZ | NOT NULL | When this period began |
| 9 | end_date | TIMESTAMPTZ | NULL | NULL means this period is current |
| 10 | day_key | string | NOT NULL | Current day bucket (`YYYY-MM-DD`) for the token counter |
| 11 | tokens_today | integer | NOT NULL, DEFAULT 0 | Tokens consumed today |
| 12 | month_key | string | NOT NULL | Current month bucket (`YYYY-MM`) |
| 13 | tokens_month | integer | NOT NULL, DEFAULT 0 | Tokens consumed this month |
| 14 | created_at | TIMESTAMPTZ | NOT NULL | Record creation |
| 15 | updated_at | TIMESTAMPTZ | NOT NULL | Updated on renewal or tier change |

Thêm hai dòng ghi chú dưới bảng:

> Constraint: `CREATE UNIQUE INDEX ux_subscription_one_active_per_user ON subscription(user_id) WHERE end_date IS NULL` — prevents two concurrent active periods for one user, which a retried payment webhook could otherwise create without any error being raised.
>
> The token counters live here rather than being summed from `tool_call` at read time. Quota must be checked before every chat turn, and a `SUM` across `tool_call → message → conversation → user` on the fastest-growing table in the system would not hold up.

---

## A4. `1.5.6 Notification`

**Đổi gì:** thêm `created_at`.

Chèn thêm dòng vào cuối bảng hiện có:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| … | created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | When the notification was raised. Without it notifications cannot be ordered by time, which is essentially the only thing done with this table |

Và một dòng ghi chú:

> Index: `(user_id, created_at DESC)` — serves the notification list and the unread badge.

---

## A5. `1.5.8 Email`

**Đổi gì:** bỏ `email_seq` · thêm `updated_at`.

Bỏ dòng `email_seq` khỏi bảng, rồi thêm:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| … | updated_at | TIMESTAMPTZ | NOT NULL | Updated whenever the AI labels or the read status change |

Thêm ghi chú dưới bảng:

> Identity is `UNIQUE (thread_id, provider_message_id)`. Display order within a thread is `ORDER BY received_at ASC, provider_message_id ASC` — deterministic on its own, because `provider_message_id` is already unique within the thread. An extra sequence column was considered and dropped: assigning gap-free numbers would require locking the parent thread row on every insert, which serialises exactly the hottest path during the initial mailbox sync.

---

## A6. `1.5.9 Attachment`

**Đổi gì:** khoá chính thành tổ hợp, bỏ `id` và `attachment_seq` · thêm `sha256` ·
`storage_ref` đổi tên thành `storage_key`. Cột `extracted_text` **giữ nguyên** — nó đã có sẵn.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | email_id | UUID | PK (composite), FK (EMAIL) | The email this file is attached to |
| 2 | provider_attachment_id | string | PK (composite) | The ID assigned to the file by the provider. Together with `email_id` this is the real identity, so no surrogate key is needed |
| 3 | filename | string | NOT NULL | Name of the attached file |
| 4 | size_bytes | BIGINT | NULL | File size |
| 5 | type | string | NULL | MIME type |
| 6 | storage_key | text | NOT NULL | Logical address used to fetch the file back |
| 7 | sha256 | CHAR(64) | NOT NULL | Content hash, used to avoid storing the same file twice |
| 8 | extracted_text | text | NULL | Text extracted from the document, used as grounding for embeddings and search |

---

## A7. `1.5.11 Embeddings`

**Đổi gì:** bỏ `embedding_type` (trùng với `model_name`) · gộp `chunk_index` và
`embedding_seq` thành một · `vector` cố định số chiều · thêm `source_attachment_id`.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | embedding_id | UUID | PK | Unique identifier for the embedding record |
| 2 | email_id | UUID | FK (EMAIL), NOT NULL | The email this vector was derived from |
| 3 | source_attachment_id | string | NULL, FK (email_id, source_attachment_id) → ATTACHMENT | NULL means the chunk came from the email body; a value means it came from that attachment's extracted text |
| 4 | chunk_type | string | NOT NULL | `body`, `header`, or `attachment` — which part of the source this chunk came from |
| 5 | chunk_index | integer | NOT NULL, UNIQUE (email_id, chunk_index) | Position of the chunk within its source, and the ordering key for retrieval |
| 6 | chunk_text | text | NULL | Raw text this vector was computed from |
| 7 | vector | vector(768) | NOT NULL | The numerical array, stored via the pgvector extension |
| 8 | dimension | integer | NOT NULL | Size of the vector. Informational: the MVP fixes one model, so the column type carries a literal dimension — pgvector requires a constant at CREATE TABLE time, and an unconstrained vector cannot carry an HNSW index |
| 9 | model_name | string | NOT NULL | The embedding model used |
| 10 | created_at | TIMESTAMPTZ | NOT NULL | When the vector was generated |

Ghi chú dưới bảng:

> Index: `CREATE INDEX ON embedding USING hnsw (vector vector_cosine_ops)`. Without it every semantic search is a sequential scan of the whole table.

---

## A8. `1.5.15 Toolcall`

**Đổi gì:** bỏ `tool_id` (bảng Tool bị loại) · thêm `mcp_credential_id` và ràng buộc chỉ
một trong hai · `call_seq` cho phép rỗng · `token_usage` đổi sang số nguyên.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | tool_call_id | UUID | PK | Unique identifier for the tool call |
| 2 | message_id | UUID | FK (MESSAGE), NULL | The assistant message that triggered this call — the in-app chat path |
| 3 | mcp_credential_id | UUID | FK (MCP_CREDENTIAL), NULL | The external agent credential that triggered it — the MCP path |
| 4 | tool_name | string | NOT NULL | Technical name of the tool, e.g. `send_email` |
| 5 | status | string | NOT NULL | `pending`, `running`, `awaiting_confirmation`, `success`, `failed` |
| 6 | input | JSONB | NOT NULL | Parameters produced by the model |
| 7 | output | JSONB | NULL | Raw result returned by the tool |
| 8 | token_usage | integer | NULL | Tokens consumed by this call |
| 9 | call_seq | integer | NULL, UNIQUE (message_id, call_seq) WHERE message_id IS NOT NULL | Order within one message's set of calls. NULL on the MCP path, which has no parent message to order against |
| 10 | created_at | TIMESTAMPTZ | NOT NULL | Record creation |

Ghi chú dưới bảng:

> Constraint: `CHECK ((message_id IS NOT NULL)::int + (mcp_credential_id IS NOT NULL)::int = 1)` — a tool call comes from exactly one of the two entry points, never both and never neither.
>
> Index: `(message_id)` and `(mcp_credential_id, created_at DESC)`.

---

## A9. `1.5.17 EmailDraft`

**Đổi gì:** khoá chính thành tổ hợp `(message_id, draft_seq)`, bỏ `id` · bỏ
`recipientAddress` (tách thành bảng riêng, xem B6).

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | message_id | UUID | PK (composite), FK (MESSAGE) | The assistant message that produced this draft |
| 2 | draft_seq | integer | PK (composite) | Order of drafts produced within that message |
| 3 | account_id | UUID | FK (CONNECTED_ACCOUNT), NOT NULL | The mailbox the draft will be sent from — required once a user can connect more than one |
| 4 | reply_to_email_id | UUID | FK (EMAIL), NULL | The original email when this draft is a reply |
| 5 | subject | string | NULL | Proposed subject line |
| 6 | body | text | NULL | Proposed body |
| 7 | status | string | NOT NULL | `pending`, `sent`, `discarded` |
| 8 | created_at | TIMESTAMPTZ | NOT NULL | When the draft was generated |
| 9 | updated_at | TIMESTAMPTZ | NOT NULL | Last edit by the user (UC010) |

---

## A10. `1.5.18 ConfirmationRequest`

**Đổi gì:** không còn thực thể yếu — thành bảng mở rộng 1-1 của `Toolcall`. Bỏ `id`, khoá
chính chính là `tool_call_id`.

Mô tả giữ nguyên. Thay bảng bằng:

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | tool_call_id | UUID | PK, FK (TOOLCALL) | The tool execution awaiting approval. Being both the primary and the foreign key enforces at most one confirmation per tool call structurally |
| 2 | action | string | NOT NULL | Technical name of the action, e.g. `bulk_delete` |
| 3 | description | text | NOT NULL | Plain-language summary shown to the user, e.g. "Xoá 15 email đã chọn?" — the user approves what they can read, not a function name |
| 4 | status | string | NOT NULL, DEFAULT `pending` | `pending`, `approved`, `rejected` |
| 5 | created_at | TIMESTAMPTZ | NOT NULL | When the request was raised |
| 6 | updated_at | TIMESTAMPTZ | NOT NULL | Updated when the user responds |

Ghi chú dưới bảng:

> `approve()` and `reject()` may only be called while `status = 'pending'`. This single rule is what prevents a double submission from executing an irreversible action twice: once approved the row is no longer pending, so a second click cannot run the action again.

---

## A11. `1.5.10 Auditlog`

**Đổi gì:** không đổi cột nào — chỉ thêm một dòng ghi chú về chỉ mục.

Thêm dưới bảng hiện có:

> Index: `(user_id, created_at DESC)`. The real query is always "this user's activity, most
> recent first". Two separate indexes on `user_id` and `created_at` cannot serve that as well
> as one composite index: the database must filter by user and then sort again. This table
> only ever grows, so the gap widens over time.


---

# PHẦN B — THÊM bảng mới (chèn sau 1.5.18)

## B1. `1.5.19 Plan_Catalog`

> The published price list and policy. Separate from `subscription` so that changing a price
> never rewrites what past periods were charged.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | plan_catalog_id | UUID | PK | Unique identifier for the price entry |
| 2 | tier | string | NOT NULL | `free`, `pro`, `pro_max` |
| 3 | price | NUMERIC(12,2) | NOT NULL | Listed price |
| 4 | currency | CHAR(3) | NOT NULL, DEFAULT `VND` | ISO 4217 code |
| 5 | mailbox_scope_days | integer | NOT NULL | AI processing window offered by this tier |
| 6 | effective_from | TIMESTAMPTZ | NOT NULL | When this price takes effect |
| 7 | effective_to | TIMESTAMPTZ | NULL | NULL means currently in effect |
| 8 | created_by | UUID | FK (USER), NULL | Administrator who created the entry. Nullable so that the rows seeded at install time, before any administrator exists, can still be inserted |
| 9 | created_at | TIMESTAMPTZ | NOT NULL | Record creation |

> Constraint: `UNIQUE INDEX ux_plan_catalog_one_active_per_tier ON plan_catalog(tier) WHERE effective_to IS NULL`.

---

## B2. `1.5.20 User_Preference`

> One-to-one extension of `user` holding personalisation the user controls. These values are
> injected into the system prompt when the assistant runs.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | user_id | UUID | PK, FK (USER) | The user these preferences belong to |
| 2 | language | string | NOT NULL, DEFAULT `vi` | Interface language |
| 3 | theme | string | DEFAULT `system` | Light, dark, or follow the system |
| 4 | display_name | string | NULL | Name the assistant uses when addressing the user |
| 5 | tone_preference | string | NULL | Preferred writing tone for drafted mail |
| 6 | signature_note | text | NULL | Signature appended to drafts |
| 7 | custom_instructions | text | NULL | Free-form standing instructions for the assistant |
| 8 | updated_at | TIMESTAMPTZ | NOT NULL | Last change |

---

## B3. `1.5.21 Connected_Account_Scope`

> The OAuth permissions the user actually granted to a connection. Stored so that
> "may this external agent do this?" (FR-05.2) can be answered without asking the provider.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | account_id | UUID | PK (composite), FK (CONNECTED_ACCOUNT) | The connection |
| 2 | scope | string | PK (composite) | One granted permission, e.g. `gmail.modify` |

---

## B4. `1.5.22 Email_Recipient`

> Multivalued child of `email` — an email has many recipients.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | email_id | UUID | PK (composite), FK (EMAIL) | The email |
| 2 | recipient_address | string | PK (composite) | One recipient address |

---

## B5. `1.5.23 Email_Label`

> Multivalued child of `email` — provider labels applied to a message.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | email_id | UUID | PK (composite), FK (EMAIL) | The email |
| 2 | label | string | PK (composite) | One label name from the provider |

---

## B6. `1.5.24 Email_Draft_Recipient`

> Multivalued child of `email_draft`, replacing the single `recipientAddress` column so that
> a draft can address more than one person and distinguish To from Cc and Bcc.

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | message_id | UUID | PK (composite), FK (EMAIL_DRAFT) | Part of the parent draft's key |
| 2 | draft_seq | integer | PK (composite), FK (EMAIL_DRAFT) | Part of the parent draft's key |
| 3 | recipient_address | string | PK (composite) | One recipient address |
| 4 | recipient_type | string | NOT NULL | `to`, `cc`, or `bcc` |

---

## B7. `1.5.25 MCP_Credential`

> Credentials issued so that an external agent (for example Claude Desktop) can reach the
> MeoArc tools without going through the web interface (UC012).

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | mcp_credential_id | UUID | PK | Unique identifier for the credential |
| 2 | user_id | UUID | FK (USER), NOT NULL | The user on whose behalf the external agent acts |
| 3 | encrypted_secret | text | NOT NULL, UNIQUE | The credential itself, stored encrypted |
| 4 | status | string | NOT NULL | `active` or `revoked` |
| 5 | created_at | TIMESTAMPTZ | NOT NULL | When issued |
| 6 | expires_at | TIMESTAMPTZ | NULL | Optional expiry |

---

## B8. `1.5.26 MCP_Credential_Scope`

> Multivalued child of `mcp_credential` — the permissions this credential carries. An
> external agent may never exceed them (FR-05.2).

| Seq | Attribute | Data Type | Key/Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 1 | mcp_credential_id | UUID | PK (composite), FK (MCP_CREDENTIAL) | The credential |
| 2 | scope | string | PK (composite) | One permission |

---

# PHẦN C — XOÁ

## C1. Xoá hẳn mục `1.5.16 Table: Tool`

Lý do ghi vào tài liệu (dán vào cuối §1.5, mục "Entities excluded from the database
schema" nếu PA2 có, không thì thêm một đoạn ngắn):

> `Tool` is deliberately not a database table. The tool registry in the source code is the
> single source of truth for tool names, descriptions and parameter schemas; storing them
> again in the database would create two definitions that drift apart, and the one the code
> actually executes would always be the code's.

Nhớ đánh số lại các mục sau đó, và bỏ cột `tool_id` khỏi `Toolcall` (đã có trong A8).

---

# PHẦN D — Ba chỗ khác cần sửa

## D1. `§1.3.5 Class "ConfirmationRequest"`

Thêm một dòng vào phần mô tả lớp:

> Realised in the data design as a one-to-one extension table keyed on `tool_call_id`
> (§1.5.18), not as a weak entity. A `UNIQUE(tool_call_id)` constraint already limits it to
> one row per tool call, which leaves a partial key with no second value to distinguish.

## D2. Bảng tổng hợp Weak Entity

Bỏ `ConfirmationRequest` khỏi danh sách. Danh sách còn lại:

| Weak entity | Owner | Identifying relationship | Composite key |
| :---- | :---- | :---- | :---- |
| Message | Conversation | CONTAINS | (conversation_id, message_seq) |
| Email | EmailThread | INCLUDES | (thread_id, provider_message_id) |
| Embeddings | Email | HAS_VECTOR | (email_id, chunk_index) |
| Attachment | Email | HAS_ATTACHMENT | (email_id, provider_attachment_id) |
| EmailDraft | Message | MAY_GENERATE | (message_id, draft_seq) |

## D3. Bảng tổng hợp Bảng phụ trợ

Thêm các dòng mới:

| Bảng | Loại | PK |
| :---- | :---- | :---- |
| Connected_Account_Scope | Multivalued child | (account_id, scope) |
| Email_Recipient | Multivalued child | (email_id, recipient_address) |
| Email_Label | Multivalued child | (email_id, label) |
| Email_Draft_Recipient | Multivalued child | (message_id, draft_seq, recipient_address) |
| MCP_Credential_Scope | Multivalued child | (mcp_credential_id, scope) |
| User_Preference | 1-1 extension table | user_id |
| ConfirmationRequest | 1-1 extension table | tool_call_id |

---

# Bảng kiểm sau khi sửa xong

- [ ] Tìm `**` trong PA2 → 0 kết quả
- [ ] Tìm `tool_id` → chỉ còn `tool_call_id`, không còn FK sang bảng Tool
- [ ] Tìm `Table: Tool` → 0 kết quả (đã xoá 1.5.16)
- [ ] Tìm `embedding_type` → 0 kết quả
- [ ] Tìm `email_seq` → 0 kết quả
- [ ] Tìm `recipientAddress` → 0 kết quả (đã tách sang Email_Draft_Recipient)
- [ ] Tìm `scopes` trong Connected_Account → 0 kết quả (đã tách sang bảng riêng)
- [ ] Mục lục §1.5 chạy liên tục 1.5.1 → 1.5.26, không trùng số, không nhảy cóc
- [ ] Đếm số bảng trong §1.5 → **25**
