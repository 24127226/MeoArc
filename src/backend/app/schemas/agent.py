# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/schemas/agent.py — THỰC THI SAU DUYỆT (agent bridge, Nấc 10)   ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: khuôn dữ liệu cho 2 endpoint "đôi tay" của agent:        ║
# ║   • /agent/plan/execute  — chạy 1 PlanOp SAU KHI user bấm Approve. ║
# ║   • /agent/autopilot/apply — chạy lô hành động đã duyệt (UC017).   ║
# ║ Đây KHÔNG phải LLM: chỉ nhận hành động ĐÃ ĐƯỢC DUYỆT rồi gọi xuống  ║
# ║ cùng lớp service Gmail (gmail_actions) — khép kín human-in-the-loop.║
# ║ Khớp `PlanOp`/`AutopilotResult` của FE (docs/01-DATA-MODEL §4).    ║
# ╚══════════════════════════════════════════════════════════════════╝

from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field


# ── PlanOp = "union phân biệt theo `type`" (mỗi loại có field riêng) ──
# Pydantic đọc field `type` để biết phải dựng lớp nào → tự kiểm dữ liệu đúng loại.
class ArchiveOp(BaseModel):
    type: Literal["archive"]
    ids: list[str]


class DeleteOp(BaseModel):
    type: Literal["delete"]
    ids: list[str]


class MarkReadOp(BaseModel):
    type: Literal["markRead"]
    ids: list[str]
    read: bool = True


class LabelOp(BaseModel):
    type: Literal["label"]
    ids: list[str]
    category: str | None = None   # màu chip FE — BE bỏ qua, chỉ dùng `label` làm tên nhãn
    label: str


class AutoLabelItem(BaseModel):
    id: str
    category: str | None = None
    label: str


class AutoLabelOp(BaseModel):
    type: Literal["autoLabel"]
    items: list[AutoLabelItem]


# Annotated[..., Field(discriminator="type")] = bảo Pydantic chọn lớp theo `type`.
PlanOp = Annotated[
    Union[ArchiveOp, DeleteOp, MarkReadOp, LabelOp, AutoLabelOp],
    Field(discriminator="type"),
]


class ExecutePlanReq(BaseModel):
    """Body /agent/plan/execute — bọc đúng 1 PlanOp đã được user Approve."""
    op: PlanOp


class ExecuteResult(BaseModel):
    """Trả về kèm câu tóm tắt để FE đẩy thành AgentReply kind 'done'."""
    ok: bool = True
    done: str


class AutopilotApplyReq(BaseModel):
    """Body /agent/autopilot/apply — 3 lô id đã duyệt (khớp AutopilotResult của FE)."""
    archive: list[str] = []
    markRead: list[str] = []
    flag: list[str] = []


class OkResult(BaseModel):
    ok: bool = True
