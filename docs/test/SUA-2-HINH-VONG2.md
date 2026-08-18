# Vòng 2 — dò lại Data Diagram và Class Diagram bản mới

> **Kết luận trước:** hai hình đã đúng phần lớn. Data Diagram đủ **25 bảng**, khớp đúng dãy
> §1.5.1 → §1.5.25; bảng `TOOL` đã xoá, `email_seq` đã bỏ, không còn cột kiểu mảng, không
> còn camelCase. Class Diagram đã thêm `UserPreference`, `PlanCatalog`, `MCPCredential`,
> `Embedding`, đổi `OAuthAccount` → `ConnectedAccount`, sửa `recipientAddress` → `recipients`,
> thêm `storageKey` + `sha256`.
>
> Còn lại: **4 lỗi thật ở Data Diagram**, **3 lỗi thật ở Class Diagram**, cộng một ít chỗ vụn.
>
> File này **thay thế** mục 3 và mục 4 của [GUI-BAN-SUA-DESIGN.md](GUI-BAN-SUA-DESIGN.md) —
> hai mục đó đã làm xong.

---

# A. DATA DIAGRAM — 4 lỗi phải sửa

### 🔴 A1. `supscription_id` sai chính tả — mà lại là khoá chính

Bảng `SUBSCRIPTION`, dòng đầu tiên:

```
uuid | supscription_id | PK      ← thiếu chữ 'b'
```

Sửa thành **`subscription_id`**. Đây là chỗ nặng nhất trong hình vì nó là tên khoá chính,
và §1.5.7 ghi đúng là `subscription_id`.

### 🔴 A2. `MCP_CREDENTIAL` có `updated_at`, nhưng phải là `expires_at`

| Hình đang có | §1.5.24 chốt |
| :---- | :---- |
| mcp_credential_id, user_id, encrypted_secret, status, created_at, **updated_at** | mcp_credential_id, user_id, encrypted_secret, status, created_at, **expires_at** |

Sửa `updated_at` → **`expires_at`** (kiểu `timestamptz`, cho phép NULL).

Đây không phải chuyện đặt tên. `expires_at` là hạn dùng của credential cấp cho agent ngoài —
bỏ nó đi thì token MCP không có ngày hết hạn, mất luôn một lớp an toàn. **Hình class bên
cạnh cũng đang ghi `expiresAt`**, nên hiện hai hình đang nói ngược nhau.

### 🔴 A3. `MCP_CREDENTIAL_SCOPE.scope` sai kiểu

```
uuid | scope | PK      ← scope là tên quyền, không phải khoá
```

§1.5.25 ghi `scope` kiểu **string**. Sửa `uuid` → **`string`**.

Đối chiếu cho chắc: `CONNECTED_ACCOUNT_SCOPE` ngay bên trên ghi đúng `string | scope | PK`.
Hai bảng cùng dạng mà một cái sai kiểu.

### 🔴 A4. `TOOL_CALL.token_usage` sai kiểu

```
json | token_usage      ← còn sót từ schema cũ
```

§1.5.19 chốt **`integer`**. Sửa lại.

Lý do phải sửa: cả thiết kế đếm token đều dựa trên chỗ này. `subscription.tokens_today` và
`tokens_month` là số nguyên cộng dồn — nếu `token_usage` là JSON thì mỗi lần cộng phải parse
JSON ra, đúng cái mà nhóm đã quyết định tránh khi chốt phương án đếm token.

*(Lưu ý: `MESSAGE.token_usage` vẫn là `json` là **đúng** — §1.5.18 để JSON vì nó chứa cả
prompt/completion tách riêng. Chỉ `TOOL_CALL` mới phải đổi.)*

---

# B. DATA DIAGRAM — 6 chỗ vụn

| # | Chỗ | Đang là | Nên là |
| :---- | :---- | :---- | :---- |
| B1 | **Mọi bảng** | `timestampz` | `timestamptz` — sai chính tả hệ thống, khoảng 20 chỗ. Ctrl+H một lần là xong |
| B2 | `CONFIRMATIONREQUEST` (tên bảng) | `CONFIRMATIONREQUEST` | `CONFIRMATION_REQUEST` — mọi bảng khác đều có gạch dưới (`EMAIL_THREAD`, `TOOL_CALL`, `PLAN_CATALOG`) |
| B3 | `SUBSCRIPTION.plan_catalog_id` | cột Key để trống | `FK` — §1.5.7 ghi `FK (PLAN_CATALOG)` |
| B4 | `ATTACHMENT.size_bytes` | `integer` | `bigint` — §1.5.13. File đính kèm > 2 GB thì `integer` tràn |
| B5 | `ATTACHMENT.sha256` | `char` | `char(64)` — §1.5.13 ghi rõ độ dài |
| B6 | `CONFIRMATIONREQUEST.description` | `string` | `text` — §1.5.23 |

---

# C. CLASS DIAGRAM — 3 lỗi phải sửa

### 🔴 C1. Enum `EmailCategory` vẫn sai — mới sửa được một nửa

Hình cũ có 7 giá trị trong đó `Personal` bị trùng. Bản mới đã **xoá cái trùng**, nhưng chỉ
còn 6 và vẫn chưa đúng:

```
Hiện tại:  Spam, School, Career, System, SocialNetwork, Personal        (6)
Phải là:   School, Career, System, Personal, SocialNetwork, Shopping, Finance   (7)
```

Cách sửa đúng không phải xoá giá trị trùng, mà là **thay nó bằng hai nhãn còn thiếu**:

| Việc | Chi tiết |
| :---- | :---- |
| ❌ Xoá | `Spam` — code không có nhãn này |
| ➕ Thêm | `Shopping` — ứng với `mua_sam` "Mua sắm & Ưu đãi" |
| ➕ Thêm | `Finance` — ứng với `tai_chinh` "Tài chính" |

Bảy nhãn trong code (`app/core/labeling.py`): Học tập · Công việc · Cập nhật & Hệ thống ·
Cá nhân · Mạng xã hội · Mua sắm & Ưu đãi · Tài chính.

Chỗ này cần sửa dứt điểm vì **§1.7.1 trong tài liệu đã liệt kê đúng bảy nhãn** (School,
Work, Finance, Social, Shopping, System, Personal). Hiện §1.2 và §1.7 đang nói khác nhau.

### 🔴 C2. Người nhận — một chỗ chưa sửa, một chỗ mới sửa được nửa

**a) `Email.recipient` vẫn số ít.** Còn nguyên `+string recipient`, trong khi Data Diagram
đã có bảng `EMAIL_RECIPIENT` và §1.5.11 đã chốt nhiều người nhận.

→ Sửa thành **`+string[] recipients`**.

**b) `EmailDraft.recipients` mới đổi tên, chưa đổi kiểu.** Hình đang ghi:

```
+string recipients        ← tên số nhiều nhưng kiểu vẫn là một chuỗi đơn
```

Đổi tên mà giữ nguyên kiểu `string` thì vẫn chỉ chứa được một người nhận. Ngoài ra §1.5.21
còn có cột `recipient_type` (to / cc / bcc) mà kiểu `string` không chở nổi.

→ Sửa thành **`+Recipient[] recipients`** với một lớp nhỏ `Recipient { address, type }`,
hoặc gọn hơn thì **`+string[] recipients`** và ghi chú trong mô tả rằng to/cc/bcc được lưu
ở bảng `EMAIL_DRAFT_RECIPIENT`.

### 🔴 C3. `Conversation` thiếu `isPinned`

Lớp `Conversation` đang có: `title`, `addMessage()`, `getRecentHistory()`.

Nhưng **Data Diagram bên cạnh đã có `boolean is_pinned`**, và §1.5.17 cũng có. Thêm
`+bool isPinned` vào lớp.

Đây là chỗ hai hình mới vẽ lại vẫn chưa khớp nhau.

---

# D. CLASS DIAGRAM — thuộc tính còn thiếu so với §1.5

Không mâu thuẫn, chỉ là hình ít hơn bảng. Sửa được thì tốt, không sửa cũng không sai logic.

| Lớp | Còn thiếu | §1.5 |
| :---- | :---- | :---- |
| `ConnectedAccount` | `providerUserId`, `emailAddress` | 1.5.3 |
| `GmailAccount` | `watchExpiration`, `lastSyncedAt` | 1.5.5 |
| `OutlookAccount` | `watchExpiration`, `lastSyncedAt` | 1.5.6 |
| `Subscription` | `amount`, `currency`, `tokensToday`, `tokensMonth` | 1.5.7 |
| `Message` | `messageSeq`, `tokenUsage` | 1.5.18 |
| `ToolCall` | `callSeq` | 1.5.19 |
| `AuditLog` | `endpoint`, `httpStatus` | 1.5.14 |

**Ưu tiên hai dòng đầu tiên và dòng `Subscription`.** `Subscription` thiếu `tokensToday`/
`tokensMonth` là đáng nói nhất, vì lớp đã có sẵn thao tác `checkAndConsumeToken(amount)` —
mà thao tác này cộng trừ vào đúng hai thuộc tính không được vẽ. Người đọc sẽ hỏi "trừ vào đâu".

---

# E. Ba chỗ hai hình mâu thuẫn nhau

Đây là loại lỗi dễ bị bắt nhất vì chỉ cần đặt hai hình cạnh nhau là thấy:

| # | Class Diagram | Data Diagram | Ai đúng |
| :---- | :---- | :---- | :---- |
| 1 | `MCPCredential.expiresAt` | `MCP_CREDENTIAL.updated_at` | **Class đúng** → sửa Data Diagram (A2) |
| 2 | `Conversation` không có `isPinned` | `CONVERSATION.is_pinned` | **Data đúng** → sửa Class (C3) |
| 3 | `Embedding` (số ít) | `EMBEDDINGS` (số nhiều) | §1.5.15 ghi `Embeddings` → đổi lớp thành `Embeddings`, hoặc chấp nhận vì quy ước lớp thường để số ít |

Chỗ số 3 tuỳ — quy ước UML hay để tên lớp số ít, nên `Embedding` không sai. Chỉ cần biết
là có khác nhau nếu bị hỏi.

---

# F. Một chỗ §1.5 tự mâu thuẫn — không phải lỗi của hình

Hình vẽ `toolcall_id` ở cả bốn chỗ (`TOOL_CALL`, `AUDITLOG`, `CONFIRMATIONREQUEST`,
`TOOL_CALL_EMAIL`) — **nhất quán**.

Nhưng §1.5 thì không: §1.5.19 ghi `toolcall_id`, còn §1.5.14 và §1.5.23 ghi `tool_call_id`.

→ Chọn một kiểu rồi sửa **trong docx**, không phải sửa hình. Mình nghiêng về `tool_call_id`
ở cả bốn chỗ, vì snake_case thì tách từ ra: `tool_call` là hai từ, giống `plan_catalog_id`
và `mcp_credential_id` đang làm.

Nếu chọn `tool_call_id` thì hình cũng phải đổi theo — 4 chỗ.

---

# H. DANH SÁCH THAO TÁC — làm theo thứ tự này

Cả hai hình đều vẽ tay, nên sửa cũng là sửa tay từng ô. Tổng cộng **13 ô bắt buộc**
+ 1 lần Find/Replace. Khoảng 15 phút.

> Đừng vẽ lại từ đầu. Bố cục hiện tại đọc được và rõ, vẽ lại chỉ tốn công.

## H1. Data Diagram — 9 ô + 1 Find/Replace

Sắp theo vị trí trên hình, đi từ trái sang phải cho dễ lần:

| # | Bảng (vị trí) | Ô nào | Sửa thành |
| :---- | :---- | :---- | :---- |
| 1 | `SUBSCRIPTION` (trên cùng bên trái) | dòng 1, tên cột `supscription_id` | **`subscription_id`** |
| 2 | `SUBSCRIPTION` | dòng `plan_catalog_id`, cột Key đang **để trống** | gõ **`FK`** |
| 3 | `MCP_CREDENTIAL` (giữa bên trái) | dòng cuối, tên cột `updated_at` | **`expires_at`** |
| 4 | `MCP_CREDENTIAL_SCOPE` (ngay dưới) | dòng `scope`, cột **kiểu** đang là `uuid` | **`string`** |
| 5 | `CONFIRMATIONREQUEST` (dưới bên trái) | **tên bảng** | **`CONFIRMATION_REQUEST`** |
| 6 | `CONFIRMATION_REQUEST` | dòng `description`, cột kiểu `string` | **`text`** |
| 7 | `TOOL_CALL` (dưới, giữa) | dòng `token_usage`, cột kiểu `json` | **`integer`** |
| 8 | `ATTACHMENT` (bên phải) | dòng `size_bytes`, cột kiểu `integer` | **`bigint`** |
| 9 | `ATTACHMENT` | dòng `sha256`, cột kiểu `char` | **`char(64)`** |

**Rồi làm một lần Find/Replace cho cả hình:**

```
Tìm:      timestampz
Thay:     timestamptz
```

Khoảng 20 chỗ. Nếu công cụ vẽ có Find/Replace thì một lần là xong; draw.io là
`Ctrl + Shift + F`. Không có thì phải sửa tay, nhưng nó rải khắp hình nên đừng bỏ qua —
`timestampz` không phải kiểu dữ liệu có thật của PostgreSQL.

⚠️ **Cẩn thận thứ tự:** làm Find/Replace **sau** chín ô ở trên. Nếu làm trước, mấy ô vừa
gõ lại có thể lẫn `timestampz` mới.

## H2. Class Diagram — 4 chỗ bắt buộc

**① Enum `EmailCategory`** (khung góc trên bên phải) — sửa cho ra đúng 7 dòng:

| Thao tác | Giá trị |
| :---- | :---- |
| ❌ Xoá | `Spam` |
| ➕ Thêm | `Shopping` |
| ➕ Thêm | `Finance` |

Kết quả cuối phải đúng bằng danh sách này:

```
School
Career
System
Personal
SocialNetwork
Shopping
Finance
```

**② Lớp `Email`** (giữa, dưới) — sửa một dòng:

```
+string recipient          →     +string[] recipients
```

**③ Lớp `EmailDraft`** — chỉ cần thêm hai ký tự `[]` vào kiểu:

```
+string recipients         →     +string[] recipients
```

Nếu muốn chuẩn hơn thì tạo một lớp nhỏ `Recipient { +string address; +string type }` rồi
để `+Recipient[] recipients`, vì §1.5.21 có cột `recipient_type` (to/cc/bcc) mà mảng chuỗi
không chở được. Nhưng `string[]` là đủ dùng — chỉ cần ghi thêm một câu trong mô tả rằng
to/cc/bcc lưu ở bảng `EMAIL_DRAFT_RECIPIENT`.

**④ Lớp `Conversation`** — thêm một dòng thuộc tính:

```
+bool isPinned
```

Đặt ngay dưới `+string title`, trên phần các thao tác.

## H3. Nhóm tuỳ chọn — làm nếu còn thời gian

Bảy dòng dưới đây chỉ là thêm thuộc tính cho đủ với §1.5, không mâu thuẫn gì cả. Nếu ít
thời gian thì **làm dòng đầu tiên thôi**, sáu dòng còn lại bỏ qua được.

| Lớp | Thêm | Vì sao ưu tiên |
| :---- | :---- | :---- |
| `Subscription` | `+int tokensToday`, `+int tokensMonth` | ⭐ **Nên làm.** Lớp đã có `checkAndConsumeToken(amount)` — thao tác này cộng trừ vào đúng hai thuộc tính chưa được vẽ. Người đọc sẽ hỏi "trừ vào đâu" |
| `Subscription` | `+decimal amount`, `+string currency` | Cho khớp §1.5.7 |
| `ConnectedAccount` | `+string providerUserId`, `+string emailAddress` | §1.5.3 |
| `GmailAccount` | `+datetime watchExpiration`, `+datetime lastSyncedAt` | §1.5.5 |
| `OutlookAccount` | `+datetime watchExpiration`, `+datetime lastSyncedAt` | §1.5.6 |
| `Message` | `+int messageSeq`, `+json tokenUsage` | §1.5.18 |
| `ToolCall` | `+int callSeq` | §1.5.19 |
| `AuditLog` | `+string endpoint`, `+int httpStatus` | §1.5.14 |
| `Notification` | đổi `+bool read` → `+bool isRead` | Cho khớp §1.5.8 và lớp `Email` (đang dùng `isRead`) |

## H4. Một quyết định cần chốt trước khi sửa: `toolcall_id` hay `tool_call_id`?

Chỗ này **không sửa trên hình được** — phải chốt tên trước rồi sửa cả hai nơi.

Hiện trạng:

| Nơi | Đang ghi |
| :---- | :---- |
| Cả 4 bảng trên **hình** | `toolcall_id` — nhất quán |
| §1.5.19 trong **docx** | `toolcall_id` |
| §1.5.14 và §1.5.23 trong **docx** | `tool_call_id` |

Hai lựa chọn:

- **Chọn `tool_call_id`** *(mình nghiêng về cái này)* — sửa **4 ô trên hình** + **1 ô trong
  docx** (§1.5.19). Tổng 5 chỗ. Lý do: snake_case thì tách từ ra, và `plan_catalog_id`,
  `mcp_credential_id` trong cùng schema đều đang làm vậy.
- **Chọn `toolcall_id`** — hình khỏi đụng, sửa **2 ô trong docx** (§1.5.14, §1.5.23). Tổng
  2 chỗ, nhanh hơn nhưng lệch quy ước với các khoá khác.

Chọn cái nào cũng được, miễn là **cả hình lẫn docx cùng một kiểu**.

---

# I. KIỂM TRA QUAN HỆ GIỮA CÁC BẢNG

## I0. Cách kiểm nhanh nhất: đếm số đường chạm vào mỗi bảng

Lần từng sợi dây trong hình 25 bảng thì rối và dễ sót. Cách chắc hơn: **đếm xem mỗi bảng có
bao nhiêu đường cắm vào nó**, rồi so với bảng dưới đây. Thiếu một đường là biết ngay phải
đi tìm ở đâu.

Schema có đúng **31 quan hệ**. Số đường chạm vào từng bảng:

| Bảng | Số đường | Nối với |
| :---- | :----: | :---- |
| `USER` | **8** | user_preference · connected_account · subscription · notification · conversation · auditlog · mcp_credential · plan_catalog |
| `EMAIL` | **7** | email_thread · email_recipient · email_label · attachment · embeddings · tool_call_email · email_draft |
| `CONNECTED_ACCOUNT` | **6** | user · connected_account_scope · gmail_account · outlook_account · email_thread · email_draft |
| `TOOL_CALL` | **5** | message · mcp_credential · tool_call_email · confirmation_request · auditlog |
| `EMAIL_DRAFT` | **4** | message · connected_account · email · email_draft_recipient |
| `MESSAGE` | **3** | conversation · tool_call · email_draft |
| `MCP_CREDENTIAL` | **3** | user · mcp_credential_scope · tool_call |
| `SUBSCRIPTION` | **2** | user · plan_catalog |
| `PLAN_CATALOG` | **2** | user *(created_by)* · subscription |
| `EMAIL_THREAD` | **2** | connected_account · email |
| `ATTACHMENT` | **2** | email · embeddings |
| `EMBEDDINGS` | **2** | email · attachment |
| `CONVERSATION` | **2** | user · message |
| `TOOL_CALL_EMAIL` | **2** | tool_call · email |
| `AUDITLOG` | **2** | user · tool_call |
| `NOTIFICATION` · `USER_PREFERENCE` · `GMAIL_ACCOUNT` · `OUTLOOK_ACCOUNT` · `CONNECTED_ACCOUNT_SCOPE` · `EMAIL_RECIPIENT` · `EMAIL_LABEL` · `CONFIRMATION_REQUEST` · `MCP_CREDENTIAL_SCOPE` · `EMAIL_DRAFT_RECIPIENT` | **1** mỗi bảng | (bảng cha duy nhất của nó) |

Cộng lại: 62 đầu dây ÷ 2 = **31 quan hệ**. Nếu đếm ra 62 đầu dây thì hình đủ.

## I1. Chỗ khả năng cao nhất đang thiếu: `SUBSCRIPTION → PLAN_CATALOG`

Ở mục H1 mình có ghi cột Key của `SUBSCRIPTION.plan_catalog_id` đang **để trống**, chưa
đánh `FK`. Quên đánh dấu FK thường đi kèm với **quên vẽ luôn đường nối**.

→ Kiểm trước tiên: có đường nào chạy từ `SUBSCRIPTION` sang `PLAN_CATALOG` không? Hai bảng
này nằm xa nhau trên hình (một ở góc trên trái, một ở trên giữa) nên rất dễ bỏ sót.

Nếu thiếu thì vẽ: `PLAN_CATALOG` **một** ──── **nhiều** `SUBSCRIPTION`, và đầu phía
SUBSCRIPTION phải là **tuỳ chọn** (xem I2), vì §1.5.7 cho `plan_catalog_id` NULL.

## I2. Sáu khoá ngoại được phép NULL — phải vẽ ký hiệu "tuỳ chọn"

Đây là chỗ hay sai nhất và cũng khó nhìn ra nhất. Sáu FK này **NULL được**, nên đầu dây phía
bảng cha phải là vòng tròn `○` (không bắt buộc), **không phải** gạch `|` (bắt buộc):

| Bảng | Cột | NULL nghĩa là |
| :---- | :---- | :---- |
| `SUBSCRIPTION` | `plan_catalog_id` | Gói cấp tay, không theo bảng giá nào |
| `PLAN_CATALOG` | `created_by` | Gói do hệ thống tạo, không phải người tạo |
| `TOOL_CALL` | `message_id` | Lời gọi đến từ đường MCP, không có tin nhắn cha |
| `TOOL_CALL` | `mcp_credential_id` | Lời gọi đến từ chat trong app |
| `EMAIL_DRAFT` | `reply_to_email_id` | Thư mới, không phải thư trả lời |
| `EMBEDDINGS` | `source_attachment_id` | Đoạn văn lấy từ thân thư, không từ tệp đính kèm |

Vẽ gạch bắt buộc ở sáu chỗ này là **nói sai schema** — nó bảo mọi tool call đều phải có tin
nhắn cha, trong khi cả nhánh MCP thì không.

## I3. Năm quan hệ 1:1 — **không được** vẽ chân quạ

Năm cặp này là một-một, hai đầu đều là gạch đơn:

| Cặp | Vì sao 1:1 |
| :---- | :---- |
| `USER` ↔ `USER_PREFERENCE` | `user_id` vừa PK vừa FK |
| `CONNECTED_ACCOUNT` ↔ `GMAIL_ACCOUNT` | Bảng con của phân loại, `account_id` vừa PK vừa FK |
| `CONNECTED_ACCOUNT` ↔ `OUTLOOK_ACCOUNT` | như trên |
| `TOOL_CALL` ↔ `CONFIRMATION_REQUEST` | `tool_call_id` vừa PK vừa FK — đúng cái điểm nhóm đang khoe: cấu trúc tự cấm một hành động có hai phiếu duyệt |
| `TOOL_CALL` ↔ `AUDITLOG` | §1.5.14 ghi `UNIQUE` trên `tool_call_id` |

Hai bảng con Gmail/Outlook còn phải là **tuỳ chọn** ở đầu con: một `connected_account` là
Gmail *hoặc* Outlook, không bao giờ cả hai. Nếu công cụ vẽ được ký hiệu phân loại rời nhau
(disjoint) thì càng tốt, không thì ghi chú một câu.

⚠️ **Riêng dòng `AUDITLOG` cần chốt lại với cả nhóm.** §1.5.14 ghi UNIQUE, tức là **mỗi tool
call chỉ có một dòng nhật ký**. Nhưng hình §2 Conceptual Model đang vẽ quan hệ `LOGS` theo
kiểu nhiều-một. Hai chỗ đang nói khác nhau, và về mặt thiết kế thì "một tool call chỉ ghi
được một dòng log" là hơi chặt — nếu muốn ghi cả lúc bắt đầu và lúc kết thúc thì phải bỏ
UNIQUE. Chốt xong mới sửa, và sửa **cả ba chỗ** (§1.5.14, hình §1.4, hình §2).

## I4. Hai khoá ngoại ghép — vẽ **một** đường, đừng vẽ hai

| Quan hệ | Cột ghép |
| :---- | :---- |
| `EMBEDDINGS` → `ATTACHMENT` | `(email_id, source_attachment_id)` → `(email_id, provider_attachment_id)` |
| `EMAIL_DRAFT_RECIPIENT` → `EMAIL_DRAFT` | `(message_id, draft_seq)` |

Chỗ dễ nhầm: `EMBEDDINGS.email_id` **làm hai việc cùng lúc** — vừa là FK riêng sang `EMAIL`,
vừa là nửa đầu của khoá ghép sang `ATTACHMENT`. Nên `EMBEDDINGS` phải có **đúng hai** đường
(một sang EMAIL, một sang ATTACHMENT), không phải ba.

Và `source_attachment_id` **một mình nó không phải FK** — khoá chính của `ATTACHMENT` là cặp
`(email_id, provider_attachment_id)`, nên không thể trỏ tới bằng một cột. Nếu hình đang đánh
`FK` riêng cho `source_attachment_id` thì nên gộp chú thích lại cho rõ là khoá ghép.

## I5. Một ràng buộc không vẽ được bằng ký hiệu — phải ghi chú lên hình

`TOOL_CALL` có hai FK cha đều NULL được (`message_id`, `mcp_credential_id`), nhưng §1.5.19
kèm ràng buộc:

```
CHECK ((message_id IS NOT NULL)::int + (mcp_credential_id IS NOT NULL)::int = 1)
```

Nghĩa là **đúng một trong hai**, không bao giờ cả hai, không bao giờ không cái nào. Ký hiệu
chân quạ không diễn tả được điều này — vẽ hai FK tuỳ chọn rời nhau thì hình đang cho phép cả
hai cùng NULL.

→ Thêm một dòng chú thích cạnh `TOOL_CALL` trên hình:

> *Exactly one of `message_id` / `mcp_credential_id` is set (CHECK constraint) — a tool call
> originates from either the in-app chat or the MCP path, never both.*

Đây cũng chính là chỗ đáng khoe khi thuyết trình, nên để nó hiện lên hình thì hơn.

## I6. Bảng kiểm quan hệ — tick từng dòng

Chín quan hệ dễ sót nhất, kiểm riêng:

- [ ] `SUBSCRIPTION` → `PLAN_CATALOG` *(khả năng cao đang thiếu — xem I1)*
- [ ] `PLAN_CATALOG.created_by` → `USER`
- [ ] `EMAIL_DRAFT.account_id` → `CONNECTED_ACCOUNT` *(không phải sang USER)*
- [ ] `EMAIL_DRAFT.reply_to_email_id` → `EMAIL`
- [ ] `EMAIL_THREAD.account_id` → `CONNECTED_ACCOUNT` *(không phải sang USER)*
- [ ] `TOOL_CALL` → `MCP_CREDENTIAL`
- [ ] `EMBEDDINGS` → `ATTACHMENT` *(khoá ghép)*
- [ ] `AUDITLOG` → `TOOL_CALL`
- [ ] `AUDITLOG` → `USER`

Ba dòng in nghiêng là chỗ hay bị vẽ nhầm sang `USER`, vì theo phản xạ thì cái gì cũng thuộc
về người dùng. Nhưng trong schema này thư và bản nháp gắn với **tài khoản đã kết nối**, không
gắn thẳng vào người dùng — vì một người nối được nhiều hộp thư.

---

# G. Bảng kiểm sau khi sửa

**Data Diagram**
- [ ] Tìm `supscription` → 0 kết quả
- [ ] Tìm `timestampz` → 0 kết quả (đã thành `timestamptz`)
- [ ] `MCP_CREDENTIAL` có `expires_at`, không có `updated_at`
- [ ] `MCP_CREDENTIAL_SCOPE.scope` kiểu `string`
- [ ] `TOOL_CALL.token_usage` kiểu `integer` (còn `MESSAGE.token_usage` vẫn `json`)
- [ ] `SUBSCRIPTION.plan_catalog_id` có chữ `FK`
- [ ] Tên bảng `CONFIRMATION_REQUEST` có gạch dưới
- [ ] Đếm lại → vẫn đủ **25 bảng**

**Class Diagram**
- [ ] Enum `EmailCategory` có đúng **7** giá trị, không có `Spam`, có `Shopping` và `Finance`
- [ ] `Email` có `recipients` (số nhiều, kiểu mảng)
- [ ] `Conversation` có `isPinned`
- [ ] `Subscription` có `tokensToday` và `tokensMonth` (vì đã có `checkAndConsumeToken`)

**Đặt hai hình cạnh nhau**
- [ ] Mọi tên lớp ↔ tên bảng khớp nhau
- [ ] Không còn chỗ nào một hình có thuộc tính mà hình kia không có
