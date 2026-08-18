# Câu hỏi gửi lại về `MeoArc_DB_Schema_Reference_v6.md`

> Bản v6 làm kỹ — nhất là chỗ snapshot `amount`/`mailbox_scope_days` vào `subscription`
> thay vì join sang bảng giá, partial unique index `WHERE end_date IS NULL`, và lập luận
> #33 khai tử `confirmation_seq`. Mấy câu dưới đây là chỗ mình đọc chưa thông hoặc thấy
> vênh nhau, muốn hỏi cho rõ trước khi sinh DDL.

---

## A. Hai chỗ mình nghĩ sẽ kẹt lúc chạy DDL thật

**1. `embedding.vector` — kiểu `vector(dimension)` lấy số chiều từ cột được không?**

§11 khai `dimension INTEGER NN` và `vector vector(dimension)`. Theo mình biết pgvector đòi
số chiều là **hằng số lúc `CREATE TABLE`** (`vector(768)`), không nhận tên cột.

Mà nếu để `vector` không ràng buộc chiều thì lại **không dựng được index HNSW** — đúng cái
§16 nói là bắt buộc.

→ Ý bạn là cố định một số chiều (rồi cột `dimension` chỉ để ghi chú), hay định cho nhiều mô
hình cùng lúc? Nếu là vế sau thì mình nên tách bảng theo mô hình, hay chấp nhận mất HNSW?

**2. Bảng `user` — có định đổi tên không?**

`user` là từ khoá của Postgres, `CREATE TABLE user (...)` sẽ lỗi cú pháp; phải viết `"user"`
có nháy kép ở **mọi** truy vấn, quên một lần là hỏng. Code hiện tại đang dùng `users`.

→ Đổi thành `users` hay `app_user` được không, hay bạn có lý do giữ nguyên?

---

## B. Hai chỗ mình đọc thấy vênh giữa các mục

**3. `attachment.extracted_text` nằm ở đâu?**

Quyết định #34 và §11 đều nói chunk có thể đến từ `attachment.extracted_text`. Nhưng bảng
`attachment` ở §10 chỉ có: `provider_attachment_id, filename, size_bytes, type, storage_key,
sha256, email_id` — mình không thấy cột `extracted_text`.

→ Cột này bị rơi lúc soạn §10, hay ý bạn là text trích xuất nằm chỗ khác (ví dụ chỉ sống
trong `embedding.chunk_text`)? Nếu là vế sau thì mô tả ở #34 nên sửa lại cho khớp.

**4. Khoá chính của `email` tên là `email_id` hay `id`?**

§9 khai `email_id UUID PK`, nhưng §9a, §9b, §10, §11, §12, §13a đều ghi FK `→ email.id`.

→ Chốt một tên giúp mình để lúc sinh DDL không phải đoán.

---

## C. Mấy quyết định mình muốn hiểu thêm lý do

**5. `email_seq` / `message_seq` — có nhất thiết phải có không?**

Bản v6 nói `email_seq` "KHÔNG phải partial key", định danh thật là
`(thread_id, provider_message_id)`, và nó chỉ dùng để tiebreak khi sắp xếp hiển thị.

Nếu vậy thì `ORDER BY received_at ASC, provider_message_id ASC` đã tất định rồi — bỏ được
cả cột lẫn hợp đồng `SELECT ... FOR UPDATE` ở #32. Với `message_seq` thì một `BIGSERIAL`
toàn cục vẫn tăng đơn điệu trong phạm vi một hội thoại mà không cần khoá.

→ Mình có bỏ sót ràng buộc nào bắt buộc phải có seq liên tục trong phạm vi cha không?
Mình hơi ngại chỗ `FOR UPDATE` vì lúc bulk-sync lần đầu (nhiều email cùng thread) nó sẽ
nối tiếp hoá đúng chỗ nóng nhất.

**6. `embedding_type` còn dùng để làm gì?**

§11 có cả `embedding_type` (NULL) lẫn `chunk_type` (NN), mà #34 đã chọn `chunk_type` làm
discriminator (`body` / `header` / `attachment`).

→ Vậy `embedding_type` giữ lại cho trường hợp nào? Hỏi vì nó khá giống tình huống
`confirmation_seq` mà chính #33 đã khai tử — một cột không còn giá trị nào để phân biệt.

**7. `connected_account.refresh_token` để `NOT NULL` có chặt quá không?**

Google không trả refresh token ở lần cấp quyền lại, Microsoft cũng có luồng không trả. Để
NN thì mình buộc phải nhét chuỗi rỗng, mất luôn khả năng phân biệt "chưa từng có" với
"có mà rỗng".

→ Cho NULL được không?

**8. `notification` không có `created_at` là cố ý?**

§3 có `notification_id, type, message, read, user_id` — không có mốc thời gian, nên không
sắp xếp thông báo theo thời gian được, mà đó gần như là việc duy nhất người ta làm với bảng
này. §16 cũng chỉ index `(user_id, read)`.

→ Thêm `created_at` + index `(user_id, created_at DESC)` được không?

**9. `subscription` có cần cột `status` riêng không?**

Hiện `end_date IS NULL` đang mang hai nghĩa: "đang chạy" và "chưa đặt ngày kết thúc". Gói đã
huỷ nhưng còn hạn sử dụng (huỷ giữa kỳ, dùng hết tháng) thì mình chưa thấy cách biểu diễn.

→ Ý bạn là ghi `end_date` = ngày hết kỳ ngay lúc huỷ, hay cần thêm `status`?

**10. `audit_log` không nằm trong §16 là cố ý?**

Nó là bảng phình nhanh nhất (mỗi tool_call một dòng) và luôn truy vấn theo người + thời
gian, nhưng §16 không liệt kê index nào cho nó.

→ Có định thêm `(user_id, created_at DESC)` không? Và có tính chuyện dọn theo thời hạn chưa?

