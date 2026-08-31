# Kịch bản bảo vệ MeoArc — 15 phút

> **Lời dặn của thầy:** *"Nói nhanh gọn trong 15p, cái gì hay ho nhất thì đưa lên nói sớm để tránh bị bỏ sót."*
> *"Thầy không hỏi code, thầy hỏi về cách các em tạo ra sản phẩm, lý do các em chọn giải pháp."*

Nghĩa là **kể tính năng sẽ mất điểm**. Mỗi phần trình bày phải kể một *quyết định*.

---

## 1. Công thức trả lời — dùng cho mọi câu, mọi người

| Bước | Nội dung |
|---|---|
| **Vấn đề** | Chuyện gì hỏng nếu không làm gì cả |
| **Đã loại** | Phương án hiển nhiên mà nhóm *không* chọn |
| **Vì sao loại** | Điều gì ở phương án đó sẽ hỏng — nói cụ thể |
| **Đã chọn** | Giải pháp, gọn trong một câu |
| **Bằng chứng** | Một con số, hoặc một thao tác chạy được |

Phần **"đã loại"** là chỗ ăn điểm. Nói được mình đã cân nhắc và bỏ cái gì thì thầy thấy có suy nghĩ; chỉ liệt kê tính năng thì nghe như đọc README.

---

## 2. Sáu chỗ ăn điểm

*(xếp theo thứ tự nên nói — hay nhất lên trước)*

### 01 · Lịch trình sinh ra từ hộp thư

- **Vấn đề** — Gmail đã có danh sách thư. Làm thêm một Gmail nữa thì không ai dùng.
- **Đã loại** — Trích "sự kiện" như Google Calendar.
- **Vì sao** — Sự kiện chỉ là một khối thời gian. Nhóm trích **cam kết** — có thêm trạng thái, **người đang chờ**, và lá thư sinh ra nó. Đó là khoảng cách giữa một cuốn lịch và một người trợ lý.
- **Đã chọn** — Luật trước, mô hình sau. Bắt buộc có **cả** động từ cam kết lẫn mốc thời gian mới nhận — nên thư "Sale 9/9" bị bỏ qua dù có ngày tháng.
- **Bằng chứng** — 55 ca kiểm thử dùng chung cho cả hai bản cài đặt; trích được "thứ Sáu tuần này" — dạng Google Calendar bỏ qua.

**Files:**
```
src/backend/app/core/cam_ket.py
src/frontend/src/lib/cam-ket.ts
src/shared/ca-cam-ket.json
src/frontend/src/pages/schedule.tsx
```

---

### 02 · Agent không tự ý làm điều không hoàn tác được

- **Vấn đề** — Mô hình ngôn ngữ có thể gọi "xoá 50 thư" — và nói "đã xoá xong" kể cả khi lệnh lỗi.
- **Đã loại** — Dặn mô hình trong prompt là "nhớ hỏi trước khi xoá".
- **Vì sao** — Lời dặn là **gợi ý**, không phải ràng buộc. Một prompt dài vài trăm dòng thì mô hình bỏ sót là chuyện thường, và hậu quả không hoàn tác được.
- **Đã chọn** — Chặn ở **tầng mã**. Mỗi công cụ khai báo mức rủi ro; loại không-hoàn-tác bị `tool_node` chặn lại thành thẻ chờ duyệt. Thẻ dựng **tất định từ tham số**, không nhờ mô hình viết lại — nên thứ người dùng duyệt *chính là* thứ sẽ chạy.
- **Bằng chứng** — Đo thật: bảo "xoá hết thư quảng cáo" → agent tìm 50 thư rồi DỪNG chờ bấm duyệt.

**Files:**
```
src/backend/app/agent/nodes/tool_node.py
src/backend/app/tools/registry.py
src/backend/app/models/confirmation.py
```

---

### 03 · Agent biết việc gì nó không làm được

- **Vấn đề** — Bảo agent "đặt vé máy bay đi Đà Nẵng", nó đi *tìm thư về vé máy bay* rồi báo "không tìm thấy".
- **Vì sao tệ** — Người dùng hiểu là **hộp thư trống**, không hiểu là MeoArc không làm được. Một yêu cầu ngoài tầm bị âm thầm diễn giải thành việc khác — với agent sắp tiêu tiền thì đây là tính chất nguy hiểm nhất.
- **Đã chọn** — Một **công cụ từ chối** riêng, kèm khối "Phạm vi" đặt *trước* luật "luôn phải tìm thư". Làm thành công cụ chứ không phải lời cấm: mô hình bám theo danh sách công cụ chặt hơn bám theo lời cấm.
- **Bằng chứng** — Lỗi này do chính nhóm đo ra rồi mới sửa; có kịch bản đo 10 yêu cầu ngoài phạm vi.

**Files:**
```
src/backend/app/agent/nodes/agent_node.py
src/backend/app/tools/email_tools.py     (hàm tu_choi_ngoai_pham_vi)
src/backend/tests/test_pham_vi.py
```

---

### 04 · Cổng tiền — bốn lớp, mỗi lớp chặn một kiểu hỏng khác

- **Vấn đề** — Nối agent vào đặt vé thì nó chạm tới tiền thật.
- **Đã loại** — Chỉ dựa vào cổng xác nhận ở mục 02.
- **Vì sao** — Cổng đó chặn *agent*, không chặn *sự cố*. Mạng đứt giữa chừng rồi thử lại thì thành hai vé.
- **Đã chọn** — Khoá chống trùng · trần chi tiêu · nhật ký ghi **trước và sau** · bắt buộc có người duyệt. Ghi trước để biết đã *định* làm gì kể cả khi tiến trình chết giữa chừng.
- **Bằng chứng** — Phép thử giết tiến trình giữa lúc đặt rồi chạy lại → không sinh đơn thứ hai.

**Files:**
```
src/backend/app/services/cong_tien.py
src/backend/app/models/dat_cho.py
src/backend/tests/test_cong_tien.py
```

---

### 05 · MCP hai chiều — vừa là máy chủ, vừa là máy khách

- **Vấn đề** — Trợ lý AI khác (Claude Desktop) muốn thao tác hộp thư này thì phải làm sao.
- **Đã chọn** — MeoArc **là MCP server**: agent ngoài gọi thẳng công cụ, không qua lớp ngôn ngữ. Và MeoArc **là MCP client** khi gọi ra nhà cung cấp đặt chỗ. Cùng một registry công cụ phục vụ cả hai — không viết hai lần, không lệch hành vi.
- **Đáng nói** — Cổng xác nhận có bản *riêng* cho đường MCP. Vì đường đó không đi qua LangGraph, nên chặn ở một chỗ là hở chỗ kia.

**Files:**
```
src/backend/app/mcp/server.py
src/backend/app/tools/registry.py
src/backend/app/services/dat_cho.py
```

---

### 06 · Hai quyết định hạ tầng, cả hai đều từ số đo

**Chặn vùng.** Google không phục vụ Gemini cho Hong Kong, mà máy chủ đặt ở Azure East Asia. Chạy máy nhà thì được, deploy thì không — **lỗi chỉ xuất hiện ở một môi trường**.
*Đã loại:* dời App Service (URL đổi → phải khai báo lại OAuth).
*Đã chọn:* Cloudflare Worker đẩy lời gọi qua Durable Object ghim ở Bắc Mỹ.
*Bằng chứng:* đo từ bên thứ ba — lời gọi đi ra từ `172.68.35.102` · Denver · Colorado · US.

**Hạn mức.** Gemini free chỉ **20 lượt/ngày mỗi model** — đủ để chết giữa buổi bảo vệ. Hạn mức tính riêng từng model, nên nhóm xâu chuỗi dự phòng. Chỉ rơi khi *hết hạn mức*: rơi vì lỗi khác là che mất lỗi thật.

**Files:**
```
infra/cf-gemini-proxy/src/worker.js
src/backend/app/core/llm.py
src/backend/tests/test_llm_du_phong.py
```

---

## 3. Chia phần — 15 phút

| Phút | Người | Nói gì | Đọc file nào để chuẩn bị |
|---|---|---|---|
| **0–2** | Mở đầu | MeoArc **không phải Gmail thứ hai**. Vấn đề: người ta lỡ hẹn không phải vì thiếu hộp thư, mà vì cam kết nằm rải rác trong thư. Nêu luôn điều khác biệt để không bị bỏ sót. | `README.md`, `src/frontend/CLAUDE.md` |
| **2–6** | Lịch trình | Điểm 01. **Demo trước, giải thích sau.** Mở `/lich`, chỉ một đợt dài trải ba tuần, rê chuột cho cả đợt sáng, bấm "+N" mở bảng ngày. Rồi mới nói vì sao trích cam kết chứ không trích sự kiện. | `app/core/cam_ket.py`, `lib/cam-ket.ts`, `pages/schedule.tsx` |
| **6–10** | An toàn | Điểm 02 + 03 + 04. Phần nặng ký nhất — **chặn ở tầng mã, không tin lời dặn**. Demo: bảo agent xoá thư, nó dừng chờ duyệt. | `agent/nodes/tool_node.py`, `services/cong_tien.py`, `tests/test_cong_tien.py` |
| **10–13** | Đi lại & MCP | Điểm 05. Mở khung **Tra cứu đi lại**, để thầy **tự gõ chặng**. Bấm số hiệu → thẻ chuyến bay thật trên Google. Chỉ vào cột giá "—" và giải thích vì sao để trống. Nói rõ: *khâu thanh toán cố ý không làm*. | `api/dat_cho_routes.py`, `services/dat_cho.py`, `mcp/server.py` |
| **13–15** | Hạ tầng & kết | Điểm 06 + kiểm thử. Kết bằng **hướng cải tiến**: đặt vé thật cần hợp đồng đại lý và PCI DSS. | `infra/cf-gemini-proxy/README.md`, `app/core/llm.py` |

Nhóm đông hơn 5 thì tách phần **An toàn** (dài nhất) thành hai: một người nói cổng xác nhận, một người nói cổng tiền. Ít hơn thì gộp phút 10–15 lại.

---

## 4. Ba câu chắc chắn bị hỏi

**"AI ở đây thật ra làm gì?"**
Trả lời thẳng, đừng phóng đại: **AI làm phần trò chuyện và chọn công cụ**. Phần đọc cam kết từ thư là **luật viết tay**, cố ý — vì nó phải chạy trên mọi thư đến, mà gọi mô hình cho mọi thư thì hạn mức cạn trong vài giờ. Lọc rẻ trước, phần khó mới đưa cho mô hình. Nói được cái này là ghi điểm về *tư duy chi phí*.

**"Dữ liệu chuyến bay này thật hay giả?"**
**Mời thầy tự kiểm, đừng trả lời bằng lời.** Bấm vào chính **số hiệu** trên màn hình — nó mở thẳng thẻ chi tiết chuyến bay đó trên Google: đúng giờ, đúng nhà ga, đúng loại máy bay. Rồi chỉ vào cột giá đang để dấu **"—"**: *"Cột giá em để trống. Nguồn này cung cấp lịch bay, không bán vé, nên em không có giá — và em không điền một con số cho bảng trông đầy đủ hơn."* Thiếu cột giá ở đây là **điểm mạnh**, không phải điểm yếu.

*(Chưa cắm khoá thì lui về mô phỏng: chỉ vào nhãn nguồn, nói thẳng là mô phỏng, và nói thêm rằng số hiệu cố ý **không** bấm được vì nó dẫn tới trang trống.)*

**"Sao không đặt vé luôn cho hoàn chỉnh?"**
Câu **dễ ăn điểm nhất** nếu trả lời đúng. Đặt thật cần hợp đồng đại lý với hãng và tuân thủ PCI DSS cho dữ liệu thẻ — **không phải vấn đề kỹ thuật**, và không phù hợp với một đồ án môn học. Nhóm dừng ở đúng ranh giới đó và làm đầy đủ mọi thứ trước nó. Biết mình dừng ở đâu và vì sao là một quyết định, không phải một thiếu sót.

---

## 5. Đừng nói những câu này

Nói quá là cách nhanh nhất mất điểm.

- ❌ **"MeoArc đặt vé được"** — không. Khâu đặt là mô phỏng, và giao diện tự ghi rõ. Bị bắt nói quá một lần thì mọi câu sau đều bị nghi.
- ❌ **"AI tự phân tích và trích lịch trình"** — phần trích là luật viết tay. Nói thật lại *hay hơn*, vì nó cho thấy nhóm cân nhắc chi phí.
- ❌ **"Chạy được hết mọi trường hợp"** — bộ trích không hiểu "nộp sau khi thầy duyệt đề cương". Mọi cam kết đều mang **độ tin cậy**, và dưới ngưỡng thì giao diện *hỏi* chứ không khẳng định. Đó là thiết kế, không phải lỗi.
- ❌ **Đừng đọc code lên slide.** Thầy đã nói không hỏi code. Chỉ nói *quyết định* và *vì sao*.

---

## 6. Cho các bạn tự tra bằng AI riêng

Dán nguyên đoạn này vào AI của bạn ấy:

> "Mình đang chuẩn bị bảo vệ đồ án. Đọc file `<tên file>` trong repo `24127226/MeoArc` nhánh `integration` và trả lời giúp mình ba ý: **(1)** file này giải quyết vấn đề gì, **(2)** nó chọn cách làm nào và *bỏ* cách làm nào, **(3)** có con số hay phép thử nào chứng minh nó chạy đúng không. Trả lời bằng tiếng Việt, đừng giải thích cú pháp code."

Chú thích trong mã đã ghi sẵn phần "vì sao" và "đã loại phương án nào" — đó là chỗ AI của bạn ấy sẽ tìm thấy câu trả lời, không phải ở tên hàm.
