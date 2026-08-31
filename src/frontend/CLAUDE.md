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

### Hệ thống thiết kế "Iridescent" — `src/index.css`
2 theme chốt: Light **"Twilight Sky"** (nền trời lam tím `#C6CBF4`, KHÔNG dùng trắng) + Dark **"Iridescent Night"** (nền tím đêm `#0A0718`). Màu rút trực tiếp từ khung hình đầu trang giới thiệu (`public/landing/flower-field-poster.jpg`): tím điện `#977DFF` = hành động · cyan `#87F5F5` = trạng thái/chưa đọc · amber `#FF8A1E` = nhấn · magenta `#FF2FA3` = cảnh báo. Cùng hệ với landing nên đăng nhập xong vào app không bị "nhảy màu".
Nền app có **dải cực quang** (`.aurora-stage` + `.aurora-ribbon-1/2/3` trong app-shell) mô phỏng vệt sáng trong ảnh; đặt dưới tầng `relative z-10` của 3 cột.
Token `--background/--list/--panel/--rail/--spark/--active/--accent/--sc-base/--sc-ink`... Utilities chất liệu (dùng lại, tự đổi theo theme — KHÔNG hardcode màu):
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
  - **Ba mục chính to + thư mục thành LƯỚI Ô VUÔNG luôn hiện** (`OThuMuc`, 3 cột khi
    mở / 1 cột khi thu). Bản trước giấu 6 thư mục sau nút "Thư mục": sửa được thứ
    bậc nhưng để lại khoảng trống cao ~350px giữa thanh (đo trên 1440×900) và thêm
    một cú bấm mới tới được Thư rác. Lưới vuông xoá cả hai.
  - **Dải áp lực 7 ngày** (`DaiApLuc`) lấp phần trống còn lại bằng THÔNG TIN, không
    phải hoạ tiết. Thang TUYỆT ĐỐI (trần 6 giờ) chứ không co theo tuần — co thang
    thì tuần nhẹ trông y hệt tuần nặng. Tuần nhẹ cho cột thấp nên có thêm dòng số
    bên dưới. `apLuc` do app-shell tính rồi truyền vào; không truyền thì không vẽ,
    giữ nav rail độc lập với tầng lịch trình.

### Bộ thư dày — `src/data/demo-qua-tai.ts`
~50 cam kết dồn cục (vài ngày 8–10 việc) + 2 đợt nhiều tuần, để ba cơ chế xử lý quá
tải (xếp làn, chip "+N", bảng ngày) THẬT SỰ chạy khi xem. Bộ thường chỉ 17 việc rải
đều nên chúng gần như không bao giờ kích hoạt — không thấy chạy thì cũng không biết
đúng hay sai. Tắt bằng `BAT = false` trong chính file đó.

### Hai bẫy bố cục đã sửa (đo được, dễ tái phát)
- **`DialogContent` thiếu trần chiều cao.** Chỉ có `top-1/2 -translate-y-1/2` mà
  không `max-height`/`overflow`, nên hộp thoại cao hơn màn hình tràn CẢ HAI đầu và
  không cuộn được — mất luôn phần trên lẫn dưới. Đo ở tab "Cá nhân hoá": nội dung
  816px trong khung 804px. Đã đặt `max-h-[calc(100dvh-2rem)] overflow-y-auto` ở
  `ui/dialog.tsx` (áp cho MỌI hộp thoại, không riêng màn Cài đặt). `dvh` chứ không
  `vh` vì thanh địa chỉ di động co giãn.
- **Nav thu gọn đẩy cụm đáy ra ngoài màn hình.** Phần giữa thiếu `min-h-0 flex-1
  overflow-y-auto` nên nó không co được và đẩy hồ sơ/cài đặt/thông báo ra ngoài —
  đo được: nội dung 820px trong khung 804px, nút hồ sơ đáy ở 808px. Dải áp lực
  cũng chỉ vẽ khi ĐANG MỞ: ở 76px nó không đọc được mà vẫn ăn 64px chiều cao.

### Chuyển cảnh — `src/lib/chuyen-canh.ts`
`chuyenCanh(fn)` bọc thay đổi trạng thái trong View Transitions API. `flushSync` là
BẮT BUỘC (React 19 gom cập nhật; thiếu nó thì trình duyệt chụp "ảnh mới" lúc DOM
chưa đổi và không có chuyển tiếp nào). Thoái lui an toàn khi trình duyệt thiếu API,
tôn trọng `prefers-reduced-motion`. Dùng cho: đổi trang (nav rail → `/lich`, nút quay
lại), mở/đóng thư toàn màn, mở chat ở trang lịch. CSS `::view-transition-old/new(root)`
thêm trượt nhẹ — mờ chồng thuần không cho biết cái cũ đi đâu, cái mới từ đâu tới.
Đã đo: bấm "Lịch trình" → gọi 1 lần, bấm quay lại → 2 lần.

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

## Lịch trình — trang riêng `/lich` (thêm 2026-08-28)

**Vì sao là TRANG RIÊNG, không phải một tab trong hộp thư.** Hộp thư cố ý chiếm
một cột hẹp — đó là quyết định sản phẩm: người ta không vào MeoArc để đọc thư và
thao tác từng lá như Gmail; nếu chỉ cần thế thì họ đã ở lại Gmail. Lịch trình thì
ngược lại — đó chính là thứ MeoArc làm mà Gmail không làm, nên nhét nó vào một cột
giữa ba cột là tự hạ nó xuống ngang hàng với "Thùng rác".

- `src/lib/cam-ket.ts` — trích **cam kết** (không phải "sự kiện") từ thư. Cam kết
  có thêm trạng thái, người đang chờ, và nguồn gốc — đó là khoảng cách giữa một
  cuốn lịch và một người trợ lý. Đọc được: ngày tuyệt đối, "trong vòng N ngày
  (làm việc)", **thứ trong tuần + tuần này/sau**, "ngày mai/kia/cuối tuần", giờ
  đứng riêng. Bắt buộc có CẢ động từ cam kết LẪN mốc thời gian mới nhận.
  Mọi cam kết mang `doTinCay`; dưới 0.6 thì giao diện HỎI chứ không tự khẳng định.
- `src/pages/schedule.tsx` — HAI KHUNG cạnh nhau, KHÔNG cuộn: cột trái là lịch nhỏ
  + danh sách "Sắp tới" (phần tóm tắt), cột phải là lưới thẻ. Bản trước xếp dọc
  (lịch to rồi tóm tắt bên dưới) nên phải cuộn — mà cuộn trong một trang lịch là
  hỏng: người ta mở lịch để NHÌN THẤY CẢ BỨC TRANH.
  - **Thanh, không phải chấm — và vẽ theo LỚP PHỦ, không theo ô.** Một hạn nộp
    thứ Sáu KHÔNG phải việc của thứ Sáu: cần 6 tiếng thì nó là việc của cả thứ Tư
    và thứ Năm. Bản đầu để mỗi ô ngày tự vẽ phần của mình rồi trông chờ các mảnh
    cạnh nhau trông liền — chúng KHÔNG liền (khe lưới, viền, padding), nên một
    việc ba ngày hiện ra ba viên rời và mắt đọc ra ba việc. Nay `xepDoanTheoTuan`
    tính sẵn mỗi việc chiếm cột nào tới cột nào trên hàng tuần, và `HangTuan` vẽ
    MỘT phần tử trải ngang qua các cột đó. Lớp thanh dùng lại đúng `grid-cols-7
    gap-1` của lớp ô bên dưới nên tự khớp cột, không tính phần trăm tay.
  - **Xếp làn khi nhiều.** Mỗi làn là một hàng của lưới con (`grid-rows-[repeat(3,17px)]`).
    Quá 3 làn thì không vẽ, ngày đó mang số "+N" — thà nói thẳng "còn nữa" hơn vẽ
    tràn làm méo lưới. Ba quy tắc thứ tự, mỗi cái sửa một lỗi đo được:
    1. **Đợt dài xuống làn CUỐI**, việc ngắn lên trên. Đợt dài là bối cảnh; việc
       ngắn mới là thứ phải làm hôm nay. Phân loại theo TỔNG số ngày của cả đợt
       (`tongNgay >= 3 || khoangRoRang`), không theo bề rộng đoạn trong tuần —
       một đợt hai tuần bị cắt thành hai đoạn 7 ngày vẫn là đợt dài.
    2. **Đợt dài xếp TRƯỚC**, từ làn cuối đi lên. Xếp việc ngắn trước thì một tuần
       đông chiếm sạch làn và đợt dài BIẾN MẤT — tệ hơn hẳn mất một việc lẻ, vì
       việc lẻ còn hiện ở "+N" của đúng ngày nó, còn đợt dài không có "ngày của
       nó" để tìm. Xếp từ dưới lên cũng giữ đợt dài CÙNG MỘT LÀN qua các hàng tuần;
       nhảy làn giữa hai hàng thì mắt đọc ra hai việc khác nhau.
    3. **Làn 0 CHỪA RIÊNG cho việc ngắn** — đợt dài chỉ dùng làn 1–2. Đo trên bộ
       thư dày: tuần 14–20/9 có BA đợt dài chồng nhau, chiếm sạch ba làn, và cả
       tuần không hiện nổi một việc hằng ngày nào (tám việc thứ Sáu dồn vào "+8").
       Lịch không cho thấy việc phải làm hôm nay thì hỏng nặng hơn lịch giấu bớt
       một đợt dài.
  - **Ưu tiên là TRỤC RIÊNG (`mucUuTien`), không phải `mucRuiRo`.** Thang rủi ro cố
    ý giữ cấp 3 cực hiếm nên 13/13 việc demo đều cấp 1 — dùng nó để tô thì mọi
    thanh giống hệt nhau. `mucUuTien` gộp `priority` với khoảng cách tới hạn, đi
    theo hệ màu riêng (`.uu-tien-1/2/3`, biến `--ut`) để đỏ ở hai thang không lẫn
    nghĩa. Ba mức khác nhau ở BỐN thứ cùng lúc: hình (▲◆▪), độ dày vạch trái,
    cường độ quầng, độ đậm chữ — chỉ đổi màu là không đủ.
  - **Lưới là BẢN ĐỒ, bảng rê chuột là CHI TIẾT.** Thanh cao 17px trong ô ngày thì
    tiêu đề LUÔN bị cắt — giới hạn của lưới tháng, không sửa được bằng cỡ chữ.
    `ThanhViec` (rộng 300px) mới là chỗ đọc đủ: nhãn ưu tiên, hạn, tiêu đề đầy đủ,
    người chờ, thời lượng, rồi hai nút. Tự lật lên trên khi thẻ sát đáy màn hình.
  - **Mở ra ở chỗ CÓ VIỆC** (`thangNenMo`): nhảy tới tháng chứa việc gần nhất thay
    vì tháng hiện tại — nếu không, ngày 29/08 mở ra là một tháng 8 trống trơn còn
    nội dung thật nằm ở hàng ngoài tháng và bị làm mờ. Chỉ nhảy MỘT LẦN.
  - **Cắt hàng tuần rỗng ở đáy.** Lưới luôn 42 ô nhưng phần lớn tháng chỉ cần 5
    hàng; giữ hàng thừa là ăn mất 1/6 chiều cao để không nói gì.
  - **Vạch tải ở đáy mỗi ô**: `phutMoiNgay` chia đều theo số ngày việc trải qua.
    Cộng thẳng `uocLuongPhut` cho mọi ngày (bản cũ) thì việc 6 tiếng trải 3 ngày
    thành 18 tiếng và ngày nào cũng "quá tải" — cảnh báo luôn bật thì hết tác dụng.
  - **Tràn quá 3 làn → BẢNG NGÀY (`BangNgay`), không nới số làn.** Cho ô cao thêm
    để chứa 7 việc thì hàng tuần đó cao gấp đôi hàng khác, lưới méo, và mất khả
    năng so ngày này với ngày kia bằng mắt — thứ cuốn lịch tồn tại để làm. Phần
    tràn cần một MẶT PHẲNG KHÁC. Số ngày và chip "+N" đều là nút mở bảng; bảng
    liệt kê đủ, cuộn được, không có trần số việc. Trước đó "+N" là chữ chết: nói
    có thứ bị giấu rồi bỏ mặc — tệ hơn không hiện gì.
  - **Đợt nhiều tuần**: `docKhoang` đọc "từ 7/9 đến 25/9". Trước đó `batDau` chỉ suy
    ra từ ước lượng thời lượng (tối đa 480 phút = 3 ngày) nên KHÔNG đợt nào vắt quá
    một tuần. Khoảng nói thẳng dùng `TRAN_NGAY_RO_RANG` (70) thay vì
    `TRAN_NGAY_SUY_RA` (14) — chặn dữ liệu thật ở 14 ngày là tự bóp méo nó.
    Đã đo: đợt 7/9–25/9 ra 3 đoạn ở 3 hàng tuần, đoạn đầu mang chữ, hai đoạn sau
    mở bằng "‹".
  - **`.goc-cat` đặt `position: relative` và THẮNG `fixed` của Tailwind** (CSS tự
    viết nằm ngoài `@layer`). Mọi phần tử nổi dùng class này PHẢI ghi `position`
    nội tuyến. Đã vấp hai lần — nút trợ lý và thanh hành động (đo được: left 2260,
    top 1017 trên khung 1440×900, tức ngoài màn hình).
  - **Chat = nút nổi góc dưới phải.** Mở ra thì lưới tháng NHƯỜNG CHỖ cho danh
    sách — vừa mở chat là đang muốn BÀN về lịch, không phải ngắm lưới tháng.
  Dùng lại đúng `ChatPanel`; truyền `EmailActions` rỗng: trang này không thao tác thư.
- `src/components/layout/alert-overlay.tsx` — báo hiệu nổi trên cùng. Ba quy tắc
  chống làm phiền: một lần cho mỗi thứ (nhớ qua `sessionStorage`), tối đa 2 tin
  cùng lúc, và chỉ báo khi còn kịp làm gì đó (<24h và chưa quá hạn).

### Thang rủi ro — `.rui-ro-1/2/3` trong `index.css`
Khác `.den-vien` (mã hoá trạng thái con trỏ), thang này mã hoá **hỏng thì mất gì**:
hoàn tác được / người khác đã thấy / mất tiền thật. Màu NGỮ NGHĨA tách hẳn khỏi
màu thương hiệu. **Cấp 3 phải hiếm** — cho quá nhiều thứ vào đó thì người dùng học
được rằng ánh đỏ không có nghĩa gì, và đúng lúc cần nó nhất thì nó đã mất tác dụng.
`AgentReply` có thêm kind `dudinh` (thẻ dự định) dùng thang này.
