# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/schemas/actions.py — KHUÔN dữ liệu cho các hành động (Nấc 6a)  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: mô tả CHÍNH XÁC body JSON mà FE gửi lên cho mỗi hành     ║
# ║ động, và body trả về. Dùng Pydantic để FastAPI TỰ kiểm tra: thiếu  ║
# ║ field / sai kiểu → tự trả lỗi 422, ta không phải kiểm tay.         ║
# ║ Khớp "hợp đồng" mục C trong docs/02-API-CONTRACT.md.               ║
# ╚══════════════════════════════════════════════════════════════════╝

from pydantic import BaseModel


class IdsReq(BaseModel):
    """Body tối thiểu cho hành động chỉ cần danh sách thư (archive, delete).
    FE luôn gửi MẢNG id — nhờ vậy 1 endpoint dùng được cho cả 1 thư lẫn hàng loạt."""
    ids: list[str]


class ReadReq(IdsReq):
    """POST /emails/actions/read — kế thừa `ids`, thêm `read`.
    read=True  → đánh dấu ĐÃ đọc (bớt nhãn UNREAD).
    read=False → đánh dấu CHƯA đọc (thêm nhãn UNREAD)."""
    read: bool = True


class ImportantReq(IdsReq):
    """POST /emails/actions/important — FE gọi 'important' nhưng bản chất là GẮN SAO.
    value=True → thêm STARRED; value=False → bỏ STARRED."""
    value: bool = True


class LabelReq(IdsReq):
    """POST /emails/actions/label — gắn NHÃN (tên tự do) cho thư.
    `category` (màu chip bên FE) hiện BE chưa map sang màu Gmail → nhận để khớp hợp đồng
    nhưng chỉ dùng `label` làm TÊN nhãn Gmail."""
    category: str | None = None
    label: str


class ReadOneReq(BaseModel):
    """POST /emails/{id}/read — đánh dấu 1 thư khi MỞ (FE chỉ gửi {read})."""
    read: bool = True


class ActionResult(BaseModel):
    """Body trả về CHUNG cho mọi hành động (đúng hợp đồng: { ok, affected }).
    `affected` = số thư thực sự đổi thành công → FE hiện 'Đã lưu trữ 3 thư…'."""
    ok: bool = True
    affected: int
