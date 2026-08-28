"""Gửi bộ thư demo vào chính hộp thư đang đăng nhập, để màn Lịch trình có dữ liệu THẬT.

── VÌ SAO CẦN KỊCH BẢN NÀY ──
Bộ thư demo trong `src/frontend/src/data/demo-lich.ts` là DỮ LIỆU GIẢ nằm trong mã
nguồn frontend. Nó chỉ hiện ở chế độ mock (`VITE_API_BASE_URL` rỗng). Bản chạy thật
và bản deploy đều đọc Gmail thật, nên dữ liệu giả đó KHÔNG BAO GIỜ xuất hiện ở đó.

Muốn hộp thư thật có sự kiện để trình bày thì phải thật sự gửi thư vào nó. Kịch bản
này làm đúng việc đó: dùng phiên đăng nhập sẵn có trong DB để gửi thư TỪ tài khoản
của bạn TỚI chính nó.

── CÁCH CHẠY ──
    cd src/backend
    ./.venv/Scripts/python.exe scripts/gui_thu_demo.py            # xem trước, KHÔNG gửi
    ./.venv/Scripts/python.exe scripts/gui_thu_demo.py --gui-that # gửi thật

Mặc định là XEM TRƯỚC. Gửi thư là việc không hoàn tác được — nó rời khỏi máy bạn và
nằm trong hộp thư thật — nên phải gõ thêm cờ mới gửi. Cùng nguyên tắc confirm-gate
mà sản phẩm này áp cho agent.

── LƯU Ý ──
Thư gửi cho CHÍNH MÌNH sẽ nằm ở cả Đã gửi lẫn Hộp thư đến, và Gmail gộp chúng thành
một luồng. Đó là hành vi đúng của Gmail, không phải lỗi.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import SessionLocal              # noqa: E402
from app.models.user import User                  # noqa: E402
from app.services import gmail_send               # noqa: E402
from app.services.sync_service import _token_for_user  # noqa: E402

# Nội dung giữ ĐÚNG như bộ demo của frontend, để hai bên nói cùng một chuyện.
# Bốn tình huống bộ trích cam kết phải xử lý đúng + hai thư bẫy không phải cam kết.
THU_DEMO: list[tuple[str, str]] = [
    (
        "Đăng ký học phần HK1 2026-2027",
        "Chào các em,\n\n"
        "Sinh viên hoàn tất đăng ký học phần học kỳ 1 năm học 2026-2027 trên cổng "
        "thông tin trước 17:00 ngày 5/9. Sau thời hạn này hệ thống sẽ khoá, các "
        "trường hợp bổ sung phải làm đơn.\n\n"
        "Lưu ý kiểm tra kỹ số tín chỉ tối thiểu và các môn tiên quyết.\n\n"
        "Phòng Đào tạo",
    ),
    (
        "Lịch bảo vệ đồ án Nhập môn CNPM",
        "Chào em,\n\n"
        "Nhóm 7 chuẩn bị slide và bản demo chạy được. Buổi bảo vệ diễn ra lúc 8h "
        "thứ Ba tuần sau tại phòng I.53.\n\n"
        "Mỗi nhóm trình bày 15 phút, hỏi đáp 10 phút. Nhớ gửi slide trước một ngày.\n\n"
        "GVHD",
    ),
    (
        "Xác nhận tham dự vòng chung kết 12/09",
        "Xin chào đội MeoArc,\n\n"
        "Đội của bạn đã lọt vào vòng chung kết ngày 12/09 tại Đà Nẵng. Vui lòng xác "
        "nhận tham dự trong vòng 3 ngày làm việc kể từ khi nhận thư này.\n\n"
        "Ban tổ chức hỗ trợ chi phí đi lại cho tối đa 3 thành viên mỗi đội.",
    ),
    (
        "Nộp báo cáo Testing (PA3) — Nhóm 7",
        "Chào các em,\n\n"
        "Các nhóm nộp báo cáo Testing (PA3) đầy đủ lên Moodle trước 23:59 ngày 18/9, "
        "kèm minh chứng chạy test và bảng phân công công việc của từng thành viên.\n\n"
        "Báo cáo cần có đủ: kế hoạch kiểm thử, đặc tả ca kiểm thử cho toàn bộ use case "
        "đã đăng ký, kết quả chạy thực tế, phần đánh giá độ phủ, và phụ lục minh chứng.\n\n"
        "Đây là hạng mục chiếm trọng số lớn nhất của học phần. Các em bố trí thời gian "
        "sớm, đừng để dồn vào tuần cuối.\n\n"
        "Giáo vụ",
    ),
    (
        "Re: Chia việc phần backend tuần này",
        "Ok bạn,\n\n"
        "Mình nhận phần MCP server. Bạn gửi lại đặc tả tool trước thứ Năm để mình còn "
        "kịp làm.\n\n"
        "Phần confirm-gate mình thấy nên gom về một chỗ, tránh mỗi tool tự làm một kiểu.",
    ),
    (
        "Đóng học phí học kỳ 1",
        "Thông báo,\n\n"
        "Sinh viên hoàn tất đóng học phí học kỳ 1 trước ngày 25/9 qua cổng thanh toán "
        "của trường.\n\n"
        "Quá hạn sẽ bị khoá kết quả học tập cho tới khi hoàn tất.\n\n"
        "Phòng CTSV",
    ),
    # ── HAI THƯ BẪY: có ngày tháng nhưng KHÔNG phải cam kết ──
    # Chúng ở đây để chứng minh bộ trích không nhận bừa mọi thứ có con số — đó là
    # câu hỏi khó nhất khi trình bày.
    (
        "Sale 9.9 — giảm đến 50% ngày 9/9",
        "Đừng bỏ lỡ ngày hội mua sắm 9/9 với hàng ngàn ưu đãi giảm đến 50% toàn sàn.",
    ),
    (
        "Sinh nhật mình 15/9 nhé",
        "Mình tổ chức nhỏ ở nhà, hẹn gặp lại mọi người ngày 15/9 nha. Không cần mang gì đâu.",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Gửi bộ thư demo vào hộp thư đang đăng nhập.")
    ap.add_argument("--gui-that", action="store_true",
                    help="GỬI THẬT. Không có cờ này thì chỉ xem trước.")
    ap.add_argument("--email", default=None,
                    help="Địa chỉ nhận. Mặc định: chính tài khoản đang đăng nhập.")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).order_by(User.id.desc()).first()
        if user is None:
            print("Chưa có người dùng nào trong DB. Đăng nhập vào MeoArc một lần rồi chạy lại.")
            return 1

        cap = _token_for_user(db, user.id)
        if cap is None:
            print(f"Không tìm thấy phiên đăng nhập còn hiệu lực cho {user.email}. "
                  "Đăng nhập lại vào MeoArc rồi chạy lại.")
            return 1
        token, provider = cap
        if provider != "google":
            print(f"Kịch bản này chỉ gửi qua Gmail; tài khoản đang dùng là {provider}.")
            return 1

        nguoi_nhan = args.email or user.email
        print(f"Tài khoản : {user.email}")
        print(f"Gửi tới   : {nguoi_nhan}")
        print(f"Số thư    : {len(THU_DEMO)}\n")

        if not args.gui_that:
            for i, (tieu_de, _) in enumerate(THU_DEMO, 1):
                print(f"  {i}. {tieu_de}")
            print("\n── XEM TRƯỚC, CHƯA GỬI GÌ ──")
            print("Gửi thư là việc KHÔNG HOÀN TÁC ĐƯỢC. Chạy lại kèm --gui-that nếu chắc chắn.")
            return 0

        xong = 0
        for i, (tieu_de, than) in enumerate(THU_DEMO, 1):
            try:
                gmail_send.send_email(token, to=nguoi_nhan, subject=tieu_de, body=than)
                xong += 1
                print(f"  [{i}/{len(THU_DEMO)}] đã gửi: {tieu_de}")
            except Exception as exc:
                # Một thư hỏng KHÔNG được làm dừng cả bộ — báo rồi đi tiếp.
                print(f"  [{i}/{len(THU_DEMO)}] LỖI: {tieu_de} — {exc}")

        print(f"\nĐã gửi {xong}/{len(THU_DEMO)} thư.")
        print("Mở MeoArc, bấm nút làm mới ở khung Thư, rồi vào Lịch trình để xem.")
        return 0 if xong else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
