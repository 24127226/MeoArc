# Kịch bản thuyết trình PA2 — Design (phần của Quân)

> **Bối cảnh đã tính vào:** đây là buổi thứ **ba**. Lớp đã nghe Proposal (PA0) và
> Requirement Analysis (PA1) rồi, nên phần mở đầu **không giới thiệu lại sản phẩm** —
> làm vậy là đốt thời gian vào thứ người nghe đã biết.
>
> **Phân vai theo đúng "Written by" trong tài liệu:**
>
> | Mục | Người trình bày |
> | :---- | :---- |
> | Mở đầu + điều phối | **Quân (24127226)** |
> | §2 Conceptual Model | Thiên (24127545) |
> | §1.1 Architecture + §1.2 Class Diagram + §1.3 Class Specs | Tài (24127529) |
> | §1.4 Data Diagram + §1.5 Data Specification | Tiến (24127250) |
> | §1.6 Screen Diagram + §1.7 Screen Specifications | **Quân (24127226)** |
>
> Kịch bản viết bằng tiếng Việt vì đó là ngôn ngữ nhóm đang làm việc. Nếu buổi này
> trình bày bằng tiếng Anh thì nói mình, mình chuyển — thuật ngữ giữ nguyên tiếng Anh
> đúng như trong tài liệu nên chuyển rất nhanh.

---

# PHẦN A — MỞ ĐẦU

**Người nói:** Quân · **Thời lượng:** ~90 giây · **Slide:** 1 slide tiêu đề + 1 slide sơ đồ 4 mục

## A1. Kịch bản (đọc gần như nguyên văn được)

> Em là Phạm Trần Anh Quân, nhóm 7.
>
> Hai buổi trước nhóm em đã trình bày Proposal và Requirement Analysis — MeoArc **là gì**,
> và **phải làm được những gì**. Hôm nay là tài liệu Design: **làm bằng cách nào**.
>
> Em xin phép không giới thiệu lại sản phẩm, mà bắt đầu thẳng bằng bài toán thiết kế khó
> nhất nhóm em gặp trong giai đoạn này.
>
> MeoArc cho AI thao tác trực tiếp trên hộp thư thật của người dùng — gắn nhãn, xoá thư,
> gửi mail. Nghĩa là một câu trả lời sai của mô hình không dừng lại ở màn hình: nó gửi mất
> một email thật, hoặc xoá mất một email thật. Toàn bộ thiết kế của nhóm em xoay quanh đúng
> câu hỏi đó — **làm sao cho AI đủ quyền để có ích, nhưng không bao giờ tự ý làm điều không
> đảo ngược được.**
>
> Câu trả lời của nhóm em là một cổng xác nhận bắt buộc. Điều đáng nói là nó không nằm ở
> một chỗ, mà xuất hiện ở **cả bốn mục** của tài liệu hôm nay:
>
> - Trong **kiến trúc**, nó là Confirmation Service, và là nhóm quyền `WRITE_DESTRUCTIVE`
>   trong Tool Registry — mọi tool thuộc nhóm này bị chặn lại chờ duyệt.
> - Trong **thiết kế lớp**, nó là lớp `ConfirmationRequest` với hai thao tác `approve()`
>   và `reject()`.
> - Trong **thiết kế dữ liệu**, nó là bảng `confirmation_request` mà khoá chính chính là
>   `tool_call_id` — tức là **cấu trúc bảng tự nó cấm** một hành động có hai phiếu duyệt,
>   không cần code kiểm tra.
> - Và trong **giao diện**, nó là thẻ Approve / Reject nằm ngay trong khung chat, với các
>   tin nhắn xung quanh bị làm mờ đi.
>
> Bốn mục, bốn người trình bày, nhưng là cùng một sợi chỉ. Mong thầy và các bạn theo dõi
> sợi chỉ đó xuyên suốt.
>
> Thứ tự hôm nay: bạn Thiên trình bày Conceptual Model, bạn Tài trình bày Architectural
> Design và Class Diagram, bạn Tiến trình bày Data Design, và em kết lại bằng phần Giao diện.
>
> Em xin mời bạn Thiên.

## A2. Vì sao mở như vậy — để bạn tự chỉnh khi cần

Ba lý do, nói ra để bạn biết chỗ nào cắt được chỗ nào không:

1. **Không lặp lại PA0/PA1.** Buổi thứ ba mà còn "MeoArc là trợ lý email dùng AI…" thì
   người nghe biết ngay là đọc slide. Câu "em xin phép không giới thiệu lại" nói thẳng
   điều đó và mua được thiện cảm.
2. **Mở bằng bài toán, không mở bằng danh sách.** "Hôm nay em trình bày 4 mục: A, B, C, D"
   là cách mở yếu nhất. Mở bằng một câu hỏi khó rồi mới đến cấu trúc thì người nghe có lý
   do để nghe tiếp.
3. **Sợi chỉ xuyên suốt là thứ khó bịa.** Việc cổng xác nhận xuất hiện ở cả bốn mục chứng
   minh nhóm thiết kế có hệ thống chứ không phải mỗi người làm một mảnh rời. Đây cũng đúng
   là tiêu chí "artifacts must remain consistent and synchronized" mà đề bài nhấn mạnh.

**Nếu bị ép thời gian:** cắt phần liệt kê 4 gạch đầu dòng, giữ lại đoạn "bài toán khó nhất"
và câu chuyển. Còn ~40 giây.

---

# PHẦN B — §1.6 SCREEN DIAGRAM

**Thời lượng:** ~2 phút · **Slide:** sơ đồ màn hình + bảng 14 màn hình

## B1. Kịch bản

> Phần cuối là thiết kế giao diện. Em phụ trách hai mục: Screen Diagram và Screen
> Specifications.
>
> Hệ thống có 14 màn hình. Nhưng con số đó không phải điều đáng nói — điều đáng nói là
> **phần lớn chúng không phải là trang riêng**.
>
> MeoArc chỉ có ba lần chuyển trang thật sự: Landing Page → Login → Main Workspace. Và
> chuyển một chiều — đăng nhập xong thì không quay lại Landing nữa.
>
> Từ Main Workspace trở đi, mọi thứ diễn ra **bên trong một cái khung ba cột cố định**:
> thanh điều hướng bên trái, danh sách email ở giữa, khung AI bên phải. Các "màn hình"
> còn lại là các panel thay nhau xuất hiện trong khung đó — hoặc lớp phủ đè lên nó.
>
> Lý do là một ràng buộc rất cụ thể: **ngữ cảnh hội thoại của agent không được phép mất.**
> Nếu người dùng đang nhờ trợ lý xử lý một loạt thư, rồi bấm vào đọc một email và bị chuyển
> sang trang khác, thì cuộc hội thoại đứt. Nên khi mở email, nó mở **bên cạnh** khung chat
> chứ không thay thế khung chat — hai thứ cùng nằm trong cột phải và trượt qua lại.
>
> Cùng nguyên tắc đó, bốn màn hình này được thiết kế thành lớp phủ chứ không phải trang:
> hộp thoại soạn thư, bảng Settings, ngăn kéo Lịch sử hội thoại, và Command Palette. Người
> dùng đóng lớp phủ là quay lại đúng chỗ đang làm dở.
>
> Đây không phải quyết định thẩm mỹ. Nó là hệ quả trực tiếp của việc sản phẩm này lấy hội
> thoại làm trung tâm.

## B2. Nếu bị hỏi "sao nhiều màn hình vậy mà chỉ đặc tả 7?"

> Template yêu cầu chọn 5–6 màn hình quan trọng nhất để đặc tả, phần còn lại chỉ cần vẽ
> giao diện. Nhóm em đặc tả 7 — chọn theo tiêu chí: màn hình nào **mang một quyết định
> thiết kế**, chứ không phải màn hình nào phức tạp nhất.

---

# PHẦN C — §1.7 SCREEN SPECIFICATIONS

**Thời lượng:** ~4 phút · **Slide:** 3 slide (mỗi màn hình 1 slide, có ảnh chụp)

Đừng đọc lần lượt cả 7 màn hình — hết giờ và người nghe chán. Nói kỹ **3 màn hình mang
quyết định thiết kế**, ba màn hình còn lại gộp một câu.

## C1. Confirmation Dialog — nói đầu tiên, vì nó chốt lại sợi chỉ ở phần mở đầu

> Em quay lại cổng xác nhận mà em nói ở đầu buổi. Ở phía giao diện, nó trông như thế này.
>
> Nó **không phải một hộp thoại bật ra giữa màn hình**. Nó là một thẻ nằm ngay trong dòng
> chat, đúng chỗ agent vừa đề xuất. Bên trong thẻ là tiêu đề, danh sách các bước được đánh
> số, và nếu hành động là không đảo ngược được thì có thêm một dải cảnh báo.
>
> Chi tiết em muốn nhấn: khi thẻ này đang chờ, **mọi tin nhắn khác bị làm mờ đi và thẻ được
> làm nổi lên**. Đây là lựa chọn có chủ đích. Người dùng đọc chat rất nhanh và rất dễ bấm
> Approve theo quán tính. Làm mờ phần còn lại là cách buộc mắt dừng lại đúng chỗ cần quyết định.
>
> Chỉ khi người dùng bấm Approve thì backend mới bắt đầu chạy. Bấm Reject thì kế hoạch bị
> huỷ và agent xác nhận lại là đã huỷ — không im lặng.

## C2. Email List — màn hình dùng nhiều nhất

> Đây là cột giữa, và là màn hình người dùng nhìn lâu nhất nên em thiết kế kỹ nhất.
>
> Hai điểm đáng nói. Thứ nhất là **7 chip phân loại theo màu** — Học tập, Công việc, Tài
> chính, Mạng xã hội, Mua sắm, Hệ thống, Cá nhân. Bảy nhãn này là bảy nhãn AI thật sự gán,
> không phải bảy nhãn trang trí: chúng khớp đúng với taxonomy trong phần Data Design của
> bạn Tiến.
>
> Thứ hai là ô tìm kiếm có **công tắc chuyển sang chế độ ngôn ngữ tự nhiên**. Tắt thì tìm
> theo từ khoá như bình thường. Bật thì người dùng gõ nguyên câu tiếng Việt, và câu đó đi
> vào tool `semantic_search` mà bạn Tài đã trình bày ở Tool Registry. Cùng một ô nhập, hai
> đường xử lý khác hẳn nhau ở dưới.
>
> Ngoài ra màn hình này có chọn nhiều thư để thao tác hàng loạt, và điều hướng bằng bàn
> phím j/k — vì người dùng chính của sản phẩm là người xử lý thư mỗi ngày.

## C3. Settings — panel MCP, chỗ duy nhất câu chuyện MCP hiện ra với người dùng

> Màn hình cuối em muốn nói là Settings, cụ thể là tab MCP.
>
> Ở phần kiến trúc, bạn Tài có nhắc tới khối Public MCP Server — cho phép các AI khác như
> Claude Desktop nối vào MeoArc và dùng hộp thư qua giao thức MCP. Ở phần dữ liệu, bạn Tiến
> có bảng `mcp_credential` và `mcp_credential_scope`.
>
> Tab này chính là chỗ hai thứ đó hiện ra với người dùng: địa chỉ server để sao chép, token
> truy cập, danh sách quyền đã cấp — đọc, sửa, gửi — và trạng thái kết nối cùng số client
> đang nối.
>
> Em nhấn chi tiết này vì nó cho thấy quyền của agent ngoài là thứ **người dùng nhìn thấy
> và thu hồi được**, không phải thứ ẩn trong file cấu hình.

## C4. Ba màn hình còn lại — gộp một đoạn

> Ba màn hình còn lại em xin nói ngắn. **Landing Page** là màn hình duy nhất trước khi đăng
> nhập, giới thiệu sản phẩm và ba gói dịch vụ cùng cửa sổ thời gian mà AI được phép quét —
> 90, 180 và 365 ngày. **Login** là màn hình OAuth, có ghi rõ MeoArc xin quyền gì và thu hồi
> ở đâu. **Lịch sử hội thoại** là ngăn kéo trượt ra, cho ghim, đổi tên, tìm và xoá các phiên
> chat cũ — và xoá thì phải xác nhận thêm một lần, cùng nguyên tắc với cổng xác nhận ở trên.

## C5. Câu kết buổi (Quân nói, ~20 giây)

> Đó là phần giao diện, và cũng là phần cuối của tài liệu Design.
>
> Nếu thầy và các bạn chỉ nhớ một điều từ buổi hôm nay, nhóm em mong đó là: cổng xác nhận
> không phải một tính năng nhóm em gắn thêm vào cuối. Nó là ràng buộc có từ đầu, và cả bốn
> mục của tài liệu đều được thiết kế quanh nó.
>
> Nhóm em xin hết. Rất mong nhận được câu hỏi ạ.

---

# PHẦN D — CHUẨN BỊ CÂU HỎI

Sáu câu nhiều khả năng bị hỏi nhất, kèm hướng trả lời. Đọc trước buổi.

**D1. "Vì sao 14 màn hình mà chỉ đặc tả 7?"**
→ Template cho phép chọn 5–6 quan trọng nhất. Nhóm chọn 7, tiêu chí là màn hình có mang
quyết định thiết kế. Bảy màn hình còn lại vẫn có bản vẽ giao diện.

**D2. "Người dùng bấm Approve theo quán tính thì sao? Cổng xác nhận có tác dụng gì?"**
→ Câu hỏi hay và thật. Trả lời: đó chính là lý do có hiệu ứng làm mờ và làm nổi — nhưng
nhóm thừa nhận nó không giải quyết triệt để. Lớp phòng thủ thứ hai là **audit log**: mọi
hành động đều ghi lại ai làm, bằng tool nào, tác động lên thư nào, kết quả ra sao. Nên
thao tác lỡ tay vẫn truy được. *(Đừng nói cổng xác nhận là đủ — nói có hai lớp thì thuyết
phục hơn nhiều.)*

**D3. "Sao không dùng modal cho xác nhận mà lại nhét vào chat?"**
→ Vì ngữ cảnh. Modal tách quyết định ra khỏi lý do dẫn tới quyết định. Đặt thẻ ngay trong
dòng chat thì người dùng vẫn thấy câu mình vừa yêu cầu và các bước agent đề xuất, ở cùng
một chỗ.

**D4. "Chế độ tìm kiếm ngôn ngữ tự nhiên khác gì tìm kiếm thường?"**
→ Tìm thường khớp từ khoá, đi thẳng vào tool `search_emails`. Tìm ngôn ngữ tự nhiên đi qua
`semantic_search` — so khớp theo ý nghĩa bằng vector, nên tìm được cả khi thư không chứa
đúng chữ đó.

**D5. ⚠️ "Cho xem bảng `confirmation_request` trong code"** — câu này có rủi ro
→ **Sự thật:** thiết kế chốt khoá chính là `tool_call_id`, nhưng code hiện tại chưa theo —
đang nối qua `conversation_id`. Nếu bị hỏi, trả lời thẳng: *"Đó là thiết kế đích của tài
liệu này. Bản cài đặt hiện tại còn nối theo hội thoại, nhóm em sẽ chuyển theo đúng thiết
kế ở giai đoạn tiếp theo."* **Đừng khẳng định code đã làm rồi.** Thiết kế đi trước code là
bình thường; bị bắt nói sai mới là vấn đề.

**D6. "Phiên đăng nhập lưu ở đâu?"** — cũng có rủi ro, xem mục E3
→ Hiện §1.5 không có bảng nào cho phiên. Nếu chưa kịp sửa trước buổi thì trả lời: *"Phiên
đăng nhập nhóm em đang xử lý ở tầng session, chưa đưa vào Data Specification — đây là chỗ
nhóm em sẽ bổ sung."* Thừa nhận thiếu sót gọn gàng tốt hơn là bịa.

---

# PHẦN E — BỐN CHỖ PHẢI SỬA TRONG CHÍNH MỤC CỦA BẠN

Đây là mục mang tên bạn ở dòng "Written by", nên sửa trước khi trình bày.

### 🔴 E1. Bảng liệt kê màn hình: dòng 1 và dòng 2 **trùng tên nhau**

Cả hai dòng đều ghi `Login & Connect Account`. Nhưng đọc mô tả dòng 1 thì rõ ràng đó là
**Landing Page** — "public marketing page", giới thiệu bảy nhãn, các gói dịch vụ. Và §1.7.1
cũng đặt tên là "Landing Page".

→ Đổi tên dòng 1 thành **`Landing Page`**. Đây là lỗi dễ bị soi nhất vì nó nằm ngay dòng
đầu bảng.

### 🟡 E2. §1.7.2 Login chỉ có nút Google, thiếu Outlook

§1.7.1 Landing viết rõ có cả *"Đăng nhập với Google"* và *"Đăng nhập với Outlook"*. Nhưng
§1.7.2 chỉ mô tả một nút Google, và câu trấn an cũng chỉ nhắc *"your Google account"*.
Code thì có cả hai đường (`/google/start` và `/outlook/start`).

→ Thêm Outlook vào §1.7.2 cho khớp với §1.7.1 và với phần kiến trúc.

### 🔴 E3. §1.7.2 nhắc tới bảng `sessions` mà §1.5 không có

Nguyên văn: *"opens a sessions row (Gmail tokens encrypted)"*. Nhưng §1.5 có 25 bảng và
**không có bảng nào tên `sessions`**. Người chấm dò chéo §1.7 với §1.5 sẽ thấy ngay.

→ Hai cách, chọn một: (a) nói bạn Tiến thêm bảng `Session` vào §1.5, hoặc (b) sửa câu ở
§1.7.2 thành mô tả trung tính, không gọi tên bảng — ví dụ *"establishes an authenticated
session with the provider tokens encrypted at rest"*.

Cách (b) nhanh hơn và không phải chờ ai. Nhưng (a) mới là đúng, vì phiên đăng nhập có tồn
tại thật trong code.

### 🟡 E4. Ba tiêu đề đầu §1.7 không có số

Trong thân bài, `Screen "Landing Page"`, `Screen "Login & Connect Account"` và
`Screen "Main screen"` đang không có số 1.7.1 / 1.7.2 / 1.7.3, trong khi 1.7.4 → 1.7.7 có
đủ. Mục lục thì đúng cả bảy.

→ Mở đúng trang đó xem trên màn hình có hiện số không. Có hiện thì Word đang đánh số tự
động, không phải làm gì. Không hiện thì gõ tay thêm ba số.

---

### ✅ Một điểm mục của bạn đang **đúng**, và nên biết để tự tin

§1.7.1 liệt kê bảy nhãn: *School, Work, Finance, Social, Shopping, System, Personal* —
**khớp chính xác** với taxonomy trong code (`app/core/labeling.py`).

Trong khi đó **Class Diagram ở §1.2 đang sai**: enum `EmailCategory` ở đó có `Spam` (code
không có nhãn này), thiếu `Shopping` và `Finance`, và có `Personal` **hai lần**.

Nếu ai đó phát hiện hai chỗ vênh nhau trong buổi, thì chỗ sai là hình class, không phải
mục của bạn. Chi tiết ở [DOI-CHIEU-HINH-11-12.md](DOI-CHIEU-HINH-11-12.md) mục D2.
