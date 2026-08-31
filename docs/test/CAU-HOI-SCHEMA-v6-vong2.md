# Vòng 2 — sau khi đọc REPLY

> Cảm ơn bạn trả lời nhanh. Sáu câu đã chốt gọn, mình ghi lại bên dưới để khỏi hỏi lại.
> Còn **bốn chỗ** mình muốn làm rõ nốt, trong đó chỗ đầu tiên là quan trọng nhất.

## Đã chốt (mình hiểu vậy, sai thì bạn sửa giúp)

| # | Chốt |
| :---- | :---- |
| 1 | Một model, một dimension → `vector(768)` cố định. Cột `dimension` giữ lại chỉ để ghi chú. |
| 2 | Bảng đổi tên thành `users`. |
| 3 | Bổ sung `extracted_text` vào `attachment` (§10). |
| 4 | Khoá chính là `email_id`, sửa lại 6 chỗ đang ghi `email.id`. |
| 7 | `refresh_token` cho NULL. |
| 8 | `notification` thêm `created_at` + index `(user_id, created_at DESC)`. |
| 9 | MVP không cần `subscription.status`. |

---

## A. Chuyện dọn `email` theo mailbox scope — mình nghĩ có nhầm lẫn ở đây

Bạn nói đang tính dọn `email` / `email_thread` theo đúng mailbox scope của gói. Mình lo hai
chuyện, và cả hai đều nằm trong tài liệu tụi mình **đã nộp** rồi.

**A1. Đá thẳng vào NFR-SCO-03.** PA1 §3.2.2.8 viết nguyên văn:

> *Email List View and Keyword & Criteria-Based Email Search (FR-03.1, FR-03.2) **shall not
> be subject to this time window limitation**.*

Cửa sổ 90/180/365 là giới hạn **AI được đọc bao nhiêu**, không phải giới hạn **người dùng
được giữ bao nhiêu**. Nếu xoá thư cũ hơn 90 ngày khỏi DB thì người dùng gói Miễn phí mất
luôn khả năng xem và tìm thư cũ của chính họ — một biện pháp kiểm soát chi phí AI biến
thành mất dữ liệu.

→ Ý bạn là xoá thật, hay chỉ xoá **phần nặng** (`body`, `embedding`, `attachment`) và giữ
metadata để list/search vẫn chạy? Nếu là vế sau thì mình thấy hợp lý, chỉ cần ghi rõ trong
tài liệu là dọn cái gì và giữ cái gì.

**A2. Nếu xoá `email` thì `audit_log` bạn muốn giữ vĩnh viễn sẽ mất một nửa.**

`tool_call_reference` có FK trỏ sang `email`. Xoá `email` thì hoặc ràng buộc chặn không cho
xoá, hoặc cascade xoá luôn dòng liên kết — nhật ký còn nguyên nhưng **không còn biết hành
động đó đã đụng vào thư nào**.

→ Hai quyết định này (giữ log mãi mãi + dọn email định kỳ) mình thấy đang chống nhau. Bạn
tính xử lý thế nào — cho `tool_call_reference` giữ lại `provider_message_id` dạng chuỗi thay
vì FK, hay chấp nhận mất mối nối?

---

## B. `email_seq` — mình có thêm một dữ kiện, muốn hỏi lại

Bạn nói thêm `_seq` vì sợ "2 cái được đưa vào cùng lúc". Nhưng chính bản v6 đã khai
`UNIQUE(thread_id, provider_message_id)` — nghĩa là `provider_message_id` **vốn đã duy nhất
trong mỗi thread**.

Vậy `ORDER BY received_at ASC, provider_message_id ASC` đã tất định hoàn toàn: hai thư về
cùng một mili-giây vẫn xếp ổn định, mà không cần khoá gì cả. Còn cột `_seq` thì ngược lại —
để gán được số không đụng nhau thì **bắt buộc** phải khoá row cha, tức là nó tạo ra đúng
vấn đề nó định giải.

→ Mình đề nghị tách hai cột ra, đừng gộp làm một quyết định:
- **`email_seq`**: chính v6 nói nó *không phải* partial key → bỏ được, không mất gì.
- **`message_seq`**: §6 khai nó *là* partial key của weak entity → giữ vì giá trị mô hình
  hoá, nhưng đổi sang khoá **lạc quan**: cứ insert rồi bắt lỗi `UNIQUE` mà thử lại. Đụng độ
  chỉ xảy ra khi hai tin nhắn vào cùng một hội thoại đúng lúc — hiếm. Còn `FOR UPDATE` thì
  trả giá ở *mọi* lần insert, kể cả lúc bulk-sync lần đầu.

Bạn thấy sao?

---

## C. `embedding_type` — nó khác `model_name` chỗ nào?

Bạn nói `embedding_type` để ghi embedding tạo theo kiểu/model nào. Nhưng §11 đã có sẵn cột
**`model_name VARCHAR(100) NN`** làm đúng việc đó. Và theo quyết định #1 vừa chốt (một model
cho MVP) thì cả hai cột đều là hằng số.

→ Có phải ý bạn `embedding_type` là *loại nội dung* (body/attachment/header)? Nếu vậy thì nó
trùng luôn với `chunk_type` mà #34 đã chọn làm discriminator. Mình thấy giống hệt tình huống
`confirmation_seq` mà chính #33 đã khai tử — bỏ được không?

---

## D. Hai câu còn treo

**D1.** Câu 10 bạn mới trả lời phần retention, chưa trả lời phần **index**. Mà giữ
`audit_log` vĩnh viễn thì index `(user_id, created_at DESC)` càng cần chứ không phải càng
bớt — bảng chỉ có tăng, truy vấn thống kê sẽ chậm dần đều. Thêm được không?

**D2.** Câu 11 và 12 chưa có trả lời, mà đây là hai câu ảnh hưởng tới lịch nộp nhiều nhất:

- **v6 có thay thế phần Data Design của PA2 không?** Nếu có thì PA2 phải nộp bản mới, và ai
  làm? Hiện code có 10 bảng, PA2 đã nộp mô tả 18 bảng, v6 là ~25 — ba phiên bản khác nhau.
- **Trước hạn nộp thì làm phần nào?** Mình đề xuất chỉ lấy mấy thứ rẻ mà không phá cấu trúc:
  partial unique index cho `subscription`, snapshot `amount`/`mailbox_scope_days`,
  `created_at` cho `notification`, index HNSW. Còn `connected_account` + `email_thread` +
  `tool_call` để sau khi nộp vì phải viết lại gần hết tầng dữ liệu.

→ Bạn chốt giúp mình hai ý này, vì mình không tự quyết được phần đụng tới tài liệu đã nộp.
