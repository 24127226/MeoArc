# 03 — Agent / LLM Spec (UC007 là trung tâm)

> Đặc tả hành vi agent để BE/LLM (Gemini) thay `interpretCommand` (`src/lib/agent.ts` — bản mock rule-based) mà **vẫn ăn khớp với canvas FE**. FE đã định nghĩa "agent phải nói thứ tiếng gì" — chính là union `AgentReply` ([01 §3](01-DATA-MODEL.md)).

## 1. Vai trò & pipeline

Agent là **controller** điều phối toàn bộ AI skill. Pipeline mỗi lượt:

```
Lời người dùng (NL, có thể từ voice)
   → Guardrails (kiểm tra phạm vi, an toàn)
   → Reasoning loop (chọn skill/tool; nếu rủi ro → tạo confirmation)
   → (Read-only) trả kết quả NGAY  |  (Mutating) trả PLAN/DRAFT chờ duyệt
   → Sau Approve: thực thi qua service (Gmail) → trả 'done' + tóm tắt
```

Tất cả đầu ra phải là **một** `AgentReply`. FE tự lo render, spotlight xác nhận, đọc TTS, v.v.

## 2. Bảng ánh xạ ý định → `AgentReply` (reference behavior)

Trích từ `interpretCommand`. Cột "mock match" là từ khoá bản FE hiện dùng (đã bỏ dấu) — LLM thật hiểu rộng hơn nhưng **phải ra đúng `kind`**.

| Ý định (UC) | Mock match (regex rút gọn) | `kind` trả về | Ghi chú |
|---|---|---|---|
| Autopilot (017) | `tu lai`, `autopilot`, `de meo lo`, `don het hop thu` | `autopilot` | đặt **trước** "dọn" để không nhầm archive |
| Daily Digest (014) | `digest`, `diem tin`, `bao cao` | `digest` | read-only |
| Meeting Brief (016) | `brief`, `cuoc hop`, `meeting`, `hop` | `brief` | read-only |
| Summarize (008) | `tom tat`, `summar`, `tong hop` | `result` | có thể giới hạn "chưa đọc" |
| Triage (015) | `trieu`, `triage`, `uu tien`, `sap xep` | `triage` | nhóm high/normal + gợi ý |
| Compose/Reply (010) | `soan`, `tra loi`, `reply`, `compose` | `draft` | **cần duyệt trước khi gửi** |
| Mark read | `danh dau ... doc`, `doc het` | `plan` (`markRead`) | |
| Phân loại tự động (009) | `phan loai tu dong`, `tu dong gan nhan` | `categorize` | user chỉnh nhãn rồi áp dụng |
| Gắn nhãn thủ công (006) | `gan nhan`, `label` | `plan` (`label`) | cần đủ category + thư mục tiêu |
| Lưu trữ/Xoá (006) | `luu tru`/`archive` · `xoa`/`delete` | `plan` (`archive`/`delete`) | **delete có `warn`** |
| Không rõ | (mặc định) | `text` | **hỏi lại**, gợi ý ví dụ |

### Chọn target thư (khi lệnh nhắm vào tập thư)
`interpretCommand` chọn theo: category-keyword (vd "bản tin"→`terra`), hoặc tên/người gửi, hoặc trạng thái (`chưa đọc`, `gắn sao`). LLM thật nên hiểu ngữ nghĩa rộng hơn nhưng **trả về đúng `op.ids`** (danh sách id cụ thể) để FE/BE thực thi không mơ hồ.

## 3. Human-in-the-loop — bắt buộc

| Loại hành động | Ví dụ | Cơ chế |
|---|---|---|
| **Read-only** | tóm tắt, triage, digest, brief | trả kết quả ngay, không hỏi |
| **Ghi, hoàn tác được** | markRead, gắn nhãn, archive, flag | `plan` → Approve (1 bước nhẹ) |
| **Không hoàn tác** | **xoá, gửi thư, bulk** | `plan` có `warn` **/** `draft` → **bắt buộc** Approve; autopilot xếp vào "chờ duyệt" (`risky:true`) |

Quy tắc vàng: **agent KHÔNG bao giờ tự gửi/xoá khi chưa có xác nhận tường minh.** `op` chỉ được thực thi sau khi user bấm Approve (FE gọi `/agent/plan/execute`).

## 4. Guardrails

1. **Mơ hồ → hỏi lại** bằng `text` (vd: "gắn nhãn" mà thiếu nhãn/đối tượng → hỏi "gắn nhãn gì cho thư nào?").
2. **Rỗng → báo nhẹ nhàng** (vd không có thư chưa đọc → `text` "Hộp thư đã sạch 🎉"), không tạo plan rỗng.
3. **Giới hạn phạm vi**: chỉ thao tác trên hộp thư của user hiện tại, trong scope đã cấp.
4. **Tôn trọng folder**: autopilot chỉ quét `folder='inbox'`.
5. **Không bịa dữ liệu**: tóm tắt/brief phải dựa trên nội dung thư thật (BE truyền context email cho LLM).

## 5. Chi tiết từng skill (input → output)

### Summarize — UC008 → `result`
- Input: phạm vi (tất cả / chưa đọc). Output `lines: string[]` (mỗi dòng 1 thư: "Người gửi — Tiêu đề" hoặc tóm tắt câu). `intro` mô tả ngắn.

### Triage — UC015 → `triage`
- Nhóm theo ưu tiên: `high` (priority `action` hoặc starred) vs `normal`. Mỗi item: `{sender, initial, subject, suggest}`. `suggest` = gợi ý hành động ("Trả lời / xử lý ngay", "Đang chờ phản hồi", "Đọc nhanh khi rảnh").

### Digest — UC014 → `digest`
- `stats`: Tổng thư / Chưa đọc / Quan trọng. `breakdown`: số thư theo `label`. `highlights`: vài thư nổi bật.

### Meeting Brief — UC016 → `brief`
- Phân tích thread cuộc họp → `when`, `deadline?`, `attendees[]`, `actions[]` (việc cần làm — FE cho tick), `points[]` (điểm chính).

### Categorize — UC009 → `categorize`
- Đề xuất `category`+`label` cho từng thư (`items[]`). FE cho user **chỉnh từng nhãn + bỏ chọn** rồi mới áp dụng → mỗi thư áp qua `applyLabel`.

### Compose/Reply — UC010 → `draft`
- Sinh `to`, `subject` (Re: …), `body`. FE cho 4 hành động: Gửi / Sửa inline / Viết lại (kèm gợi ý: "ngắn gọn hơn", "trang trọng hơn"…) / Huỷ. **Chỉ gửi sau khi user bấm Gửi.**

### Autopilot — UC017 → `autopilot`
- Quét `inbox`, mỗi thư ra `AutopilotStep` (action + reason + risky). FE tự diễn hoạt (chạy từng bước, time machine, duyệt thư rủi ro) rồi gửi `AutopilotResult` để áp dụng. Quy tắc quyết định: [01 §5](01-DATA-MODEL.md).

## 6. Định dạng & streaming
- Trả **JSON hợp lệ** đúng schema `AgentReply`. Trường thừa sẽ bị bỏ qua; trường thiếu (bắt buộc) làm FE render lỗi.
- Stream tối thiểu: `thinking` → `reply` (xem [02 §E](02-API-CONTRACT.md)).
- `intro` của các kind có canvas (result/plan/draft/brief/triage/digest/categorize/autopilot) là câu dẫn hiển thị dạng bong bóng chat phía trên widget.

## 7. Voice (mở rộng UC007)
- FE có STT (Web Speech, vi-VN) → gửi `message` kèm `viaVoice:true`. Khi `viaVoice`, FE đọc to `text`/`intro` của reply bằng TTS. BE **không cần xử lý audio** — chỉ nhận/đáp text; pipeline NL giữ nguyên. Đây là input modality, không phải UC mới.

## 8. Khác biệt mock ↔ thật (để không hiểu lầm)
- Mock dùng regex bỏ dấu + field tĩnh (`priority`, `tldr` có sẵn trong data). LLM thật phải **tự sinh** `priority`/`tldr`/tóm tắt/brief từ nội dung thư.
- Mock chọn target bằng so khớp chuỗi; LLM thật hiểu ngữ nghĩa nhưng **vẫn phải kết về `op.ids` cụ thể** để thực thi an toàn, có thể kiểm chứng.
