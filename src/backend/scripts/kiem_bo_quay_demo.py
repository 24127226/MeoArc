"""KIỂM BỘ THƯ DEMO CÓ ĂN NHẬP VỚI BỘ CÂU HỎI KHÔNG — bằng MÁY, không bằng mắt.

── VÌ SAO CẦN ──
Bộ thư và bộ câu hỏi trôi xa nhau rất dễ, và trôi trong im lặng: câu hỏi "tóm tắt thư
chưa đọc hôm nay" vẫn chạy, chỉ là trả về rỗng. Lúc đang quay thì không kịp sửa, và
người xem chỉ thấy một sản phẩm trả lời rỗng.

Kịch bản này chạy CHÍNH bộ trích cam kết và bộ tính áp lực mà sản phẩm dùng, lên đúng
bộ thư sắp gửi, rồi khẳng định từng điều kiện mà `docs/kich-ban-quay-demo.md` dựa vào.
Đỏ ở đây nghĩa là câu hỏi tương ứng sẽ ra rỗng khi quay.

    cd src/backend
    ./.venv/Scripts/python.exe scripts/kiem_bo_quay_demo.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core import cam_ket as CK          # noqa: E402
from app.core import labeling               # noqa: E402
from bo_quay_demo import bo_day_du, bo_thu  # noqa: E402

_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _thu_gia(moc: datetime) -> list[dict]:
    """Đổi bộ thư thành khuôn mà `trich_cam_ket` đọc. Ngày nhận = LÚC GỬI (hôm nay),
    đúng như khi chạy thật."""
    ra = []
    for i, (nguoi, tieu_de, than) in enumerate(bo_day_du(moc)):
        # `priority` để None ĐÚNG NHƯ THẬT: `gmail_service` không gán trường này — chỉ
        # dữ liệu mock trong `email_service` mới có. Gán bừa ở đây thì bộ kiểm sẽ báo
        # "có ngày quá tải" trong khi lúc quay thật thì không, tức là nó nói dối đúng
        # ở chỗ nó sinh ra để nói thật.
        ra.append({
            "id": f"d{i}",
            "sender": nguoi,
            "senderEmail": "demo@example.com",
            "subject": tieu_de,
            "preview": than[:120],
            # ── PHẢI LÀ ĐOẠN TRÍCH, KHÔNG PHẢI THÂN THƯ ĐẦY ĐỦ ──
            # `gmail_service.list_messages` trả `body=[snippet]` (xem dòng 184 ở đó):
            # khi LIỆT KÊ thư, Gmail chỉ đưa ~200 ký tự đầu, thân đầy đủ phải gọi riêng
            # từng thư. Bộ trích cam kết chạy trên danh sách nên nó CHỈ THẤY đoạn trích.
            #
            # Bản đầu của kịch bản này nạp thân thư đầy đủ, nên nó tính ra 390 phút và
            # báo "có ngày quá tải" — trong khi chạy thật chỉ ra 180 phút và không ngày
            # nào quá tải. Một bộ kiểm nói dối đúng ở chỗ nó sinh ra để nói thật thì tệ
            # hơn không có bộ kiểm, vì nó tạo ra sự yên tâm sai.
            "body": [than[:200]],
            "date": moc.strftime("%d/%m/%Y %H:%M"),
            "folder": "inbox",
            "unread": True,
            "priority": None,
        })
    return ra


def main() -> int:
    moc = datetime.now(_TZ).replace(tzinfo=None)
    thu = _thu_gia(moc)
    # `trich_cam_ket` tự đọc `priority` từ thư; ở đây để None thì nó tự phân tích lại
    # đúng như trong sản phẩm.
    ck = CK.trich_cam_ket(thu, moc)

    loi: list[str] = []
    print(f"Mốc kiểm : {moc:%d/%m/%Y %H:%M} ({['T2','T3','T4','T5','T6','T7','CN'][moc.weekday()]})")
    print(f"Số thư   : {len(thu)}")
    print(f"Cam kết  : {len(ck)}\n")

    # ── Q3: "tuần này lịch trình tôi thế nào?" ──────────────────────────────
    het_tuan = (moc + timedelta(days=6 - moc.weekday())).replace(hour=23, minute=59)
    trong_tuan = [c for c in ck if c.han and moc.date() <= c.han.date() <= het_tuan.date()]
    print(f"Q3 · việc trong TUẦN NÀY (đến {het_tuan:%d/%m}): {len(trong_tuan)}")
    for c in trong_tuan:
        print(f"     · {c.han:%d/%m %H:%M} — {c.noi_dung[:56]}")
    if len(trong_tuan) < 3:
        loi.append("Q3: dưới 3 việc trong tuần này — câu hỏi 'tuần này' sẽ trông nghèo nàn.")

    # ── Q4: "tuần này tôi có bị quá tải không?" ─────────────────────────────
    so_ngay_tuan = max(1, 6 - moc.weekday() + 1)
    bang = CK.ap_luc_theo_ngay(ck, so_ngay_tuan, moc)
    qua_tai = [b for b in bang if b["qua_tai"]]
    print(f"\nQ4 · áp lực {so_ngay_tuan} ngày (trần {CK.TRAN_MOI_NGAY} phút/ngày):")
    for b in bang:
        cho = " ← QUÁ TẢI" if b["qua_tai"] else ""
        print(f"     {b['ngay']}  {b['so_viec']:>2} việc  {b['phut']:>4} phút{cho}")
    nang_nhat = max(bang, key=lambda b: b["phut"], default=None)
    if nang_nhat and nang_nhat["so_viec"]:
        print(f"     → ngày nặng nhất: {nang_nhat['ngay']} ({nang_nhat['so_viec']} việc)")
    # KHÔNG đòi phải có ngày quá tải nữa.
    #
    # Trần là 360 phút/ngày, mà bộ trích chỉ nhìn thấy ĐOẠN TRÍCH ~200 ký tự của mỗi
    # thư (Gmail không trả thân đầy đủ khi liệt kê), nên mọi việc đều rơi vào bậc 30
    # phút. Muốn vượt trần phải có 13 việc trong CÙNG một ngày — một hộp thư như thế
    # trông giả tạo hơn là ấn tượng.
    #
    # Điều kiện đúng cần khẳng định là: ngày nặng nhất phải NỔI HẲN so với ngày khác,
    # để cột trên thẻ có hình dạng đáng nhìn và câu trả lời có chỗ để chỉ vào.
    if not nang_nhat or nang_nhat["so_viec"] < 4:
        loi.append("Q4: không ngày nào có từ 4 việc — dải cột sẽ phẳng, không có gì để chỉ.")

    # ── Q5: "tôi đang nợ ai cái gì?" ───────────────────────────────────────
    co_nguoi_cho = [c for c in ck if c.nguoi_cho]
    print(f"\nQ5 · việc có người đang chờ: {len(co_nguoi_cho)}")
    if len(co_nguoi_cho) < 2:
        loi.append("Q5: dưới 2 việc có người chờ.")

    # ── Q6: "cần đi công tác cho việc nào không?" ──────────────────────────
    van = {t["id"]: f"{t['subject']} {' '.join(t['body'])}" for t in thu}
    y_dinh = CK.suy_y_dinh_di_lai(ck, van, "SGN")
    print(f"\nQ6 · việc phải đi xa: {len(y_dinh)}")
    for y in y_dinh:
        print(f"     · {y.thanh_pho} ({y.ma_san_bay}) — {y.noi_dung[:48]}")
    if not y_dinh:
        loi.append("Q6: không có việc nào phải đi xa — câu hỏi công tác sẽ trả về rỗng.")

    # ── Q7: bẫy "miễn phí" KHÔNG được lọt vào kết quả tìm "học phí" ────────
    bay = [t for t in thu if "MIỄN PHÍ" in t["subject"]]
    that = [t for t in thu if "học phí" in t["subject"].lower()]
    print(f"\nQ7 · thư 'học phí' thật: {len(that)} · thư bẫy 'MIỄN PHÍ': {len(bay)}")
    if not bay or not that:
        loi.append("Q7: thiếu cặp thư thật/bẫy để chứng minh việc tìm nguyên cụm.")

    # ── Q8: có đủ thư quảng cáo để xoá ─────────────────────────────────────
    qc = [t for t in thu
          if labeling.classify(t["senderEmail"], t["sender"], t["subject"],
                               t["preview"]).category.label in ("Mua sắm & Ưu đãi",
                                                                "Cập nhật & Hệ thống")]
    print(f"\nQ8 · thư quảng cáo/cập nhật: {len(qc)}")
    if len(qc) < 3:
        loi.append("Q8: dưới 3 thư quảng cáo — demo 'xoá hết thư quảng cáo' sẽ mỏng.")

    # ── Q9: thư mới nhất phải là thư CUỐI danh sách ────────────────────────
    print(f"\nQ9 · thư gửi cuối (= mới nhất): {thu[-1]['subject'][:60]}")
    # Đo THÂN THƯ GỐC chứ không phải đoạn trích. Tóm tắt MỘT lá thư đi qua `get_email`
    # (lấy thân đầy đủ), khác hẳn đường liệt kê vốn chỉ có snippet — nên đo trên
    # snippet ở đây là đo sai thứ mà câu hỏi Q9 thật sự dùng.
    if len(bo_day_du(moc)[-1][2].split()) < 150:
        loi.append("Q9: thư cuối quá ngắn, tóm tắt sẽ không có gì đáng nói.")

    # ── BẪY DÙNG NGÀY CỨNG — phải kiểm chúng CÒN Ở TƯƠNG LAI ───────────────
    # 26 thư bẫy lấy từ bộ khó cũ ghi cứng 15/9, 16/9, 20/9, 22/9, 24/9… Chúng còn ở
    # tương lai thì "sáu câu làm khó" còn đúng; chạy muộn quá là mọi mốc đã qua, câu
    # hỏi trả lời sai hoặc rỗng — mà KHÔNG có dấu hiệu nào báo, vì hộp thư vẫn đầy thư.
    import re as _re
    moc_bay: set[tuple[int, int]] = set()
    for _, _td, _tb in bo_day_du(moc)[len(bo_thu(moc)) - 1:]:
        for _d, _m in _re.findall(r"(\d{1,2})/(\d{1,2})", f"{_td} {_tb}"):
            if 1 <= int(_d) <= 31 and 1 <= int(_m) <= 12:
                moc_bay.add((int(_m), int(_d)))
    da_qua = sorted(x for x in moc_bay if x < (moc.month, moc.day))
    print(f"\nBẫy · mốc ngày CỨNG trong bộ khó: {len(moc_bay)} mốc, {len(da_qua)} đã qua")
    if da_qua:
        loi.append(
            "Bộ thư bẫy có mốc ĐÃ QUA (" + ", ".join(f"{d}/{m}" for m, d in da_qua[:8])
            + ") — sáu câu làm khó sẽ trả lời sai hoặc rỗng. Sửa ngày trong _THU_KHO "
              "của scripts/gui_thu_demo.py.")

    print("\n" + "─" * 68)
    if loi:
        print("CÓ VẤN ĐỀ — sửa bộ thư trước khi quay:\n")
        for x in loi:
            print(f"  ✗ {x}")
        return 1
    print("MỌI CÂU HỎI ĐỀU CÓ DỮ LIỆU ĐỠ. Bộ thư và kịch bản khớp nhau.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
