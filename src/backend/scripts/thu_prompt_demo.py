"""CHẠY THỬ CÁC CÂU HỎI TRONG KỊCH BẢN QUAY DEMO — trên hộp thư THẬT, mô hình THẬT.

── VÌ SAO CẦN ──
Tài liệu kịch bản ghi "chờ thấy thẻ Lịch trình", "chờ thấy cột đỏ"… nhưng đó chỉ là ý
định của người viết. Thứ quyết định là mô hình có gọi ĐÚNG TOOL hay không — và nó có
thể trả lời bằng văn xuôi cho đúng câu mà ta đinh ninh sẽ ra thẻ. Lúc đó người quay
mới phát hiện, giữa buổi quay.

Kịch bản này đi đúng đường mà `/agent/chat` đi (cùng graph, cùng bộ dựng thẻ, cùng thứ
tự ưu tiên thẻ), rồi in ra ba thứ cho mỗi câu:
    · tool nào ĐƯỢC GỌI THẬT
    · thẻ (`kind`) trả về
    · thẻ đó có ĐÚNG cái tài liệu hứa không

── TỐN QUOTA ──
Mỗi câu tốn 2–3 lượt gọi mô hình. Chạy cả bộ ≈ 30 lượt. Truyền số thứ tự để chạy
riêng vài câu:

    ./.venv/Scripts/python.exe scripts/thu_prompt_demo.py            # xem danh sách
    ./.venv/Scripts/python.exe scripts/thu_prompt_demo.py 3 4 6      # chạy Q3, Q4, Q6
    ./.venv/Scripts/python.exe scripts/thu_prompt_demo.py --tat-ca   # chạy hết
"""

from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Windows: console cp1252 làm vỡ mọi dòng có dấu tiếng Việt.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from langchain_core.messages import HumanMessage        # noqa: E402

from app.agent.graph import build_graph                 # noqa: E402
from app.agent.skills.skill_loader import load_skills   # noqa: E402
from app.api.app import (                               # noqa: E402
    _categorize_card, _confirm_card, _di_lai_card, _digest_card,
    _lich_trinh_card, _triage_card,
)
from app.core.db import SessionLocal                    # noqa: E402
from app.models.user import User                        # noqa: E402
from app.services.sync_service import _token_for_user   # noqa: E402
from app.tools.registry import RequestContext           # noqa: E402
from app.agent.nodes.agent_node import coerce_text      # noqa: E402

# (số, câu hỏi, thẻ mà docs/kich-ban-quay-demo.md HỨA)
CAU_HOI: list[tuple[int, str, str]] = [
    (1, "tóm tắt hộp thư hôm nay", "digest"),
    (2, "triage hộp thư", "triage"),
    (3, "tuần này lịch trình tôi thế nào?", "lichtrinh"),
    (4, "tuần này tôi có bị quá tải không?", "lichtrinh"),
    (5, "tôi đang nợ ai cái gì?", "lichtrinh"),
    (6, "mình cần đi công tác cho việc nào không?", "lichtrinh"),
    (7, "tìm thư về học phí", "result|text"),
    (8, "xoá hết thư quảng cáo", "plan"),
    (9, "tóm tắt lá thư mới nhất", "result|text"),
    (10, "soạn thư cảm ơn thầy Sơn về buổi họp hội đồng", "draft"),
]


def _the(result: dict) -> dict:
    """Dựng thẻ ĐÚNG THỨ TỰ ƯU TIÊN như `/agent/chat`. Sai thứ tự thì kết quả kiểm
    không nói lên điều gì về thứ người dùng thật sự nhìn thấy."""
    last_ai = next((m for m in reversed(result["messages"])
                    if getattr(m, "type", None) == "ai" and getattr(m, "content", None)), None)
    out = result.get("final_output") or {
        "kind": "text",
        "text": (coerce_text(last_ai.content).strip() if last_ai else "") or "Mình đã xử lý xong.",
    }
    for dung in (_categorize_card, _di_lai_card, _digest_card, _triage_card, _lich_trinh_card):
        c = dung(result["messages"])
        if c:
            out = c
    c = _confirm_card(result["messages"])
    if c:
        out = c
    return out


async def _chay(so: int, cau: str, mong: str, ctx, graph) -> bool:
    print(f"\n{'═' * 74}\nQ{so}. {cau}\n{'─' * 74}")
    try:
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=cau)],
            "request_ctx": ctx,
            "skill_context": load_skills(cau),
            "user_context": "",
            "pending_confirmation": None,
            "iteration_count": 0,
            "final_output": None,
        })
    except Exception as exc:
        print(f"  LỖI khi chạy: {str(exc)[:220]}")
        return False

    tools = [getattr(m, "name", "?") for m in result["messages"]
             if getattr(m, "type", None) == "tool"]
    the = _the(result)
    kind = the.get("kind", "?")
    ok = kind in mong.split("|")

    print(f"  tool gọi : {', '.join(tools) or '(KHÔNG GỌI TOOL NÀO)'}")
    print(f"  thẻ trả  : {kind}   (tài liệu hứa: {mong})")
    if kind == "lichtrinh":
        print(f"    · {len(the.get('viec') or [])} việc · {len(the.get('ngay') or [])} ngày")
        print(f"    · intro: {the.get('intro', '')[:90]}")
        for v in (the.get("viec") or [])[:3]:
            print(f"      – {v.get('noi_dung', '')[:52]}  [thư: {v.get('email_id') or 'KHÔNG CÓ'}]")
    elif kind == "digest":
        print(f"    · {the.get('title')} · stats={[s['value'] for s in the.get('stats', [])]}")
        print(f"    · {len(the.get('emails') or [])} thư mở nhanh được")
    elif kind == "triage":
        n = sum(len(g.get("items", [])) for g in the.get("groups", []))
        co_id = sum(1 for g in the.get("groups", []) for i in g.get("items", []) if i.get("id"))
        print(f"    · {n} thư, {co_id} thư có id (mở được)")
    else:
        print(f"    · {str(the.get('text') or the.get('intro') or '')[:150]}")

    print(f"  → {'ĐÚNG như tài liệu' if ok else '*** LỆCH TÀI LIỆU ***'}")
    return ok


async def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args:
        print("Các câu có thể chạy (mỗi câu tốn 2–3 lượt gọi mô hình):\n")
        for so, cau, mong in CAU_HOI:
            print(f"  {so:>2}. {cau:<48} → {mong}")
        print("\nChạy vài câu:  ... thu_prompt_demo.py 3 4 6")
        print("Chạy tất cả :  ... thu_prompt_demo.py --tat-ca")
        return 0

    chon = CAU_HOI if "--tat-ca" in args else [c for c in CAU_HOI if str(c[0]) in args]
    if not chon:
        print("Không có câu nào khớp số bạn truyền.")
        return 1

    db = SessionLocal()
    try:
        user = token = None
        for u in db.query(User).order_by(User.id.desc()).all():
            cap = _token_for_user(db, u.id)
            if cap and cap[1] == "google":
                user, token = u, cap[0]
                break
        if not user:
            print("Không có tài khoản Google nào còn phiên. Đăng nhập MeoArc rồi chạy lại.")
            return 1

        print(f"Hộp thư : {user.email}")
        print(f"Số câu  : {len(chon)}  (≈ {len(chon) * 3} lượt gọi mô hình)")

        ctx = RequestContext(user_id=str(user.id), access_token=token,
                             email_provider="gmail", tier="free", scan_days=30)
        graph = build_graph()

        ket = []
        for so, cau, mong in chon:
            ket.append((so, await _chay(so, cau, mong, ctx, graph)))

        print(f"\n{'═' * 74}")
        hong = [s for s, ok in ket if not ok]
        if hong:
            print(f"LỆCH TÀI LIỆU ở {len(hong)}/{len(ket)} câu: " + ", ".join(f"Q{s}" for s in hong))
            print("Sửa docs/kich-ban-quay-demo.md hoặc sửa mã cho khớp — ĐỪNG quay khi còn lệch.")
            return 1
        print(f"CẢ {len(ket)} CÂU ĐỀU TRẢ ĐÚNG THẺ NHƯ TÀI LIỆU GHI.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
