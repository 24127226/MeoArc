# MeoArc — Ghi chú Defense (trả lời chênh lệch Proposal ↔ Bản dựng + kịch bản demo)

> Dùng cho buổi bảo vệ 20/7. Nguyên tắc: KHÔNG né — chủ động nêu chênh lệch TRƯỚC khi thầy hỏi,
> kèm lý do kỹ thuật + cái thay thế. "Cắt có chủ đích" là quyết định kỹ sư; "quên" mới là lỗi.

## 1. Vì sao bản dựng lệch proposal? (câu trả lời gốc)

Proposal (12/6) viết Ở GIAI ĐOẠN CHƯA CODE — là kiến trúc kỳ vọng. Khi triển khai, nhóm ưu tiên
nguồn lực cho **tiêu chí chấm cao nhất** (agent-native/MCP = 10đ theo Q&A của thầy) thay vì trải
mỏng qua hạ tầng chưa cần. Mỗi hạng mục cắt đều có bản thay thế đang chạy + đường nâng cấp rõ:

| Proposal ghi | Bản dựng thực tế | Trạng thái |
|---|---|---|
| **Redis** (cache/session) | ✅ **ĐÃ GIẢI QUYẾT**: kho KV cắm-rút (`app/core/kv.py`) — đặt `REDIS_URL` là cache Gmail + rate-limit chạy trên Redis (đa worker); trống = in-memory; Redis chết giữa chừng → tự rơi về memory, app sống (có test) | Khớp proposal, 2 chế độ |
| **pgvector** (semantic search) | ✅ **ĐÃ GIẢI QUYẾT bằng bản tốt hơn cho phạm vi này**: tool `semantic_search` — Gemini embeddings (`gemini-embedding-001`) re-rank tại thời điểm hỏi → "thư về tiền nong" khớp "Invoice #123" dù không chung từ (đã demo thật). pgvector = đường nâng cấp khi cần PERSIST embeddings (ghi rõ trong Design) | Tinh thần proposal đạt; không cần cài extension |
| **LangSmith** (logging) | ✅ **ĐÃ GIẢI QUYẾT**: opt-in qua `LANGSMITH_API_KEY` (0 dòng code khi tắt). Mặc định TẮT có chủ đích: dữ liệu email không rời máy. Bật khi demo → chiếu trace từng bước agent gọi tool cho thầy xem | Khớp proposal + lý do riêng tư |
| **JWT** | Cookie phiên `httponly + samesite=lax` lưu DB, kèm hỗ trợ `Authorization: Bearer` | GIỮ — an toàn hơn JWT-localStorage (chống XSS) + thu hồi được ngay (UC002); Bearer vẫn có cho API client |
| **Deploy Vercel/Render** | Chạy local đầy đủ (FE 5173 + BE 8000 + Postgres) | GIỮ local-first cho demo (OAuth + MCP stdio); deploy là mục tiêu sau 12/7 nếu dư thời gian |
| Gemini "function calling" thuần | **LangGraph** ReAct + structured output (đúng proposal phần AI) | Giữ nguyên, còn nâng: responder ép thẻ + skill library |

**Câu chốt khi thầy hỏi:** *"Nhóm em cắt phạm vi có chủ đích: dồn nguồn lực vào tiêu chí agent-native
(MCP tool hạt mịn + confirm-gate) là thứ quyết định mức điểm, và thay mỗi hạng mục hạ tầng bằng bản
nhẹ hơn nhưng ĐO ĐƯỢC (30+ NFR test, header X-Process-Time). Mỗi chỗ cắt đều chừa sẵn đường nâng cấp."*

## 2. Kịch bản demo 2 cảnh (theo đúng gợi ý của thầy)

**Cảnh 1 — Web app (LLM-Powered):** đăng nhập Google → chat "Thống kê hộp thư" (thẻ digest) →
"Phân loại theo ưu tiên" (thẻ triage) → "Gửi mail cho X..." → agent hỏi xác nhận → "Đồng ý" → gửi
thật → mở drawer lịch sử, F5 vẫn còn phiên (UC011).

**Cảnh 2 — Agent-native (vé 10đ):** đóng web. Mở Claude Desktop → menu (+) chọn prompt
**triage_inbox** của MeoArc → agent ngoài TỰ search/phân tích → bảo nó "xoá các thư bản tin" →
**confirm-gate chặn, agent quay ra hỏi** → đồng ý → chạy thật. Nói với thầy: *"App em phơi tool hạt
mịn, suy luận nằm ở agent CỦA NGƯỜI DÙNG; nhưng hành động không hoàn tác vẫn bị app cưỡng chế
human-in-the-loop ở tầng tool."*

**Backup khi trục trặc:** quota Gemini chết → Cảnh 2 vẫn chạy (không cần key). MCP chết → còn
`uv run pytest tests/ -v` chiếu 48 test xanh + NFR.md làm bằng chứng.

## 3. Giới hạn đã biết (nói trước, đừng để bị hỏi)

- Quota Gemini free (flash-lite ~20 lượt/ngày) → app có rate-limit 8 lượt/phút/người + thẻ lỗi
  phân loại (🚦/⏳/🔑) thay vì sập. Nâng cấp = key trả phí, không đổi code.
- Phân loại `category` màu FE chưa nối enum AI (UC009) — quyết định KHÔNG đoán bừa bằng luật cứng;
  chờ classifier LLM đúng nghĩa. Nêu như "future work có chủ đích".
- Rate-limit/cache in-memory = đúng cho 1 instance; đa instance cần Redis (đã ghi ở NFR.md).
- Các widget FE `plan/draft/categorize/autopilot` hoạt động ở chế độ mock (demo SRS);
  backend thật hiện trả text + xác nhận cho các luồng đó.

## 4. Số liệu "khoe" nhanh

- 61+ test tự động **khách quan** (chuẩn từ hợp đồng FE/SRS/Gmail thật — từng bắt được 8+ bug thật,
  có test từng FAIL sản phẩm trước khi fix: TC-02 triage).
- E2E thật đã chứng minh: gửi mail 2 bước có nhớ ngữ cảnh; **reply nằm đúng thread Gmail**;
  token mã hoá `enc:` trong DB; phiên chat sống qua restart.
- NFR 2 đợt: xem `NFR.md` — mỗi dòng có lệnh chứng minh chạy được.
