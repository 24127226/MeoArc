# CLAUDE.md — MeoArc Frontend (Use Case context)

> File ngữ cảnh cho Claude Code. Đọc trước khi dựng/sửa màn theo use case.
> Phần giao diện/bảng màu đã chốt trong code rồi — file này KHÔNG đụng tới thiết kế, chỉ nạp đúng Use Case.

## Dự án
MeoArc — Email Intelligence Platform quản lý Gmail bằng LLM agent. Đồ án Intro2SE, HCMUS, Nhóm 7. Repo này là frontend (React). Backend (FastAPI/Gemini/Gmail/MCP) là repo khác, không dựng ở đây.
Người làm: Phạm Trần Anh Quân — Frontend Lead. Giải thích tiếng Việt, ngắn gọn.

## Mục tiêu
Dựng/hoàn thiện màn theo từng Use Case để chụp ảnh bỏ vào SRS và demo. Mỗi mockup phải bám đúng Main Scenario của UC tương ứng (giữ đồng bộ với tài liệu).

## Actor
- User — dùng qua web.
- External AI Agent (Claude Desktop/Codex) — chỉ qua MCP, duy nhất ở UC012.

## Cơ chế then chốt (áp cho các màn AI)
Human-in-the-loop: mọi hành động không hoàn tác (gửi mail, xóa, bulk) → agent hiện confirmation với đầy đủ chi tiết → user Approve (thực thi) / Reject (hủy, re-plan). Agent hiện plan trước khi chạy multi-step; hỏi lại khi request mơ hồ; báo completion summary sau khi xong.

## 16 Use Cases (đúng tên & ID theo SRS mới nhất)
- UC001 Authenticate with Google — login bằng Google OAuth 2.0, lần đầu tự tạo account. Pre-condition cho mọi UC khác.
- UC002 Logout & Revoke Access — mở account menu → Logout → dialog xác nhận sẽ thu hồi quyền Gmail → confirm → về trang login.
- UC003 View Email List — dashboard hiện list email card (sender, subject, timestamp, preview, read/unread).
- UC004 View Email Details — mở 1 email xem đầy đủ (sender, recipients, subject, body, attachment); cập nhật trạng thái Read.
- UC005 Search & Filter Emails — tìm theo tiêu chí (sender/recipient/subject/date/label/read) HOẶC bằng ngôn ngữ tự nhiên (semantic).
- UC006 Manage Emails — chọn 1/nhiều email → mark read/unread, mark important, apply label, delete; delete cần confirm; hỗ trợ bulk theo tiêu chí.
- UC007 Manage Mailbox via Natural Language — TRUNG TÂM. User chat NL, agent là controller: nhận request → guardrails → reasoning loop (chọn tool / request_confirmation nếu rủi ro) → thực thi qua MCP adapter → trả kết quả ra canvas. Entry point của UC008/009/010/014/015/016.
- UC008 Summarize Email — tóm tắt 1 hoặc nhiều email (read-only). (extend UC007)
- UC009 Categorize Email — phân loại email. (extend UC007)
- UC010 Compose & Send Email — soạn + gửi email, cần confirm trước khi gửi. (extend UC007)
- UC011 Manage Conversation History — xem lại / tiếp tục các phiên chat đã lưu.
- UC012 MCP Client Access — External AI Agent kết nối qua MCP server, gọi trực tiếp các tool (search/summarize/draft/send/reply/bulk/extract tasks) trong phạm vi quyền user cấp, không qua lớp NL. (actor: External AI Agent)
- UC013 Manage Settings — đổi ngôn ngữ hiển thị, đổi theme light/dark.
- UC014 Get Daily Email Digest — báo cáo tóm tắt email theo khoảng thời gian. (AI Skill, extend UC007)
- UC015 Triage Inbox — phân loại email chưa đọc theo độ ưu tiên + gợi ý hành động. (AI Skill, extend UC007)
- UC016 Prepare Meeting Brief — phân tích thread liên quan cuộc họp → brief (action items, deadline, điểm chính). (AI Skill, extend UC007)

## Canvas (panel AI bên phải) cần thể hiện được
ô chat NL · plan card (kế hoạch trước khi chạy) · confirmation prompt (Approve/Reject) · draft/email preview · kết quả dạng card · danh sách task · completion notification · gợi ý skill (Digest/Triage/Meeting Brief).

## Trạng thái triển khai (cập nhật 2026-06-20)

### Stack
React 19 + Vite + TypeScript, Tailwind v4 (CSS-first, token trong `src/index.css`), shadcn-style UI (`src/components/ui`), lucide-react, react-router-dom. Dữ liệu mock trong `src/data`, logic agent/search trong `src/lib`. Chạy: `npm run dev`; kiểm tra: `npm run build`.

### Layout 3 cột — `src/components/layout/app-shell.tsx`
`NavRail` (trái) · `EmailList` (giữa) · panel phải đổi giữa `EmailDetail` (khi mở 1 thư) và `ChatPanel` (AI canvas, mặc định).
- **Nav lọc thật**: `activeNav` ở app-shell → `folder` truyền vào EmailList lọc theo `email.folder` (inbox/sent/drafts/archive/trash, `starred`=thư gắn sao). Tab `agent` chỉ chuyển focus sang ChatPanel. Badge inbox = số chưa đọc thật. Mock có sẵn thư ở sent/drafts/trash (`src/data/emails.ts`). Nút "Trả lời" ở EmailDetail → đẩy `soạn trả lời {sender}` qua `onAgentAction`.

### Hệ thống thiết kế "Cherry căng mọng dưới ánh sáng" — `src/index.css`
2 theme chốt: Light "Pomegranate Editorial" + Dark "Cherry Noir" (token `--background/--list/--panel/--rail/--spark/--active/--accent`...). Utilities chất liệu (dùng lại, tự đổi theo theme — KHÔNG hardcode màu):
- `.glass` frosted · `.gloss` + `.gloss-sweep` (specular + vệt sáng lướt hover) · `.edge-light` (rim mép trên).
- `.ripe` (bề mặt mọng: specular gắt + subsurface đỏ thấu từ trong + tối dồn đáy; CHỒNG lên `.glass`, KHÔNG dùng chung `.gloss` vì cùng chiếm `::after`).
- `.cherry-dot` (chấm/hạt cherry có glow — chưa đọc & grip kéo) · `.bokeh` (đốm sáng nhoè quanh mascot/empty-state) · `.ripe-pulse` (1 nhịp glow khi xong việc) · `.glow-active` · `.stars-faint` · `.skeleton` (shimmer tông cherry).
- `.ai-orb` (AI orb) · `.meo-pet` (mascot mèo SVG, `src/components/meo-mascot.tsx`).
- **Easing vật lý**: class `ease-spring` (nảy/overshoot — hover/press) & `ease-soft` (giảm tốc — panel/width). Token `--ease-spring`/`--ease-soft` trong @theme.
- **Colored shadow**: `.shadow-tint` / `.shadow-tint-lg` đổ bóng theo biến `--tint` (set = màu category) → card/khối AI có quầng đúng màu nội dung (specular ambient occlusion).
- **`.fade-y`**: mask mép trên/dưới vùng cuộn mờ dần (edge-fade "cuộn phim") — dùng cho email-list & canvas chat.
- **Extreme type contrast**: tiêu đề cột serif lớn (Hộp thư 27px, Trợ lý MeoArc 22px) + dòng phụ Super-Micro uppercase `tracking-[0.16-0.18em]` 10px.
- **Agent Thought-Map**: plan card vẽ sơ đồ node (Fetch→…→Done) nối nét đứt, node chạy = spinner/skeleton, xong = `.ripe-pulse` (chỉ hiện khi plan >1 bước; plan bulk đã tăng lên 2-3 bước).
- Cường độ hiệu ứng đang để mức "rõ & mọng". Đã tôn trọng `prefers-reduced-motion` + focus ring a11y.

### Panel co giãn (đã làm)
- **Dải hộp thư** (`email-list.tsx`): kéo giãn bằng grip mép phải (pointer events + pointer capture), kẹp 300–560px, double-click reset (384px), phím ←/→ khi focus, nhớ qua `localStorage['meoarc:listWidth']`.
- **Nav rail** (`nav-rail.tsx`): nút chevron thu (icon-only 76px) ↔ mở (sidebar có nhãn 212px), animate `transition-[width]`, nhớ qua `localStorage['meoarc:navCollapsed']`.

### Tính năng Agent-Native (đã thêm 2026-06-20)
- **AI Triage Badge** (UC015): field `priority` ('action'/'waiting'/'fyi') + `tldr` trong `src/data/emails.ts`; badge "Cần xử lý/Đang đợi" trên email card (`PRIORITY` map trong email-list.tsx).
- **Thread Smart Card** (UC008): khối bento `.ripe` tóm tắt luồng thư ở đầu `email-detail.tsx` (mở/đóng).
- **Contextual Agent Action** (UC016): nút "đoán trước ý định" (Meeting Brief / Trích việc / Tóm tắt / Trả lời) sinh theo nội dung thư → bấm đẩy lệnh qua `app-shell` (`pendingCommand`) vào `ChatPanel` (`injectedCommand`) tự gửi cho agent.
- **Plan tiến trình** (UC007): duyệt plan chạy từng bước skeleton→`.ripe-pulse` (state `exec`/`executedIds` trong chat-panel).
- **Confirmation spotlight** (UC006/010): khi có plan/draft chờ duyệt, làm mờ các message khác + ring `spark` quanh card.
- **Ghost-text compose** (UC010): "Soạn với AI" gõ dần kiểu typewriter + ghost text mờ + con trỏ phát sáng (compose-dialog.tsx).
- **Generative bento widgets** (UC014/015/016): AgentReply kind `brief`/`triage`/`digest` render thành widget tương tác trong chat-panel — Meeting Brief (checklist tick được + avatars + deadline), Triage (nhóm ưu tiên + tick đã xử lý), Digest (tiles số liệu + mini-bar theo nhãn). Kèm **skeleton morphing** khi thinking (khung bento đang hình thành).
- **Signature motion**: View Transitions API morph panel phải khi đổi chi tiết↔canvas (app-shell `withTransition`, `view-transition-name: rightpanel`, thoái lui an toàn) · `.panel-flash` glow viền ChatPanel khi xong tác vụ · spring easing toàn cục.
- **Command Palette ⌘K** (`command-palette.tsx`): mở bằng ⌘/Ctrl+K, gõ lệnh/hỏi trợ lý (đẩy NL qua `runAgentAction`), đổi theme; điều hướng ↑↓/↵/esc.
- **Voice Mode** (`voice-mode.tsx`, mở rộng UC007): nút mic ở ô chat → overlay **mèo MeoMascot làm linh hồn AI bóp to/nhỏ + quầng sáng theo biên độ giọng** (Web Audio) + STT Web Speech API (vi-VN, interim) → transcript đẩy vào `send(text, viaVoice=true)`. Thoái lui an toàn nếu trình duyệt không hỗ trợ / mic bị chặn.
- **TTS 2 chiều** (chat-panel): khi lệnh đến từ voice, agent **đọc lại** câu trả lời (SpeechSynthesis vi-VN, `replyToSpeech`); nút loa bật/tắt ở header (`ttsOn`). Backend thật chỉ cần thay STT/TTS — kế thừa pipeline NL của UC007.
- **Email Detail editorial** (`email-detail.tsx`): eyebrow micro uppercase (nhãn + thời gian) + subject serif 28px + meta "Tới" micro — đồng bộ extreme type contrast.
- **Polish pack:** Toast "cherry glass" (icon tint + thanh đếm giờ `toast-bar`) · **phím tắt** (`/` focus tìm kiếm, `c` soạn thư, `j/k` duyệt thư, `Enter` mở, `Esc` bỏ chọn — trong email-list & compose-dialog) · **hover quick-action** trên thẻ thư (Lưu trữ/Quan trọng/Xoá, `CardAction`) · **AnimatedNumber** (số chưa đọc đếm trượt) · mèo header `is-thinking` khi TTS đọc (`speaking`).
- **Mèo biểu cảm** (`meo-mascot.tsx` prop `mood: idle/happy/thinking/worry`): cười (mắt cong + miệng rộng) khi xong việc (`celebrate()` qua `triggerFlash`); **lo** (mày nhíu + giọt mồ hôi + miệng ∩) khi có plan cảnh báo xoá chờ duyệt (`worried` trong chat-panel).
- **Adaptive accent** (`email-detail.tsx`): panel nhuốm gradient theo `CATEGORY[].bar` của thư đang đọc (lớp top h-44).
- **Onboarding coachmark** (`onboarding.tsx`): thẻ chào mừng + 4 mẹo (3 cột/NL/voice/phím tắt), hiện LẦN ĐẦU, nhớ `localStorage['meoarc:onboarded']`; render trong app-shell.
- **A11y**: reduced-motion phủ mọi animation (ripe-pulse, panel-flash, view-transition, skeleton, orb, pet); `aria-modal` cho palette & drawer; focus-visible ring toàn cục. (Lưu ý: vài chỗ text muted trên nền đỏ chưa đạt WCAG AA — chưa đổi vì palette đã chốt.)

### Tình trạng UC (mockup)
Đủ 16/16: UC001 (login), UC002 (account-menu), UC003 (email-list), UC004 (email-detail + smart card), UC005 (search + NL toggle), UC006 (bulk + label + delete confirm), UC007 (chat-panel: plan/confirm/draft/result/done), UC008 (tóm tắt), UC009 (CategorizeWidget — checklist sửa nhãn từng thư rồi áp dụng), UC010 (DraftCard 4 hành động Gửi/Chỉnh sửa-inline/Viết lại/Huỷ + compose-dialog), UC011 (drawer: View/Continue/Search + Pin/Đổi tên/Xoá có xác nhận + ghim lên đầu), UC012/UC013 (settings-dialog), UC014/015/016 (digest/triage/brief widget).

### Quy ước kỹ thuật
Màu LUÔN qua token/utility (không hardcode hex trong component, trừ `src/data/categories.ts` là nguồn màu category duy nhất). Mỗi panel co giãn dùng `shrink-0` + panel phải `flex-1`. Trạng thái UI cá nhân hoá lưu `localStorage` prefix `meoarc:`.

## Quy ước
Giải thích tiếng Việt file nào sửa và vì sao. Không đổi bảng màu / thiết kế đã chốt trừ khi được yêu cầu.
