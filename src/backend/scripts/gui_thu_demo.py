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
    ./.venv/Scripts/python.exe scripts/gui_thu_demo.py --gui-that # gửi thật (8 thư)

    # Thêm ~51 thư dồn cục để xem màn Lịch trình DƯỚI TẢI THẬT:
    ./.venv/Scripts/python.exe scripts/gui_thu_demo.py --bo-day             # xem trước
    ./.venv/Scripts/python.exe scripts/gui_thu_demo.py --bo-day --gui-that  # gửi 59 thư

Mặc định là XEM TRƯỚC. Gửi thư là việc không hoàn tác được — nó rời khỏi máy bạn và
nằm trong hộp thư thật — nên phải gõ thêm cờ mới gửi. Cùng nguyên tắc confirm-gate
mà sản phẩm này áp cho agent.

`--bo-day` gửi 59 thư, và vì thư tự gửi nằm ở CẢ Hộp thư đến LẪN Đã gửi nên hộp thư
sẽ có ~118 mục cần dọn. Kịch bản in cảnh báo kèm truy vấn dọn trước khi chạy. Nên gửi
trước buổi trình bày ít nhất một hôm để còn kịp kiểm tra.

── LƯU Ý ──
Thư gửi cho CHÍNH MÌNH sẽ nằm ở cả Đã gửi lẫn Hộp thư đến, và Gmail gộp chúng thành
một luồng. Đó là hành vi đúng của Gmail, không phải lỗi.

CÓ VÀO THƯ RÁC KHÔNG? Gần như chắc chắn là không. Thư đi qua chính Gmail API bằng
phiên OAuth của bạn, nên với Gmail đây là thư do CHÍNH BẠN gửi: xác thực đầy đủ
(SPF/DKIM/DMARC đều đạt vì nó thật sự phát từ máy chủ Google), người gửi lại nằm
trong danh bạ của chính mình. Bộ lọc rác không có gì để nghi.

Rủi ro thật nằm ở chỗ khác: Gmail có thể xếp thư "Sale 9.9" vào thẻ **Quảng cáo**
thay vì Chính. Điều đó KHÔNG ảnh hưởng tới MeoArc — thẻ phân loại chỉ là nhãn phụ,
thư vẫn mang nhãn INBOX nên vẫn về đủ. Chỉ khi mở Gmail bằng mắt mới thấy nó nằm tab
khác.

TÊN NGƯỜI GỬI: mỗi thư đặt tên hiển thị riêng (xem THU_DEMO). ĐỊA CHỈ thì vẫn là tài
khoản đang đăng nhập — Gmail từ chối gửi hộ địa chỉ lạ. Nên trong Gmail bạn sẽ thấy
"Giáo vụ HCMUS" nhưng địa chỉ thật là email của bạn. Đủ cho demo, và cũng đúng: đây
là thư demo, không phải giả mạo trường.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import SessionLocal              # noqa: E402
from app.models.user import User                  # noqa: E402
from app.services import gmail_send               # noqa: E402
from app.services.sync_service import _token_for_user  # noqa: E402

# Nội dung giữ ĐÚNG như bộ demo của frontend, để hai bên nói cùng một chuyện.
# Bốn tình huống bộ trích cam kết phải xử lý đúng + hai thư bẫy không phải cam kết.
#
# Phần tử đầu là TÊN HIỂN THỊ người gửi. Không có nó thì Gmail điền tên chủ tài khoản
# vào cả 8 thư, và màn Lịch trình hiện tám cái thẻ cùng đề tên bạn — lúc demo trông
# như hỏng. Địa chỉ thì vẫn là tài khoản đang đăng nhập (Gmail không cho gửi hộ địa
# chỉ lạ); chỉ tên hiển thị là đổi được.
THU_DEMO: list[tuple[str, str, str]] = [
    (
        "Phòng Đào tạo HCMUS",
        "Đăng ký học phần HK1 2026-2027",
        "Chào các em,\n\n"
        "Sinh viên hoàn tất đăng ký học phần học kỳ 1 năm học 2026-2027 trên cổng "
        "thông tin trước 17:00 ngày 5/9. Sau thời hạn này hệ thống sẽ khoá, các "
        "trường hợp bổ sung phải làm đơn.\n\n"
        "Lưu ý kiểm tra kỹ số tín chỉ tối thiểu và các môn tiên quyết.\n\n"
        "Phòng Đào tạo",
    ),
    (
        "GVHD Nguyễn Văn Sơn",
        "Lịch bảo vệ đồ án Nhập môn CNPM",
        "Chào em,\n\n"
        "Nhóm 7 chuẩn bị slide và bản demo chạy được. Buổi bảo vệ diễn ra lúc 8h "
        "thứ Ba tuần sau tại phòng I.53.\n\n"
        "Mỗi nhóm trình bày 15 phút, hỏi đáp 10 phút. Nhớ gửi slide trước một ngày.\n\n"
        "GVHD",
    ),
    (
        "Ban tổ chức Hackathon",
        "Xác nhận tham dự vòng chung kết 12/09",
        "Xin chào đội MeoArc,\n\n"
        "Đội của bạn đã lọt vào vòng chung kết ngày 12/09 tại Đà Nẵng. Vui lòng xác "
        "nhận tham dự trong vòng 3 ngày làm việc kể từ khi nhận thư này.\n\n"
        "Ban tổ chức hỗ trợ chi phí đi lại cho tối đa 3 thành viên mỗi đội.",
    ),
    (
        "Giáo vụ HCMUS",
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
        "Trần Minh Khoa",
        "Re: Chia việc phần backend tuần này",
        "Ok bạn,\n\n"
        "Mình nhận phần MCP server. Bạn gửi lại đặc tả tool trước thứ Năm để mình còn "
        "kịp làm.\n\n"
        "Phần confirm-gate mình thấy nên gom về một chỗ, tránh mỗi tool tự làm một kiểu.",
    ),
    (
        "Phòng CTSV",
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
        "Shopee",
        "Sale 9.9 — giảm đến 50% ngày 9/9",
        "Đừng bỏ lỡ ngày hội mua sắm 9/9 với hàng ngàn ưu đãi giảm đến 50% toàn sàn.",
    ),
    (
        "Lê Thu Hà",
        "Sinh nhật mình 15/9 nhé",
        "Mình tổ chức nhỏ ở nhà, hẹn gặp lại mọi người ngày 15/9 nha. Không cần mang gì đâu.",
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# BỘ THƯ DÀY (--bo-day) — để xem màn Lịch trình DƯỚI TẢI THẬT trên hộp thư THẬT
#
# Bộ 8 thư ở trên rải đều nên ba cơ chế xử lý quá tải (xếp làn, chip "+N", bảng
# ngày) gần như không bao giờ chạy. Bộ này dồn cục: vài ngày 8–10 việc, hai đợt
# kéo dài nhiều tuần chồng nhau.
#
# GIỮ ĐỒNG BỘ với `src/frontend/src/data/demo-qua-tai.ts`. Hai nơi vì hai đích
# khác nhau — bên kia là dữ liệu giả cho chế độ mock, bên này là thư THẬT gửi vào
# hộp thư thật. Sửa một bên mà quên bên kia thì demo mock và demo thật lệch nhau,
# và đó là kiểu lệch chỉ lộ ra đúng lúc đang trình bày.
# ══════════════════════════════════════════════════════════════════════════════

# [ngày/tháng, giờ hạn, người gửi, động từ + việc]
_VIEC_DAY: list[tuple[str, str, str, str]] = [
    # ── Tuần 7–13/9 ──
    ("7/9", "17:00", "Giáo vụ HCMUS", "nộp danh sách nhóm đồ án"),
    ("7/9", "23:59", "Nguyễn Hoàng Anh", "gửi bản vẽ use case cho nhóm"),
    ("8/9", "09:00", "GVHD Nguyễn Văn Sơn", "trình bày tiến độ tuần 2"),
    ("8/9", "17:00", "Phòng Đào tạo HCMUS", "xác nhận lịch thi giữa kỳ"),
    ("8/9", "23:59", "Trần Minh Khoa", "gửi đặc tả API cho backend"),
    ("8/9", "23:59", "CLB Học thuật", "đăng ký suất trình bày seminar"),
    ("9/9", "12:00", "Thư viện HCMUS", "gia hạn sách mượn"),
    ("9/9", "17:00", "Lê Thu Hà", "phản hồi bản thiết kế giao diện"),
    ("9/9", "23:59", "Giáo vụ HCMUS", "nộp biên bản họp nhóm tuần 2"),
    ("11/9", "08:00", "Phòng CTSV", "nộp đơn xin miễn giảm học phí"),
    ("11/9", "17:00", "Nguyễn Hoàng Anh", "gửi số liệu đo hiệu năng"),
    ("11/9", "23:59", "Ban tổ chức Hackathon", "xác nhận danh sách thành viên dự thi"),
    ("11/9", "23:59", "Trần Minh Khoa", "trả lời góp ý pull request #48"),
    ("11/9", "23:59", "Đoàn khoa CNTT", "đăng ký tham gia ngày hội việc làm"),
    # ── Tuần 14–20/9: ĐỈNH ĐIỂM ──
    ("14/9", "09:00", "GVHD Nguyễn Văn Sơn", "trình bày tiến độ tuần 3"),
    ("14/9", "17:00", "Giáo vụ HCMUS", "nộp phiếu tự đánh giá giữa kỳ"),
    ("14/9", "23:59", "Lê Thu Hà", "gửi bản dịch phần tài liệu tiếng Anh"),
    ("14/9", "23:59", "Phòng Đào tạo HCMUS", "đăng ký môn học bổ sung"),
    ("14/9", "23:59", "Thư viện HCMUS", "trả sách quá hạn đợt hai"),
    ("15/9", "08:30", "Phòng Quan hệ Doanh nghiệp", "nộp nhật ký thực tập tuần 1"),
    ("15/9", "10:00", "Nguyễn Hoàng Anh", "trình bày phần kiến trúc cho nhóm"),
    ("15/9", "15:00", "Trần Minh Khoa", "gửi kết quả chạy kiểm thử tích hợp"),
    ("15/9", "17:00", "Giáo vụ HCMUS", "nộp bản mô tả ca kiểm thử"),
    ("15/9", "17:00", "Phòng CTSV", "xác nhận thông tin bảo hiểm y tế"),
    ("15/9", "23:59", "CLB Học thuật", "gửi slide buổi chia sẻ kỹ thuật"),
    ("15/9", "23:59", "Lê Thu Hà", "phản hồi bản nháp phần mở đầu"),
    ("15/9", "23:59", "Đoàn khoa CNTT", "đăng ký ca trực hỗ trợ tân sinh viên"),
    ("17/9", "09:00", "GVHD Nguyễn Văn Sơn", "bảo vệ tiến độ giữa kỳ"),
    ("17/9", "14:00", "Ban tổ chức Hackathon", "trình bày sản phẩm vòng loại"),
    ("17/9", "17:00", "Nguyễn Hoàng Anh", "gửi bản cập nhật sơ đồ lớp"),
    ("17/9", "23:59", "Trần Minh Khoa", "hoàn thành phần tài liệu triển khai"),
    ("17/9", "23:59", "Phòng Đào tạo HCMUS", "xác nhận đăng ký thi lại"),
    ("17/9", "23:59", "Thư viện HCMUS", "thanh toán phí phạt quá hạn"),
    ("18/9", "08:00", "Phòng Quan hệ Doanh nghiệp", "nộp nhật ký thực tập tuần 2"),
    ("18/9", "10:00", "Giáo vụ HCMUS", "nộp phụ lục minh chứng kiểm thử"),
    ("18/9", "15:00", "Lê Thu Hà", "gửi ảnh chụp giao diện đã dựng"),
    ("18/9", "17:00", "Nguyễn Hoàng Anh", "phản hồi bảng phân công công việc"),
    ("18/9", "23:59", "Trần Minh Khoa", "gửi bản ghi buổi họp nhóm"),
    ("18/9", "23:59", "CLB Học thuật", "xác nhận tham dự buổi tổng kết"),
    ("18/9", "23:59", "Phòng CTSV", "nộp đơn xin xác nhận thực tập"),
    # ── Tuần 21–27/9 ──
    ("22/9", "09:00", "GVHD Nguyễn Văn Sơn", "trình bày tiến độ tuần 4"),
    ("22/9", "17:00", "Giáo vụ HCMUS", "nộp bản chỉnh sửa theo góp ý"),
    ("22/9", "23:59", "Nguyễn Hoàng Anh", "gửi phần đánh giá độ phủ kiểm thử"),
    ("23/9", "17:00", "Phòng Quan hệ Doanh nghiệp", "nộp nhật ký thực tập tuần 3"),
    ("23/9", "23:59", "Trần Minh Khoa", "hoàn tất phần hướng dẫn cài đặt"),
    ("24/9", "10:00", "Ban tổ chức Hackathon", "xác nhận tham dự lễ trao giải"),
    ("24/9", "17:00", "Lê Thu Hà", "gửi bản in màu để nộp cứng"),
    ("24/9", "23:59", "Phòng Đào tạo HCMUS", "đăng ký học phần học kỳ 2"),
]

# Đợt kéo dài nhiều tuần — dạng "từ … đến …", tức khoảng NÓI THẲNG.
# [người gửi, tên đợt, từ, đến]
_DOT_DAY: list[tuple[str, str, str, str]] = [
    ("Phòng Khảo thí", "Đợt kiểm tra giữa kỳ toàn khoa", "14/9", "19/9"),
    ("Nhóm 7 — Anh Quân", "Giai đoạn hoàn thiện tài liệu PA3", "9/9", "22/9"),
    ("Phòng Quan hệ Doanh nghiệp", "Đợt thực tập doanh nghiệp", "7/9", "25/9"),
]


def _canh_bao_bo_day(tong: int, nguoi_nhan: str) -> None:
    """Nói THẲNG cái giá phải trả, trước khi người dùng bấm.

    Gửi thư là việc không hoàn tác được, và ~50 thư thì không phải "một chút lộn
    xộn" mà là hộp thư đổi hẳn diện mạo. Người bấm phải biết trước cả hậu quả lẫn
    cách dọn — chôn thông tin đó trong tài liệu thì lúc cần không ai tìm ra."""
    print("┌─ CẢNH BÁO ─────────────────────────────────────────────────────────")
    print(f"│ Kịch bản sẽ gửi {tong} thư vào {nguoi_nhan}.")
    print("│ KHÔNG HOÀN TÁC ĐƯỢC. Thư tự gửi nằm ở CẢ Hộp thư đến LẪN Đã gửi,")
    print("│ nên hộp thư sẽ có khoảng gấp đôi số đó cần dọn.")
    print("│")
    print("│ Dọn lại: mở Gmail, tìm  from:me to:me newer_than:1d  rồi chọn tất cả.")
    print("│ Nên gửi TRƯỚC buổi bảo vệ ít nhất một hôm để còn kịp kiểm tra.")
    print("└────────────────────────────────────────────────────────────────────")


def _dung_bo_day() -> list[tuple[str, str, str]]:
    """Dựng bộ thư dày từ hai bảng gọn ở trên."""
    ra: list[tuple[str, str, str]] = []
    for ngay, gio, nguoi, viec in _VIEC_DAY:
        tieu_de = f"{viec[0].upper()}{viec[1:]} — hạn {ngay}"
        than = (
            "Chào bạn,\n\n"
            f"Bạn {viec} trước {gio} ngày {ngay}.\n\n"
            "Nếu có vướng mắc thì báo lại sớm để còn kịp xử lý trong tuần."
        )
        ra.append((nguoi, tieu_de, than))
    for nguoi, ten, tu, den in _DOT_DAY:
        than = (
            "Thông báo,\n\n"
            f"{ten} diễn ra từ ngày {tu} đến ngày {den}. Bạn hoàn thành các đầu việc "
            "được giao trong suốt đợt và nộp kết quả vào cuối đợt.\n\n"
            "Lịch chi tiết từng ngày xem trong tệp đính kèm của thông báo gốc."
        )
        ra.append((nguoi, f"{ten} ({tu} – {den})", than))
    return ra


def main() -> int:
    ap = argparse.ArgumentParser(description="Gửi bộ thư demo vào hộp thư đang đăng nhập.")
    ap.add_argument("--gui-that", action="store_true",
                    help="GỬI THẬT. Không có cờ này thì chỉ xem trước.")
    ap.add_argument("--email", default=None,
                    help="Địa chỉ NHẬN. Mặc định: chính tài khoản đang đăng nhập.")
    ap.add_argument("--tai-khoan", default=None,
                    help="Địa chỉ GỬI ĐI — chọn tài khoản nào trong DB. Mặc định: tài "
                         "khoản mới nhất còn phiên Gmail dùng được.")
    ap.add_argument("--bo-day", action="store_true",
                    help="Gửi THÊM ~50 thư dồn cục để xem màn Lịch trình dưới tải "
                         "thật (xếp làn, chip +N, bảng ngày). Hộp thư sẽ rất lộn xộn "
                         "sau đó — đọc kỹ cảnh báo khi xem trước.")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        moi_nhat_truoc = db.query(User).order_by(User.id.desc()).all()
        if not moi_nhat_truoc:
            print("Chưa có người dùng nào trong DB. Đăng nhập vào MeoArc một lần rồi chạy lại.")
            return 1

        if args.tai_khoan:
            moi_nhat_truoc = [u for u in moi_nhat_truoc
                              if (u.email or "").lower() == args.tai_khoan.lower()]
            if not moi_nhat_truoc:
                print(f"Không có tài khoản {args.tai_khoan} trong DB.")
                return 1

        # Duyệt từ mới tới cũ, lấy tài khoản ĐẦU TIÊN còn phiên Gmail dùng được.
        # Bản trước chỉ lấy đúng người dùng mới nhất rồi bỏ cuộc — mà DB thường có
        # lẫn tài khoản test (vd qa…@example.test) nằm sau tài khoản thật, nên nó
        # báo "không có phiên" trong khi tài khoản thật vẫn đăng nhập tốt.
        user = token = None
        bo_qua: list[str] = []
        for u in moi_nhat_truoc:
            cap = _token_for_user(db, u.id)
            if cap is None:
                bo_qua.append(f"{u.email} (chưa/hết phiên đăng nhập)")
                continue
            tok, provider = cap
            if provider != "google":
                bo_qua.append(f"{u.email} (đăng nhập bằng {provider}, không phải Gmail)")
                continue
            user, token = u, tok
            break

        if user is None:
            print("Không tài khoản nào trong DB có phiên Gmail dùng được.\n")
            for d in bo_qua:
                print(f"  ✗ {d}")
            print("\nĐăng nhập vào MeoArc bằng Google rồi chạy lại.")
            return 1

        if bo_qua:
            print(f"(Bỏ qua {len(bo_qua)} tài khoản không dùng được: {', '.join(bo_qua)})\n")

        bo = list(THU_DEMO)
        if args.bo_day:
            bo += _dung_bo_day()

        nguoi_nhan = args.email or user.email
        print(f"Tài khoản : {user.email}")
        print(f"Gửi tới   : {nguoi_nhan}")
        print(f"Số thư    : {len(bo)}"
              + (f"  (8 bộ gốc + {len(bo) - len(THU_DEMO)} bộ dày)" if args.bo_day else "")
              + "\n")

        if not args.gui_that:
            for i, (nguoi_gui, tieu_de, _) in enumerate(bo, 1):
                print(f"  {i:>2}. {nguoi_gui:<26} │ {tieu_de}")
            print("\n── XEM TRƯỚC, CHƯA GỬI GÌ ──")
            print("Gửi thư là việc KHÔNG HOÀN TÁC ĐƯỢC. Chạy lại kèm --gui-that nếu chắc chắn.")
            if args.bo_day:
                _canh_bao_bo_day(len(bo), nguoi_nhan)
            return 0

        if args.bo_day:
            _canh_bao_bo_day(len(bo), nguoi_nhan)
            print()

        xong = 0
        for i, (nguoi_gui, tieu_de, than) in enumerate(bo, 1):
            try:
                gmail_send.send_email(
                    token, to=nguoi_nhan, subject=tieu_de, body=than,
                    # Địa chỉ vẫn là tài khoản đang đăng nhập — Gmail không cho gửi hộ
                    # địa chỉ lạ. Chỉ TÊN HIỂN THỊ là đổi, để thẻ lịch trình hiện
                    # "Giáo vụ HCMUS" thay vì tám thẻ cùng đề tên bạn.
                    from_addr=f'"{nguoi_gui}" <{user.email}>',
                )
                xong += 1
                print(f"  [{i}/{len(bo)}] đã gửi: {nguoi_gui} │ {tieu_de}")
            except Exception as exc:
                # Một thư hỏng KHÔNG được làm dừng cả bộ — báo rồi đi tiếp.
                print(f"  [{i}/{len(bo)}] LỖI: {tieu_de} — {exc}")
            # NGHỈ GIỮA CÁC LẦN GỬI. Bắn 50 lệnh liên tiếp rất dễ ăn 429 từ Gmail,
            # và lúc đó nửa bộ đã đi rồi nửa chưa — trạng thái tệ nhất, vì gửi lại
            # thì thành hàng đôi mà bỏ dở thì demo thiếu.
            if i < len(bo):
                time.sleep(0.4)

        print(f"\nĐã gửi {xong}/{len(bo)} thư.")
        print("Mở MeoArc, bấm nút làm mới ở khung Thư, rồi vào Lịch trình để xem.")
        if args.bo_day and xong:
            print("\nDỌN LẠI khi xong việc — mở Gmail, tìm bằng truy vấn này rồi chọn tất cả:")
            print("    from:me to:me newer_than:1d")
            print("(nhớ dọn ở CẢ Hộp thư đến lẫn Đã gửi — thư tự gửi nằm ở cả hai)")
        return 0 if xong else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
