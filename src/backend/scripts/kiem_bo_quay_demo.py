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
from bo_quay_demo import bo_thu             # noqa: E402

_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _thu_gia(moc: datetime) -> list[dict]:
    """Đổi bộ thư thành khuôn mà `trich_cam_ket` đọc. Ngày nhận = LÚC GỬI (hôm nay),
    đúng như khi chạy thật."""
    ra = []
    for i, (nguoi, tieu_de, than) in enumerate(bo_thu(moc)):
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
            "body": than.split("\n\n"),
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
    if not qua_tai:
        loi.append("Q4: KHÔNG ngày nào quá tải — thẻ sẽ không có cột đỏ nào để chỉ.")

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
    if len(" ".join(thu[-1]["body"]).split()) < 150:
        loi.append("Q9: thư cuối quá ngắn, tóm tắt sẽ không có gì đáng nói.")

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
