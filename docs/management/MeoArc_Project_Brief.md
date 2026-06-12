# MeoArc – Project Brief (cập nhật 12/06/2026)
> File ngữ cảnh cho AI assistant. Gửi file này ở đầu phiên chat mới để khôi phục toàn bộ thông tin đồ án.

## 1. Thông tin chung
- Môn: Nhập môn Công nghệ Phần mềm (Intro2SE), HCMUS – VNU, Nhóm 7
- Đề tài: **MeoArc** – trợ lý quản lý email thông minh (Gmail), LLM agent làm bộ não điều phối
- Người đang chat: **Phạm Trần Anh Quân (24127226) – Frontend Lead**, kiêm setup GitHub/Jira, tổng hợp Mục 1, điều phối video

## 2. Thành viên & vai trò
| Tên | MSSV | Vai trò |
|---|---|---|
| Nguyễn Chí Tài | 24127529 | Backend Lead (FastAPI, PostgreSQL, Redis, Gmail API, OAuth) |
| Nguyễn Ngọc Thiên | 24127545 | AI Lead (Gemini function calling, LangGraph, prompt engineering) |
| Phạm Trần Anh Quân | 24127226 | Frontend Lead (React, Figma, UI) |
| Phan Quang Tiến | 24127250 | QA/Tester (test plan, Docker, CI, Mục 6-7-9) |

## 3. Deadline
- Template 0 Proposal: **14/6** · Template 1 Requirements: **28/6** · Template 2 Design: **5/7** · Template 3 Testing: **12/7** · **Defense: 20/7**
- Jira có 5 sprint: S0-Proposal → S4-Defense Prep (13–20/7)

## 4. Kiến trúc đã chốt (trong proposal)
- FE: React (Vercel), chat + **dynamic canvas** (email cards, draft preview, timeline tiến trình, nút xác nhận)
- BE: FastAPI (Render), AI Gateway, OAuth2 + JWT, rate limit, logging (LangSmith)
- AI: Gemini API + **LangGraph** agent, function calling, human-in-the-loop (Plan → Approve → Execute → Notify)
- Data: PostgreSQL + pgvector (Neon), Redis (cache/session)
- External: Gmail API, Gemini API
- Costing: toàn bộ free-tier, 0 VND

## 5. TIÊU CHÍ ĐIỂM (từ thầy – quan trọng nhất)
README môn: old-school ≤7 · smart không LLM ≤8.5 · LLM wrapper ≤9 · **LLM as main program (tools/API/MCP/skills) = 10**

Q&A thầy giải thích:
- "Smart" = có gợi ý/đề xuất/AI-ML; tự động hóa đơn thuần KHÔNG tính
- Điểm = sự nghiêm túc + độ hoàn thiện + độ phức tạp TRONG TỪNG BÀI NỘP
- App gọi API GPT/Gemini = "LLM-Powered App", **tối đa 9đ**
- "LLM as main program" = **agent-native software**: user dùng AGENT CỦA HỌ tương tác với app (không dùng app trực tiếp); app phải MỞ KÊNH cho agent ngoài (MCP/CLI)
- Ví dụ cụ thể thầy cho (đề email): app tự đọc mail → gửi LLM trích đơn → tạo đơn = 9đ. Mở kênh MCP/CLI để Claude/Codex CỦA USER tự lấy mail, TỰ TRÍCH, tự gọi tool tạo đơn = 10đ
- Hệ quả thiết kế: MCP server phải phơi **tool hạt mịn** (search_emails, get_email_content, send_email, apply_label, batch_delete...) để agent ngoài TỰ SUY LUẬN — không phơi tool to kiểu summarize_and_process (suy luận vẫn của app → vẫn 9đ)

## 6. Chiến lược 10 điểm
- Mốc 9 (sàn): hoàn thiện app + Gemini agent nhúng như kiến trúc hiện tại
- Vé lên 10: thêm **MCP server** phơi bộ tool email cho agent ngoài (Claude Desktop/Codex). Một bộ tool lõi, 3 khách: UI người dùng, Gemini nội bộ, agent ngoài qua MCP
- Demo defense 2 cảnh: (1) dùng web app, (2) Claude Desktop điều khiển MeoArc qua MCP không mở web
- CLI là phương án dự phòng hợp lệ nếu MCP trục trặc
- Đã thêm vào proposal: user story MCP (3.1.1), khối MCP Server trong sơ đồ (3.1.2), activities MCP trong Dev Plan (mục 4)

## 7. Trạng thái Template 0 (đến 12/6)
Đã xong: Mục 2, 3.1.1 (có dòng dynamic canvas + đang thêm MCP), 3.1.2 (sơ đồ đẹp), 3.2, 4, 5, 9; GroupID/tên đã điền; entry Gemini hết lặp
Còn thiếu / đang làm:
- Mục 1: chuyển Jira sang **subtask** (1 task mẹ/người + subtask = từng mục template), điền Start/Due date ≤14/6, kéo Done, chụp panel TỪNG SUBTASK (đủ 5 trường: Task Name, Assignee, Status, Assigned Date, Completion Date). Lưu ý: evidence chứng minh CẢ chia việc VÀ đã hoàn thành (Status=Done)
- SCRUM-2: chưa gán người, due 19/6 (sai, phải ≤14/6)
- Mục 7: thiếu **entry Claude** (bắt buộc khai – đã dùng Claude cho: chọn đề tài, kế hoạch sprint, phân công, hướng dẫn tool, review proposal, gợi ý dynamic canvas + MCP); placeholder <gpt-chat-history> chưa thay link thật; version GPT không nhất quán (GPT5.5 vs GPT-4o – cần xác nhận)
- Mục 8: chưa có link YouTube (video chưa quay – việc gấp nhất)

## 8. Quy ước làm việc đã thống nhất
- Mỗi task Jira 1 người; người Edit/Review ≠ người Write; % đóng góp tổng ≤100 (đang chia 25×4)
- Repo GitHub "MeoArc" (public): /src (frontend, backend, agent) + /docs (management, requirements, analysis and design, test) + /pa (pa0…)
- AI Usage: mọi lần dùng AI phải log (tool, version, giờ, prompt, mục đích, phần AI làm/người làm, screenshot/link)
- Mọi sửa đổi proposal sau khi nộp → tạo version mới, lưu mọi version
