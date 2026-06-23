```bash
MeoArc/src/backend/
│
├── main.py                          # Uvicorn entry point. Chỉ gọi uvicorn.run() trỏ vào app.application:app
│
├── app/
│   │
│   ├── app.py                       # FastAPI factory: create_app(), đăng ký lifespan (khởi tạo graph, db pool, redis pool),
│   │                                # mount FastMCP sub-app tại /mcp, include routers, đăng ký middleware (CORS, logging, rate limit)
│   │
│   ├── core/                        # Shared infrastructure — không chứa business logic, được import bởi mọi layer
│   │   ├── config.py                # Pydantic BaseSettings: đọc .env, expose typed settings singleton
│   │   ├── security.py              # JWT encode/decode (access + refresh token), OAuth2 state generation/validation
│   │   ├── logging.py               # structlog setup, request-id middleware, log context binding
│   │   ├── llm.py                   # Gemini client wrapper duy nhất (google-genai). Được dùng bởi agent_node
│   │   │                            # VÀ classification_service — không đặt ở integrations/ vì không phải email provider
│   │   └── exceptions.py            # Base domain exception classes, FastAPI exception handlers (404, 422, 500)
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py              # Endpoints: GET /auth/google, GET /auth/callback, POST /auth/refresh, DELETE /auth/logout
│   │       ├── chat.py              # POST /chat — UC07 entrypoint. Nhận message, gọi runner.stream_agent(), trả SSE stream
│   │       ├── emails.py            # GET /emails, GET /emails/{id} — non-AI read path (không qua agent)
│   │       ├── settings.py          # GET/PATCH /settings — user preferences, connected accounts, AI scope tier
│   │       └── deps.py              # FastAPI Depends: get_current_user(), get_db(), get_email_service(),
│   │                                # build_request_context() — inject ctx vào tool_registry.call()
│   │
│   ├── agent/                       # LangGraph ReAct loop. LLM (Gemini) là bộ não chính, code chỉ cung cấp môi trường
│   │   ├── graph.py                 # build_graph(): khởi tạo StateGraph, thêm agent_node + tool_node,
│   │   │                            # định nghĩa conditional_edge (tiếp tục loop hay kết thúc), compile graph
│   │   ├── state.py                 # AgentState(TypedDict): messages, request_ctx, skill_context, pending_confirmation
│   │   ├── runner.py                # stream_agent(): nhận graph + input từ api/v1/chat.py, chạy graph.astream(),
│   │   │                            # yield token events ra SSE
│   │   │
│   │   ├── nodes/
│   │   │   ├── agent_node.py        # Gọi LLM qua core/llm.py với tools đã bind từ registry.to_langchain_tools().
│   │   │   │                        # LLM tự quyết định gọi tool nào, không có if/else điều khiển luồng ở đây
│   │   │   └── tool_node.py         # Nhận tool_calls từ agent_node, gọi tool_registry.call(name, args, **ctx),
│   │   │                            # trả kết quả vào messages để agent_node evaluate tiếp
│   │   │
│   │   ├── guardrails/
│   │   │   ├── input_guardrail.py   # Chạy trước agent_node: kiểm tra prompt injection, validate scope (AI Processing
│   │   │   │                        # Scope Limitation theo tier Free/Pro/Pro Max), sanitize input
│   │   │   └── output_guardrail.py  # Chạy sau agent_node quyết định tool call: nếu tool có requires_confirmation=True
│   │   │                            # mà chưa có pending_confirmation → ép agent gọi request_confirmation trước
│   │   │
│   │   ├── memory/
│   │   │   └── memory_manager.py    # pgvector: lưu conversation turns, đọc lại N turns gần nhất làm context,
│   │   │                            # lưu/truy xuất user preferences dạng embedding
│   │   │
│   │   └── skills/
│   │       ├── skill_loader.py      # Nhận user message → pgvector similarity search → chọn skill files phù hợp
│   │       │                        # → inject nội dung vào AgentState.skill_context → agent_node đọc làm system prompt bổ sung.
│   │       │                        # Không inject tất cả skills mọi lúc — chỉ inject đúng skill cần thiết cho request hiện tại
│   │       │
│   │       └── library/             # Markdown/YAML context files. KHÔNG phải code, không đăng ký vào tool registry
│   │           ├── workflows/       # Multi-step task recipes
│   │           │   ├── email_triage.md      # Quy trình: classify unread → xác định priority → summarize → suggest actions
│   │           │   ├── daily_digest.md      # Quy trình: collect emails theo period → group by category → generate report
│   │           │   ├── meeting_prep.md      # Quy trình: phân tích thread → extract action items/deadlines → tạo meeting brief
│   │           │   └── inbox_cleanup.md     # Quy trình: bulk delete spam, archive old, mark read — safe batch workflow
│   │           │
│   │           ├── writing/         # Inject khi agent soạn/reply email
│   │           │   ├── tone_guide.md        # Formal / casual / assertive / empathetic — điều kiện chọn tone
│   │           │   ├── email_structure.md   # Subject formula, opening/body/CTA/closing pattern
│   │           │   ├── reply_etiquette.md   # Thread quoting, cc/bcc conventions, response time norms
│   │           │   └── language_vi.md       # Văn phong tiếng Việt: xưng hô, kính ngữ, format chuẩn
│   │           │
│   │           ├── domain/          # Inject theo loại email đang xử lý
│   │           │   ├── academic_email.md    # Email trường/giảng viên: xưng hô, format, tone phù hợp
│   │           │   ├── job_application.md   # Email xin việc/internship: structure + tone đặc thù
│   │           │   └── client_comms.md      # Email khách hàng/đối tác: professional tone, follow-up etiquette
│   │           │
│   │           └── provider/        # Inject theo email provider của user
│   │               ├── gmail_quirks.md      # Label vs folder, thread model, Gmail search syntax
│   │               └── outlook_quirks.md    # Category vs folder, Focused Inbox, Graph API nuances
│   │
│   ├── tools/                       # Tool Registry — single source of truth cho Agent Runtime VÀ MCP Server.
│   │   │                            # Agent gọi qua to_langchain_tools(), MCP gọi qua to_mcp_tool_defs() + call().
│   │   │                            # Cả hai path đều đi qua cùng một registry.call() để đảm bảo hành vi nhất quán
│   │   ├── registry.py              # ToolRegistry singleton + @register decorator. Validate input bằng pydantic trước khi
│   │   │                            # handler chạy. Expose to_langchain_tools(), to_mcp_tool_defs(), call()
│   │   ├── schemas.py               # Pydantic input/output schemas cho từng tool.
│   │   │                            # TÁCH KHỎI app/schemas/ (API DTO) và models/ (ORM) — tránh circular import
│   │   ├── email_tools.py           # search_emails, get_email, list_labels, summarize_email
│   │   │                            # Category: READ — không bao giờ destructive, không cần confirmation
│   │   ├── compose_tools.py         # draft_email, send_email, reply_email
│   │   │                            # Category: WRITE_DESTRUCTIVE — requires_confirmation=True
│   │   ├── management_tools.py      # apply_labels (WRITE_REVERSIBLE), bulk_delete, mark_read
│   │   │                            # bulk_delete: WRITE_DESTRUCTIVE + requires_confirmation=True
│   │   │                            # apply_labels: WRITE_REVERSIBLE, apply trực tiếp không cần popup
│   │   └── system_tools.py          # ask_clarification: agent thiếu thông tin → hỏi user trước khi lập plan
│   │                                # request_confirmation: agent sắp thực hiện destructive action → xác nhận yes/no
│   │                                # Cả hai: Category SYSTEM, không gọi service, chỉ trả message cho frontend render
│   │
│   ├── mcp/                         # MeoArc AS MCP Server (ưu tiên) + MCP Client adapter (future)
│   │   ├── server.py                # FastMCP instance. Expose tools từ registry.to_mcp_tool_defs().
│   │   │                            # Khi external agent gọi tools/call → registry.call() trực tiếp.
│   │   │                            # KHÔNG import agent/graph.py — bypass hoàn toàn ReAct loop
│   │   ├── tool_exports.py          # Map ToolSpec metadata → MCP tool schema (name, description, inputSchema JSON)
│   │   ├── client_adapter.py        # MCP Client: abstract interface để kết nối Gmail/Outlook như MCP provider (future)
│   │   └── auth.py                  # Validate credentials của external agent khi kết nối vào MCP Server
│   │
│   ├── services/                    # TOÀN BỘ business logic (SOLID). Tool handlers và API routes chỉ delegate vào đây.
│   │   │                            # Không được gọi integrations/ từ ngoài service layer
│   │   ├── email_service.py         # Core email CRUD: fetch, search, send, reply, label.
│   │   │                            # Chọn gmail_client hay outlook_client dựa trên provider của user
│   │   ├── classification_service.py # Auto-classification: gán Category/Priority/Status cho email mới.
│   │   │                            # System-initiated, HOÀN TOÀN ĐỘC LẬP UC07 (không phải từ chat).
│   │   │                            # Gọi core/llm.py trực tiếp (1 LLM call đơn), KHÔNG qua agent/graph.py
│   │   ├── auth_service.py          # OAuth2 flow (Google/Microsoft), lưu/refresh token, account linking
│   │   ├── conversation_service.py  # Lưu/load conversation turns, manage session, link message với email context
│   │   └── settings_service.py      # User preferences, theme, language, AI Processing Scope tier (Free/Pro/Pro Max)
│   │
│   ├── integrations/                # External email/calendar provider adapters ONLY.
│   │   │                            # Gemini KHÔNG ở đây — Gemini là LLM runtime, không phải email provider → core/llm.py
│   │   ├── base_client.py           # Abstract EmailProviderClient: interface chung (fetch, send, search, label)
│   │   │                            # email_service.py chỉ biết interface này, không biết Gmail hay Outlook cụ thể
│   │   ├── gmail_client.py          # Google Gmail API: OAuth token inject, read threads, send, apply labels,
│   │   │                            # search, Gmail push notification (watch)
│   │   └── outlook_client.py        # Microsoft Graph API: read, send, categories, search, delta sync
│   │
│   ├── models/                      # SQLAlchemy ORM — ánh xạ DB tables. Không dùng trực tiếp ở API routes
│   │   ├── base.py                  # DeclarativeBase, TimestampMixin (created_at, updated_at)
│   │   ├── user.py                  # User, ConnectedAccount (lưu OAuth token theo provider)
│   │   ├── email.py                 # EmailRecord, Label, Classification (kết quả auto-classify)
│   │   └── conversation.py          # Conversation, Message (lịch sử chat)
│   │
│   ├── schemas/                     # Pydantic DTOs cho API layer — request/response serialization.
│   │   │                            # TÁCH KHỎI models/ (ORM) và tools/schemas.py (tool I/O) để tránh circular import
│   │   ├── auth.py                  # TokenResponse, OAuthCallbackRequest, ConnectedAccountDTO
│   │   ├── chat.py                  # ChatRequest, ChatStreamEvent (SSE payload)
│   │   ├── email.py                 # EmailDTO, LabelDTO, SearchQuery, ClassificationDTO
│   │   └── settings.py              # UserSettingsDTO, ScopeTierEnum
│   │
│   ├── db/
│   │   ├── session.py               # AsyncSession factory (SQLAlchemy async), get_db() Depends cho FastAPI
│   │   └── migrations/              # Alembic migration files (auto-generated)
│   │
│   ├── cache/
│   │   ├── redis_client.py          # Redis async connection pool, get/set/delete/expire helpers
│   │   └── keys.py                  # Cache key builder functions — tránh magic strings rải rác trong code
│   │
│   └── workers/                     # Background async jobs — chạy ngoài request/response cycle
│       ├── classification_worker.py # Lắng nghe email mới (Gmail push / Outlook delta) →
│       │                            # gọi classification_service.classify() → lưu kết quả vào DB
│       └── sync_worker.py           # Periodic sync cho accounts không có push notification
│
├── test/
│   ├── unit/                        # Test services/ và tools/ riêng lẻ, mock toàn bộ integrations/
│   ├── integration/                 # Test agent graph end-to-end với DB + Redis thật, mock Gemini + Gmail API
│   ├── e2e/                         # Test MCP client kết nối thật vào /mcp, full OAuth flow
│   └── conftest.py                  # Shared pytest fixtures: test db, redis, mock gmail client
│
├── .env                             # Local secrets — KHÔNG commit vào git
├── .env.example                     # Template với tất cả keys, values để trống — commit vào git
├── pyproject.toml                   # uv project config: dependencies, [tool.ruff], [tool.mypy]
├── uv.lock                          # Lockfile — commit vào git
├── Dockerfile                       # Multi-stage: builder (uv sync --frozen) → runtime (copy app)
├── .dockerignore                    # Loại trừ: .env, __pycache__, .venv, test/
└── alembic.ini                      # Alembic config: trỏ vào db/migrations/, đọc DATABASE_URL từ env
```