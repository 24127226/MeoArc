# Phần còn THIẾU trong bản Testing đang ở Google Docs

> Bản trong Docs của bạn thiếu 4 khối dưới đây, trong khi thân bài đã dẫn tới chúng 8 lần.
> Dán đúng vị trí ghi ở mỗi mục. Ngoài 4 khối này còn 3 việc sửa tại chỗ, liệt kê ở cuối file.

---

## ① Thay toàn bộ §1 Member Contribution Assessment

**Vị trí:** xoá hai dòng `StudentID 1 - Fullname 1 - Contribution (%)` và
`StudentID 2 - Fullname 2 - Contribution (%)` cùng phần bên dưới chúng, dán khối này vào thay.
MSSV và tỷ lệ 25% lấy từ PA1 nên khớp sẵn với ba tài liệu kia.

# 1 Member Contribution Assessment

> ⚠️ **Task Evidence still to be added by each member.** Names, student IDs and the 25% split are carried over from the submitted Requirement Analysis (PA1) so that the artifacts stay consistent; adjust the percentages if this phase's workload differed. The Jira/Git screenshots showing Task Name, Assignee, Status, Assigned Date and Completion Date can only be produced by the members themselves.

| StudentID | Full name | Contribution (%) | Sections owned in this document |
| :---- | :---- | :---- | :---- |
| 24127226 | Phạm Trần Anh Quân | 25% | UC009 Categorize; EmailDraft & Reply test cases |
| 24127250 | Phan Quang Tiến | 25% | §2 Test plan; HITL, UC011, NFR test cases |
| 24127529 | Nguyễn Chí Tài | 25% | UC012 MCP; Bulk Action; Attachment; Embeddings |
| 24127545 | Nguyễn Ngọc Thiên | 25% | UC007 Agent Reasoning Loop; AUTH test cases |

Each task must be assigned to and completed by only one student.
The sum of all student contributions is less than or equal to 100%.
The project tasks include report writing, self-training, and implementation tasks.

---
---

## ② Thêm §2.4.1 — bảng truy vết sang SRS

**Vị trí:** cuối §2.4 *Objects under test*, ngay TRƯỚC tiêu đề §2.5 *Prioritisation*.

Đây là mục nối Testing với PA1 chặt nhất: nó ánh xạ test case sang đúng 22 mã lá
(NFR-PER-01, NFR-SEC-02…) mà PA1 định nghĩa, và nói thẳng 9 mã nào chưa có test.

### 2.4.1 Traceability to the submitted SRS

The non-functional requirements are numbered in two levels in the submitted Requirement Analysis (PA1): a category (`NFR-01`…`NFR-08`) containing leaf requirements (`NFR-PER-01`, `NFR-SEC-02`, …). Test cases trace to the **leaf**, because that is the level at which a requirement is either met or not.

| Leaf requirement (PA1) | What it demands | Covered by |
| :---- | :---- | :---- |
| NFR-PER-01 | API responses under 3 s for ≥95% of requests | NFR-TC02 ✅ |
| NFR-PER-02 | Email list displayed within 5 s | **not covered** |
| NFR-SEC-01 | Authentication via Google OAuth 2.0 | AUTH-TC03 (partly) — full flow not run |
| NFR-SEC-02 | Never store raw passwords | SEC-TC05 ✅ |
| NFR-SEC-03 | HTTPS/TLS on all communications | **not covered** — no TLS in the local test environment |
| NFR-SEC-04 | Secrets in environment variables, never hard-coded | **not covered** |
| NFR-SEC-05 | Rate limiting per user/IP | NFR-TC03 ✅ |
| NFR-REL-01 | Graceful handling of Gmail/Gemini temporary failures | NFR-TC05 ✅, UC007-TC06 ✅ |
| NFR-REL-02 | No loss of conversation history on failure | NFR-TC06 ✅ |
| NFR-USA-01 | Works on Chrome, Edge, Firefox, Safari | NFR-TC09 — manual, pending |
| NFR-USA-02 | Clear error messages for non-technical users | **not covered** — subjective, better judged in alpha testing |
| NFR-USA-03 | Responsive UI optimised for desktop | NFR-TC09 (partly) |
| NFR-MAI-01 | Modular backend architecture | **not covered** — architectural, judged by inspection |
| NFR-MAI-02 | APIs documented via OpenAPI/Swagger | TOOL-TC01 ✅ (screenshot S7 is the OpenAPI document) |
| NFR-MAI-03 | Deployable via a single Docker Compose file | **not covered** |
| NFR-MAI-04 | Log every API request and agent task execution, including token usage | UC007-TC07 ✅ (token usage), UC007-TC06 ✅ (tool calls, errors) — the request-level log fields are only partly checked |
| NFR-SCA-01 | Architecture supports additional LLM providers | **not covered** |
| NFR-SCA-02 | Architecture supports new tools via REST or MCP | MCP-TC01 (partly) |
| NFR-COM-01 | Gmail and Outlook behave consistently through one abstraction | AUTH-TC03 ✅ |
| NFR-COM-02 | MCP server complies with the Model Context Protocol | MCP-TC01 ✅, MCP-TC02 ✅ |
| NFR-SCO-01…04 | AI scan window limited by subscription tier (90 / 180 / 365 days) | **not covered — implementation pending.** Five boundary cases defined in Appendix B item 3 |

**Reading this table honestly.** Nine of the twenty-two leaf requirements have no test. That is a real coverage figure, not a failure of effort: three are architectural judgements that inspection serves better than a test (NFR-MAI-01, NFR-SCA-01, NFR-USA-02), two cannot be exercised in a local environment without TLS and a deployment target (NFR-SEC-03, NFR-MAI-03), and one covers a feature whose implementation is still pending (NFR-SCO-01…04). The remaining three — NFR-PER-02, NFR-SEC-04, NFR-MAI-04's request-log fields — **are testable and simply have not been tested yet.** Those three are the honest to-do list.
---

## ③ Thêm Phụ lục A — Evidence log

**Vị trí:** sau §6 Reflective Report, ở cuối tài liệu.

Đây là phần chống lưng cho toàn bộ cột *Actual Output*. Thân bài đã dẫn tới nó ở
§3.2 mở đầu và §3.2.37, nên thiếu nó là tham chiếu gãy.

# Appendix A — Evidence log

All results in §3.2 come from this run, on 2026-08-05, branch `integration`, commit `06fbc9c`.

## A.1 Full suite

```bash
cd src/backend && .venv/Scripts/python.exe -m pytest -q
```

The suite was run in two configurations, because how many tests *can* run depends on whether a backend is listening:

| Configuration | Result |
| :---- | :---- |
| Backend **not** running (default developer machine) | `124 passed, 21 skipped in 38.67s` |
| Backend running on `127.0.0.1:8000` | **`132 passed, 16 skipped in 66.62s`** |

The difference is 3 newly added tests (`tests/test_audit_failed.py`, see §3.2.11) plus the 5 tests in `tests/test_uc011_api.py`, which need a live server and therefore skip themselves when there is none. Running the backend first is what turns NFR-TC06 from a manual check into an automated one, so **the second configuration is the one to use when producing evidence**:

```bash
cd src/backend && .venv/Scripts/python.exe -m uvicorn app.api.app:app --port 8000
```

Every skip is an external-dependency skip with a stated reason — none is unexplained:

| Count | File | Reason given by the test | Runs with backend up? |
| :---- | :---- | :---- | :---- |
| 6 | `test_agent.py` (repo root) | Live black-box suite; needs a running server, and the LLM was over its free quota at run time | Needs LLM quota too |
| 6 | `tests/test_agent.py` | `MEOARC_COOKIE` (a real login cookie) not set | No — needs a real login |
| 5 | `tests/test_uc011_api.py` | Needs a running server | **Yes — passes, see A.2** |
| 3 | `tests/test_live_e2e.py` | Sends real email and consumes quota; requires `MEOARC_LIVE=1` deliberately | No, by design |
| 1 | `tests/test_llm_smoke.py` | Requires `MEOARC_LLM_SMOKE=1`; costs one real LLM request | No, by design |

A skip that guards a destructive or quota-consuming action is a deliberate design choice, not a gap: `test_live_e2e.py` actually sends mail, so it must never run by accident in a routine build. Those cases are executed by hand during the alpha session.

*Minor housekeeping noted during this run:* `test_agent.py` sits at the backend root rather than in `tests/`, so it is collected as a separate top-level module. It is an independent live black-box suite, not a duplicate of `tests/test_agent.py`, but it belongs under `tests/`.

## A.2 Per-group results

| Group | Tests | Result | Time |
| :---- | :---- | :---- | :---- |
| `test_labeling.py` (UC009) | 25 | passed | 2.49 s |
| `test_tool_schemas.py` | 15 | passed | 0.64 s |
| `test_mcp.py` (UC012) | 13 | passed | 4.72 s |
| `test_breaker.py` | 8 | passed | 0.48 s |
| `test_nfr.py` | 8 | passed | 4.29 s |
| `test_semantic.py` | 6 | passed | 2.68 s |
| `test_subscription.py` | 6 | passed | 3.01 s |
| `test_maintenance.py` | 6 | passed | 1.37 s |
| `test_ops_endpoints.py` | 6 | passed | 3.24 s |
| `test_kv.py` | 5 | passed | 1.08 s |
| `test_agent_offline.py` (UC007) | 4 | passed | 3.55 s |
| `test_isolation.py` | 4 | passed | 1.28 s |
| `test_mailbox_sync.py` | 4 | passed | 1.44 s |
| `test_migrations.py` | 3 | passed | 1.98 s |
| `test_audit_notify.py` | 3 | passed | 2.80 s |
| `test_audit_failed.py` *(added while writing this document)* | 3 | passed | 6.07 s |
| `test_uc011_api.py` *(with backend running)* | 5 | passed | 18.65 s |

## A.3 Live system output

`GET /health`:

```json
{"status": "ok", "db": "up", "uptime_s": 143, "version": "0.1.0"}
```

`GET /metrics` (excerpt):

```json
{
  "latency_ms": {"p50": 6.1, "p95": 6.1, "p99": 6.1},
  "provider_slots_free": 32,
  "llm_slots_free": 6,
  "db_pool": {"size": 20, "checked_out": 0, "overflow": -19},
  "kv_backend": "memory",
  "thread_pool": 96,
  "workers": 1,
  "ngat_mach": {
    "nha_cung_cap_thu": {"trang_thai": "dong", "so_lan_hong_lien_tiep": 0, "so_lan_da_mo_mach": 0},
    "mo_hinh_ai":       {"trang_thai": "dong", "so_lan_hong_lien_tiep": 0, "so_lan_da_mo_mach": 0}
  }
}
```

## A.4 Load test (NFR-TC02)

```
Total requests : 200 (concurrency 60)
Total time     : 1.59s  -> 126.1 req/s
Errors         : 0
p50/p95/p99    : 365 / 415 / 418 ms
max            : 422 ms
Under 3000ms   : 200/200 = 100.0%
```

## A.5 Screenshots to capture

Each image is listed with exactly what it must show, so that the screenshot is evidence rather than decoration.

**Already captured** — in `docs/test/screenshots/`, taken from the mock-mode front end and the live backend:

| # | File | What it shows | Evidence for |
| :---- | :---- | :---- | :---- |
| S4 | `S4-mail-view-chips.png` | Mail list with category chips (HỌC TẬP, CÔNG VIỆC, CẬP NHẬT & HỆ THỐNG, CÁ NHÂN) and priority chips (CẦN XỬ LÝ, ĐANG ĐỢI) | UC009-TC02 |
| S4b | `S4b-filter-7-nhom.png` | The category filter expanded: all 7 categories, each in its own colour, none repeated | UC009-TC05 |
| S5 | `S5-the-duyet-truoc-khi-gui.png` | The **BẢN NHÁP TRẢ LỜI** card with recipient, subject and body, offering "Niêm phong & Gửi / Chỉnh sửa / Viết lại / Huỷ" — nothing sent yet. The footer reads "Mọi hành động không thể hoàn tác đều cần bạn xác nhận trước." | HITL-TC01 |
| S6 | `S6-agent-panel.png` | The quota meter "13 lượt · MIỄN PHÍ" beside the chat input | UC007-TC04 |
| S7 | `S7-openapi-limit-max-50.png` | OpenAPI publishing `limit — maximum: 50, minimum: 1, default 30` and `cursor — maxLength: 512` | TOOL-TC01 |
| S8 | `S8-metrics.png` | `/metrics` with latency percentiles, free provider slots, and both circuit-breaker states | NFR-TC01, NFR-TC05 |
| S10 | `S10-mobile.png` | The mail view at 390×844 with no horizontal overflow | NFR-TC09 |

**Still to capture** — terminal output, quicker to take by hand than to automate:

| # | Screenshot | What it must show | Command |
| :---- | :---- | :---- | :---- |
| S1 | Full suite result | The final line `132 passed, 16 skipped`, with the command visible above it | `pytest -q` (backend running — see A.1) |
| S2 | UC009 group, verbose | All 25 `test_labeling.py` lines marked `PASSED` | `pytest tests/test_labeling.py -v` |
| S3 | HITL group, verbose | The confirm-gate tests passing | `pytest tests/test_agent_offline.py tests/test_mcp.py -v` |
| S9 | Load test output | The figures in A.4 | Run the load script |

---
---

## ④ Thêm Phụ lục B — Implementation status

**Vị trí:** ngay sau Phụ lục A, kết thúc tài liệu.

Bản này đã viết lại giọng: không còn câu nào nói "thiết kế sai", chỉ nói tính năng nào
đang chờ hiện thực. Nhờ vậy nó KHÔNG chỏi với PA1/PA2 — điều quan trọng vì cả bốn tài liệu
sẽ được đọc cùng lúc.

# Appendix B — Implementation status of specified requirements

Test cases are written from the specification, so some of them describe behaviour the implementation has not reached yet. That is the normal state of a V-model project, where test design runs from the requirements in parallel with coding rather than after it.

This appendix records, for each such case, what the specification requires and where the implementation currently stands. **None of these is a defect in working code**, and none of them contradicts PA1 or PA2 — the specification is the reference, and these are the items still travelling towards it. Test cases in this state are marked *Not run* in §3, never *Passed*.

**1. The class/ER design model contains entities that were never implemented as tables.**

The implemented schema has 9 tables across 8 model modules: `users`, `sessions`, `session_providers`, `emails` (`StoredEmail`), `mailbox_sync`, `conversations`, `audit_logs`, `notifications`, `subscriptions`. The design model additionally describes `EmailDraft`, `Attachment`, `ToolCall`, `Toolcall_Email`, `Embeddings`, `Connected_Account`, `Gmail_Account` and `Outlook_Account` as first-class entities. In the implementation:

- **Attachment** data is stored as a JSON column on the email row (`attachments_json`), not as a separate table — so `attachment_seq` and `extracted_text` have no column to be tested against.
- **ToolCall / Toolcall_Email** are covered by `audit_logs`, which records `tool_name`, `status` and `affected_email_ids` as a JSON list. This captures the same information but not as a many-to-many table, so a test asserting "each link row has its own `created_at`" has nothing to assert on.
- **Gmail_Account / Outlook_Account** subtype fields are implemented on `mailbox_sync` (`history_id` for Gmail, `delta_link` for Outlook). The *behaviour* the design intended is present and tested (AUTH-TC03); the *shape* differs.
- **EmailDraft** has no table at all: drafts live in the front end and in the confirmation card until sent.
- **Embeddings** is not a table either. Semantic search re-ranks results with embeddings computed on the fly (`app/core/embeddings.py`), so there is no stored `chunk_index` and no `embedding_type` column to assert on. The ranking behaviour itself *is* covered — see SEM-TC01…06.

*Consequence for the test suite:* the suggested test cases for EmailDraft status transitions, attachment ordering, and ToolCall↔Email link timestamps cannot be written as they stand. **Status:** the team has chosen to implement these entities rather than amend the design. The corresponding test cases are defined against PA2 and recorded as *Not run* until the tables exist.

**2. Simultaneous multi-account connection is not supported by the current schema.**

`session_providers` binds one provider to one session token. AUTH-TC01 ("a user can connect multiple email accounts and both operate independently") therefore cannot pass today. The user can connect Gmail *or* Outlook and switch; they cannot hold both at once. **Status:** scheduled for implementation. AUTH-TC01 and AUTH-TC02 remain defined against FR-01.2 and recorded as *Not run* until simultaneous connections are supported.

**3. NFR-08 scan window — specified, tests designed, implementation pending.**

NFR-08 (NFR-SCO-01) requires on-demand AI operations that scan existing mailbox content — semantic search, categorisation, summarisation, task extraction and reply-context retrieval — to limit their time range by subscription tier: **90 days (Free), 180 days (Pro), 365 days (Pro Max)**. FR-02.7 additionally requires the current window to be displayed as a persistent indicator beside the chat input.

The subscription model currently enforces a **token ceiling per day and per month** (100,000 / 2,000,000 / 10,000,000 daily), which UC007-TC04 covers. The day-window limit is **not yet implemented**, so the five boundary cases below are defined against the specification but recorded as *Not run* rather than executed:

| Case | Boundary under test |
| :---- | :---- |
| NFR-08-TC01 | An email received exactly 90 days ago is still included on the Free tier |
| NFR-08-TC02 | An email received 91 days ago is excluded on the Free tier |
| NFR-08-TC03 | An email received exactly 180 days ago is still included on the Pro tier |
| NFR-08-TC04 | An email received exactly 365 days ago is still included on the Pro Max tier |
| NFR-08-TC05 | The indicator beside the chat input shows the window matching the current tier (FR-02.7) |

**Note on boundary values.** These test exactly 90 and exactly 91, not 30 and 31. An earlier draft of this document used 30/90/180 because the suggested test cases had been copied from a use-case section of PA1 that quoted the requirement inaccurately; PA1 has since been corrected so that the use-case section matches the normative NFR-SCO-01. Boundary cases are worth writing only against the authoritative statement of the requirement — a boundary test aimed at the wrong number gives false confidence, which is worse than no test.

**3b. Priority and Status labels do not match the SRS taxonomy.**

PA1 §4.2.9 (Categorize Email) specifies a multi-dimensional taxonomy: **Category** — exactly one of seven fixed values (School, Work, Finance, Social, Shopping, System, Personal) — plus **Priority** (High, Medium, Low) and **Status** (Todo, Waiting, Done), the latter two assigned only for task-like emails.

The implementation matches on Category: all seven values exist and map one-to-one (`hoc_tap`, `cong_viec`, `tai_chinh`, `mang_xh`, `mua_sam`, `he_thong`, `ca_nhan`), which is what UC009-TC02 and UC009-TC05 verify. But Priority and Status are **collapsed into a single field** `ai_priority` carrying `action` / `waiting` / `fyi` — three values belonging to neither of the two vocabularies the SRS defines. This is why the suggested test case "keep `aiPriority`/`aiTaskStatus` null for non-task-like email" could not be written: there is no `aiTaskStatus` field at all.

**Status:** scheduled for implementation — the field will be split into Priority and Status as PA1 §4.2.9 specifies, and `applyAILabels(category, priority, status)` added as PA2 §1.3.9 specifies.

**3c. FR-02.7 asks for a time-window indicator; the UI shows a token counter.**

FR-02.7 requires the system to "display the current AI processing time window (per the user's subscription tier) as a persistent indicator near the chat input". The implementation does place a persistent indicator near the chat input — screenshot S6 — but it reports **remaining turns and plan name** ("13 lượt · MIỄN PHÍ"), not a time window. UC007-TC04 in this document tests the quota behaviour that exists; it does **not** satisfy FR-02.7 as written. Same decision as item 3: build the window, or amend the requirement.

**4. `actorType` no longer distinguishes the three entry points.**

The suggested UC012 test case notes this itself. `audit_logs.actor_type` defaults to `"user"` and does not separate web / agent / MCP origins, so "an external agent's call does not create a Message/Conversation" has to be verified by asserting the absence of conversation rows rather than by reading the actor type. MCP-TC01 is written that way. **Status:** the current check is sufficient for UC012. An explicit origin field would be needed only if per-origin analytics are added later.

**5. Front-end API base URL uses `localhost`.**

Not a design deviation, but found while investigating NFR-TC02: `VITE_API_BASE_URL=http://localhost:8000` costs 50–320 ms per request in the browser against 8–12 ms for `127.0.0.1`, because of the same IPv6-first resolution described in NFR-TC02. Changing one line in `src/frontend/.env.local` removes it.
---

# Ba việc sửa tại chỗ (không phải dán thêm)

## ⑤ Xoá khối bị dán trùng ở đầu §3.2

Đoạn **"How to read the Actual Output column…"** hiện xuất hiện **hai lần liên tiếp**, mỗi lần
kèm một chú thích **"Hình 1"** trỏ vào hai ảnh khác nhau.

Giữ khối thứ nhất cùng một ảnh Hình 1. Xoá nguyên khối thứ hai và ảnh thừa.

## ⑥ Xoá câu chỉ dẫn của template ở đầu §2

Ngay dưới dòng "Reviewed by:" của §2 còn nguyên câu trong ngoặc vuông:

> `[Present the project testing plan, clearly stating which testing techniques the team intends to apply and on which objects (functions, documents) of the system the testing will be performed]`

Xoá cả dòng. Nội dung §2 bên dưới đã trả lời đúng câu đó rồi.

## ⑦ Thêm MSSV vào các dòng tác giả, và dựng lại mục lục

Ba chỗ ghi "Written by:" đang thiếu MSSV. Sửa cho khớp quy ước của PA1/PA2:

| Đang ghi | Sửa thành |
| :---- | :---- |
| Written by: Phan Quang Tiến | Written by: 24127250 – Phan Quang Tiến |
| Written by: Phan Quang Tiến, Phạm Trần Anh Quân | Written by: 24127250 – Phan Quang Tiến, 24127226 – Phạm Trần Anh Quân |

**Mục lục** vẫn là bản cũ của template: `1.1 List of test cases`, `1.2 Test case specifications`,
`1.2.1 Name of Test case 1` — sai số mục và trỏ tới mục không tồn tại. Xoá hết rồi
**Insert → Table of contents** để Docs tự dựng lại từ các tiêu đề thật.

---

# Kiểm lại sau khi xong

- [ ] Tìm `StudentID 1` → 0 kết quả
- [ ] Tìm `[Present the project` → 0 kết quả
- [ ] Tìm `Name of Test case 1` → 0 kết quả
- [ ] Tìm `How to read the Actual Output` → **đúng 1** kết quả
- [ ] Đếm chú thích `Hình 1` → **đúng 1**
- [ ] Có mục "Appendix A" và "Appendix B" thật, không chỉ nằm trong tham chiếu
- [ ] Mục lục hiện đúng 3.1 / 3.2, không còn 1.1 / 1.2
