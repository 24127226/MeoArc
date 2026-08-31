# PA3 — phần còn lại sau khi dò PDF bản 20/08 23:18

> Dò 116 trang PDF. **5 mục đã sửa đúng, còn 4 việc.** File này chỉ chứa phần chưa xong.
>
> Đã xong, không đụng nữa: số liệu tổng (227/16 · 222/21) · `14 tables` · Appendix B mục 3
> · lý do AUTH · escaping §3.2.7.
>
> Quyết định đã chốt: **giữ §3.2.39, bỏ §3.2.40** (§3.2.40 không chỗ nào trỏ tới, bỏ an toàn).

---

# VIỆC 1 — Chèn §3.2.39 (bắt buộc)

Hiện có **5 chỗ trong bài trỏ tới mục này** mà nó chưa tồn tại: 4 chỗ trong bảng §2.5 và
1 chỗ trong Appendix B mục 3.

**Chèn vào đâu:** ngay sau mục `3.2.38 SEM-TC01…06`, trước phần `4 AI Usage Declaration`.

**Ảnh kèm:** `TC-3.2.39-SCOPE-TC0108.png` (31 passed) — đặt ngay dưới dòng `**Automated test:**`.

### Dán nguyên khối dưới đây

```
### ***3.2.39 SCOPE-TC01…08 — AI scan window by subscription tier (NFR-08)***

| *Test case* | SCOPE-TC01–08: AI operations that scan existing mailbox content respect the tier's time window |
| :---- | :---- |
| Related feature | NFR-SCO-01…04, FR-02.7 |
| Context | NFR-SCO-01 limits on-demand AI operations to **90 days (Free), 180 days (Pro), 365 days (Pro Max)** of mailbox history. The boundary is *inclusive*: an email received exactly **scan\_days** ago is still in scope. Time is pinned to a fixed date (2026-08-07) in the tests, so that a boundary case does not pass today and fail tomorrow. |
| Input Data | Emails received 0, 1, 90, 91, 180, 181, 365 and 366 days before the pinned date, evaluated against each of the three tiers; plus a tool run with a stubbed mail provider that records the arguments it was called with. |
| Expected Output | **TC01** exactly 90 days → in scope (Free). **TC02** 91 days → out of scope (Free). **TC03** 180 in / 181 out (Pro). **TC04** 365 in / 366 out (Pro Max). **TC05** task extraction capped at 90 days on every tier, and the cap never *widens* a narrower tier. **TC06** **search\_emails** receives **no** window — NFR-SCO-03 exempts keyword search, and limiting it would take away the user's ability to find their own older mail. **TC07** **categorize\_emails** and **semantic\_search** both pass the tier's cutoff down to the provider call. **TC08** the indicator beside the chat input reads "quét 90 ngày" on the Free tier. |
| Test steps | 1\) Evaluate the scope predicate on both sides of each boundary with the date pinned.  2\) Check the task-extraction cap on every tier.  3\) Invoke each tool with a stubbed provider and read back the arguments it received.  4\) Invoke **search\_emails** and assert no window was passed.  5\) Read the indicator in the running UI. |
| Actual Output | All boundary cases behaved as specified; the cutoff reached the provider call for both scanning tools and for all three tiers; **search\_emails** received none; an out-of-scope result returns an explanation naming the window rather than "mailbox empty" — **31 passed in 1.83s**. TC08 verified visually — the meter reads "MIỄN PHÍ · quét 90 ngày". |
| Result | **Passed** |

**Automated test:** *pytest tests/test\_scope.py tests/test\_scope\_tools.py \-v*

**Why the date is pinned.** A boundary test written against "today" is a test that changes meaning every night. Passing an explicit date into the scope functions makes 90-versus-91 a fixed, repeatable question — and it is the only way the failing side of the boundary can be asserted at all.

**Why the exemption is tested as hard as the limit.** SCOPE-TC06 asserts that keyword search is *not* restricted. A limit that is too aggressive breaks the product just as thoroughly as one that is absent: NFR-08 exists to bound what the *AI* reads, not to stop a user finding an email they received last year. Without this test, a future change that applies the window everywhere would look like a tightening of a security control rather than the data-loss bug it actually is.
```

> ⚠️ **Số đã được sửa so với bản nháp trong `docs/test/Testing.md`.** Bản nháp ghi
> *"18 passed + 10 passed"*; chạy lại đúng lệnh bây giờ ra **31 passed in 1.83s**
> (21 ở `test_scope.py` + 10 ở `test_scope_tools.py`). Khối trên đã dùng số đúng —
> **đừng chép lại từ bản nháp**, nó cũ.

---

# VIỆC 2 — Sửa bảng §2.5 (2 chỗ)

## 2a. Dòng `NFR-SCO-01…04` đang mâu thuẫn với Appendix B

**Tìm chuỗi:** `not covered — implementation pending`

**Hiện tại**
```
| NFR-SCO-01…04 | AI scan window limited by subscription tier (90 / 180 / 365 days) | not covered — implementation pending. Five boundary cases defined in Appendix B item 3 |
```

**Sửa thành**
```
| NFR-SCO-01 | AI scan window limited by subscription tier (90 / 180 / 365 days) | SCOPE-TC01…TC04 |
```

**Vì sao:** Appendix B mục 3 giờ ghi *"implemented and covered"*, còn dòng này vẫn ghi
*"implementation pending"* — hai chỗ trong cùng tài liệu nói ngược nhau. Đây là loại lỗi
máy dò chéo bắt được đầu tiên. Đổi mã từ `NFR-SCO-01…04` thành `NFR-SCO-01` vì ba mã
`SCO-02/03/04` đã có dòng riêng ngay bên dưới rồi — để dải `01…04` là trùng.

## 2b. Lỗi gõ — một ký tự

**Tìm chuỗi:** `SCOPE=TC06`

Dấu **bằng** thành dấu **gạch ngang**: `SCOPE-TC06`

---

# VIỆC 3 — Bảy cụm số trong §3.2 (chưa sửa)

Bảy mục ghi số của **cả nhóm test**, còn lệnh dẫn kèm chỉ chạy 1–2 test. Người chấm gõ
lệnh sẽ thấy số khác, và **ảnh minh chứng cũng sẽ chỏi với chữ** vì ảnh chụp đúng kết quả
của lệnh đó.

| Mục | Bài đang ghi | Sửa cụm số thành |
| :---- | :---- | :---- |
| 3.2.2 | `13 passed in 4.72s (whole MCP group)` | **`2 passed in 4.08s`** |
| 3.2.4 | `15 passed in 0.64s` | **`1 passed in 0.72s`** |
| 3.2.6 | `4 passed in 3.55s` | **`1 passed in 1.14s`** |
| 3.2.8 | `8 passed in the contract group` | **`1 passed in 2.79s`** |
| 3.2.10 | `8 passed in 4.29s (NFR group)` | **`1 passed in 1.23s`** |
| 3.2.11 | `3 passed in 6.07s (new) + MCP group 13 passed` | **`4 passed in 3.97s`** |
| 3.2.25 | `13 passed in 4.72s` | **`1 passed in 3.88s`** |

**Chỉ đổi cụm số**, giữ nguyên toàn bộ mô tả quan sát phía trước.

**Nếu gấp, sửa ba mục trước:** `3.2.4`, `3.2.6`, `3.2.25` — ba mục này không có ghi chú
"(group)" nên trông giống số bịa nhất.

---

# VIỆC 4 — Nửa câu ở §2.7 (không bắt buộc)

**Tìm chuỗi:** `PostgreSQL 18.4`

Thêm vào cuối ô đó:
```
Automated tests run against in-memory SQLite fixtures; the PostgreSQL instance is used by the running application and by the migration tests.
```

**Vì sao:** hiện đọc như thể toàn bộ test chạy trên PostgreSQL, thực tế fixture dùng
`create_engine("sqlite://")`. Nói rõ thì tránh bị hỏi vặn.

---

# BẢNG KIỂM TRƯỚC KHI XUẤT PDF LẦN CUỐI

- [ ] Có mục `3.2.39` với tiêu đề đầy đủ, và ảnh `TC-3.2.39-SCOPE-TC0108.png` nằm dưới nó
- [ ] Tìm `implementation pending` → **0 kết quả**
- [ ] Tìm `SCOPE=TC` → **0 kết quả**
- [ ] Tìm `13 passed` → **0 kết quả**
- [ ] Tìm `15 passed` → **0 kết quả**
- [ ] Tìm `8 passed in the contract` → **0 kết quả**
- [ ] Tìm `3.2.40` → **0 kết quả** (đã quyết bỏ, không được để tham chiếu treo)
- [ ] Mọi mã `SCOPE-TC01…TC08` trong §2.5 đều tìm thấy đích ở §3.2.39
- [ ] Chạy `cd src/backend && .venv/Scripts/python.exe -m pytest -q` → `227 passed, 16 skipped`
      (có backend chạy) hoặc `222 passed, 21 skipped` (không backend)
- [ ] Cuộn hết PDF một lượt xem có ảnh nào vỡ không

---

### Nhắc lại phần mình KHÔNG kiểm được

Mình chưa mở §4 AI Usage Declaration, §5 Presentation, §6 Reflective Report, và
Appendix A.2/A.3/A.4. **A.4 tên là "Load test (NFR-TC02)"** — nhiều khả năng chứa số đo cũ,
cùng bệnh với Appendix B. Nếu còn thời gian thì mở hai chỗ đó dò số trước khi nộp.
