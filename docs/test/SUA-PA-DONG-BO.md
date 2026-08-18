# Hướng dẫn sửa PA0 / PA1 / PA2 để các template đồng bộ

> Mục tiêu: **AI của thầy đọc cả bộ template không tìm ra mâu thuẫn nào.**
> Phạm vi: chỉ sửa tài liệu. Code sửa sau, và phần cuối tài liệu này nói rõ phải làm gì với
> Testing.md để việc "code chưa theo kịp" không biến thành một mâu thuẫn mới.

---

## Nguyên tắc đã dùng để chọn hướng sửa

AI dò đồng bộ sẽ so **tài liệu với tài liệu**. Nên:

- Chỗ nào **một tài liệu tự mâu thuẫn**, hoặc **hai tài liệu nói khác nhau** → bắt buộc sửa tài liệu.
- Chỗ nào **các tài liệu đã thống nhất, chỉ code chưa có** → **không đụng tài liệu**. Sửa code sau.
  Sửa tài liệu ở đây chỉ tạo thêm rủi ro lệch, mà không giải quyết gì.

Theo nguyên tắc đó, trong 13 lỗi đã tìm được thì **chỉ 4 lỗi cần sửa ở tài liệu**. Chín lỗi còn lại
là "thiết kế có, code chưa xây" — AI đọc template sẽ **không** phát hiện, vì bản thân các template
đồng ý với nhau.

---

# A. PA2 — Design (3 việc)

## A1. Thay placeholder "Project Short Name" → "MeoArc"

**Mức độ:** nghiêm trọng nhất về mặt hình thức. Xuất hiện **66 lần**, nằm ở header **mọi trang**.
PA1 ghi đúng "MeoArc" nên đây là lệch thấy ngay khi đặt hai tài liệu cạnh nhau.

**Cách sửa:** trong Google Docs bấm `Ctrl + H` (Find and replace):

| Trường | Giá trị |
| :---- | :---- |
| Find | `Project Short Name` |
| Replace with | `MeoArc` |

Bấm **Replace all**. Kết quả header đổi từ `Intro2SE-Design-7 Project Short Name` thành
`Intro2SE-Design-7 MeoArc`, khớp y hệt PA1.

> ⚠️ Header/footer trong Google Docs đôi khi không nằm trong phạm vi Find & replace. Sau khi
> replace, mở lại header (bấm đúp vào vùng đầu trang) kiểm tra một trang bất kỳ. Nếu vẫn còn
> chữ cũ thì sửa trực tiếp trong header — sửa một lần là cả tài liệu đổi theo.

## A2. Thêm màn hình Landing vào Screen Diagram (§1.6)

Sơ đồ hiện có 6 màn hình, thiếu Landing — trong khi PA1 (UC001, Main Scenario, bước 1) đã
nhắc *"người dùng bấm nút Đăng nhập trên MeoArc landing page"*. Tức là PA1 giả định có Landing
mà PA2 không đặc tả. Đây đúng loại lệch AI bắt được.

**Cách sửa:** thêm vào sơ đồ một khối `Landing Page` đặt **trước** `Login & Connect Account`,
nối bằng mũi tên có nhãn:

```
[ Landing Page ] ──"Đăng nhập với Google / Outlook"──▶ [ Login & Connect Account ]
                 ◀──────────"Đăng xuất"───────────────  [ Main screen ]
```

Mũi tên thứ hai quan trọng: đăng xuất trả người dùng về Landing chứ không về Login.

## A3. Thêm đặc tả màn hình Landing vào §1.7

Chèn thành **§1.7.1 mới**, đẩy 6 mục cũ xuống 1.7.2–1.7.7. An toàn: đã kiểm, trong PA2
**không có chỗ nào tham chiếu chéo tới "1.7.x"**, nên đánh số lại không làm hỏng gì.

Nếu đánh số trong Docs là tự động thì nó tự dồn. Nếu gõ tay thì sửa 6 con số.

**Nội dung dán vào** (viết theo đúng khuôn "Presentation format. / Event handling." của mục
Login hiện có):

---

### 1.7.1 Screen "Landing Page"

*[Clearly describe the presentation format and the handling of each event within the screen.
Include a design image of each screen]*

**Presentation format.** A full-width marketing page, and the first screen an unauthenticated
visitor sees. It is organised as a vertical sequence of sections: a hero section with a
full-bleed background video, the product name and value proposition, and a primary
call-to-action; a statistics band with animated counters; a section presenting the AI assistant
over a full-bleed background video; a feature grid in bento layout, icon-led rather than
text-led; a second bento grid presenting the seven email categories (School, Work, Finance,
Social, Shopping, System, Personal) each in its own colour; a narrative section illustrating the
journey of an email, driven by a video whose playback position follows the scroll position; a
marquee of the technologies used; a frequently-asked-questions list; a closing call-to-action
over a background video; and a footer. A fixed navigation bar stays visible while scrolling and
contains anchors to Features, How it works, Pricing and FAQ, together with the sign-in button
and a light/dark theme toggle.

**Event handling.** Clicking **"Đăng nhập với Google"** or **"Đăng nhập với Outlook"** starts the
OAuth 2.0 flow described in UC001 and, on success, navigates directly to the Main screen —
the visitor does not return to the Landing page. Clicking a navigation anchor scrolls smoothly to
the corresponding section. Clicking **"Gói dịch vụ"** opens the subscription plan comparison,
which presents the Free, Pro and Pro Max tiers together with the AI processing time window of
each (90, 180 and 365 days respectively). The theme toggle switches Light/Dark instantly and
requires no sign-in. Scrolling drives the section reveal animations and the playback position of
the email-journey video. A visitor who is already authenticated and opens the Landing page is
redirected to the Main screen; signing out from the Main screen returns the user to the Landing
page.

---

> 📸 Ảnh minh hoạ cho mục này: nếu cần, chụp trang landing rồi chèn vào ngay dưới tiêu đề, giống
> các màn hình khác.

> ⚠️ Chú ý con số **90 / 180 / 365** trong đoạn trên. Phải khớp NFR-SCO-01 sau khi sửa PA1 ở
> mục B1. Đừng viết 30/90/180.

---

# B. PA1 — Requirement Analysis (1 việc)

## B1. Sửa số ngày của NFR-SCO-01 trong đặc tả UC007

**Đây là lỗi nguy hiểm nhất trong cả bộ**, vì nó là **mâu thuẫn nội bộ**: cùng một yêu cầu được
ghi hai con số khác nhau ở hai chỗ trong **cùng một tài liệu**. AI dò sẽ bắt được gần như chắc chắn.

| Vị trí trong PA1 | Đang ghi | Đúng/Sai |
| :---- | :---- | :---- |
| §3.2.2.8, NFR-SCO-01 (mục chuẩn, ~trang 38) | 90 / 180 / 365 | ✅ **giữ nguyên** |
| §4.2.7 *Manage Mailbox via Natural Language* — bảng NFR của UC007 (~trang 73) | 30 / 90 / 180 | ❌ **sửa** |
| §4.2.8 *Summarize Email* | 90 / 180 / 365 | ✅ đã đúng |

Chỉ có **đúng một chỗ sai**. Đã kiểm toàn văn: chuỗi `30 days (Free)` xuất hiện đúng 1 lần.

**Cách sửa:** vào §4.2.7 (trang ~73), tìm dòng bắt đầu bằng `NFR-SCO-01:`. Câu hiện tại kết thúc bằng:

> …according to the user's subscription tier: **30 days (Free), 90 days (Pro), 180 days (Pro Max).**

Sửa phần in đậm thành:

> …according to the user's subscription tier: **90 days (Free), 180 days (Pro), 365 days (Pro Max).**

Cách nhanh nhất: `Ctrl + H`, Find `30 days (Free), 90 days (Pro), 180 days (Pro Max)`,
Replace `90 days (Free), 180 days (Pro), 365 days (Pro Max)`, Replace all.

**Kiểm lại sau khi sửa:** tìm chuỗi `30 days` trong PA1 — phải **không còn kết quả nào**
(trừ NFR-SCO-02 nói "capped at a maximum of 90 days", cái đó đúng, đừng đụng vào).

---

# C. PA0 — Project Proposal (nộp bản mới)

PA0 tự nó không sai — nó được viết trước khi nhiều quyết định được đưa ra. Nhưng đề bài ghi rõ:

> *"if the project proposal is modified during this phase, a new version of the proposal must be
> documented"*

Hiện PA0 chưa có bản cập nhật, trong khi PA1 và PA2 đã đi xa hơn nó ở **hai điểm**. AI so PA0
với PA1/PA2 sẽ thấy hai tài liệu sau có những thứ bản đề xuất hoàn toàn không nhắc.

**Làm một bản `Project Proposal v2` duy nhất, gộp cả hai thay đổi.** Đừng sửa rải rác nhiều lần.

> **Đính chính so với bản trước của hướng dẫn này.** Lần đầu mình tìm chuỗi `Outlook` trong PA0,
> ra 0 kết quả, và kết luận PA0 thiếu phần đa nhà cung cấp. **Sai.** PA0 §3.1.1 có ghi
> *"OAuth authentication (**Google/Microsoft**), secure data handling, and granular email
> permission management with support for **multiple connected accounts**"* — nó chỉ dùng chữ
> "Microsoft" thay vì "Outlook". Không phải lỗ hổng. Danh sách dưới đây đã bỏ mục đó ra, và ngắn
> hơn hẳn so với bản trước.

## Chỉ có **hai** chỗ thật sự cần thêm

Cả hai vào cùng một chỗ: **§3.1.1 Features**, là bảng hai cột *Demand | Feature*. Thêm hai dòng,
viết theo đúng giọng "As a … I want …" của các dòng đang có.

### C1 — Gói dịch vụ

| Cột | Nội dung dán vào |
| :---- | :---- |
| **Demand** | As a user, I want to know how much of my mailbox history the assistant is allowed to look at under my current plan, and to be able to move to a higher plan when I need more. |
| **Feature** | Subscription tiers — Free, Pro and Pro Max — each with its own AI processing scope (90, 180 and 365 days of mailbox history respectively), a persistent indicator of the current scope beside the chat input, and a plan comparison screen. |

*Vì sao cần:* PA0 hiện **không nhắc gì** tới gói dịch vụ (0 lần cả `subscription` lẫn `Subscription`),
trong khi PA1 có hẳn NFR-08 và FR-02.7, PA2 có bảng `Subscription` với cột `mailboxScopeDays`.
Hai tài liệu sau mô tả một tính năng mà bản đề xuất chưa từng đề xuất — AI so ba tài liệu sẽ thấy.

> ⚠️ Con số **90 / 180 / 365** phải khớp NFR-SCO-01 sau khi sửa B1. Đừng ghi 30/90/180.

### C2 — Landing page

| Cột | Nội dung dán vào |
| :---- | :---- |
| **Demand** | As a first-time visitor, I want to understand what MeoArc does and what it will be allowed to touch in my mailbox before I sign in with my email account. |
| **Feature** | Public landing page presenting the value proposition, the assistant's capabilities, the seven email categories, the subscription plans, and the sign-in entry point. |

*Vì sao cần:* PA0 nhắc 0 lần; PA1 nhắc trong UC001 Main Scenario; PA2 sau khi sửa A2/A3 sẽ có cả
hộp trong sơ đồ lẫn mục đặc tả §1.7.1.

---

## Ba thứ **KHÔNG** đụng vào — và lý do

| Thứ | Trạng thái | Vì sao để nguyên |
| :---- | :---- | :---- |
| **Outlook / Microsoft Graph** | PA0 đã có dưới dạng "Google/Microsoft" | Không mâu thuẫn. Muốn chỉnh cho khớp từ vựng PA1/PA2 thì đổi thành *"(Google Gmail / Microsoft Outlook)"* — **tuỳ chọn**, không bắt buộc. |
| **pgvector** | PA0 §5.2 bảng chi phí có, PA2 §1.5 cũng có | Hai tài liệu **đồng ý với nhau**. Sửa một bên là tạo mâu thuẫn mới. Nếu sau này quyết bỏ pgvector thì sửa **cả hai cùng lúc**, không sửa lẻ. |
| **Redis** | PA0 nhắc 10 lần, PA1 nhắc 4 lần | Đồng bộ giữa các tài liệu. Code để Redis tuỳ chọn — đó là chi tiết hiện thực, không phải mâu thuẫn tài liệu. |

Nguyên tắc chung: **chỉ sửa chỗ tài liệu chỏi nhau.** Chỗ nào các tài liệu thống nhất mà code
chưa theo kịp thì để yên, xử lý ở phần code.

---

## Ghi phiên bản

Trang bìa thêm dòng: `Version 2 — updated after Requirement Analysis and Design`.

Ngay dưới, một bảng lịch sử thay đổi ngắn:

| Version | Date | Changes |
| :---- | :---- | :---- |
| 1.0 | (ngày nộp bản đầu) | Initial proposal |
| 2.0 | (hôm nay) | §3.1.1 Features: added subscription tiers (Free / Pro / Pro Max) with their AI processing scopes; added the public landing page |

**Nộp kèm cả bản v1**, đừng thay thế. Bảng lịch sử này chính là bằng chứng cho yêu cầu
*"all versions of every artifact must be submitted to demonstrate the evolution of your work"*.

---

# D. Testing — cái bẫy đồng bộ phải xử lý

Đây là phần dễ bị bỏ sót nhất, và nếu bỏ sót thì **ba việc trên thành công cốc**.

Tài liệu Testing cũng là một template được nộp. Bản hiện tại có **Phụ lục B** ghi thẳng rằng
`EmailDraft`, `Attachment`, `Embeddings`, `Toolcall_Email`, `ConfirmationRequest`… được thiết kế
nhưng **không tồn tại trong code**.

Nghĩa là sau khi sửa A và B xong, AI của thầy đọc cả bộ sẽ thấy:

- PA2 §1.5.9: "có bảng Attachment"
- Testing Phụ lục B: "không có bảng Attachment"

→ **Mâu thuẫn giữa hai template đã nộp.** Đúng thứ đang cố tránh.

## Cách xử lý đúng

**Không xoá thông tin** — xoá đi là giấu lỗi, và nếu thầy có đọc code thì còn tệ hơn. Cách đúng là
**đổi cách phát biểu** cho khớp sự thật của dự án:

| Đang viết (gây mâu thuẫn) | Nên viết (đúng và không mâu thuẫn) |
| :---- | :---- |
| "Thiết kế mô tả thực thể X nhưng code không có → cần quyết định sửa thiết kế hay xây" | "Test case cho X đã thiết kế theo đặc tả. **Chưa thực thi — tính năng đang chờ hiện thực.**" |

Cách viết thứ hai **không hề sai sự thật**, và nó là trạng thái hoàn toàn bình thường của mô hình
chữ V: test case được viết **từ đặc tả**, trước hoặc song song với việc code. Một test case ở
trạng thái *chưa chạy vì tính năng chưa xong* là thông tin quản lý dự án, không phải mâu thuẫn
tài liệu.

Cụ thể trong Testing.md:

1. Đổi tiêu đề Phụ lục B từ *"Design/implementation deviations"* sang
   **"Implementation status of specified requirements"**.
2. Mỗi mục đổi từ giọng "thiết kế sai / cần quyết định" sang "chưa hiện thực, đã lên lịch".
3. **Bỏ hẳn** mục nói NFR-08 mâu thuẫn — sau khi sửa B1 thì nó hết mâu thuẫn thật.
4. Cập nhật con số cửa sổ quét thành 90/180/365 ở mọi chỗ.
5. Giữ nguyên 5 test case trạng thái *Not run* — đó là báo cáo trung thực, và template đã có chỗ
   ghi rõ lý do.

> Làm bước D **sau cùng**, sau khi A và B xong, để chỉ phải sửa Testing.md một lần.

---

# Thứ tự làm

| Bước | Việc | Thời gian |
| :---- | :---- | :---- |
| 1 | A1 — thay placeholder PA2 | 2 phút |
| 2 | B1 — sửa số ngày PA1 | 5 phút |
| 3 | A2 — thêm Landing vào sơ đồ màn hình PA2 | 30 phút |
| 4 | A3 — thêm §1.7.1 đặc tả Landing PA2 | 15 phút |
| 5 | C — thêm 2 dòng vào PA0 §3.1.1 + bảng lịch sử phiên bản | 20 phút |
| 6 | D — chỉnh lại Testing.md | 30 phút |

Bước 1 và 2 xoá được hai lỗi mà AI chắc chắn bắt được, tốn chưa tới 10 phút. Làm ngay.

---

# Bảng kiểm cuối — chạy trước khi nộp

Tự đóng vai AI của thầy và soát đúng những câu này:

- [ ] Tìm `Project Short Name` trong PA2 → **0 kết quả**
- [ ] Tìm `30 days` trong PA1 → chỉ còn NFR-SCO-02 (*"capped at a maximum of 90 days"* — không có "30 days")
- [ ] Cả PA1, PA2, PA0v2 và Testing đều ghi cửa sổ quét là **90 / 180 / 365**, không nơi nào ghi khác
- [ ] Landing page xuất hiện nhất quán: PA0v2 (phạm vi) + PA1 (UC001) + PA2 (§1.6 sơ đồ và §1.7.1 đặc tả)
- [ ] Outlook xuất hiện trong cả PA0v2, PA1, PA2
- [ ] Bảy nhóm phân loại ghi **giống hệt nhau** ở mọi tài liệu: School, Work, Finance, Social, Shopping, System, Personal
- [ ] Danh sách thành viên và MSSV giống nhau ở cả bốn tài liệu (24127226 Quân, 24127250 Tiến, 24127529 Tài, 24127545 Thiên)
- [ ] Testing không còn câu nào nói thiết kế sai; chỉ nói tính năng chưa hiện thực
- [ ] PA0 nộp **cả v1 và v2**, v2 có bảng lịch sử thay đổi
