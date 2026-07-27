from __future__ import annotations

import re
import unicodedata
from typing import Literal, TypedDict

# ═══════════════════════════════════════════════════════════════════
# Input Guardrail — pattern matching + context-aware scoring
# ═══════════════════════════════════════════════════════════════════
# Ternary output: block (score >= 0.8) / warn (score >= 0.4) / pass

_INJECTION_PATTERNS_LEGACY = [
    r"(bỏ qua|phớt lờ|quên).{0,20}(lệnh|chỉ dẫn|hướng dẫn|quy tắc|luật).{0,20}(trước|trên|hệ thống)",
    r"(ignore|disregard|forget|override).{0,20}(previous|above|prior|system).{0,20}(instruction|prompt|rule)",
    r"(từ giờ|from now).{0,15}(bạn là|you are).{0,25}(developer mode|dan|không giới hạn|no restriction|unrestricted)",
    r"(in ra|tiết lộ|reveal|show me|lộ).{0,20}(system prompt|prompt hệ thống|lời dặn hệ thống|your instructions)",
]

# (name, regex, weight)
_EXTRA_PATTERNS: list[tuple[str, str, float]] = [
    # Unicode homoglyph — ký tự Cyrillic giả Latin
    ("unicode", r"[аееіоорсхуАВЕЕІКОРСХУ]", 0.3),

    # Base64-like payload
    ("base64", r"(?:base64|b64)\s*[\(\[][a-zA-Z0-9+/=]{20,}[\)\]]", 0.4),

    # Delimiter / fence injection
    ("delimiter", r"-{3,}\s*(?:end\s+system|end|system|input|output)\s*-{3,}", 0.6),
    ("fence", r"```\s*(?:system|assistant|input)", 0.6),

    # Role-play persona
    ("dan", r"\b(?:dan mode|developer mode|do anything now)\b", 0.7),
    ("claim_admin", r"(?:tôi là|tao là|mày là)\s*(?:admin|hệ thống|system|chủ nhân)", 0.7),
    ("claim_system_ref", r"(?<![a-zA-Z])(?:admin|system)\s*(?:override|access|privilege)\b", 0.4),

    # System prompt extraction
    ("extract_prompt", r"(?:prompt|instructions|chỉ dẫn|hướng dẫn)\s*(?:của bạn|system|đầu tiên|gốc)", 0.8),
    ("repeat_words", r"(?:repeat|nhắc lại|lặp lại)\s*(?:the words|toàn bộ|câu trên|ở trên|verbatim)", 0.8),

    # XSS / HTML injection
    ("html_script", r"<script[\s>]", 0.5),
    ("html_event", r"\bon\w+\s*=\s*['\"]", 0.5),
    ("html_iframe", r"<iframe[\s>]", 0.5),
]

_LEGACY_WEIGHT = 0.9

_REFUSAL = (
    "Mình không thể bỏ qua các quy tắc an toàn đã đặt ra. Nhưng mình vẫn sẵn sàng giúp bạn "
    "đọc, tóm tắt, tìm, phân loại hay soạn/gửi thư như bình thường — bạn cần gì cứ nói nhé."
)

_WARNING_PREFIX = (
    "[CẢNH BÁO AN TOÀN: Người dùng vừa gửi yêu cầu có dấu hiệu thao túng "
)


class GuardrailResult(TypedDict, total=False):
    action: Literal["block", "warn", "pass"]
    score: float
    reason: str | None


def _detect_homoglyphs(text: str) -> int:
    count = 0
    for ch in text:
        if ord(ch) > 127:
            try:
                name = unicodedata.name(ch, "")
                if "CYRILLIC" in name:
                    count += 1
            except ValueError:
                pass
    return count


def _match_patterns(message: str) -> list[tuple[str, float]]:
    matched: list[tuple[str, float]] = []
    low = message.lower()
    for name, pat, weight in _EXTRA_PATTERNS:
        if re.search(pat, low):
            matched.append((name, weight))
    for pat in _INJECTION_PATTERNS_LEGACY:
        if re.search(pat, low):
            matched.append(("legacy", _LEGACY_WEIGHT))
    return matched


def _heuristic_score(message: str) -> float:
    score = 0.0
    low = message.lower()

    if len(message) > 2000:
        score += 0.15

    if re.search(r"(?<!của )(?:tôi là|tao là|mày là)\s*(?:admin|hệ thống|system)", low):
        score += 0.2

    cyrillic_count = _detect_homoglyphs(message)
    if cyrillic_count >= 3:
        score += 0.2
    elif cyrillic_count >= 1:
        score += 0.1

    return score


def score_message(message: str) -> GuardrailResult:
    matched = _match_patterns(message)
    pattern_score = sum(w for _, w in matched)
    heuristic_score = _heuristic_score(message)
    categories = {name for name, _ in matched}
    if len(categories) > 1:
        pattern_score += 0.1 * (len(categories) - 1)

    total = min(pattern_score + heuristic_score, 1.0)
    reason = ", ".join(sorted(categories)) if categories else None

    if total >= 0.8:
        return GuardrailResult(action="block", score=total, reason=reason)
    if total >= 0.4:
        return GuardrailResult(action="warn", score=total, reason=reason)
    return GuardrailResult(action="pass", score=total, reason=None)


def check_input(message: str) -> str | None:
    """Legacy API — giữ nguyên chữ ký. None = an toàn."""
    result = check_input_ext(message)
    return _REFUSAL if result["action"] == "block" else None


def check_input_ext(message: str) -> GuardrailResult:
    if not message:
        return GuardrailResult(action="pass", score=0.0, reason=None)
    return score_message(message)
