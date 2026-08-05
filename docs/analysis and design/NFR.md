# MeoArc — Yêu cầu Phi chức năng (NFR) đã triển khai

> Tài liệu cho báo cáo SRS/demo. Mỗi mục ghi: cơ chế → file → **cách chứng minh** (lệnh chạy được).
> Toàn bộ có test tự động khách quan kèm theo (`backend/tests/`), tổng cộng 30+ test PASS.

## 1. PERFORMANCE / SPEED (Hiệu năng)

| Cơ chế | File | Chứng minh |
|---|---|---|
| **Tool chạy song song**: LLM xin N tool trong 1 lượt → `asyncio.gather` chạy đồng thời, tổng thời gian ≈ tool chậm nhất (giữ nguyên thứ tự kết quả) | `app/agent/nodes/tool_node.py` | `uv run pytest tests/test_nfr.py::test_tool_node_chay_song_song -v` (3 tool × 0.35s xong trong <0.8s) |
| **Nén GZip** response lớn (danh sách email JSON nặng chữ, nén ~70-80%) | `app/api/app.py` (GZipMiddleware) | `curl -s -H "Accept-Encoding: gzip" -D - -o /dev/null localhost:8000/emails` → header `content-encoding: gzip` |
| **Đo thời gian xử lý từng request** — nói "nhanh" phải có số | middleware trong `app/api/app.py` | Mọi response có header `X-Process-Time-Ms`; request >10s bị log WARNING kèm request-id |
| **Cache Gmail 60s** (đợt trước, của quan) + connection pooling Postgres (`pool_size=20, max_overflow=10, pool_recycle=3600`) | `app/services/gmail_service.py`, `app/core/db.py` | vào cùng hộp thư 2 lần trong 60s → lần 2 tức thì |
| **Tiết kiệm lượt gọi LLM**: câu thuần chitchat đi thẳng END (bỏ lần gọi trình bày thứ 2) | `app/agent/graph.py` (`_should_continue`) | log: câu "chào bạn" chỉ 1 lần gọi Gemini |

## 2. MEMORY (Bộ nhớ)

| Cơ chế | File | Chứng minh |
|---|---|---|
| **Kho upload có trần + TTL**: tổng ≤25MB (FIFO evict), tệp quá 30 phút tự dọn — trước đây giữ bytes trong RAM VĨNH VIỄN | `app/services/upload_store.py` | `pytest tests/test_nfr.py::test_upload_store_co_tran_va_ttl -v` |
| **Chặn tệp upload quá trần** (mặc định 15MB, chỉnh `UPLOAD_MAX_MB`) → HTTP 413, không cho 1 tệp 2GB chiếm 2GB RAM | `app/api/app.py` (/uploads) | `pytest tests/test_nfr.py::test_upload_vuot_tran_bi_413 -v` |
| **Cache Gmail có trần 256 mục** + tự dọn mục hết hạn (trước đây dict phình vô hạn) | `app/services/gmail_service.py` | `pytest tests/test_nfr.py::test_gmail_cache_co_tran -v` |
| **Nén lịch sử hội thoại**: JSON email thô trong ToolMessage bị cắt còn 600 ký tự khi CẤT KHO (lượt sau đỡ phình token), giữ tối đa 30 tin/phiên | `app/api/app.py` (`_compact_tools`, `_trim_history`) | test đợt trước (cắt 5000→<700 ký tự, giữ tool_call_id) |

## 3. RELIABILITY (Độ tin cậy)

| Cơ chế | File | Chứng minh |
|---|---|---|
| **`GET /health`** — bắt mạch chuẩn production: kiểm DB thật (SELECT 1), báo uptime/version; DB đứt → 503 "degraded" | `app/api/app.py` | `curl localhost:8000/health` → `{"status":"ok","db":"up","uptime_s":…}` |
| **Rate limit theo người**: mặc định 8 lượt agent/phút (chỉnh `AGENT_RATE_LIMIT_PER_MIN`) — 1 người spam không thể đốt cạn quota Gemini của cả nhóm; chặn TRƯỚC khi chạm LLM, trả lời nhẹ nhàng 🐢 | `app/api/app.py` (`_rate_limited`) | `pytest tests/test_nfr.py::test_rate_limit_dung_nguong_cong_bo -v` |
| **Retry + exponential backoff**: Gemini (`max_retries=3, timeout=60`); Gmail **chỉ thao tác ĐỌC** (429/5xx/timeout, 3 lần, chờ 1→8s). ⚠️ Cố tình KHÔNG retry thao tác GHI — thử lại lệnh gửi/xoá có thể gửi trùng/xoá 2 lần | `app/core/llm.py`, `app/core/retry.py` | `pytest tests/` — test phân biệt 429 (retry) vs 403 (không) |
| **Hội thoại bền qua restart**: lịch sử chat lưu Postgres (bảng `conversations`), không phải RAM — sập server không mất phiên (UC011) | `app/models/conversation.py` + repo | tắt/bật backend → drawer vẫn còn phiên, tiếp tục được |
| **Phân loại lỗi thân thiện**: 429 quota → 🚦 hướng dẫn; 503 quá tải → ⏳ thử lại; 403 → 🔑 đăng nhập lại; lượt lỗi vẫn được LƯU vào phiên + trả đúng `conversationId` (không đẻ phiên rác) | `app/api/app.py` (except của /agent/chat) | tắt mạng/hết quota → thẻ lỗi đẹp thay vì stack-trace |
| **Log truy vết theo request**: mỗi request 1 `request-id` (header `X-Request-ID` + mọi dòng log gắn `rid=`), log xoay file 10MB×3 (`logs/app.log`) | `app/core/logging.py` + middleware | `curl -D -` thấy X-Request-ID; mở `logs/app.log` |
| **Kho KV cắm-rút Redis↔memory** (scale-out): `REDIS_URL` bật là cache Gmail + rate-limit chạy Redis (chia sẻ đa worker); Redis chết giữa chừng → tự rơi về in-memory, app không sập | `app/core/kv.py` | `pytest tests/test_kv.py -v` (5 test, gồm test Redis chết không sập) |
| **LangSmith tracing opt-in** (observability, đúng proposal): điền `LANGSMITH_API_KEY` là bật trace toàn vòng agent; mặc định tắt để dữ liệu email không rời máy | `app/core/llm.py`, `config.py` | `pytest tests/test_nfr.py::test_langsmith_opt_in -v` |
| **Trần tham số đầu vào**: `limit≤50`, `q≤200` ký tự, `cursor≤512`, body `≤2MB`. Trước đây `/emails?limit=5000` bắn 5000 lệnh gọi Gmail cho MỘT request — một người đủ sức làm nghẽn hệ thống và đốt sạch hạn ngạch chung | `app/core/limits.py`, `app/api/app.py` | OpenAPI ghi `limit maximum=50`; gửi body 3MB → HTTP 413 |
| **Backpressure (trần lệnh gọi ra ngoài)**: 32 suất Gmail/Graph + 6 suất LLM cho toàn cụm, **tự chia theo `WEB_CONCURRENCY`** (4 worker → 8 suất/worker, tổng vẫn 32). Hết suất → xếp hàng; chờ quá lâu → **503 + `Retry-After`** thay vì treo rồi 500 | `app/core/limits.py` (`provider_slot`) | `/metrics` xem `provider_slots_free`; 60 request đồng thời → 0 lỗi |
| **Rate limit riêng cho lượt ĐỌC thư**: 90 lượt/phút/người (`READ_RATE_LIMIT_PER_MIN`) — một tab kẹt vòng lặp cũng không làm cạn hạn ngạch Gmail của cả hệ thống | `app/api/app.py` (`/emails`) | vượt ngưỡng → HTTP 429 + `Retry-After` |
| **Nới luồng cho route đồng bộ**: 40 → 96 (`WEB_THREAD_POOL`). Route chờ I/O lâu (Gmail ~2.5s) chứ không tốn CPU nên 40 luồng nghẽn quá sớm. ⚠️ `current_default_thread_limiter()` chỉ đọc được trong ngữ cảnh async — để `def` thường thì việc nới **im lặng không có tác dụng** | `app/api/app.py` (startup) | `/metrics` → `thread_pool: 96` |
| **`/metrics`**: p50/p95/p99, số suất còn trống, trạng thái pool DB, backend KV, số dòng các bảng tích luỹ, số lượt bị từ chối. Không đo thì không biết lúc nào sắp quá tải | `app/core/limits.py` (`_Metrics`) | `curl /metrics` |
| **Dọn dữ liệu cũ (retention)**: `sessions`/`audit_logs`/`notifications` chỉ thêm không bớt → index phình, truy vấn chậm dần. Dọn định kỳ mỗi 60 phút; giữ nhật ký 180 ngày, thông báo **đã đọc** 30 ngày (**chưa đọc thì giữ nguyên dù cũ tới đâu**). Đa worker → khoá trên KV để mỗi chu kỳ chỉ 1 tiến trình dọn thật. Cùng tinh thần "trần + TTL" của kho upload | `app/core/maintenance.py` | `pytest tests/test_maintenance.py -v` (6 test) |

## 4. SECURITY (Bảo mật)

| Cơ chế | File | Chứng minh |
|---|---|---|
| **Mã hoá token Gmail trong DB** (Fernet AES-128 + HMAC): cột `google_access_token/refresh_token` lưu `enc:…` — DB bị lộ cũng không chiếm được hộp thư. Opt-in qua `TOKEN_ENCRYPTION_KEY`, tương thích ngược token cũ | `app/core/crypto.py`, `app/models/session.py` | pgAdmin: `SELECT left(google_access_token,20) FROM sessions` → `enc:gAAAA…` |
| **Guardrail chống prompt-injection**: regex chặn "bỏ qua lệnh hệ thống / ignore previous instructions / lộ system prompt" TRƯỚC khi vào LLM (nhanh, 0 quota) | `app/agent/guardrails/input_guardrail.py` | `pytest tests/test_contract_fe.py::test_endpoint_guardrail_prompt_injection -v` |
| **Human-in-the-loop cưỡng chế ở tầng tool**: `send_email/reply_email/bulk_action` gắn cờ `requires_confirmation=True` (registry policy theo category) | `app/tools/registry.py` | `pytest tests/test_tool_schemas.py::test_tool_khong_hoan_tac_phai_yeu_cau_xac_nhan -v` |
| **Header bảo mật OWASP** trên mọi response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (chống clickjacking), `Referrer-Policy` | middleware `app/api/app.py` | `curl -D - localhost:8000/health` |
| **Quyền sở hữu dữ liệu**: user A không đọc/sửa/xoá được phiên chat của user B (404) | `app/repo/conversation_repo.py` (`get_owned`) | `pytest tests/test_uc011_api.py::test_quyen_so_huu_user_khac_khong_doc_duoc -v` |
| **Cookie phiên `httponly` + `samesite=lax`** (chống XSS đọc cookie + CSRF cơ bản); **CORS khoá origin cụ thể** (không dùng `*`) | `app/api/auth.py`, `app/api/app.py` | DevTools → Application → Cookies |
| **Validate đầu vào tại cổng duy nhất**: mọi tool call qua `registry.call` → Pydantic chặn input sai TRƯỚC khi handler chạy (limit 1–50, to/subject/body không rỗng, date hợp lệ, bulk ≤100 thư) | `app/tools/registry.py`, `app/tools/schemas.py` | `pytest tests/test_tool_schemas.py -v` (15 test) |
| **Confirm-gate MCP cho agent NGOÀI**: send/reply/bulk-delete qua MCP lần đầu chỉ trả bản xem trước, phải `confirm=true` (sau khi người dùng duyệt) mới thực thi — HITL cưỡng chế ở tầng tool, không trông chờ thiện chí LLM ngoài | `app/mcp/server.py` | `pytest tests/test_mcp.py -v` (13 test) |

## 5. PORTABILITY / QUY TRÌNH (Docker + CI)

| Cơ chế | File | Chứng minh |
|---|---|---|
| **Đóng gói Docker**: 1 lệnh `docker compose up --build` dựng đủ Postgres + backend + frontend (kèm profile `--profile redis`); bí mật ở ngoài image (`env_file`), healthcheck xích `db → backend → frontend` bằng chính `/health` | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | `docker compose up --build` → mở 5173 (build image cần máy có Docker — máy dev hiện tại chưa cài, verify trên máy QA/CI) |
| **CI GitHub Actions**: mỗi push/PR tự chạy ~60 test khách quan trên Postgres thật + typecheck/build FE — chặn code hỏng vào main | `.github/workflows/ci.yml` | push lên GitHub → tab Actions; lệnh test đã chạy xanh local: `uv run pytest tests/ --ignore=tests/test_live_e2e.py` |

## Cấu hình (.env)

```env
AGENT_RATE_LIMIT_PER_MIN=8      # lượt agent/phút/người
UPLOAD_MAX_MB=15                # trần 1 tệp đính kèm
TOKEN_ENCRYPTION_KEY=...        # sinh: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Chạy toàn bộ kiểm chứng

```powershell
cd backend
uv run pytest tests/test_nfr.py tests/test_contract_fe.py tests/test_tool_schemas.py -v   # 30 test, không cần server
uv run main.py                                    # rồi cửa sổ khác:
uv run pytest tests/test_uc011_api.py test_agent.py -v                                    # REST + black-box thật
```
