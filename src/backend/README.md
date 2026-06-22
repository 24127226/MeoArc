```bash
src/backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py          # JWT access/refresh, OAuth state
│   │   ├── logging.py
│   │   └── llm.py              # Gemini client wrapper duy nhất — init từ config, expose async generate()
│   │
│   ├── api/                     # API Layer — chỉ nhận/trả dữ liệu, KHÔNG chứa business logic
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── chat.py          # UC07 entrypoint
│   │       ├── emails.py
│   │       ├── settings.py
│   │       └── deps.py
│   │
│   ├── agent/                   # Agent Runtime — "bộ não", LangGraph
│   │   ├── graph.py              # build_graph(): agent_node ↔ tool_node, conditional_edge
│   │   ├── state.py              # AgentState (pydantic)
│   │   ├── nodes/
│   │   │   ├── agent_node.py
│   │   │   └── tool_node.py
│   │   ├── guardrails/
│   │   │   ├── input_guardrail.py
│   │   │   └── output_guardrail.py
│   │   ├── memory/
│   │   │   └── memory_manager.py  # pgvector read/write, conversation history
│   │   ├── skills/
│   │   │   ├── skill_loader.py
│   │   |   ├── workflows/               # Multi-step task recipes (đã có)
│   │   |   |   ├── email_triage.md
│   │   |   |   ├── daily_digest.md
│   │   |   |   └── meeting_prep.md
│   │   |   ├── writing/                 # Inject khi agent cần soạn/reply email
│   │   |   |   ├── tone_guide.md        # formal vs casual vs assertive vs empathetic — khi nào dùng gì
│   │   |   |   ├── email_structure.md   # subject line formula, opening/body/CTA/closing pattern
│   │   │   │   ├── reply_etiquette.md   # không quote toàn bộ thread, cách xử lý cc/bcc...
│   │   │   │   └── language_vi.md       # localization — viết email tiếng Việt đúng văn phong
│   │   │   ├── domain/                  # Inject khi agent làm việc với loại email cụ thể
│   |   |   |   ├── academic_email.md    # email trường/giảng viên — cách xưng hô, format
│   |   |   |   ├── job_application.md   # email xin việc — tone, structure đặc thù
│   |   |   |   └── client_comms.md      # email khách hàng/đối tác
│   │   │   └── provider/                # Inject dựa trên email provider của user
│   │   │       └── gmail_quirks.md      # label vs folder, thread model, search syntax
│   │
│   ├── tools/                   # Tool Registry — dùng chung cho Agent lẫn MCP
│   │   ├── registry.py
│   │   ├── schemas.py            # input/output schema từng tool
│   │   ├── email_tools.py        # search, summarize, draft, send, apply_labels
│   │   └── confirmation_tool.py  # request_confirmation
│   │
│   ├── mcp/                     # MeoArc AS MCP Server + MCP Client Adapter
│   │   ├── server.py              # expose tools/registry.py trực tiếp, bypass agent/graph.py
│   │   ├── client_adapter.py      # MCP Client: gọi Gmail/Outlook/Gemini như MCP services
│   │   └── tool_exports.py        # map Tool Registry -> MCP tool schema
│   │
│   ├── services/                # Service Layer — TOÀN BỘ business logic (SOLID)
│   │   ├── email_service.py
│   │   ├── classification_service.py   # auto-classification (system-initiated, độc lập UC07)
│   │   ├── auth_service.py
│   │   └── settings_service.py
│   │
│   ├── integrations/            # External Systems adapters
│   │   └── gmail_client.py
│   │
│   ├── models/                  # SQLAlchemy ORM
│   ├── schemas/                 # pydantic DTO cho API layer (tách biệt model DB)
│   ├── db/
│   │   └── session.py
│   ├── cache/
│   │   └── redis_client.py
│   └── workers/                 # async jobs: classification, scope-limited cleanup
│       └── classification_worker.py
│
└── test/
    ├── unit/        # service, tool, skill_loader
    ├── integration/ # agent graph end-to-end
    └── e2e/         # MCP client connect thật
```