# Kịch bản thuyết trình PA3 — Testing · Nhóm 7 MeoArc

> **Đọc trang này trước, cả ba người.** Phần lớn buổi thuyết trình hỏng không phải vì
> nội dung yếu, mà vì ba người nói ba mảng rời rồi ai nấy ngồi xuống. Trang này dựng
> **một sợi dây duy nhất** xuyên qua cả buổi, và ghi rõ câu bàn giao ở mỗi mối nối.

---

# I. SỢI DÂY CỦA CẢ BUỔI

Buổi hôm nay không phải là buổi **đọc danh sách test case**. Nó là buổi **bảo vệ một lời hứa**.

**Lời hứa của MeoArc:** *AI được phép làm việc thật trên hộp thư thật của bạn — nhưng
không bao giờ tự ý làm điều không lấy lại được.*

Cả buổi là quá trình gỡ lần lượt từng câu hỏi mà một người dùng khó tính sẽ đặt ra:

| # | Người dùng hỏi | Ai trả lời | Bằng gì |
| :----: | :---- | :---- | :---- |
| 1 | *"Sao tôi phải tin cho AI đụng vào hộp thư tôi?"* | **Quân** — mở đầu | Nêu ranh giới |
| 2 | *"Các anh kiểm cái gì trước, cái gì sau?"* | **[Bạn A]** — Test Plan | Xếp ưu tiên theo thiệt hại |
| 3 | *"Ranh giới đó có thật không, hay chỉ là lời nói?"* | **[Bạn B]** — §3.2.1→24 | Cổng xác nhận, guardrail, cô lập dữ liệu |
| 4 | *"Còn AI khác nối vào thì sao? Đông người thì có sập không? Gmail chết thì sao?"* | **Quân** — §3.2.25→39 | MCP, chịu tải, ngắt mạch |
| 5 | *"Có gì các anh chưa chứng minh được không?"* | **Quân** — Reflective + Phụ lục | Nói thẳng ra |

**Nguyên tắc chung khi nói:** mỗi phần **mở bằng câu hỏi của người dùng**, không mở bằng
tên mục. Nói *"Câu hỏi tiếp theo là…"* chứ đừng nói *"Tiếp theo em trình bày mục 3.2.25"*.

---

# II. BỐN MỐI NỐI — chép nguyên văn cho từng người

Đây là phần các bạn đang thiếu. Bốn câu này làm buổi thuyết trình liền mạch.

### Mối nối 1 · Quân → [Bạn A]

**Quân kết phần mở đầu bằng:**
> *"Ranh giới em vừa nói là lời hứa của sản phẩm. Phần còn lại của buổi hôm nay là bằng
> chứng. Và việc đầu tiên phải làm không phải là viết test — mà là quyết định **kiểm cái
> gì trước**. Em xin mời bạn [A]."*

### Mối nối 2 · [Bạn A] → [Bạn B]

**[Bạn A] kết phần Test Plan bằng:**
> *"Xếp ưu tiên xong thì thấy rõ: thứ nằm ở vị trí số một không phải tính năng dùng nhiều
> nhất, mà là tính năng **hỏng thì không sửa được** — cổng xác nhận. Nên đó cũng là phần
> được kiểm kỹ nhất. Mời bạn [B]."*

### Mối nối 3 · [Bạn B] → Quân ⭐ *mối nối quan trọng nhất*

**[Bạn B] kết phần test case bằng:**
> *"Vậy là cổng xác nhận đứng vững — trong điều kiện bình thường, một người dùng, hệ thống
> khoẻ mạnh. Nhưng sản phẩm thật không chạy trong điều kiện đó. Bạn Quân sẽ nói về phần
> còn lại: khi có AI khác nối vào, khi nhiều người bấm cùng lúc, và khi Gmail ngừng trả
> lời."*

**Quân bắt vào:**
> *"Cảm ơn bạn [B]. Bạn [B] vừa chứng minh hàng rào giữ được. Phần của em trả lời câu hỏi
> tiếp theo mà một khách hàng khó tính sẽ hỏi ngay: **hàng rào ấy có còn giữ được không,
> khi mọi thứ quanh nó bắt đầu hỏng?**"*

### Mối nối 4 · Quân → phần tự đánh giá

> *"Đó là những gì nhóm em chứng minh được. Nhưng một báo cáo chỉ nói phần chứng minh được
> thì mới kể một nửa câu chuyện."*

---

# III. KỊCH BẢN CỦA QUÂN

## A · MỞ ĐẦU — 70 giây

**[MÀN HÌNH]** Slide tiêu đề. Không quay app.

> Kính chào thầy, chào các bạn. Em là Phạm Trần Anh Quân, mã số 24127226, nhóm 7. Thay mặt
> nhóm, em xin phép mở đầu buổi báo cáo hôm nay.
>
> Em xin nhắc lại sản phẩm trong một phút, để thầy tiện nối mạch với ba buổi trước.
>
> **MeoArc là trợ lý thư điện tử chạy bằng trí tuệ nhân tạo.** Người dùng nối hộp thư Gmail
> hoặc Outlook vào, rồi ra lệnh bằng tiếng Việt như nói với một người thư ký: *tìm giúp tôi
> thư về hạn nộp tuần này*, *phân loại hộp thư*, *soạn giúp tôi thư trả lời*. Trợ lý tự hiểu
> và tự làm — nó đọc thư thật, gắn nhãn thật, gửi thư thật.
>
> Và chính chữ **thật** đó là lý do có buổi hôm nay.
>
> Một trợ lý gợi ý sai thì người dùng bỏ qua, không mất gì. Nhưng một trợ lý **tự ý gửi**
> một lá thư sai, hay **tự ý xoá** một lá thư quan trọng, thì không có nút hoàn tác nào cả.
> Cho nên ngay từ bản thiết kế, nhóm em đặt ra một ranh giới: **mọi hành động không lấy lại
> được đều phải chờ người dùng bấm duyệt.**
>
> Ba buổi trước, nhóm em trình bày việc **xây** ranh giới ấy. Hôm nay là buổi **chứng minh
> nó đứng vững.**
>
> *(chuyển sang Mối nối 1)*

**Nếu thầy tỏ ý đã nhớ sản phẩm:** bỏ đoạn nhắc lại, nhảy thẳng vào *"Một trợ lý gợi ý sai
thì người dùng bỏ qua…"*. Còn 40 giây.

---

## B · PHẦN CHÍNH — 3 phút 20

Mười lăm mục, gộp thành **bốn câu hỏi của khách hàng**. Mỗi khối mở bằng câu hỏi, đóng bằng
một câu chốt.

### B1 · *"Còn AI khác nối vào thì sao?"* — §3.2.25, §3.2.26 — 40 giây

**[MÀN HÌNH]** Claude Desktop đã nối vào MeoArc, mở danh sách tool. Không kịp dựng thì quay
**Settings → tab MCP**, chỗ hiện endpoint, token và danh sách quyền.

> MeoArc không chỉ có giao diện của mình. Nó còn mở một cổng cho các AI khác — Claude
> Desktop chẳng hạn — nối vào và dùng hộp thư qua giao thức MCP.
>
> Cổng đó đặt ra một câu hỏi: **cho AI ngoài mượn quyền gì?**
>
> Nhóm em chọn phơi ra **nhiều tool nhỏ, mỗi tool một việc rõ ràng** — tìm thư, đọc thư,
> gắn nhãn, gửi thư — thay vì một tool to nhận câu lệnh tự do. Đây không phải chuyện thẩm
> mỹ. Một tool to thì **không giới hạn quyền được**, và nhật ký cũng chỉ ghi được "đã gọi
> tool", không biết nó làm gì bên trong. Phép thử khẳng định đúng bộ tool đã công bố, và
> **không có tool bao trùm nào lọt vào**.
>
> **Chốt:** *quyền của agent ngoài là thứ người dùng nhìn thấy được và thu hồi được, không
> phải thứ ẩn trong file cấu hình.*

### B2 · *"Đông người dùng cùng lúc thì có sập không?"* — §3.2.27, 28, 31, 32 — 50 giây

**[MÀN HÌNH]** Swagger `/docs`, quay thật ba lần: `limit=5000` → **422**, bấm liên tục
`/emails` → **429**, tải tệp 3 MB → **413**.

> Bốn phép thử này cùng một triết lý: **thà từ chối sớm và lịch sự, còn hơn nhận hết rồi
> chết chùm.**
>
> Một người dùng — hoặc một script lỗi — hỏi xin năm nghìn lá thư trong một lần gọi thì hệ
> thống bắn năm nghìn lệnh sang Gmail, đốt sạch hạn ngạch chung của **mọi người**. Nên trần
> được đặt ngay ở cửa: quá 50 thư một lần thì bị chặn trước khi vào tới hàm xử lý.
>
> Điểm em muốn nhấn: cả bốn phép thử này **kỳ vọng một mã lỗi, không phải mã thành công.**
> Với bốn ca đó, chụp được màn hình "200 OK" nghĩa là test **trượt**, không phải đạt. Nhóm
> em ghi rõ điều này trong báo cáo, vì đây là chỗ rất dễ dán nhầm bằng chứng.
>
> **Chốt:** *hệ thống biết nói không, và nói không đúng cách.*

### B3 · ⭐ *"Có chậm không?"* — §3.2.30 — 65 giây

**[MÀN HÌNH]** Terminal chạy script đo tải, rồi mở `/metrics` cạnh bên. **Quay kỹ nhất chỗ này.**

> Câu trả lời cho câu hỏi này ban đầu là: **có, rất chậm.** Và đó là câu chuyện em muốn kể.
>
> Lần đo đầu tiên cho kết quả: p95 bằng **3.088 mili giây**, chỉ 85% số request dưới ngưỡng.
> Theo đúng con số đó thì sản phẩm **không đạt** yêu cầu hiệu năng.
>
> Nhưng có ba chi tiết mâu thuẫn với kết luận ấy.
>
> Thứ nhất, `/metrics` — tức **chính server tự đo mình** — báo 6 mili giây cho cùng một
> endpoint. Thứ hai, độ trễ **không tăng theo số luồng**: chạy tuần tự 2.047 mili giây,
> chạy 40 luồng song song 2.078 — một hệ thống quá tải thì phải ngược lại hoàn toàn. Thứ ba,
> một câu lệnh `SELECT 1` không thể mất hai giây.
>
> Ba dấu hiệu cùng nói một điều: **lỗi nằm ở cái thước, không phải ở hệ thống.**
>
> Và đúng vậy. Trên Windows, `localhost` phân giải sang IPv6 trước, trong khi máy chủ chỉ
> lắng nghe IPv4 — mỗi request phải chờ hết hạn rồi mới lùi về, mất khoảng hai giây, **mỗi
> lần**. Đo lại bằng `127.0.0.1` thì ra **5 tới 8 mili giây**.
>
> Nhóm em giữ nguyên câu chuyện này trong báo cáo thay vì lặng lẽ xoá con số cũ đi.
>
> **Chốt:** *bài học không phải "sản phẩm nhanh". Bài học là khi phép đo nói một đằng mà
> ba dấu hiệu khác nói một nẻo, hãy nghi cái thước trước.*

**Đây là khối không được cắt.** Thiếu giờ thì cắt B1 hoặc B4.

### B4 · *"Gmail chết thì sao?"* — §3.2.29, 33 → 36 — 45 giây

**[MÀN HÌNH]** `/metrics`, kéo tới khối `ngat_mach` cho thấy trạng thái hai cầu dao.

> Sản phẩm này sống nhờ hai dịch vụ bên ngoài: Gmail và mô hình AI. Cả hai đều có thể chết,
> và nhóm em không kiểm soát được lúc nào.
>
> Nên có một **cầu dao**. Gọi Gmail hỏng liên tiếp mấy lần thì cầu dao mở, ngừng gọi một
> lúc, để hệ thống không xếp hàng chờ chết chùm.
>
> Nhưng chỗ tinh tế là chiều ngược lại: cầu dao **phải đóng nguyên** khi chỉ là lỗi nghiệp
> vụ. Gửi thư cho một địa chỉ sai là lỗi của người dùng, không phải Gmail chết. Nếu cầu dao
> mở ra vì chuyện đó, thì **một người gõ sai địa chỉ sẽ làm ngưng dịch vụ của tất cả mọi
> người.** Phép thử kiểm cả hai chiều — mở khi cần mở, và đóng khi không được mở.
>
> Ba phép thử còn lại trong nhóm: lịch sử trò chuyện **sống qua lần khởi động lại**, tắt
> máy chủ **không treo**, và migration **dựng lại toàn bộ cơ sở dữ liệu từ con số không**.
>
> **Chốt:** *hỏng là chuyện chắc chắn xảy ra. Điều nhóm em kiểm là hỏng có kiểm soát.*

### B5 · *"AI đọc bao nhiêu thư của tôi?"* — §3.2.38, §3.2.39 — 45 giây

**[MÀN HÌNH]** Thanh token trong app hiện `MIỄN PHÍ · quét 90 ngày`.

> Câu hỏi cuối là câu hỏi về sự riêng tư, và cũng là câu hỏi về giá.
>
> Trợ lý không đọc toàn bộ hộp thư. Nó chỉ đọc trong một **cửa sổ thời gian** tuỳ theo gói:
> 90 ngày với gói miễn phí, 180 và 365 với hai gói trả phí. Người dùng nhìn thấy con số đó
> ngay cạnh ô chat, không phải đoán.
>
> Nhóm em kiểm bằng **phân tích giá trị biên**: thư đúng 90 ngày phải **còn** trong phạm vi,
> 91 ngày thì **ra ngoài** — kiểm cả ba gói, cả hai phía của mỗi ranh giới.
>
> Một chi tiết nhỏ mà quyết định: ngày trong phép thử được **ghim cố định**. Viết phép thử
> biên theo "hôm nay" thì đó là phép thử **đổi ý nghĩa mỗi đêm** — hôm nay xanh, mai đỏ, mà
> chẳng có lỗi nào phát sinh.
>
> Và nhóm em kiểm cái **ngoại lệ** chặt như kiểm cái giới hạn: tìm kiếm bằng từ khoá **không**
> bị giới hạn. Vì giới hạn quá tay cũng phá sản phẩm y như không có giới hạn — ranh giới này
> sinh ra để chặn cái **AI** đọc, chứ không phải để chặn người dùng tìm lại thư năm ngoái
> của chính mình.
>
> **Chốt:** *giới hạn phải đúng ở cả hai đầu — không quá lỏng, và cũng không quá chặt.*

### B6 · Một câu cho §3.2.37

> Riêng tương thích đa trình duyệt, nhóm em ghi là **chưa chạy** — việc đó cần mở tay trên
> nhiều trình duyệt khác nhân, để lại cho buổi alpha.

---

## C · TỰ ĐÁNH GIÁ — 80 giây

*(vào bằng Mối nối 4)*

**[MÀN HÌNH]** Slide, hoặc mở trang Reflective trong PDF.

> Phần này bạn Tài viết, em biên tập. Có bốn ý, em xin nói hai ý đáng nhất.
>
> **Ý thứ nhất: ô hữu ích nhất của mẫu tài liệu không phải nhờ định dạng, mà nhờ nó ép mình
> trung thực.** Bảng test case bắt ghi *Kết quả mong đợi* **trước khi chạy**, và *Kết quả
> thực tế* **sau khi chạy**. Nghe thì hiển nhiên — nhưng đảo thứ tự là hỏng hoàn toàn: chạy
> trước rồi mới ghi kỳ vọng thì **bất kỳ con số nào máy trả về cũng trông như đúng**, và
> phép thử chẳng chứng minh được gì.
>
> Chuyện này có trả giá thật trong đồ án. Ở phép thử đếm token, kỳ vọng *"150 token, không
> phải 1149"* được viết ra **từ yêu cầu, trước khi mở code**. Chính con số ấy quyết định dữ
> liệu thử — một lượt cũ 999 token đặt ngay trước ranh giới — và chính nó bắt được lỗi đếm
> trùng. Nếu chạy trước ghi sau, lỗi đó đã lọt.
>
> **Ý thứ hai: chỗ mẫu tài liệu còn thiếu — không có ô nào để ghi một phép thử chưa chạy.**
> Ô kết quả chỉ có *Đạt* và *Không đạt*. Điều đó lặng lẽ đẩy người viết vào hai lựa chọn
> xấu: hoặc ghi bừa là "Đạt", hoặc xoá luôn ca đó đi cho khuất mắt. **Cả hai đều giấu rủi ro.**
>
> Nhóm em thêm trạng thái **Chưa chạy** và dùng ở đúng những chỗ chưa chạy. Và có một chuyện
> đáng nói: hai phép thử từng mang trạng thái đó — kiểm thứ tự nhiều bước, và kiểm việc lưu
> thông tin đăng nhập — **nay đã tự động hoá xong và chuyển thành Đạt**. Trạng thái *Chưa
> chạy* đã làm đúng việc của nó: **giữ phần chưa làm nằm trong tầm mắt, thay vì để nó biến mất.**

**Cắt xuống 45 giây:** bỏ ý thứ nhất, giữ ý thứ hai — ý thứ hai mạnh hơn.

---

## D · PHỤ LỤC — 45 giây

**[MÀN HÌNH]** Terminal chạy `cd src/backend && .venv/Scripts/python.exe -m pytest -q`,
để chạy tới dòng tổng kết rồi dừng.

> Hai phụ lục cuối, em xin nói rất nhanh.
>
> **Phụ lục A là nhật ký bằng chứng.** Toàn bộ bộ kiểm thử chạy ở **hai cấu hình**, vì số
> phép thử chạy được phụ thuộc vào việc có máy chủ đang bật hay không: **222 đạt / 21 bỏ
> qua** khi không bật, **227 đạt / 16 bỏ qua** khi có bật.
>
> Nhóm em ghi **cả hai** thay vì chỉ ghi con số đẹp hơn. Lý do rất thực tế: thầy chạy trên
> máy của thầy sẽ ra con số thứ nhất — nếu báo cáo chỉ ghi con số thứ hai thì trông như
> nhóm em khai khống.
>
> **Phụ lục B ghi những thứ đặc tả có mà mã nguồn chưa tới.** Nhóm em nói rõ ngay đầu phụ
> lục: đây **không phải lỗi trong mã đang chạy** — đây là những mục vẫn đang đi về phía đặc
> tả. Ví dụ bản nháp thư và tệp đính kèm chưa có bảng riêng; nối nhiều tài khoản cùng lúc
> thì tầng dữ liệu đã xong nhưng chưa chạy thật với OAuth của hai nhà cung cấp.

---

## E · CÂU KẾT — 25 giây

> Nhóm em xin khép lại bằng đúng chỗ đã mở.
>
> Đầu buổi em nói MeoArc hứa một điều: **AI được làm việc thật trên hộp thư thật, nhưng
> không bao giờ tự ý làm điều không lấy lại được.** Toàn bộ những gì ba đứa em vừa trình
> bày là bằng chứng cho lời hứa đó — và cả những chỗ bằng chứng còn thiếu.
>
> Nếu thầy và các bạn chỉ nhớ một điều từ hôm nay, nhóm em mong đó là câu chuyện phép đo
> tải: con số đầu tiên nói sản phẩm chậm gấp năm trăm lần sự thật. Thứ cứu nhóm em không
> phải một công cụ nào cả — mà là chịu khó hỏi lại: *nếu con số này đúng, thì hai chỗ kia
> phải sai. Vậy chỗ nào sai thật?*
>
> Nhóm em xin hết ạ. Rất mong nhận được câu hỏi từ thầy và các bạn.

---

# IV. BẢNG THỜI GIAN

| Phần | Đầy đủ | Bản rút |
| :---- | :----: | :----: |
| A · Mở đầu | 70s | 40s |
| B1 · AI ngoài nối vào | 40s | *bỏ* |
| B2 · Đông người | 50s | 25s |
| B3 · ⭐ Đo sai | 65s | **65s — không cắt** |
| B4 · Gmail chết | 45s | 20s |
| B5 · Đọc bao nhiêu thư | 45s | 30s |
| B6 · Trình duyệt | 10s | 10s |
| C · Tự đánh giá | 80s | 45s |
| D · Phụ lục | 45s | 30s |
| E · Kết | 25s | 25s |
| **Tổng** | **~7 phút 55** | **~4 phút 50** |

*(Chưa tính bốn mối nối — mỗi mối khoảng 8 giây.)*

---

# V. ⚠️ HAI VIỆC PHẢI SỬA TRƯỚC KHI QUAY

Cả hai nằm đúng trong phần Quân nói. Quay trước khi sửa là tự đọc ra chỗ sai của mình.

### 1. §3.2.30 và Phụ lục A.4 đang ghi hai bộ số khác nhau cho **cùng một phép đo**

| Chỗ | Số |
| :---- | :---- |
| §3.2.30 | `1.59s → 126 req/s · p50 365 · p95 415 · p99 418ms` |
| Phụ lục A.4 | `0.40s → 503.4 req/s · p50 95 · p95 187 · p99 196ms` |

Chốt bộ số của **A.4** (mới hơn), sửa §3.2.30 cho khớp. Đây chính là mục kể chuyện đo sai —
để hai số đo chỏi nhau trong mục dạy về đo cẩn thận thì mất sạch luận điểm.

### 2. Phần tự đánh giá nêu ba ví dụ *"Chưa chạy"*, hai cái đã hết đúng

Đang ghi: *"…the four OAuth cases, **the multi-step ordering case (UC007-TC02)**, and one
half of **SEC-TC05**."* Nhưng UC007-TC02 giờ đã **Đạt**, SEC-TC05 đã có phép thử thật.

**Sửa thành:**
```
We added a Not run state and used it where it applied — the four OAuth cases that need a real provider round trip. Two cases that once carried this state, UC007-TC02 and SEC-TC05, have since been automated and now read Passed; the state did its job by keeping them visible instead of letting them disappear.
```

Bản mới **mạnh hơn** bản cũ, và chính là ý bạn sẽ nói ở khối C.

---

# VI. CHECKLIST QUAY MÀN HÌNH

Quay rời từng clip rồi ghép — đừng quay một mạch.

- [ ] **Sửa xong hai việc ở mục V**
- [ ] Máy chủ chạy: `.venv/Scripts/python.exe -m uvicorn app.api.app:app --port 8000`
- [ ] Swagger: 3 clip — `limit=5000` ra **422** · bấm liên tục `/emails` ra **429** · tải
      tệp 3 MB ra **413**
- [ ] `/metrics`: quay khối `latency_ms` và khối `ngat_mach`
- [ ] Script đo tải: từ lúc gõ lệnh tới lúc ra p50/p95/p99
- [ ] App: thanh token hiện `MIỄN PHÍ · quét 90 ngày`
- [ ] Settings → tab MCP, hoặc Claude Desktop đã nối vào
- [ ] Terminal: `pytest -q` chạy hết, dừng ở dòng `227 passed, 16 skipped`

> **Ba clip Swagger phải ra 422 / 429 / 413.** Clip nào ra 200 thì bỏ — nghĩa là phép thử
> trượt, không phải quay hỏng.
