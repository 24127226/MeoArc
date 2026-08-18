# Vòng 3 — còn đúng một câu

> Cảm ơn bạn, hai vòng vừa rồi chốt được **11/13 mục**. Chỗ A2 bạn tự soát lại rồi đổi
> hướng là chuẩn — giữ metadata thì `tool_call_reference` không gãy mà vẫn tiết kiệm được
> phần chiếm chỗ thật.
>
> Còn đúng một câu, và mình cần nó ở dạng **chọn A hay B** vì nó quyết định tuần này mình
> làm gì.

---

## Câu duy nhất: PA2 xử lý thế nào?

Vòng 2 bạn trả lời *"lo phần tài liệu trước, code thì thời gian khá dư giả"*. Mình hiểu tinh
thần, nhưng "lo tài liệu trước" đang có **hai nghĩa** khác hẳn nhau về khối lượng việc, nên
mình chưa bắt đầu được.

### Phương án A — PA2 nộp lại theo v6

| | |
| :---- | :---- |
| Tài liệu | PA2 §1.5 viết lại: 18 bảng → ~25 bảng, đổi cả cấu trúc (`confirmation_request` gắn vào `tool_call`, `subscription` thành lịch sử kỳ, thêm `plan_catalog` / `user_preference` / `mcp_credential` / `email_recipient` / `email_label` / `connected_account_scope`…) |
| Kéo theo | PA0 và PA1 phải rà lại cho khớp — bộ ba vừa mới đồng bộ xong |
| Code | 10 bảng → 25 bảng, viết lại gần hết tầng dữ liệu |
| Ai làm | Phần tài liệu: ? · Phần code: mình |
| Được gì | Thiết kế tốt hơn hẳn, làm một lần cho trọn |

### Phương án B — PA2 giữ nguyên, v6 là đích sau khi nộp

| | |
| :---- | :---- |
| Tài liệu | PA2 chỉ xoá 6 đoạn chỉ dẫn template còn sót. Không đụng §1.5 |
| Kéo theo | Không gì cả — PA0/PA1/PA2 đang nhất quán, giữ nguyên trạng thái đó |
| Code | Lấy 4 thứ rẻ từ v6 (xem dưới), không phá cấu trúc |
| Ai làm | Mình, trong ngày |
| Được gì | Nộp đúng hạn với bộ tài liệu sạch; v6 làm sau, không mất |

### Mình nghiêng về B, ba lý do

**Khoảng cách tài liệu–code sẽ rộng gấp đôi.** Hiện là 18 (PA2) vs 10 (code). Theo A thành
25 vs 10. Phần "đã thiết kế nhưng chưa hiện thực" trong tài liệu Testing sẽ dài thêm chứ
không ngắn đi — mà đó chính là chỗ người chấm soi.

**Bộ ba PA0/PA1/PA2 vừa mới khớp nhau.** Mình vừa dò xong, chỉ còn 6 đoạn ngoặc vuông trong
PA2. Sửa §1.5 sang v6 là làm lại từ đầu toàn bộ việc đồng bộ đó, ngay trước hạn.

**v6 không mất đi.** Nó là schema tốt cho sản phẩm thật. Để sau khi nộp thì có thời gian làm
cho tử tế, thay vì làm vội rồi vỡ ở giữa.

→ **Bạn chọn A hay B?** Nếu A thì cho mình biết ai viết lại PA2 §1.5 và deadline nào.

---

## Tiện thể, một chỗ mình đọc chưa chắc

D1 bạn trả lời *"chấp nhận tradeoff này"*. Mình hiểu là **đồng ý thêm** index
`audit_log(user_id, created_at DESC)` và chấp nhận cái giá của nó (ghi chậm hơn chút, tốn
thêm dung lượng).

→ Đúng không? Trả lời "ừ" hoặc "không" là đủ.

---

## Trong lúc chờ, mình làm bốn thứ này

Đều rẻ, không phá cấu trúc hiện có, và đúng theo A hay B cũng dùng được:

- `created_at` + index `(user_id, created_at DESC)` cho `notification`
- Partial unique index `WHERE end_date IS NULL` cho `subscription`
- Snapshot `mailbox_scope_days` vào `subscription` — khớp luôn với NFR-SCO vừa hiện thực
- Cho `refresh_token` nhận NULL

Bạn thấy có cái nào không nên làm lúc này thì nói mình dừng.
