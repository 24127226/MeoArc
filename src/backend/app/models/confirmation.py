# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/models/confirmation.py — BẢNG 'confirmation_requests'         ║
# ║ (PA2 §1.3.5 — Human-in-the-loop, FR-02.4)                         ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Trước đây việc duyệt chỉ tồn tại ở giao diện: thẻ nháp hiện nút,   ║
# ║ bấm là gọi thẳng lệnh gửi. Máy chủ KHÔNG biết gì về "một yêu cầu   ║
# ║ đang chờ duyệt", nên bấm hai lần là gửi hai lần — và mở lại hội    ║
# ║ thoại cũ thì thẻ nháp lại bấm được nữa.                           ║
# ║                                                                    ║
# ║ Ràng buộc "chỉ gọi khi status = pending" của PA2 chính là thứ vá   ║
# ║ lỗi đó: một yêu cầu duyệt xong thì không còn ở trạng thái pending, ║
# ║ nên lần bấm thứ hai không thể thực thi lần nữa.                    ║
# ║                                                                    ║
# ║ Ba trạng thái giữ ĐÚNG như đặc tả (pending/approved/rejected).     ║
# ║ `args` và `result` là chi tiết hiện thực (đặc tả không nêu): cần   ║
# ║ `args` để biết phải chạy gì khi duyệt, và `result` để lần bấm sau  ║
# ║ trả lại đúng kết quả cũ thay vì báo lỗi vào mặt người dùng.        ║
# ╚══════════════════════════════════════════════════════════════════╝

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ConfirmationRequest(Base):
    __tablename__ = "confirmation_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)     # uuid

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    #   Ai là người được quyền duyệt. Không có cột này thì người khác duyệt hộ được.

    conversation_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # ── Ba thuộc tính đúng theo PA2 §1.3.5 ───────────────────────────────────
    action: Mapped[str] = mapped_column(String)
    #   Tên kỹ thuật của hành động, vd "send_email", "bulk_delete".

    description: Mapped[str] = mapped_column(String)
    #   Câu cho NGƯỜI đọc, vd "Xoá 15 email đã chọn?". Người dùng duyệt cái họ
    #   đọc được, không phải duyệt một tên hàm.

    status: Mapped[str] = mapped_column(String, default=PENDING, index=True)
    #   pending | approved | rejected — đúng ba giá trị đặc tả nêu.

    # ── Chi tiết hiện thực ───────────────────────────────────────────────────
    args: Mapped[dict] = mapped_column(JSON, default=dict)
    #   Tham số đã chốt lúc tạo yêu cầu. Chốt tại thời điểm này là có chủ đích:
    #   người dùng duyệt CÁI HỌ THẤY, nên không được để lời gọi sau đổi tham số.

    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    #   Kết quả lần thực thi đầu tiên. Bấm lại lần nữa thì trả lại cái này.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # ── Hai thao tác đúng theo PA2 §1.3.5 ────────────────────────────────────
    def approve(self) -> bool:
        """Người dùng đồng ý. Chỉ chạy được khi đang `pending` (ràng buộc PA2).

        Trả về True nếu lần gọi này là lần chuyển trạng thái THẬT, False nếu yêu
        cầu đã được xử lý rồi. Trả bool thay vì ném lỗi vì bấm hai lần là chuyện
        bình thường của người dùng (mạng chậm, lỡ tay) — không phải sự cố. Nơi gọi
        dựa vào giá trị này để quyết định có thực thi hay chỉ trả kết quả cũ.
        """
        if self.status != PENDING:
            return False
        self.status = APPROVED
        return True

    def reject(self) -> bool:
        """Người dùng từ chối — hành động gắn kèm KHÔNG được chạy."""
        if self.status != PENDING:
            return False
        self.status = REJECTED
        return True

    @property
    def is_pending(self) -> bool:
        return self.status == PENDING
