# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/agent/skills/skill_loader.py — NẠP "KỸ NĂNG" theo ngữ cảnh   ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ v2 — P0 upgrades:                                               ║
# ║   • Word-boundary matching (giảm false positive)                ║
# ║   • Vietnamese diacritic-insensitive fallback                   ║
# ║   • Mutual-exclusion groups (triage vs digest)                  ║
# ║   • LRU cache file content (giảm disk I/O)                     ║
# ║   • Score-based ranking (ưu tiên skill khớp nhiều keyword nhất) ║
# ╚══════════════════════════════════════════════════════════════════╝

from pathlib import Path
import re
import unicodedata
from functools import lru_cache

_LIB = Path(__file__).parent / "library"


# ── Helper ─────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Loại bỏ dấu tiếng Việt → so khớp không phân biệt có dấu/không dấu."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii")


def _keyword_in_msg(keyword: str, msg: str) -> bool:
    """Word-boundary regex cho từ đơn; substring cho cụm nhiều từ."""
    if " " in keyword:
        return keyword in msg
    return bool(re.search(rf"\b{re.escape(keyword)}\b", msg))


# ── Rules ──────────────────────────────────────────────────────────
# (keywords, relative_path)
# Mỗi file chỉ xuất hiện MỘT lần. Sort order = tiebreaker khi điểm bằng.

_RAW_RULES: list[tuple[tuple[str, ...], str]] = [
    (("triage", "ưu tiên", "sắp xếp", "phân loại", "lọc thư"),        "workflows/email_triage.md"),
    (("digest", "điểm tin", "tổng hợp ngày", "bản tin", "tóm tắt"),   "workflows/daily_digest.md"),
    (("họp", "meeting", "brief", "cuộc họp", "chuẩn bị"),             "workflows/meeting_prep.md"),
    (("dọn", "dẹp", "xóa", "archive", "spam", "cleanup", "inbox", "clean"), "workflows/inbox_cleanup.md"),
    (("trả lời", "reply", "hồi âm"),                                   "writing/reply_etiquette.md"),
    (("soạn", "viết thư", "compose", "gửi mail", "draft"),            "writing/email_structure.md"),
    (("trang trọng", "lịch sự", "tone", "giọng", "casual", "thân mật", "thoải mái"), "writing/tone_guide.md"),
    (("tiếng việt", "xưng hô"),                                        "writing/language_vi.md"),
    (("giáo vụ", "giảng viên", "đại học", "trường học", "academic"),   "domain/academic_email.md"),
    (("xin việc", "ứng tuyển", "cv", "job"),                           "domain/job_application.md"),
    (("khách hàng", "đối tác", "client"),                               "domain/client_comms.md"),
    (("gmail",),                                                        "provider/gmail_quirks.md"),
    (("outlook", "microsoft", "exchange", "office"),                    "provider/outlook_quirks.md"),
    (("lừa đảo", "scam", "phishing", "suspicious", "đáng ngờ"),          "domain/phishing_detection.md"),
    (("đặt lịch", "schedule", "reschedule", "meeting request", "cancel", "hủy lịch"), "domain/scheduling.md"),
    (("khiếu nại", "complaint", "khiếu nại", "hàng lỗi", "hoàn tiền", "refund"), "domain/consumer_complaint.md"),
]

# Pre-compile: (keywords, norm_keywords, path)
_RULES: list[tuple[tuple[str, ...], tuple[str, ...], str]] = []
for keywords, path in _RAW_RULES:
    _RULES.append((keywords, tuple(_normalize(k) for k in keywords), path))

# Mutual-exclusion groups: khi 2 skill cùng group match, chỉ load skill điểm cao hơn
_MUTEX_GROUPS: list[set[str]] = [
    {"workflows/email_triage.md", "workflows/daily_digest.md"},
]


# ── Scoring ────────────────────────────────────────────────────────

def _score(keywords: tuple[str, ...], norm_keywords: tuple[str, ...],
           msg: str, norm_msg: str) -> float:
    """Điểm match: 0 = không khớp, >0 = khớp (càng cao càng tốt).

    - Từ đơn: +2 (exact), +1 (normalized)
    - Cụm multi-word (specific hơn): +3 (exact), +2 (normalized)
    - Match density bonus: +1 nếu >50% keywords khớp
    """
    score = 0.0
    matched = 0
    total = len(keywords)
    for i, kw in enumerate(keywords):
        is_phrase = " " in kw
        if _keyword_in_msg(kw, msg):
            score += 3.0 if is_phrase else 2.0
            matched += 1
        elif _keyword_in_msg(norm_keywords[i], norm_msg):
            score += 2.0 if is_phrase else 1.0
            matched += 1
    if total > 0 and matched / total > 0.5:
        score += 1.0
    return score


# ── Đọc file (cached) ──────────────────────────────────────────────

@lru_cache(maxsize=32)
def _read_skill(path: str) -> str:
    try:
        return (_LIB / path).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


# ── Public API ─────────────────────────────────────────────────────

def load_skills(message: str) -> str:
    """Trả về markdown của các skill khớp với `message`, ghép lại.

    Không khớp → "".
    An toàn: file thiếu/rỗng → BỎ QUA (không lỗi).
    """
    msg = (message or "").lower()
    norm_msg = _normalize(msg)

    # 1. Score all rules
    scored: list[tuple[float, str]] = []
    for keywords, norm_keywords, path in _RULES:
        s = _score(keywords, norm_keywords, msg, norm_msg)
        if s > 0:
            scored.append((s, path))

    # 2. Sort: điểm giảm dần, giữ stable order cho tiebreaker
    scored.sort(key=lambda x: -x[0])

    # 3. Resolve mutual exclusion
    selected: list[str] = []
    seen: set[str] = set()
    for _, path in scored:
        if path in seen:
            continue
        for group in _MUTEX_GROUPS:
            if path in group and any(m in seen for m in group if m != path):
                break
        else:
            selected.append(path)
            seen.add(path)

    # 4. Load & concat
    parts: list[str] = []
    for path in selected:
        text = _read_skill(path)
        if text:
            parts.append(f"## {path}\n{text}")

    return "\n\n".join(parts)
