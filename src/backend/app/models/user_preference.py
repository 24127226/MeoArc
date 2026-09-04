# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/user_preference.py — PA2 §1.5.2 · lớp UserPreference    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Vì sao tách khỏi bảng users thay vì thêm cột vào đó:               ║
# ║  • users là bảng danh tính — ai là ai. Sở thích là thứ người dùng  ║
# ║    đổi liên tục. Trộn hai loại vòng đời vào một bảng thì mỗi lần   ║
# ║    thêm một tuỳ chọn lại phải sửa bảng danh tính.                  ║
# ║  • Quan hệ 1-1 nên user_id vừa là khoá chính vừa là khoá ngoại —   ║
# ║    cấu trúc TỰ CẤM một người có hai bộ sở thích, không cần code    ║
# ║    kiểm. Cùng thủ pháp với confirmation_request ở §1.5.23.         ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Giọng văn cho phép — dùng chung giữa API (kiểm đầu vào) và prompt (mô tả cho mô hình).
# Để một chỗ duy nhất: thêm giọng mới chỉ sửa ở đây, không phải lùng khắp nơi.
TONES: dict[str, str] = {
    "formal": "trang trọng, giữ khoảng cách, xưng hô đầy đủ chức danh",
    "friendly": "thân thiện, gần gũi nhưng vẫn lịch sự",
    "concise": "ngắn gọn, đi thẳng vào việc, không rào đón",
    "warm": "ấm áp, quan tâm tới người nhận",
}
DEFAULT_TONE = "friendly"


class UserPreference(Base):
    """Sở thích cá nhân — thứ làm trợ lý viết ra giọng CỦA NGƯỜI NÀY."""

    __tablename__ = "user_preferences"

    # Vừa khoá chính vừa khoá ngoại: một người đúng một bộ sở thích, cấm ở tầng cấu trúc.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    language: Mapped[str] = mapped_column(String, nullable=False, default="vi")
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    theme: Mapped[str] = mapped_column(String, nullable=False, default="system")

    # tone_preference ← giọng văn mặc định khi soạn thư thay người dùng
    tone_preference: Mapped[str] = mapped_column(String, nullable=False, default=DEFAULT_TONE)

    # signature_note ← chữ ký chèn cuối thư. Text chứ không phải String vì chữ ký hay
    #   nhiều dòng (tên, chức danh, đơn vị, số điện thoại).
    signature_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # custom_instruction ← dặn dò tự do, vd "đừng dùng từ 'trân trọng'", "luôn hỏi lại
    #   trước khi hứa deadline". Đây là chỗ người dùng dạy trợ lý những thứ không có
    #   ô nào chứa được.
    custom_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    # ── PA2 §1.3: toPromptContext() ─────────────────────────────────────────
    def to_prompt_context(self) -> str:
        """Kết tinh sở thích thành đoạn văn nhét vào system prompt.

        Trả CHUỖI RỖNG khi người dùng chưa đặt gì đáng kể — quan trọng: nhét một khối
        rỗng vào prompt là vừa tốn token vừa dạy mô hình rằng phần này thường trống,
        khiến nó coi nhẹ cả những lần có nội dung thật.
        """
        dong: list[str] = []

        # ── NGÔN NGỮ TRẢ LỜI ───────────────────────────────────────────────
        # Cột `language` có trong bảng từ đầu nhưng KHÔNG AI ĐỌC — nên nút "English"
        # ở màn Cài đặt là một nút chết: bấm xong không có gì đổi.
        #
        # Đặt Ở ĐẦU danh sách có chủ ý. System prompt mở đầu bằng "nói TIẾNG VIỆT chỉn
        # chu", và khối này được nhét vào CUỐI prompt — lời đứng sau thắng lời đứng
        # trước. Nhưng để nó lẫn giữa các dòng sở thích khác thì mô hình dễ coi nó là
        # một gợi ý nhỏ; đứng đầu và viết dứt khoát thì nó đọc ra một mệnh lệnh.
        #
        # CHỈ thêm dòng khi KHÁC mặc định: người dùng để tiếng Việt thì không cần nhắc,
        # và một khối prompt thừa vừa tốn token vừa làm loãng những dòng có thật sự cần.
        if (self.language or "vi") != "vi":
            dong.append(
                "- NGÔN NGỮ: người dùng đã chọn tiếng Anh. TRẢ LỜI HOÀN TOÀN BẰNG "
                "TIẾNG ANH, kể cả khi họ hỏi bằng tiếng Việt. Giữ nguyên tiêu đề và "
                "nội dung thư gốc (đừng dịch chúng) — chỉ phần LỜI CỦA BẠN là tiếng Anh."
            )

        if self.display_name:
            dong.append(f"- Người dùng tên là {self.display_name}. Xưng hô cho đúng.")

        if self.tone_preference and self.tone_preference != DEFAULT_TONE:
            mo_ta = TONES.get(self.tone_preference)
            if mo_ta:
                dong.append(f"- Khi soạn thư, giữ giọng {mo_ta}.")

        if self.signature_note:
            dong.append(
                "- Kết thư bằng đúng chữ ký sau, giữ nguyên từng dòng, "
                f"KHÔNG tự chế thêm:\n{self.signature_note.strip()}")

        if self.custom_instruction:
            dong.append(f"- Dặn riêng của người dùng: {self.custom_instruction.strip()}")

        if not dong:
            return ""
        return "\n".join(dong)

    # ── PA2 §1.3: update(fields) ────────────────────────────────────────────
    CO_THE_SUA = frozenset(
        {"language", "display_name", "theme", "tone_preference",
         "signature_note", "custom_instruction"})

    def update(self, fields: dict) -> list[str]:
        """Cập nhật có chọn lọc. Trả về tên các trường THẬT SỰ đổi.

        Chỉ nhận những khoá nằm trong danh sách trắng: nếu nhận bừa cả dict thì một
        payload gửi kèm `user_id` sẽ đổi luôn chủ sở hữu của bản ghi.
        """
        da_doi: list[str] = []
        for k, v in fields.items():
            if k not in self.CO_THE_SUA:
                continue
            if isinstance(v, str):
                v = v.strip() or None
            if k in ("language", "theme", "tone_preference") and v is None:
                continue                      # ba trường này không được để rỗng
            if getattr(self, k) != v:
                setattr(self, k, v)
                da_doi.append(k)
        return da_doi
