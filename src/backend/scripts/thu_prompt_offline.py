"""CHẠY BỘ PROMPT DEMO với MÔ HÌNH THẬT, hộp thư NẠP SẴN (không cần đăng nhập Gmail).

── VÌ SAO CÓ BẢN NÀY BÊN CẠNH `thu_prompt_demo.py` ──
Bản kia đi qua Gmail thật nên cần một phiên đăng nhập còn hạn. Trên máy chưa đăng
nhập thì không chạy được câu nào — mà thứ đáng kiểm nhất lại KHÔNG nằm ở Gmail:

    "mô hình có gọi ĐÚNG TOOL cho cách nói này không, và câu trả lời có đúng việc không"

Đó là chỗ hay hỏng, và cũng là chỗ tốn quota. Thay Gmail bằng đúng 46 thư demo thì
câu hỏi đó được cô lập, kết quả LẶP LẠI ĐƯỢC (cùng dữ liệu vào, so được giữa các lần
chạy), và mỗi lượt gọi mô hình đổi lấy đúng thông tin ta cần.

── NÓ KHÔNG CHỨNG MINH CÁI GÌ ──
Không chứng minh OAuth/quyền Gmail còn tốt, không chứng minh gửi thư thật chạy được.
Hai thứ đó phải kiểm trên bản triển khai. Bản này chỉ trả lời: NÃO có đúng không.

    ./.venv/Scripts/python.exe scripts/thu_prompt_offline.py --tat-ca
    ./.venv/Scripts/python.exe scripts/thu_prompt_offline.py 1 2 7 12
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# stdout do  boc lai luc import — boc hai lan la dong mat luong.

from app.agent.graph import build_graph                      # noqa: E402
from app.core import labeling                                # noqa: E402
from app.schemas.email import Email                          # noqa: E402
from app.tools.registry import RequestContext                # noqa: E402
from scripts import bo_quay_demo                             # noqa: E402
from scripts.thu_prompt_demo import CAU_HOI, _chay            # noqa: E402
from scripts.tom_ket import tom_ket                          # noqa: E402


def _hop_thu() -> list[Email]:
    """46 thư demo → đối tượng Email, phân loại bằng chính engine thật.

    Người gửi để đúng địa chỉ tự-gửi-cho-mình như bản demo thật, vì đó chính là điều
    kiện làm lộ ra lỗi phân loại: địa chỉ giống nhau ở mọi thư nên không mang tín hiệu.
    """
    from datetime import datetime, timedelta
    _n = datetime.now()
    _gio, _hom_nay = _n.strftime("%H:%M"), _n.strftime("%d/%m/%Y %H:%M")
    dia = "meoarc.hcmus@outlook.com.vn"
    ra: list[Email] = []
    for i, (ten, tieu_de, than) in enumerate(bo_quay_demo.bo_day_du(), 1):
        pl = labeling.classify(dia, ten, tieu_de, than[:400])
        pt = labeling.analyze(dia, ten, tieu_de, than[:400])
        ra.append(Email(
            id=f"demo-{i:03d}", sender=ten, senderEmail=dia,
            senderInitial=(ten or "?")[:1].upper(), to="me",
            subject=tieu_de, preview=than[:120], body=[than],
            # Ngày phải là HÔM NAY: mọi câu "hôm nay"/"tuần này" lọc theo ngày, để
            # ngày cố định thì thẻ nào cũng ra rỗng và ta tưởng mô hình sai.
            time=_gio, date=_hom_nay,
            unread=True, starred=False,
            category=pl.category.color, label=pl.category.label,
            priority=getattr(pt, "priority", None) and str(pt.priority.value),
            status=getattr(pt, "status", None) and str(pt.status.value),
        ))
    return ra


def _gan_hop_thu(ds: list[Email]) -> None:
    """Thay Gmail bằng hộp thư nạp sẵn, ở ĐÚNG chỗ mọi tool đi qua (`tools.mail`).

    Chặn ở tầng này chứ không chặn từng tool: chặn từng tool thì tool nào quên chặn
    sẽ lặng lẽ gọi ra mạng thật và ta không biết kết quả đến từ đâu.
    """
    from app.tools import email_tools

    def list_messages(*_a, max_results: int = 50, **_kw):
        return ds[:max_results], None

    def get_message(_provider, _token, msg_id, **_kw):
        return next((e for e in ds if e.id == msg_id), ds[0])

    email_tools.mail.list_messages = list_messages          # type: ignore[assignment]
    email_tools.mail.get_message = get_message              # type: ignore[assignment]


async def main() -> int:
    args = [a for a in sys.argv[1:]]
    if "--tat-ca" in args:
        chon = CAU_HOI
    elif "--nhom" in args:
        chon = [c for c in CAU_HOI if c[1] == args[args.index("--nhom") + 1]]
    else:
        chon = [c for c in CAU_HOI if str(c[0]) in args]
    if not chon:
        print("Chạy:  thu_prompt_offline.py 1 2 3   |   --nhom widget   |   --tat-ca")
        print(f"Có {len(CAU_HOI)} câu.")
        return 1

    from app.core.config import settings
    ds = _hop_thu()
    _gan_hop_thu(ds)

    print(f"Hộp thư : {len(ds)} thư demo nạp sẵn (KHÔNG gọi Gmail)")
    print(f"Model   : {settings.model_name} → {settings.model_fallbacks or '(không dự phòng)'}")
    print(f"Số câu  : {len(chon)}  (≈ {len(chon) * 3} lượt gọi mô hình)")

    ctx = RequestContext(user_id="1", access_token="offline",
                         email_provider="gmail", tier="free", scan_days=30)
    graph = build_graph()

    # DỪNG khi liên tiếp KHÔNG GỌI NỔI mô hình.
    #
    # Đếm theo trạng thái 'loi' chứ không theo "trượt": một câu LỆCH THẺ là chuyện của
    # phần mềm và không có lý do gì để bỏ dở phần còn lại; còn ba câu liền nhau không
    # gọi nổi mô hình thì gần như luôn là hạn mức, và chạy tiếp chỉ tổ in thêm 23 khối
    # lỗi giống hệt nhau — đúng thứ đã xảy ra ngày 05/09.
    LOI_LIEN_TIEP_TOI_DA = 3
    ket: list[tuple[int, str]] = []
    lien_tiep = 0
    for so, nhom, cau, mong, gc in chon:
        try:
            trang = await _chay(so, nhom, cau, mong, gc, ctx, graph)
        except Exception as exc:                     # noqa: BLE001
            print(f"[{so}] LỖI: {type(exc).__name__}: {str(exc)[:200]}")
            trang = "loi"
        ket.append((so, trang))
        lien_tiep = lien_tiep + 1 if trang == "loi" else 0
        if lien_tiep >= LOI_LIEN_TIEP_TOI_DA:
            print(f"\n→ {lien_tiep} câu liên tiếp KHÔNG gọi nổi mô hình — gần như chắc"
                  " chắn hết hạn mức.")
            con = [str(c[0]) for c in chon[len(ket):]]
            if con:
                print("  Dừng ở đây. Chạy lại đúng phần còn lại khi hạn mức hồi:")
                print(f"  ./.venv/Scripts/python.exe scripts/thu_prompt_offline.py {' '.join(con)}")
            break

    print(f"\n{'═' * 76}")
    # Dùng CHUNG `tom_ket` với bộ chạy kia — hai bảng đếm khác nhau cho cùng một thứ là
    # cách chắc chắn để hai con số dần lệch nhau mà không ai biết.
    print(tom_ket(ket))
    return 1 if any(t == "lech" for _, t in ket) else 0


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(asyncio.run(main()))
