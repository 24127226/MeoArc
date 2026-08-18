# PA2 — danh sách sửa lỗi sau lần dò `Group 7_Design.docx`

> **Bản này đã tốt.** Cả 25 bảng đều có mặt, 17 cột mới đều đúng, 6 thứ phải bỏ đã sạch,
> `**` về 0, cặp MSSV đúng cả 4, bảng `Tool` đã xoá. Dưới đây chỉ là phần còn sót.
>
> Tổng: **7 chỗ đổi số · 3 chỗ ở §1.3 · 5 đoạn xoá · 1 chỗ nhìn mắt.** Khoảng 15 phút.

> ⚠️ **Đính chính từ file hướng dẫn trước của mình.** Mục D2 và D3 (cập nhật hai bảng
> tổng hợp "Weak Entity" và "Bảng phụ trợ") là **sai** — PA2 không có hai bảng đó, chúng
> nằm trong tài liệu v6 của bạn bạn. Bỏ qua hai mục ấy, đừng thêm vào.

---

## PHẦN 1 — Số hiệu §1.5 (7 chỗ)

### Vì sao lệch

Mục có tiêu đề `1.5.4 Table: Gmail_Account` **đầu tiên** thực ra là bảng
`Connected_Account_Scope` — nội dung bên dưới nó là *"The OAuth permissions the user actually
granted to a connection…"* với hai cột `account_id` và `scope`. Chỉ một tiêu đề ghi nhầm tên,
nhưng nó gây ra cả hai triệu chứng: trùng số 1.5.4, và tưởng như thiếu một bảng.

### Cách sửa ít thao tác nhất

**Bước 1.** Cắt nguyên mục `1.5.4 Table: Gmail_Account` **đầu tiên** (mục có mô tả bắt đầu
bằng *"The OAuth permissions…"*) và dán xuống **cuối §1.5**, sau `MCP_Credential_Scope`.

**Bước 2.** Đổi tiêu đề của mục vừa chuyển thành:

```
1.5.25 Table: Connected_Account_Scope
```

**Bước 3.** Sửa 6 tiêu đề còn lại:

| Bảng | Đang ghi | Sửa thành |
| :---- | :---- | :---- |
| Email_Draft | `1.5.10` | `1.5.19` |
| Email_Draft_Recipient | `1.5.19` | `1.5.20` |
| Plan_Catalog | `1.5.19` | `1.5.21` |
| Confirmation_Request | `1.5.21` | `1.5.22` |
| MCP_Credential | `1.5.22` | `1.5.23` |
| MCP_Credential_Scope | `1.5.23` | `1.5.24` |

Từ `1.5.1` đến `1.5.18` **giữ nguyên hết**, không đụng gì.

### Thứ tự đúng sau khi sửa

Đối chiếu lại cho chắc — đọc từ trên xuống phải ra đúng dãy này:

```
1.5.1  User                     1.5.14 Embeddings
1.5.2  User_Preference          1.5.15 Tool_call_Email
1.5.3  Connected_Account        1.5.16 Conversation
1.5.4  Gmail_Account            1.5.17 Message
1.5.5  Outlook_Account          1.5.18 Tool_call
1.5.6  Subscription             1.5.19 Email_Draft
1.5.7  Notification             1.5.20 Email_Draft_Recipient
1.5.8  EmailThread              1.5.21 Plan_Catalog
1.5.9  Email                    1.5.22 Confirmation_Request
1.5.10 Email_Recipient          1.5.23 MCP_Credential
1.5.11 Email_Label              1.5.24 MCP_Credential_Scope
1.5.12 Attachment               1.5.25 Connected_Account_Scope
1.5.13 Auditlog
```

**25 bảng.** Đây là dãy chuẩn để đối chiếu.

---

## PHẦN 2 — §1.3.10 Class "EmailDraft" (3 chỗ)

Phần này lệch với §1.5 vừa sửa. Đây là chỗ **file hướng dẫn trước của mình bỏ sót** — mình
chỉ soạn §1.5 mà quên phần lớp kéo theo.

### 2a. Thuộc tính `recipientAddress`

§1.5 đã tách người nhận ra bảng riêng để một bản nháp gửi được nhiều người và phân biệt
To/Cc/Bcc. Lớp phải theo.

Dòng Seq 2 hiện là:

| | Property | Modifier | Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 2 | recipientAddress | Public | Valid email format | Intended recipient of the email. |

Thay bằng:

| | Property | Modifier | Constraint | Description |
| :---- | :---- | :---- | :---- | :---- |
| 2 | recipients | Public | At least one entry with type `to` | The recipients of the draft, each with an address and a type of `to`, `cc` or `bcc`. Persisted as the EMAIL_DRAFT_RECIPIENT table so that one draft can address several people. |

### 2b. Giá trị `status`

Lớp đang ghi `{"draft", "sent", "discarded"}, default = "draft"`, còn §1.5 đã chốt
`pending` / `sent` / `discarded`. Hai chỗ nói hai bộ từ khác nhau cho cùng một trường.

Dòng Seq 3, cột Constraint — sửa thành:

```
One of {"pending", "sent", "discarded"}, default = "pending"
```

### 2c. Ba thao tác bên dưới cũng nhắc `"draft"`

`updateContent()`, `markSent()`, `discard()` đều ghi *"Can only be called when status =
'draft'"*. Sửa cả ba thành:

```
Can only be called when status = "pending"
```

Nhanh nhất: `Ctrl + H`, tìm `status = "draft"`, thay bằng `status = "pending"`, Replace all.
Nhớ kiểm lại là chỉ thay trong §1.3.10, không đụng chỗ khác.

---

## PHẦN 3 — §1.3.5 Class "ConfirmationRequest": tham chiếu sai số

Phần mô tả đang ghi:

> Realised in the data design as a one-to-one extension table keyed on `tool_call_id`
> (**§1.5.18**), not as a weak entity.

Sau khi dồn số, `Confirmation_Request` nằm ở **1.5.22**, còn 1.5.18 giờ là `Tool_call`.

Sửa `§1.5.18` thành `§1.5.22`.

---

## PHẦN 4 — §1.3.6 Class "Tool": thêm một câu

Bảng `Tool` đã xoá khỏi §1.5, nhưng lớp `Tool` vẫn còn ở §1.3.6 — và nên giữ, vì nó mô tả
khái niệm tool mà agent dùng. Chỉ cần nói rõ nó không được lưu xuống database, kẻo người đọc
thắc mắc sao §1.5 không có bảng tương ứng.

Thêm vào cuối phần mô tả của §1.3.6:

```
This class is not persisted as a database table. The tool registry in the source code is the
single source of truth for tool names, descriptions and parameter schemas; storing them again
in the database would create two definitions that drift apart, and the one the system actually
executes would always be the code's.
```

---

## PHẦN 5 — Xoá 5 đoạn chỉ dẫn của template

Tìm theo chữ đầu (`Ctrl + F`), xoá cả đoạn kể cả hai dấu ngoặc vuông:

| # | Ở mục | Bắt đầu bằng |
| :---- | :---- | :---- |
| 1 | §2 Conceptual Model | `[Present a diagram illustrating the semantic entities…` |
| 2 | §1.4 Data Diagram | `[Draw the data diagram of the system…` |
| 3 | §1.5 Data Specification | `[If using a Database Management System (DBMS)…` |
| 4 | §1.6 Screen Diagram | `[Draw a screen diagram illustrating the relationships…` |
| 5 | §1.7 Screen Specifications | `[Students should select and present the specifications…` |

---

## PHẦN 6 — Một chỗ phải nhìn mắt

Trong **thân bài** §1.7, ba tiêu đề đầu đang không có số:

```
Screen "Landing Page"                      ← lẽ ra 1.7.1
Screen "Login & Connect Account"           ← lẽ ra 1.7.2
Screen "Main screen (Chat + Dynamic Canvas)"  ← lẽ ra 1.7.3
```

Trong khi 1.7.4 → 1.7.7 vẫn có số đầy đủ. Mục lục thì đúng cả bảy.

Mở trang đó nhìn xem trên màn hình có hiện số không:
- **Có hiện** → Word đang đánh số tự động, không phải sửa gì.
- **Không hiện** → gõ thêm `1.7.1 `, `1.7.2 `, `1.7.3 ` vào đầu ba tiêu đề đó cho khớp bốn
  mục còn lại.

---

## Bảng kiểm sau khi sửa xong

- [ ] Tìm `1.5.4` → chỉ còn **1 kết quả** (Gmail_Account)
- [ ] Tìm `1.5.19` → chỉ còn **1 kết quả** (Email_Draft)
- [ ] Tìm `1.5.10` → chỉ còn **1 kết quả** (Email_Recipient)
- [ ] Có mục `1.5.25 Table: Connected_Account_Scope` ở cuối §1.5
- [ ] Đếm số mục trong §1.5 → **25**, chạy liên tục 1.5.1 → 1.5.25 không nhảy cóc
- [ ] Tìm `recipientAddress` → **0 kết quả**
- [ ] Tìm `"draft"` → **0 kết quả** (đã đổi hết sang `pending`)
- [ ] Tìm `§1.5.18` → **0 kết quả** (đã đổi thành §1.5.22)
- [ ] Tìm `[Present`, `[Draw`, `[If using`, `[Students` → **0 kết quả**
- [ ] Tìm `**` → **0 kết quả**
- [ ] §1.7 thân bài: bảy tiêu đề đều có số 1.7.1 → 1.7.7
