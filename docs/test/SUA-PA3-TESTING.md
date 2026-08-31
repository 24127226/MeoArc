# Danh sách sửa `pa/pa3/Testing (1).md`

> Số dòng theo bản `Testing (1).md` hiện tại. Nếu bạn đã sửa gì thì số dòng xê dịch —
> dùng cột **"Tìm chuỗi"** để Ctrl+F cho chắc.
>
> **Thứ tự ưu tiên:** mục 1 → 2 → 3 → 4 → 5. Năm mục đầu là **sai sự thật kiểm chứng
> được trong 30 giây** — thầy chỉ cần chạy một lệnh là thấy. Mục 6 trở đi là thiếu sót,
> nhẹ hơn.

---

## 1. 🔴 Số liệu tổng đã cũ — lệch hơn 90 test

### 1a. Dòng 253 (§2.8 Entry and exit criteria)

**Tìm chuỗi:** `100% of automated tests pass`

**Hiện tại**
```
1. 100% of automated tests pass (currently **132 passed, 16 skipped** with the backend running; 124 passed / 21 skipped without it — see Appendix A.1).
```

**Sửa thành**
```
1. 100% of automated tests pass (currently **227 passed, 16 skipped** with the backend running; 222 passed / 21 skipped without it — see Appendix A.1).
```

### 1b. Dòng 1113–1114 (Appendix A.1)

**Tìm chuỗi:** `Backend **not** running`

**Hiện tại**
```
| Backend **not** running (default developer machine) | 124 passed, 21 skipped in 38.67s |
| Backend running on **127.0.0.1:8000** | **132 passed, 16 skipped in 66.62s** |
```

**Sửa thành**
```
| Backend **not** running (default developer machine) | 222 passed, 21 skipped in 32.68s |
| Backend running on **127.0.0.1:8000** | **227 passed, 16 skipped in 31.59s** |
```

### 1c. Dòng 1116 — câu giải thích chênh lệch cũng sai theo

**Tìm chuỗi:** `The difference is 3 newly added tests`

Câu này nói chênh lệch là *"3 test mới (test_audit_failed.py) cộng 5 test trong
test_uc011_api.py"*. Nhưng chênh lệch thật bây giờ **đúng bằng 5** — 5 test trong
`test_uc011_api.py` tự bỏ qua khi không có server. Ba test `test_audit_failed.py` chạy
được ở cả hai cấu hình nên không thuộc phần chênh.

**Sửa thành**
```
The difference is the 5 tests in **tests/test\_uc011\_api.py**, which need a live server and therefore skip themselves when there is none. Running the backend first is what turns NFR-TC06 from a manual check into an automated one.
```

**Vì sao phải sửa cả ba chỗ:** đây là con số người chấm kiểm được nhanh nhất — chỉ cần gõ
đúng lệnh §2.7 đã ghi sẵn. Sai một chỗ thì mọi con số khác trong bài đều bị nghi.

---

## 2. 🔴 Appendix B mục 1 — "9 tables" nay đã là 14

### Dòng 1200

**Tìm chuỗi:** `The implemented schema has 9 tables`

**Hiện tại** — liệt kê 9 bảng, và xếp `Connected_Account`, `Gmail_Account`,
`Outlook_Account` vào nhóm *"design model describes but implementation lacks"*.

**Sửa thành**
```
The implemented schema has 14 tables across 10 model modules: **users, sessions, session\_providers, emails (StoredEmail), mailbox\_sync, conversations, audit\_logs, notifications, subscriptions, connected\_accounts, gmail\_accounts, outlook\_accounts, connected\_account\_scopes** and **confirmation\_requests**. The design model additionally describes **EmailDraft, Attachment, ToolCall, Toolcall\_Email** and **Embeddings** as first-class entities. In the implementation:
```

**Kiểm lại bằng một lệnh** — dán vào terminal, phải ra đúng 14 dòng:
```bash
grep -rhoE '__tablename__ = "[a-z_]+"' src/backend/app/models/*.py | sed 's/.*= //' | tr -d '"' | sort
```

### Dòng 1204 — gạch đầu dòng về Gmail/Outlook nay sai hẳn

**Tìm chuỗi:** `subtype fields are implemented on **mailbox\_sync**`

**Hiện tại**
```
- **Gmail\_Account / Outlook\_Account** subtype fields are implemented on **mailbox\_sync** (**history\_id** for Gmail, **delta\_link** for Outlook). The *behaviour* the design intended is present and tested (AUTH-TC03); the *shape* differs.
```

**Sửa thành**
```
- **Connected\_Account / Gmail\_Account / Outlook\_Account** are now implemented as real tables, with **connected\_account\_scopes** holding the granted OAuth scopes. The older **mailbox\_sync** table still carries the same sync cursors (**history\_id**, **delta\_link**), so the two overlap; consolidating them is open work.
```

**Vì sao:** ba bảng đó tồn tại thật trong code. Ghi là "chưa có" thì người chấm mở
`src/backend/app/models/connected_account.py` ra là thấy ngay. Câu cuối về `mailbox_sync`
trùng lặp là **thật** — nói ra thì thành điểm cộng, giấu đi mà bị hỏi thì thành điểm trừ.

**Bốn gạch đầu dòng còn lại (dòng 1202, 1203, 1205, 1206) giữ nguyên** — Attachment,
ToolCall, EmailDraft, Embeddings vẫn chưa có bảng thật. Đúng như đang viết.

---

## 3. 🔴 Appendix B mục 3 — NFR-08 đã làm xong, không còn "pending"

### Dòng 1214

**Tìm chuỗi:** `NFR-08 scan window — specified, tests designed, implementation pending`

**Hiện tại**
```
**3\. NFR-08 scan window — specified, tests designed, implementation pending.**
```

**Sửa thành**
```
**3\. NFR-08 scan window — implemented and covered.**
```

Rồi ở đoạn văn ngay dưới (dòng 1216), thay câu kết luận "chưa làm" bằng:

```
This is now implemented in **app/core/scope.py**, which resolves the window per tier (90 / 180 / 365 days), caps task extraction at 90 days on every tier, and exempts keyword search per NFR-SCO-03. Covered by **SCOPE-TC01…08** (§3.2.39) — *pytest tests/test\_scope.py tests/test\_scope\_tools.py \-v* → **31 passed**.
```

**Vì sao:** `app/core/scope.py` tồn tại và 31 test pass. Để mục này ở nhóm "chưa làm" là
tự nhận thiếu một tính năng mà nhóm đã làm xong — mất điểm oan.

---

## 4. 🔴 Lý do "không chạy được" của AUTH đã lỗi thời

Hai chỗ nói cùng một điều, sửa cả hai cho khớp.

### 4a. Dòng 817 (§3.2.24 Actual Output)

**Tìm chuỗi:** `table binds **one** provider to a session token`

**Hiện tại** — đổ lý do cho schema: *"the implemented session_providers table binds one
provider to a session token, so simultaneous multi-account connection as described is not
yet supported."*

**Sửa thành**
```
| Actual Output | **Not executed.** These four require a real OAuth round trip against both Google and Microsoft, which the automated suite deliberately does not perform: doing so would mean shipping real credentials into the test environment. Scheduled for the alpha session with a screen recording as evidence. See Appendix B, item 2\. |
```

### 4b. Dòng 1212 (Appendix B mục 2)

**Tìm chuỗi:** `session\_providers binds one provider to one session token`

**Sửa thành**
```
The supporting tables now exist — **connected\_accounts** with the **gmail\_accounts** / **outlook\_accounts** subtypes — and **app/core/deps.py** already resolves the access token from the connection rather than from the login session. What has not been exercised is the full round trip: connecting two providers and confirming they operate independently needs a real OAuth flow with both vendors. **Status:** implemented at the data layer, pending verification. AUTH-TC01 and AUTH-TC02 remain *Not run* until the alpha session.
```

**Vì sao:** kết luận *Not run* **vẫn đúng và vẫn nên giữ**, nhưng lý do thì đã sai. Giữ
nguyên lý do cũ là đang mô tả một hạn chế không còn tồn tại — và nó mâu thuẫn với chính
Appendix B mục 1 sau khi bạn sửa ở trên (mục 1 nói bảng đã có, mục 2 nói chưa có).

---

## 5. 🔴 §3.2.7 bị thoát ký tự thừa — sẽ hiện ra chữ thô

Bạn đã dán nội dung mới vào rồi, nhưng khi dán bị escape thêm một lớp.

### Dòng 511

**Hiện tại**
```
\*\*Automated test:\*\* \*pytest tests/test\\\_agent\\\_offline.py::test\\\_ba\\\_buoc\\\_chay\\\_dung\\\_thu\\\_tu\\\_nghiep\\\_vu \\-v\*
```

**Sửa thành**
```
**Automated test:** *pytest tests/test\_agent\_offline.py::test\_ba\_buoc\_chay\_dung\_thu\_tu\_nghiep\_vu \-v*
```

### Dòng 508

**Tìm chuỗi:** `search\\\_emails`

Đổi mọi `\\\_` (ba ký tự) thành `\_` (hai ký tự) trong dòng này.

**Cách kiểm nhanh:** 33 mục khác trong bài đều bắt đầu bằng `**Automated test:**`. Chỉ
dòng 511 bắt đầu bằng `\*\*Automated test`. Tìm chuỗi `\*\*Automated` → phải ra **0 kết quả**.

---

## 6. 🟡 §2.5 bỏ sót 6 NFR lá

PA1 có **27** NFR lá. Bảng §2.5 phủ **21**. Sáu mã dưới đây **không xuất hiện ở bất kỳ đâu**
trong tài liệu — kể cả để ghi "Not Covered".

Thêm sáu dòng này vào cuối bảng §2.5 (ngay sau dòng 207, `NFR-USA-03`):

```
| NFR-PER-03 | *(xem PA1)* | not covered |
| NFR-SCO-02 | Task extraction capped at 90 days on every tier | SCOPE-TC05 |
| NFR-SCO-03 | Keyword search exempt from the scan window | SCOPE-TC06 |
| NFR-SCO-04 | Scan window shown to the user | SCOPE-TC07, SCOPE-TC08 |
| NFR-SEC-06 | *(xem PA1)* | not covered |
| NFR-USA-04 | *(xem PA1)* | not covered |
```

Mở PA1 điền nội dung thật vào ba ô *(xem PA1)*.

**Vì sao:** bảng mở đầu bằng câu *"Test cases trace to the leaf"* — ngụ ý là đầy đủ. Bảng
đã thẳng thắn ghi "Not Covered" cho `NFR-PER-02`, `NFR-SEC-03`, `NFR-SEC-04` rồi, nên bỏ
sót sáu mã kia trông như sót thật chứ không phải chủ ý. **Ba trong sáu mã (SCO-02/03/04)
tự được phủ** khi bạn thêm §3.2.39 ở mục 7.

---

## 7. 🟡 Thiếu hai mục cuối so với bản làm việc

`pa/pa3` dừng ở **§3.2.38 SEM**. Bản `docs/test/Testing.md` có thêm:

| Mục | Nội dung | Ảnh đã chuẩn bị |
| :---- | :---- | :---- |
| **§3.2.39** SCOPE-TC01…08 | Cửa sổ quét theo gói (NFR-08) | `TC-3.2.39-SCOPE-TC0108.png` — 31 passed |
| **§3.2.40** UC009-TC07…09 | Ba trục nhãn AI (PA1 §4.2.9) | `TC-3.2.40-UC009-TC0709.png` — 15 passed |

Chép nguyên hai mục từ `docs/test/Testing.md` chèn sau dòng 1039 (§3.2.38).

**Vì sao:** hai mục này ứng với code đã viết và test đã pass. Thiếu chúng thì Appendix B
mục 3 mới phải ghi "pending" (xem mục 3 ở trên) — sửa một chỗ mà không thêm mục thì hai
chỗ lại chỏi nhau. Và `EV-05` không có chỗ đặt nếu thiếu §3.2.39.

---

## 8. 🟡 §3.1 — chỉ 6/16 use case của PA1 được nhắc tên

Cả tài liệu chỉ nhắc `UC001, UC002, UC005, UC007, UC009, UC012`. Mười UC còn lại
(UC003, 004, 006, 008, 010, 011, 013, 014, 015, 016) **không xuất hiện ở đâu**.

Thực tế nhóm HITL-TC **có** kiểm UC010, nhóm SEM-TC **có** kiểm UC005 — nhưng vì đặt tên
theo tính năng chứ không theo UC nên máy dò chéo không nối được.

**Cách rẻ nhất:** thêm một cột `UC` vào bảng §3.1, điền mã UC tương ứng cho từng dòng.
Không phải viết thêm test nào, chỉ là ghi lại mối liên hệ đã có.

**Vì sao đáng làm:** thầy dùng AI dò chéo tài liệu. Một use case trong PA1 mà không mã test
nào trỏ tới sẽ bị đọc là "chưa kiểm", dù thực tế có kiểm.

---

## 9. 🟢 §2.7 — một nửa câu cho chính xác

### Dòng 238

**Hiện tại**
```
| Database | PostgreSQL 18.4 (**meoarc**), schema managed by Alembic |
```

**Sửa thành**
```
| Database | PostgreSQL 18.4 (**meoarc**), schema managed by Alembic. Automated tests run against in-memory SQLite fixtures; the PostgreSQL instance is used by the running application and by the migration tests. |
```

**Vì sao:** không sai, nhưng đọc như thể toàn bộ test chạy trên PostgreSQL. Thực tế fixture
dùng `create_engine("sqlite://")`. Nói rõ nửa câu thì tránh bị hỏi vặn, và cũng cho thấy
nhóm hiểu mình đang test trên cái gì.

---

## 10. ⚠️ Xung đột với PA2 — nhưng lỗi ở PA2, đừng sửa pa3

pa3 ghi **đúng** bảy nhãn: `School, Work, Finance, Social, Shopping, System, Personal`,
kèm ánh xạ `hoc_tap, cong_viec, tai_chinh, mang_xh, mua_sam, he_thong, ca_nhan` — khớp
chính xác `app/core/labeling.py`.

**PA2 Class Diagram thì sai:** enum `EmailCategory` có `Spam` (code không có nhãn này) và
thiếu `Shopping`, `Finance`.

→ Sửa hình trong PA2, **giữ nguyên pa3**. Chi tiết ở
[SUA-2-HINH-VONG2.md](SUA-2-HINH-VONG2.md) mục C1.

*(Ngoài lề nhưng cùng gốc: `app/tools/schemas.py` dòng 403 — phần mô tả mà LLM đọc — cũng
đang ghi `'Spam', 'School', 'Career', 'Finance', 'Personal'`, sai y hệt. Cái này là lỗi
code thật, ảnh hưởng hành vi agent lúc chạy, không chỉ là chuyện tài liệu.)*

---

## 11. 🔴 Bảy mục ghi số của **cả nhóm test**, còn lệnh dẫn kèm chỉ chạy 1–2 test

Đây là mục mình phát hiện muộn nhất và là mục **nguy hiểm nhất cho bản cuối**, vì hai lý do:
người chấm gõ đúng lệnh trong bài sẽ thấy con số khác hẳn — và **ảnh minh chứng cũng sẽ
mâu thuẫn với chữ**, vì ảnh chụp đúng kết quả của lệnh đó.

Ví dụ §3.2.25: bài ghi *"13 passed in 4.72s"*, nhưng lệnh ngay dưới chỉ chạy **một** test
nên ra `1 passed`.

| Mục | Dòng | Bài đang ghi | Lệnh dẫn thực sự cho ra | Sửa cụm số thành |
| :---- | :----: | :---- | :---- | :---- |
| 3.2.2 | 418 | `13 passed in 4.72s (whole MCP group)` | 2 tests | **`2 passed in 4.08s`** |
| 3.2.4 | 452 | `15 passed in 0.64s` | 1 test | **`1 passed in 0.72s`** |
| 3.2.6 | 489 | `4 passed in 3.55s` | 1 test | **`1 passed in 1.14s`** |
| 3.2.8 | 527 | `8 passed in the contract group` | 1 test | **`1 passed in 2.79s`** |
| 3.2.10 | 564 | `8 passed in 4.29s (NFR group)` | 1 test | **`1 passed in 1.23s`** |
| 3.2.11 | 581 | `3 passed in 6.07s (new) + MCP group 13 passed` | 4 tests | **`4 passed in 3.97s`** |
| 3.2.25 | 829 | `13 passed in 4.72s` | 1 test | **`1 passed in 3.88s`** |

**Chỉ đổi cụm số** — giữ nguyên toàn bộ phần mô tả quan sát phía trước. Ví dụ §3.2.6:

```
… final\_output.kind \= "result", lines \= \[…\] — **1 passed in 1.14s**
```

**Vì sao phải là số của lệnh, không phải số của nhóm:** *Actual Output* có nghĩa là "kết quả
quan sát được khi chạy phép thử này". Phép thử này = lệnh ghi ngay bên dưới. Ghi số của cả
nhóm là trả lời một câu hỏi khác với câu đang hỏi — và người kiểm chứng không có cách nào
biết bạn đang nói về nhóm nếu dòng đó không ghi rõ.

Bốn mục (3.2.2, 3.2.8, 3.2.10, 3.2.11) **có** ghi chú "(whole MCP group)" / "(NFR group)"
nên đỡ hơn — nhưng ba mục còn lại (**3.2.4, 3.2.6, 3.2.25**) thì không, và đó là ba mục
trông giống số bịa nhất. Nếu chỉ kịp sửa ba chỗ thì sửa ba chỗ đó trước.

> **Kiểm lại sau khi sửa:** với mỗi mục, gõ đúng lệnh ở dòng `**Automated test:**` rồi so
> với cụm số vừa điền và với ảnh `TC-3.2.N-*.png`. Ba thứ phải nói cùng một con số.

---

## Bảng kiểm sau khi sửa

- [ ] Tìm `132 passed` → **0 kết quả**
- [ ] Tìm `124 passed` → **0 kết quả**
- [ ] Tìm `9 tables` → **0 kết quả**
- [ ] Tìm `implementation pending` → **0 kết quả**
- [ ] Tìm `\*\*Automated` → **0 kết quả** (dấu thoát thừa đã sạch)
- [ ] Tìm `\\\_` → **0 kết quả**
- [ ] Đếm dòng trong bảng §2.5 → **27** NFR lá
- [ ] Có mục `3.2.39` và `3.2.40`
- [ ] Chạy `cd src/backend && .venv/Scripts/python.exe -m pytest -q` → khớp con số vừa điền
- [ ] Bảy mục ở phần 11: chữ · lệnh · ảnh đều nói cùng một con số

---

## Những gì bản rà soát này KHÔNG kiểm

Bạn nói đây là bản cuối, nên phần này quan trọng ngang phần trên. Mình kiểm được thứ
**đối chiếu máy móc được**; những thứ dưới đây mình chưa đụng tới:

| Chưa kiểm | Rủi ro |
| :---- | :---- |
| **§4 AI Usage Declaration, §5 Presentation, §6 Reflective Report** | Chưa mở ra lần nào. Nếu §6 nhắc số liệu hay tên bảng thì có thể cũng cũ như Appendix B |
| **Appendix A.2, A.3, A.4** | Chỉ thấy tiêu đề. A.4 là "Load test (NFR-TC02)" — nhiều khả năng chứa số đo cũ |
| **61 dòng bảng §3.1** | Chưa dò từng dòng xem mô tả có khớp PA1 không |
| **"Expected Output" của 38 mục §3.2** | Chưa đối chiếu với đặc tả gốc trong PA1/PA2 — mình chỉ kiểm phần *Actual* |
| **PA0 (Project Proposal)** | Chưa so lần nào. Nếu PA0 hứa tính năng nào mà Testing không nhắc thì mình không biết |
| **Vì sao 61 test case mà chỉ đặc tả 38** | Mình tìm câu giải thích trong bài, **không thấy**. Nếu template không cho phép chọn lọc thì đây là chỗ bị hỏi |
| **Ảnh sau khi chèn có hiện đúng không** | base64 dài, dán hụt một ký tự là ảnh vỡ mà nhìn file md không thấy |
| **Tiếng Anh** | Không rà ngữ pháp, văn phong |

**Ba việc nên làm trước khi nộp**, xếp theo giá trị:

1. **Mở A.4 và §6 ra dò số** — hai chỗ này nhiều khả năng còn số cũ, cùng bệnh với Appendix B.
2. **Trả lời được câu "vì sao 38/61"** — thêm một câu vào đầu §3.2 nói rõ tiêu chí chọn.
   Có câu đó thì thành quyết định; không có thì thành thiếu sót.
3. **Sau khi chèn hết ảnh, mở file bằng trình xem markdown** và cuộn hết một lượt xem có
   ảnh nào vỡ không. Đừng chỉ nhìn code.

Nói mình nếu muốn dò tiếp bốn mục đầu bảng — chúng là chỗ còn sót rủi ro cao nhất.
