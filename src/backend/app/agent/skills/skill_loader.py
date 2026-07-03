# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/agent/skills/skill_loader.py — NẠP "KỸ NĂNG" theo ngữ cảnh     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ "Skill" = các file .md trong thư mục library/ chứa HƯỚNG DẪN (cách ║
# ║ triage, cách viết email trang trọng, văn phong tiếng Việt...).     ║
# ║ Thay vì nhồi HẾT vào prompt (tốn token), ta CHỈ nạp skill khớp với ║
# ║ yêu cầu hiện tại (theo từ khoá) → tiêm vào system prompt của agent.║
# ║ Đây là "trí nhớ kỹ năng" giúp agent trả lời chuẩn hơn.            ║
# ╚══════════════════════════════════════════════════════════════════╝

from pathlib import Path

# Thư mục chứa các file skill (.md). __file__ = file này → .parent = thư mục skills/.
_LIB = Path(__file__).parent / "library"

# LUẬT chọn skill: nếu câu người dùng chứa MỘT trong các từ khoá → nạp file tương ứng.
# (Sau này có thể nâng cấp thành tìm-ngữ-nghĩa; giờ khớp từ khoá cho đơn giản, đủ dùng.)
_RULES: list[tuple[tuple[str, ...], str]] = [
    (("triage", "ưu tiên", "sắp xếp", "phân loại"), "workflows/email_triage.md"),
    (("digest", "điểm tin", "tổng hợp ngày", "bản tin"), "workflows/daily_digest.md"),
    (("họp", "meeting", "brief", "cuộc họp"), "workflows/meeting_prep.md"),
    (("trả lời", "reply", "hồi âm"), "writing/reply_etiquette.md"),
    (("soạn", "viết thư", "compose", "gửi mail"), "writing/email_structure.md"),
    (("trang trọng", "lịch sự", "tone", "giọng"), "writing/tone_guide.md"),
    (("tiếng việt", "xưng hô"), "writing/language_vi.md"),
    (("giáo vụ", "giảng viên", "trường", "academic"), "domain/academic_email.md"),
    (("xin việc", "ứng tuyển", "cv", "job"), "domain/job_application.md"),
    (("khách hàng", "đối tác", "client"), "domain/client_comms.md"),
    (("triage", "ưu tiên", "sắp xếp", "phân loại", "lọc thư"), "workflows/email_triage.md"),
    (("digest", "điểm tin", "tổng hợp ngày", "bản tin", "tóm tắt"), "workflows/daily_digest.md"),
]


def load_skills(message: str) -> str:
    """Trả về phần markdown của các skill KHỚP với `message` (ghép lại). Không khớp → "".

    An toàn: file thiếu/rỗng thì BỎ QUA (thư viện skill có thể chưa viết xong) — không lỗi.
    """
    msg = (message or "").lower()
    parts: list[str] = []
    seen: set[str] = set()                       # tránh nạp trùng 1 file
    for keywords, rel_path in _RULES:
        if rel_path in seen:
            continue
        if any(k in msg for k in keywords):      # câu có chứa từ khoá nào không?
            f = _LIB / rel_path
            try:
                text = f.read_text(encoding="utf-8").strip()
            except Exception:
                text = ""                        # file không tồn tại/đọc lỗi → coi như rỗng
            if text:
                parts.append(f"## {rel_path}\n{text}")
                seen.add(rel_path)
    return "\n\n".join(parts)
