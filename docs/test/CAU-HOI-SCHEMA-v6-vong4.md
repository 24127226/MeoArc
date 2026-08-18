# Vòng 4 — mấy chỗ trống còn lại trong schema

Mình rà lại một lượt cả 25 bảng sau hai vòng vừa rồi. **Không còn chỗ nào mâu thuẫn** —
khoá ngoại nối được hết, cột chết đã dọn, `attachment.extracted_text` với `email_id` cũng
khớp rồi. Schema đứng vững.

Còn bốn chỗ **trống**, không phải sai — kiểu chưa ai nghĩ tới. Một chỗ mình nghĩ là kẹt
thật, ba chỗ còn lại nhỏ.

---

## 1. Đếm token ở đâu?

Chỗ này mình thấy kẹt nhất.

`tool_call.token_usage` ghi được từng lời gọi, nhưng `subscription` không có bộ đếm nào. Mà
hạn mức token thì phải kiểm **trước mỗi lượt chat** — "hôm nay người này dùng bao nhiêu
rồi, còn được hỏi nữa không".

Với schema hiện tại thì câu đó phải `SUM(token_usage)` qua `tool_call` → `message` →
`conversation` → `user`. Ba phép nối, chạy mỗi lượt chat, trên đúng cái bảng phình nhanh
nhất. Mình nghĩ không trụ được lâu.

Hai hướng mình nghĩ tới:

- **Bộ đếm ngay trên `subscription`**: `tokens_today` + `day_key` + `tokens_month` +
  `month_key`. Đọc một dòng là xong, sang ngày mới thì tự reset khi chạm vào. Đơn giản,
  nhưng trộn "tính tiền" với "đo mức dùng" vào một bảng.
- **Bảng `usage_counter` riêng**: `(user_id, period_key)` làm khoá, cộng dồn vào đó. Sạch
  hơn về ngữ nghĩa, thêm một bảng.

Mình nghiêng về cách 1 cho MVP. Bạn thấy sao?

---

## 2. Phiên đăng nhập web nằm ở đâu?

Có `user`, có `connected_account` (token OAuth của hộp thư), có `mcp_credential` — nhưng
mình không thấy chỗ nào lưu **phiên trình duyệt** của người đang đăng nhập.

PA0 có nhắc "Session management with JWT (access + refresh token)". Nếu đi hướng JWT thì
đúng là không cần bảng thật. Nhưng lúc đó **đăng xuất và thu hồi quyền (UC002) không vô hiệu
hoá được token đã phát** — nó vẫn sống tới lúc hết hạn, trừ khi có một danh sách chặn.

→ Ý bạn là JWT thuần, hay có bảng `session`? Nếu JWT thì mình nghĩ cần thêm bảng nhỏ kiểu
`revoked_token(jti, expires_at)` để UC002 làm được đúng việc của nó.

---

## 3. Trạng thái đồng bộ hộp thư còn thiếu hai thứ

`history_id` trên `gmail_account` và `delta_link` trên `outlook_account` là đúng chỗ rồi.
Nhưng còn thiếu:

- **`watch_expiration`** — đăng ký nhận đẩy của Gmail hết hạn sau khoảng 7 ngày, phải gia
  hạn. Không lưu hạn thì không biết lúc nào cần gia hạn, và một hôm nào đó thư ngừng tự về
  mà không ai biết vì sao.
- **`last_synced_at`** — để biết lần đồng bộ gần nhất, và để hiện "cập nhật lúc..." trên
  giao diện.

Mình nghĩ để cả hai lên `connected_account` (chung cho hai provider) hợp lý hơn là nhét vào
từng bảng subtype.

---

## 4. `tool_call.call_seq` cho lời gọi qua MCP thì đánh số thế nào?

`call_seq` để `NOT NULL`, nhưng ràng buộc duy nhất chỉ áp `WHERE message_id IS NOT NULL` —
tức là chỉ cho nhánh chat. Lời gọi từ agent ngoài (`mcp_credential_id`) vẫn buộc phải điền
`call_seq` mà không có luật nào nói điền theo cái gì.

→ Hai cách: cho `call_seq` nhận NULL ở nhánh MCP, hoặc đánh số theo `mcp_credential`. Bạn
thấy cái nào hợp?

---

## Mấy thứ nhỏ, thấy thì nói luôn

Không quan trọng, để đó cũng chạy được:

- **`email` thiếu `updated_at`** — mà `ai_category` / `ai_priority` / `ai_task_status` thì
  bị ghi lại mỗi lần phân loại lại. Có `updated_at` thì biết nhãn được gán lúc nào.
- **`embedding` có cả `chunk_index` (NULL) lẫn `embedding_seq` (NN)** — hai cột cùng để
  đánh thứ tự chunk. Giống ca `embedding_type` vừa bỏ, chắc gộp được một.
- **`plan_catalog.created_by` là FK sang `user` và `NOT NULL`** — mấy dòng giá khởi tạo lúc
  cài đặt hệ thống thì chưa có admin nào để trỏ tới. Cho NULL, hoặc dựng sẵn một user hệ
  thống.
- **`email_draft.status` đang là `pending`/`sent`/`discarded`**, còn PA2 §1.3.10 viết
  `draft`/`sent`. Chỉ là chữ, nhưng nên thống nhất một bộ.

---

Chốt xong bốn cái trên là mình bắt tay dựng được. Mình định làm theo bốn nhát: nhánh tài
khoản trước (`connected_account` + subtype), rồi nhánh thư (`email_thread` → `email` →
`attachment`), rồi nhánh agent (`message` + `tool_call` + `confirmation_request`), cuối cùng
là `plan_catalog` / `user_preference` / `mcp_credential` / `embedding`.

Nhánh thư là nặng nhất vì `email` đổi từ bảng phẳng sang ba tầng, kéo theo mọi truy vấn thư.
