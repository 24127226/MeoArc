# MeoArc — Bản tích hợp (quan ⨯ develop)

> Folder này GHÉP hai nửa thành một sản phẩm chạy được:
> - **`backend/`** = đôi tay của **quan** (Gmail/auth/Postgres/REST, đã chạy) **+** bộ não của **develop** (agent/tools/mcp).
> - **`frontend/`** = frontend của **quan** (đã nối backend).
>
> Mục tiêu: **không ai mất tính năng**, **an toàn**, ghép từng pha không qua trạng thái hỏng.
> Đây là bản dựng độc lập — KHÔNG đụng nhánh `quan`/`develop` trên GitHub.

---

## 1. Kiến trúc: 2 cửa — 1 buồng máy

```
Giao diện nút  → REST API (quan)   ┐
                                    ├→  LỚP SERVICE (quan)  → Gmail + Postgres
Chat AI / MCP  → Agent graph (dev) ┘        ↑ não develop gọi xuống đôi tay quan
```
Cả hai cửa **dùng chung `app/services/*`** → không trùng lặp, sửa 1 nơi cả 2 hưởng. Đúng thiết kế `docs/00-OVERVIEW`.

## 2. Bản đồ thư mục (ai đóng góp gì)

| Phần | Nguồn | Ghi chú |
|---|---|---|
| `app/services/*`, `repo`, `models`, `schemas`, `core/db.py`, `core/deps.py`, `core/security.py`, `core/config.py` | **quan** | đôi tay đã chạy; develop để rỗng → bỏ stub |
| `app/api/app.py`, `app/api/auth.py` | **quan** | REST + bridge `/agent/plan/execute` |
| `app/agent/*` (graph, nodes, guardrails, memory, skills/*.md) | **develop** | bộ não LangGraph + thư viện skills |
| `app/tools/registry.py`, `schemas.py` | **develop** | hợp đồng tool (Pydantic) |
| `app/tools/email_tools.py` | **TÍCH HỢP (mới)** | điền rỗng → gọi service của quan |
| `app/mcp/*`, `app/core/llm.py`, `app/core/logging.py` | **develop** | MCP + Gemini wrapper |

## 3. Đường nối "não → tay" (đã wire ở `app/tools/email_tools.py`)

Mỗi tool nhận `ctx.access_token` (RequestContext) → gọi service quan (bọc `asyncio.to_thread` vì service sync).

| Tool agent | Gọi vào (quan) |
|---|---|
| `search_emails` | `gmail_service.list_messages` |
| `get_email` | `gmail_service.get_message` |
| `list_labels` | `gmail_actions.list_label_names` *(helper cộng thêm)* |
| `send_email` | `gmail_send.send_email` |
| `reply_email` | `gmail_send.reply_email` |
| `apply_labels` | `gmail_actions.apply_label` / `modify_labels` |
| `bulk_action` | `gmail_actions.trash` / `modify_labels` / `apply_label` |

> `summarize_email`, `draft_email` cần LLM → thuộc `compose_tools` / agent node (develop làm tiếp).

## 4. ⚠️ 4 điểm NHÓM phải chốt (kẻo wire xong lại lệch)

1. **Category**: develop dùng enum `Spam/School/Finance/Career/Personal`; quan + FE dùng màu `moss/sea/sun/cherry/sky/terra/wine`. → chọn 1 chuẩn + bảng map. (Hiện `_to_summary` để `category=None`.)
2. **Auth**: develop định JWT (RequestContext.user_id/access_token); quan dùng cookie-session + `get_gmail_token`. → `api/deps` của agent nên LẤY token qua `get_gmail_token` của quan.
3. **Khuôn dữ liệu thư**: develop `EmailSummary` cần `thread_id` + `date: datetime`; quan `Email` chưa lộ `threadId`, `date` là chuỗi. → quan nên thêm `threadId` + ngày ISO 8601 (hiện đang tạm `thread_id=id`, parse chuỗi).
4. **AgentReply**: đầu ra `/agent/chat` PHẢI khớp union `AgentReply` mà FE render (docs/01) → cần adapter ở agent output.

**Bug cần sửa (develop):** `registry.to_langchain_tools()` lọc ngược — `if spec.category not in exclude: continue` khiến nó BỎ các tool không-bị-loại (chỉ giữ tool bị exclude). Sửa thành `if spec.category in exclude: continue`.

## 5. Trạng thái theo pha

- ✅ **Pha 0** — dựng nền = backend quan (chạy full-stack).
- ✅ **Pha 1** — union: bê `agent/ tools/ mcp/ llm` của develop vào (khác thư mục → không đụng file quan).
- ✅ **Pha 2** — wire `email_tools` gọi service quan + helper `list_label_names`. (Verify: import OK, tool đăng ký đủ.)
- ✅ **Pha 3 (→ LLM-Powered App, 9đ)** — graph develop RỖNG nên tự xây: `agent_node` (Gemini + bind tool), `tool_node` (chạy tool qua registry.call), `graph` (vòng ReAct), `skill_loader`. Mount `/agent/chat` → chạy graph, token qua `get_gmail_token`, **fallback** khi chưa key. + cấu hình LLM ở `config.py`/`.env.example`, `uv add langgraph langchain langchain-google-genai`, sửa bug lọc `registry`. Verify: graph compile, 7 tool bind, app nguyên (23 route).
- ✅ **Pha 4 (→ agent-native, 10đ)** — `app/mcp/server.py` (fastmcp) phơi **7 tool HẠT MỊN** cho agent NGOÀI (Claude/Codex) — đúng Q&A thầy (agent ngoài TỰ suy luận, không có tool "to" gộp suy luận). Token từ phiên đăng nhập mới nhất trong DB (tự refresh, có cache 45s) hoặc env `MEOARC_ACCESS_TOKEN`. **KHÔNG cần key Gemini**. Chạy: `uv run python -m app.mcp.server`.
  - **CONFIRM-GATE (điểm riêng)**: send/reply/bulk-delete lần gọi đầu chỉ trả BẢN XEM TRƯỚC + bắt agent hỏi người dùng, gọi lại `confirm=true` mới chạy thật → human-in-the-loop CƯỠNG CHẾ ở tầng tool cho cả agent ngoài (UC010).
  - **3 MCP prompts** (daily_digest / triage_inbox / meeting_brief) hiện trên menu Claude Desktop + resource `meoarc://whoami`.
  - Đã sửa bug enum `BulkAction.DELETE="Delete"` → `"delete"` (case-insensitive) — trước đây lệnh xoá hàng loạt fail validate. Verify: 13/13 test `tests/test_mcp.py`.
- ⬜ **Pha 5** — adapter AgentReply giàu hơn (plan/draft thay vì chỉ text) + chốt 4 điểm mục 4 → E2E mượt.

## 6. Cách chạy

```powershell
# Backend (REST + agent in-app)
cd D:\meoarc-integration\backend
copy .env.example .env      # điền GOOGLE_CLIENT_ID/SECRET + DATABASE_URL + AI_API_KEY (key Gemini, có thì agent "nghĩ" thật)
uv run main.py              # http://localhost:8000

# Frontend
cd D:\meoarc-integration\frontend
npm install
# tạo .env.local: VITE_API_BASE_URL=http://localhost:8000
npm run dev                 # http://localhost:5173

# MCP server (agent-native — cho Claude Desktop/Codex cắm vào). Cần đã đăng nhập web trước.
cd D:\meoarc-integration\backend
uv run python -m app.mcp.server

# HOẶC: dựng cả hệ bằng Docker (máy có Docker Desktop — phần QA):
cd D:\meoarc-integration
docker compose up --build          # FE 5173 + BE 8000 + Postgres (volume riêng)
# kèm Redis: docker compose --profile redis up --build (+ REDIS_URL trong backend/.env)
```

**3 chế độ giờ đều CHẠY ĐƯỢC:**
1. **App thường (bấm nút)** — luôn chạy (Pha 0–2). Không cần key.
2. **LLM-Powered App** (`/agent/chat` chat AI in-app) — cần `AI_API_KEY` (Gemini). Chưa key → fallback lịch sự.
3. **Agent-native** (Claude/Codex của user → MCP → app) — chạy được **ngay sau khi đăng nhập web**, KHÔNG cần key Gemini (trí tuệ ở agent ngoài).
