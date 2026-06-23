from __future__ import annotations

from collections.abc import Callable, Coroutine
from enum import Enum, auto
from functools import wraps
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ValidationError
from typing import Any, TypeVar


F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


class ToolCategory(Enum):
    READ = auto()               # search_emails, get_email, summarize_email
    WRITE_REVERSIBLE = auto()   # apply_labels
    WRITE_DESTRUCTIVE = auto()  # send_email, bulk_delete
    SYSTEM = auto()             # ask_clarification, request_confirmation


# Default confirmation policy theo category
_CONFIRMATION_DEFAULTS: dict[ToolCategory, bool] = {
    ToolCategory.READ: False,
    ToolCategory.WRITE_REVERSIBLE: False,
    ToolCategory.WRITE_DESTRUCTIVE: True,
    ToolCategory.SYSTEM: False,
}


class ToolSpec:
    """Metadata container for a registered tool"""

    __slots__ = (
        "name",
        "description",
        "category",
        "requires_confirmation",
        "input_schema",
        "handler"
    )

    def __init__(
        self,
        *,
        name: str,
        description: str,
        category: ToolCategory,
        input_schema: type[BaseModel],
        handler: Callable[..., Coroutine[Any, Any, Any]],
        requires_confirmation: bool | None = None
    ) -> None:
        self.name = name
        self.description = description
        self.category = category
        self.input_schema = input_schema
        self.handler = handler
        # Cho phép override default policy nếu cần
        self.requires_confirmation = (
            requires_confirmation
            if requires_confirmation is not None
            else _CONFIRMATION_DEFAULTS[category]
        )


class RequestContext(BaseModel):
    """
    Dependencies được inject vào mỗi tool call.
    Build ở api/v1/deps.py, truyền xuống qua tool_node.py và mcp/server.py
    """

    model_config = {'arbitrary_types_allowed': True}

    user_id: str
    email_provider: str = 'gmail'
    access_token: str
    conversation_id: str | None = None


# --- Tool Exceptions ---
class ToolNotFoundError(KeyError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Tool '{name}' is not registered")

class ToolInputError(ValueError):
    def __init__(self, name: str, error: ValidationError) -> None:
        super().__init__(f"Invalid input for tool '{name}': {error}")


class ToolRegistry:
    """
    Singleton registry

    Comsumer:
        - LangGraph agent_node      -> to_langchain_tools()
        - MCP Server mcp/server.py  -> to_mcp_server_defs()

    Cả 2 đều đi qua call() => consistent validation + behavior
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(
        self,
        *,
        category: ToolCategory,
        input_schema: type[BaseModel],
        requires_confirmation: bool | None = None
    ) -> Callable[[F], F]:
        """Decorator Factory"""

        def decorator(func: F) -> F:
            name = func.__name__
            description = (func.__doc__ or "").strip()

            if not description:
                raise ValueError(
                    f"Tool '{name}' must have a docstring"
                )

            spec = ToolSpec(
                name=name,
                description=description,
                category=category,
                input_schema=input_schema,
                handler=func,
                requires_confirmation=requires_confirmation
            )
            self._tools[name] = spec

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    
    async def call(
        self,
        name: str,
        args: dict[str, Any],
        ctx: RequestContext
    ) -> Any:
        """
        Unified invoke path

        Flow:
            1. Lookup spec
            2. Validate input by Pydantic
            3. Await handler
        """
        spec = self._tools.get(name)
        if spec is None:
            raise ToolNotFoundError(name)

        try:
            parsed = spec.input_schema.model_validate(args)
        except ValidationError as exc:
            raise ToolInputError(name, exc) from exc

        return await spec.handler(parsed, ctx)


    # === LangChain Adapter ===
    def to_langchain_tools(
            self,
            *,
            exclude_categories: set[ToolCategory] | None = None
    ) -> list[StructuredTool]:
        """
        Convert registered tools -> LangChain StructuredTools list để bind vào LLM

        SYSTEM tools được giữ lại mặc định vì agent cần gọi request_confirmation.
        Caller có thể exclude nếu muốn.
        """
        exclude = exclude_categories if exclude_categories is not None else set()

        def _make_coroutine(spec: ToolSpec) -> Callable[..., Coroutine[Any, Any, Any]]:
            # Capture spec trong closure — tránh late-binding bug
            async def _invoke(**kwargs: Any) -> Any:
                # ctx phải được inject từ ngoài vào kwargs khi LangGraph gọi
                ctx: RequestContext = kwargs.pop("_ctx")
                return await self.call(spec.name, kwargs, ctx)
            return _invoke

        tools: list[StructuredTool] = []
        for spec in self._tools.values():
            # Kiểm tra quyền hạn
            if spec.category not in exclude:
                continue

            # Tạo các tools mà Agent/LLM có thể gọi
            tools.append(
                StructuredTool(
                    name=spec.name,
                    description=spec.description,
                    args_schema=spec.input_schema,
                    coroutine=_make_coroutine(spec),
                    return_direct=False
                )
            )
        return tools


    # === MCP Adapter ===
    def to_mcp_server_defs(self) -> list[dict[str, Any]]:
        """
        Convert registered tools → MCP tools/list response format.

        SYSTEM tools bị filter ra — internal coordination tools
        không nên expose ra cho external agents.
        """
        result = []
        for spec in self._tools.values():
            if spec.category is ToolCategory.SYSTEM:
                continue

            result.append({
                "name": spec.name,
                "description": spec.description,
                "inputSchema": spec.input_schema.model_json_schema()
            })
        return result


    # === Introspection ===
    def get_spec(self, name: str) -> ToolSpec:
        spec = self._tools.get(name)
        if spec is None:
            raise ToolNotFoundError(name)
        return spec

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)


tool_registry = ToolRegistry()