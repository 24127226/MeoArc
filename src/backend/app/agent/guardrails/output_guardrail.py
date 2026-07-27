from __future__ import annotations

import re
from typing import Any

# ═══════════════════════════════════════════════════════════════════
# Output Guardrail — 3 lớp kiểm tra đầu ra agent
# ═══════════════════════════════════════════════════════════════════
# 1. check_tool_call  : an toàn tool call trước khi thực thi
# 2. check_content    : lọc PII + phát hiện nội dung độc hại
# 3. validate_format  : đảm bảo final_output đúng khuôn FE

# ═══════════════════════════════════════════════════════════════════
# 1. TOOL CALL SAFETY
# ═══════════════════════════════════════════════════════════════════

_SUSPICIOUS_LIMITS: dict[str, dict[str, tuple[int, int]]] = {
    "search_emails": {"limit": (1, 200)},
}
_SUSPICIOUS_RECIPIENT_MAX = 50


def _strip_id(value: Any) -> str:
    """repr an toàn cho log (cắt bớt giá trị dài)."""
    s = repr(value)
    return s[:80] + "..." if len(s) > 80 else s


def check_tool_call(name: str, args: dict) -> tuple[bool, str | None]:
    """Kiểm tra 1 tool call trước khi thực thi.

    Returns:
        (True, None) — an toàn, cho phép chạy.
        (False, reason) — bị chặn, kèm lý do.
    """
    from app.tools.registry import tool_registry, ToolNotFoundError

    try:
        spec = tool_registry.get_spec(name)
    except ToolNotFoundError:
        return False, f"Tool '{name}' không tồn tại trong registry."

    try:
        spec.input_schema.model_validate(args)
    except Exception as e:
        return False, f"Tham số '{name}' không hợp lệ: {_strip_id(e)}"

    for param, (lo, hi) in _SUSPICIOUS_LIMITS.get(name, {}).items():
        val = args.get(param)
        if val is not None and not (lo <= val <= hi):
            return False, (
                f"Tham số '{param}={val}' của '{name}' vượt ngưỡng "
                f"cho phép ({lo}-{hi})."
            )

    if name == "send_email":
        to_list = args.get("to", [])
        if len(to_list) > _SUSPICIOUS_RECIPIENT_MAX:
            return False, (
                f"Gửi email cho {len(to_list)} người nhận vượt ngưỡng "
                f"({_SUSPICIOUS_RECIPIENT_MAX})."
            )

    return True, None


# ═══════════════════════════════════════════════════════════════════
# 2. CONTENT CHECK — PII + HARMFUL CONTENT
# ═══════════════════════════════════════════════════════════════════

_PII_PLACEHOLDER = "[thông tin cá nhân đã được bảo vệ]"

_PII_PATTERNS: list[tuple[str, str]] = [
    (r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", _PII_PLACEHOLDER),
    (r"(?<![0-9])0[0-9]{9,10}(?![0-9])", _PII_PLACEHOLDER),
    (r"(?<![0-9])\+84[0-9]{9}(?![0-9])", _PII_PLACEHOLDER),
    (r"\b\d{9}\b", _PII_PLACEHOLDER),
    (r"\b\d{12}\b", _PII_PLACEHOLDER),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", _PII_PLACEHOLDER),
]

_HARMFUL_PATTERNS: list[str] = [
    r"\b(giết|đâm|chém|đánh|đập|khủng bố|đe dọa|tự tử)\b",
    r"\b(murder|terror|bomb|shoot|stab|threaten|suicide)\b",
    r"\b(chửi thề|lăng mạ|sỉ nhục)\b",
    r"\b(fuck|shit|asshole|bitch|cunt)\b",
]

_COMPILED_PII = [(re.compile(p), r) for p, r in _PII_PATTERNS]
_COMPILED_HARMFUL = re.compile("|".join(_HARMFUL_PATTERNS), re.IGNORECASE)

_HARMFUL_APPENDIX = (
    "\n\n⚠️ *Nội dung đã được kiểm duyệt — một số thông tin nhạy cảm "
    "đã được che giấu.*"
)


def sanitize_content(text: str) -> str:
    """Lọc PII (email, số điện thoại, CMND/CCCD, thẻ tín dụng)."""
    if not text:
        return text
    result = text
    for pattern, replacement in _COMPILED_PII:
        result = pattern.sub(replacement, result)
    return result


def has_harmful_content(text: str) -> bool:
    """Kiểm tra văn bản có chứa nội dung độc hại không."""
    if not text:
        return False
    return bool(_COMPILED_HARMFUL.search(text))


def check_content(text: str) -> str:
    """check + sanitize nội dung văn bản từ LLM.

    1. Lọc PII (email, SĐT, CMND, thẻ tín dụng)
    2. Phát hiện nội dung độc hại → thêm cảnh báo
    """
    cleaned = sanitize_content(text)
    if has_harmful_content(text) and text is not cleaned:
        pass
    if has_harmful_content(cleaned):
        cleaned += _HARMFUL_APPENDIX
    return cleaned


# ═══════════════════════════════════════════════════════════════════
# 3. FORMAT VALIDATION — final_output theo khuôn FE
# ═══════════════════════════════════════════════════════════════════

_VALID_KINDS = frozenset({"text", "result", "digest", "triage"})

_REQUIRED_FIELDS: dict[str, set[str]] = {
    "text": {"text"},
    "result": {"title", "lines"},
    "digest": {"title", "stats", "breakdown", "highlights"},
    "triage": {"title", "groups"},
}

_DEFAULT_TEXTS: dict[str, str] = {
    "text": "Mình đã xử lý thông tin cho bạn.",
    "result": "Kết quả",
    "digest": "Tổng quan",
    "triage": "Phân loại ưu tiên",
}


def validate_format(output: dict) -> dict:
    """Chuẩn hoá final_output cho đúng khuôn FE.

    - kind không hợp lệ → fallback 'text'
    - Thiếu field bắt buộc → thêm giá trị mặc định
    - Sai kiểu cơ bản → ép kiểu
    """
    if not isinstance(output, dict):
        return {"kind": "text", "text": _DEFAULT_TEXTS["text"]}

    kind = output.get("kind", "")
    if kind not in _VALID_KINDS:
        return {"kind": "text", "text": _DEFAULT_TEXTS["text"]}

    for field in _REQUIRED_FIELDS.get(kind, set()):
        if field not in output or output[field] is None:
            if field == "text":
                output[field] = _DEFAULT_TEXTS["text"]
            elif field == "title":
                output[field] = _DEFAULT_TEXTS[kind]
            elif field in ("lines", "stats", "breakdown", "highlights", "groups"):
                output[field] = []

    if kind == "text":
        text = output.get("text") or output.get("intro") or _DEFAULT_TEXTS["text"]
        if isinstance(text, list):
            text = " ".join(str(t) for t in text if isinstance(t, str))
        output["text"] = str(text).strip() or _DEFAULT_TEXTS["text"]

    if kind == "result" and "lines" in output:
        lines = output["lines"]
        if not isinstance(lines, list):
            lines = [str(lines)] if lines else []
        output["lines"] = [str(l).strip() for l in lines if l]

    return output
