"""XOÁ PHẢI CÓ ĐƯỜNG LÙI.

Xoá trong MeoArc vốn đã là xoá MỀM — `bulk_action(delete)` gọi `/trash` của Gmail chứ
không xoá vĩnh viễn. Nhưng suốt thời gian qua KHÔNG có tool nào đưa thư trở lại, nên
"khôi phục được" chỉ đúng trên giấy: người dùng phải tự mở Gmail mà bới.

Trợ lý xoá hộ thì phải hoàn tác hộ được. Đó là điều kiện để cổng xác nhận có nghĩa —
duyệt một việc mà không có đường lùi thì mỗi lần duyệt là một lần nín thở.

RANH GIỚI KHOÁ Ở ĐÂY: khôi phục là thao tác CHỈ THÊM, không mất gì. Nó không được
phép xoá, không được phép đụng tới thư khác.
"""

from __future__ import annotations

import pytest

from app.tools.schemas import BulkAction, BulkActionInput


def test_hanh_dong_RESTORE_ton_tai():
    assert BulkAction.RESTORE.value == "restore"


def test_schema_nhan_action_restore():
    """LLM truyền 'restore' phải qua được validation — sai chỗ này thì lệnh khôi phục
    chết ngay ở cổng vào và người dùng chỉ thấy agent loay hoay."""
    inp = BulkActionInput(email_ids=["m1", "m2"], action="restore")
    assert inp.action == BulkAction.RESTORE


def test_viet_hoa_van_nhan():
    """Đã có tiền lệ: `DELETE = "Delete"` viết hoa làm lệnh xoá hàng loạt không chạy
    được vì LLM truyền 'delete'. Đừng lặp lại với 'restore'."""
    assert BulkActionInput(email_ids=["m1"], action="RESTORE").action == BulkAction.RESTORE


@pytest.mark.asyncio
async def test_restore_goi_UNTRASH_chu_khong_phai_trash(monkeypatch):
    """Ranh giới quan trọng nhất: gọi nhầm sang `trash` thì lệnh 'khôi phục' sẽ XOÁ
    thêm một lần nữa — người dùng bấm để cứu thư và mất luôn thư."""
    from app.tools import email_tools as T
    from app.tools.registry import RequestContext

    da_goi: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(T.mail, "untrash", lambda p, tok, ids: da_goi.append(("untrash", ids)) or len(ids))
    monkeypatch.setattr(T.mail, "trash", lambda p, tok, ids: da_goi.append(("trash", ids)) or len(ids))

    out = await T.bulk_action(
        BulkActionInput(email_ids=["m1", "m2"], action="restore"),
        RequestContext(user_id="1", access_token="t", email_provider="gmail"),
    )
    assert out.success
    assert da_goi == [("untrash", ["m1", "m2"])], f"gọi nhầm hàm: {da_goi}"


def test_the_duyet_hieu_hanh_dong_restore():
    """Thẻ duyệt phải dựng được `op` cho restore. Không dựng được thì agent gọi tool
    xong mà giao diện không hiện nút nào — người dùng nhìn thấy một khoảng lặng."""
    import json
    import types

    from app.api.app import _confirm_card

    tm = types.SimpleNamespace(
        type="tool", name="bulk_action",
        content=json.dumps({"needs_confirmation": True, "action": "bulk_action",
                            "args": {"email_ids": ["m1"], "action": "restore"}}),
    )
    card = _confirm_card([types.SimpleNamespace(type="human", content="khôi phục thư vừa xoá"), tm])
    assert card and card["kind"] == "plan"
    assert card["op"]["type"] == "restore"
    assert "Khôi phục" in card["confirmLabel"]


def test_restore_KHONG_bi_doc_nham_thanh_delete():
    """`"delete" in act` chạy TRƯỚC trong bản cũ. Chuỗi 'restore' không chứa 'delete'
    nên không đụng, nhưng khoá lại phòng khi ai đó đổi thứ tự nhánh."""
    import json
    import types

    from app.api.app import _confirm_card

    tm = types.SimpleNamespace(
        type="tool", name="bulk_action",
        content=json.dumps({"needs_confirmation": True, "action": "bulk_action",
                            "args": {"email_ids": ["m1"], "action": "restore"}}),
    )
    card = _confirm_card([types.SimpleNamespace(type="human", content="x"), tm])
    assert card["op"]["type"] != "delete"
