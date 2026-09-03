"""BỘ THƯ ĐỂ QUAY DEMO — mọi mốc thời gian tính theo LÚC CHẠY, không phải ngày cứng.

── VÌ SAO PHẢI TÍNH ĐỘNG ──
Bộ thư cũ ghi cứng "trước 18/9", "ngày 12/09"… Chạy đúng đầu tháng 9 thì hợp lý; chạy
muộn hai tuần là mọi hạn đều đã qua, và câu hỏi "tuần này tôi có gì?" trả về rỗng
trong khi màn hình vẫn đầy thư. Người xem không hiểu nổi vì sao, còn người trình bày
thì không kịp sửa.

Ở đây mỗi mốc là một khoảng cách so với HÔM NAY. Chạy lúc nào cũng khớp.

── DỮ LIỆU PHẢI ĂN NHẬP VỚI CÂU HỎI ──
Mỗi thư dưới đây tồn tại để phục vụ ít nhất một câu hỏi trong `docs/kich-ban-quay-demo.md`,
và mỗi câu hỏi trong tài liệu đó đều có thư đỡ. Nhãn `# → Q3` ở mỗi nhóm là mối nối
đó. Chạy `scripts/kiem_bo_quay_demo.py` để MÁY tự kiểm lại mối nối, đừng tin vào việc
đọc bằng mắt — bộ thư và bộ câu hỏi trôi xa nhau rất dễ mà không ai nhận ra.

── CÔNG THỨC "NGÀY QUÁ TẢI" ──
Trần một ngày là 360 phút (`cam_ket.TRAN_MOI_NGAY`). Ước lượng: thư trên 90 chữ = 60
phút, nhân đôi nếu KHẨN (`labeling._PAT_GAP`: "hạn chót", "gấp", "hôm nay", "ngày
mai"…). Nên bốn thư trên 90 chữ, có chữ "hạn chót", cùng hạn một ngày = 480 phút →
ngày đó chắc chắn đỏ. Đó là lý do nhóm A có đúng bốn thư và đều dài như nhau.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")


def _moc() -> datetime:
    return datetime.now(_TZ_VN)


def bo_thu(moc: datetime | None = None) -> list[tuple[str, str, str]]:
    """Trả (tên người gửi, tiêu đề, thân thư). Thứ tự = thứ tự GỬI.

    Thư CUỐI CÙNG trong danh sách là thư MỚI NHẤT trong hộp thư sau khi gửi xong —
    câu hỏi "tóm tắt lá thư mới nhất" bám vào đúng nó, nên đừng đổi chỗ."""
    n = moc or _moc()

    def d(k: int) -> str:
        """Ngày cách hôm nay k hôm, dạng 'dd/mm'."""
        return (n + timedelta(days=k)).strftime("%d/%m")

    THU = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ nhật"]

    def t(k: int) -> str:
        return THU[(n + timedelta(days=k)).weekday()]

    return [
        # ══════════════════════════════════════════════════════════════════
        # NHÓM A — BỐN VIỆC CÙNG HẠN NGÀY MAI  → tạo NGÀY QUÁ TẢI
        # → Q4 "tuần này tôi có bị quá tải không?"  · Q3 "tuần này lịch trình"
        # Mỗi thư >90 chữ và có "hạn chót" nên được tính 120 phút; bốn thư = 480 > 360.
        # ══════════════════════════════════════════════════════════════════
        (
            "Giáo vụ HCMUS",
            f"[Hạn chót {d(1)}] Nộp báo cáo Testing PA3 — Nhóm 7",
            "Chào các em,\n\n"
            f"Hạn chót nộp báo cáo Testing (PA3) là 23:59 ngày {d(1)} ({t(1)}). Các nhóm "
            "nộp đầy đủ lên Moodle, kèm minh chứng chạy test và bảng phân công công việc "
            "của từng thành viên.\n\n"
            "Báo cáo cần có đủ các phần: kế hoạch kiểm thử, đặc tả ca kiểm thử cho toàn "
            "bộ use case đã đăng ký, kết quả chạy thực tế, phần đánh giá độ phủ, và phụ "
            "lục minh chứng. Nhóm nào dùng công cụ tự động thì đính kèm cả cấu hình và "
            "log chạy để thầy đối chiếu.\n\n"
            "Về quy cách nộp: đặt tên tệp theo mẫu Nhom07_PA3_Testing.pdf, phần phụ lục "
            "gộp chung vào một tệp nén riêng. Nhóm nào nộp nhiều tệp rời sẽ được yêu cầu "
            "nộp lại, và thời điểm tính hạn là lần nộp cuối cùng chứ không phải lần đầu.\n\n"
            "Về nội dung, thầy cô nhắc lại hai chỗ các nhóm khoá trước hay mất điểm nhất. "
            "Thứ nhất là bảng đặc tả ca kiểm thử chỉ ghi đầu vào mà không ghi kết quả "
            "mong đợi, khiến người chấm không đối chiếu được. Thứ hai là phần đánh giá độ "
            "phủ chỉ đưa một con số phần trăm mà không nói phần nào chưa phủ và vì sao. "
            "Một con số không kèm giải thích thì không chứng minh được điều gì cả.\n\n"
            "Đây là hạng mục chiếm trọng số lớn nhất của học phần nên các em bố trí thời "
            "gian sớm, đừng dồn vào buổi cuối. Nhóm nộp trễ sẽ bị trừ điểm theo quy định "
            "đã công bố đầu kỳ, không có ngoại lệ. Em nào có lý do đặc biệt thì liên hệ "
            "giáo vụ TRƯỚC hạn, sau hạn thì không giải quyết được nữa.\n\n"
            "Giáo vụ",
        ),
        (
            "GVHD Nguyễn Văn Sơn",
            f"[Hạn chót {d(1)}] Gửi slide bảo vệ đồ án trước buổi trình bày",
            "Chào em,\n\n"
            f"Hạn chót gửi slide là 17:00 ngày {d(1)}. Thầy cần xem trước để góp ý, nên "
            "em gửi đúng hạn giúp thầy.\n\n"
            "Slide nên đi theo mạch: bài toán và người dùng thật, kiến trúc tổng thể, "
            "phần nào nhóm tự làm và phần nào dùng thư viện, rồi tới demo. Phần demo nên "
            "quay sẵn một bản dự phòng phòng khi mạng ở phòng hội đồng chậm.\n\n"
            "Em nhớ chuẩn bị câu trả lời cho hai câu thầy chắc chắn sẽ hỏi: hệ thống xử "
            "lý thế nào khi mô hình trả lời sai, và dữ liệu người dùng được bảo vệ ra "
            "sao. Hai câu đó phân biệt nhóm hiểu việc mình làm với nhóm chỉ ghép thư "
            "viện lại.\n\n"
            "Thầy góp ý thêm về cách trình bày. Đừng dành quá nhiều thời gian cho phần "
            "giới thiệu bối cảnh, hội đồng đã đọc đề cương rồi. Vào thẳng chỗ nhóm giải "
            "quyết được vấn đề gì mà cách làm thông thường không giải quyết được, đó mới "
            "là phần đáng nghe. Mỗi slide giữ một ý, chữ to, và tuyệt đối không đọc lại "
            "nguyên văn slide.\n\n"
            "Phần demo em nên chọn đúng ba tình huống: một tình huống chạy trơn để người "
            "xem hiểu luồng, một tình huống hệ thống từ chối làm vì rủi ro, và một tình "
            "huống dữ liệu thiếu để cho thấy nó xử lý ra sao. Tình huống thứ hai và thứ "
            "ba mới là chỗ ghi điểm, vì nó chứng minh nhóm đã nghĩ tới lúc mọi thứ không "
            "diễn ra như ý.\n\n"
            "GVHD",
        ),
        (
            "Phòng Đào tạo HCMUS",
            f"[Hạn chót {d(1)}] Đăng ký học phần học kỳ 1",
            "Chào các em,\n\n"
            f"Hạn chót đăng ký học phần học kỳ 1 là 17:00 ngày {d(1)}. Sau thời điểm này "
            "hệ thống khoá lại, mọi trường hợp bổ sung phải làm đơn và chờ duyệt.\n\n"
            "Các em kiểm tra kỹ số tín chỉ tối thiểu, các môn tiên quyết, và lịch trùng "
            "giữa các lớp trước khi bấm xác nhận. Năm ngoái có khá nhiều trường hợp đăng "
            "ký xong mới phát hiện trùng lịch thi, và lúc đó không đổi được nữa.\n\n"
            "Sinh viên năm cuối lưu ý đăng ký đủ phần thực tập tốt nghiệp, vì đây là điều "
            "kiện xét tốt nghiệp đúng hạn. Trường hợp đã đi thực tập ngoài doanh nghiệp "
            "thì vẫn phải đăng ký học phần tương ứng, nếu không hệ thống sẽ không ghi "
            "nhận kết quả.\n\n"
            "Về mức thu, số tiền được tính theo số tín chỉ đã đăng ký tại thời điểm khoá "
            "hệ thống. Sinh viên rút bớt môn sau khi khoá vẫn phải đóng đủ phần đã đăng "
            "ký, nên các em cân nhắc kỹ khối lượng trước khi xác nhận. Kinh nghiệm các "
            "khoá trước là đừng đăng ký quá 22 tín chỉ nếu học kỳ đó còn làm đồ án.\n\n"
            "Danh sách lớp và phòng học sẽ công bố trong vòng ba ngày làm việc sau khi "
            "khoá đăng ký. Các em theo dõi thông báo trên cổng thông tin, phòng không gửi "
            "thư riêng cho từng trường hợp.\n\n"
            "Phòng Đào tạo",
        ),
        (
            "Trần Minh Khoa",
            f"Re: Đặc tả tool MCP — cần gấp trước {d(1)}",
            "Ok bạn,\n\n"
            f"Mình nhận phần MCP server. Bạn gửi lại đặc tả tool trước ngày {d(1)} để "
            "mình còn kịp làm, phần này gấp vì nó chặn cả hai người còn lại.\n\n"
            "Mình đề nghị gom phần confirm-gate về một chỗ thay vì để mỗi tool tự làm một "
            "kiểu. Làm rải rác thì lúc thêm tool mới rất dễ quên, mà quên đúng chỗ đó thì "
            "hệ thống gửi thư đi mà không hỏi ai — lỗi tệ nhất có thể có.\n\n"
            "Bạn cũng xem giúp phần đặt tên tham số cho thống nhất. Hiện có chỗ dùng "
            "camelCase, chỗ dùng snake_case, và mô hình sẽ gọi sai ở đúng những chỗ lệch "
            "đó. Mình đã gặp hai lần model sinh ra tên trường không tồn tại, cả hai lần "
            "đều rơi đúng vào tool có tên tham số lệch quy ước.\n\n"
            "Trong đặc tả, mỗi tool bạn ghi giúp mình bốn thứ: tham số bắt buộc và tham "
            "số tuỳ chọn, giá trị trả về khi thành công, hình dạng lỗi khi thất bại, và "
            "quan trọng nhất là tool đó có gây hậu quả ra bên ngoài hay không. Cái cuối "
            "quyết định nó có phải đi qua cổng xác nhận hay không, mà nhìn vào tên hàm "
            "thì không đoán được.\n\n"
            "Phần mô tả dành cho model thì bạn viết bằng câu mệnh lệnh ngắn, đừng viết "
            "kiểu tài liệu cho người đọc. Mình thử rồi: mô tả càng dài dòng thì model "
            "càng hay gọi nhầm tool, chắc vì nó bắt được nhiều từ khoá không liên quan.\n\n"
            "Khoa",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM B — VIỆC HÔM NAY và TRONG TUẦN
        # → Q3 "tuần này lịch trình"  · Q2 "thư nào cần xử lý trước"
        # ══════════════════════════════════════════════════════════════════
        (
            "Thư ký khoa CNTT",
            "Xác nhận danh sách thành viên nhóm trong hôm nay",
            "Chào em,\n\n"
            "Khoa cần em xác nhận lại danh sách thành viên Nhóm 7 trước 16:00 hôm nay để "
            "kịp chốt danh sách hội đồng. Em phản hồi thẳng thư này là được.\n\n"
            "Nếu có thay đổi thành viên so với đăng ký đầu kỳ thì ghi rõ lý do.",
        ),
        (
            "Phòng CTSV",
            f"Thanh toán học phí học kỳ 1 trước {d(2)}",
            "Thông báo,\n\n"
            f"Sinh viên hoàn tất thanh toán học phí học kỳ 1 trước ngày {d(2)} qua cổng "
            "thanh toán của trường.\n\n"
            "Quá hạn sẽ bị khoá kết quả học tập cho tới khi hoàn tất. Sinh viên thuộc "
            "diện miễn giảm nộp đơn tại phòng CTSV trước hạn trên.\n\n"
            "Phòng CTSV",
        ),
        (
            "CLB Tin học HCMUS",
            f"Xác nhận tham dự workshop {d(3)}",
            "Chào bạn,\n\n"
            f"CLB tổ chức workshop về kiểm thử tự động vào {t(3)} ngày {d(3)} tại phòng "
            "C42. Bạn vui lòng xác nhận tham dự để CLB chuẩn bị chỗ ngồi.\n\n"
            "Workshop miễn phí cho sinh viên trong trường.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM C — PHẢI ĐI XA  → Q6 "mình cần đi công tác cho việc nào không?"
        # Có TÊN THÀNH PHỐ khác nơi ở + ngày rõ ràng thì bộ suy ý định mới nhận.
        # ══════════════════════════════════════════════════════════════════
        (
            "Ban tổ chức Hackathon",
            f"Xác nhận tham dự vòng chung kết {d(9)} tại Đà Nẵng",
            "Xin chào đội MeoArc,\n\n"
            f"Đội của bạn đã lọt vào vòng chung kết diễn ra ngày {d(9)} tại Đà Nẵng. Vui "
            "lòng xác nhận tham dự trong vòng 3 ngày làm việc kể từ khi nhận thư.\n\n"
            "Ban tổ chức hỗ trợ chi phí đi lại cho tối đa 3 thành viên mỗi đội. Đội cần "
            "có mặt tại địa điểm trước 7:30 sáng để nhận thẻ và kiểm tra thiết bị.",
        ),
        (
            "Ban tổ chức Hội thảo SV",
            f"Hội thảo sinh viên toàn quốc {d(17)} tại Hà Nội",
            "Chào bạn,\n\n"
            f"Hội thảo sinh viên toàn quốc năm nay diễn ra ngày {d(17)} tại Hà Nội. Bạn "
            f"đăng ký trước ngày {d(12)} nếu muốn tham gia trình bày poster.\n\n"
            "Ban tổ chức có hỗ trợ một phần chi phí cho sinh viên ở xa.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM D — HỌC PHÍ và CÁI BẪY "MIỄN PHÍ"
        # → Q7 "tìm thư về học phí". Thư bẫy PHẢI KHÔNG được lọt vào kết quả:
        #   Gmail tách "học phí" thành hai từ rời nên nó khớp cả "MIỄN PHÍ" nếu không
        #   bọc nguyên cụm. Đây là chỗ chứng minh bản sửa đó có tác dụng thật.
        # ══════════════════════════════════════════════════════════════════
        (
            "Ngân hàng ACB",
            "Biên lai thanh toán học phí",
            "Kính gửi Quý khách,\n\n"
            "Giao dịch thanh toán học phí của Quý khách đã được ghi nhận thành công. Vui "
            "lòng lưu biên lai này để đối chiếu khi cần.\n\n"
            "Trân trọng.",
        ),
        (
            "EduMax Academy",
            "🔥 Khoá học lập trình MIỄN PHÍ 100% — chỉ còn 2 ngày!",
            # ── KHÔNG ĐƯỢC CHỨA ĐỘNG TỪ CAM KẾT KÈM MỐC THỜI GIAN ──
            # Bản đầu viết "Đăng ký ngay hôm nay…" nên bộ trích nhận nó thành một VIỆC
            # PHẢI LÀM và nó chen vào giữa danh sách lịch trình. Đã thấy tận mắt khi chạy
            # thật: "🔥 Khoá học lập trình MIỄN PHÍ 100%" nằm ngay dòng thứ hai của thẻ
            # Lịch trình. Trên máy quay thì đó là lỗi rất khó chống chế.
            # Thư này chỉ cần làm bẫy cho phép TÌM KIẾM, không cần giục ai làm gì.
            "Đừng bỏ lỡ!\n\n"
            "Trọn bộ khoá học lập trình MIỄN PHÍ, không mất một đồng học phí nào. Ưu đãi "
            "dành cho 100 người sớm nhất.\n\n"
            "Nhấn vào đây để xem chi tiết.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM E — QUẢNG CÁO  → Q8 "xoá hết thư quảng cáo" (demo cổng xác nhận)
        # ══════════════════════════════════════════════════════════════════
        (
            "Shopee",
            "Sale 9.9 — giảm đến 50% toàn sàn",
            "Ngày hội mua sắm 9.9 đã bắt đầu!\n\n"
            "Hàng ngàn ưu đãi đang chờ bạn, giảm đến 50% và freeship toàn quốc.",
        ),
        (
            "Thẻ tín dụng VIB",
            "Ưu đãi hoàn tiền 10% cho chủ thẻ",
            "Kính gửi Quý khách,\n\n"
            "Chương trình hoàn tiền 10% áp dụng cho mọi giao dịch trực tuyến trong tháng "
            "này. Không cần đăng ký.",
        ),
        (
            "TechNews Weekly",
            "Bản tin công nghệ tuần này",
            "Chào bạn,\n\n"
            "Tuần này có gì mới: mô hình ngôn ngữ mở nguồn, chip di động thế hệ mới, và "
            "một vài công cụ dành cho lập trình viên.",
        ),
        (
            "Grab",
            "Mã giảm giá 50% cho 5 chuyến tiếp theo",
            "Nhập mã GRAB50 để được giảm 50% tối đa 30.000đ cho 5 chuyến xe tiếp theo. "
            "Ưu đãi có hạn.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM F — NGƯỜI KHÁC ĐANG CHỜ MÌNH  → Q5 "tôi đang nợ ai cái gì?"
        # ══════════════════════════════════════════════════════════════════
        (
            "Phạm Thu Trang",
            "Cho mình xin lại link repo với",
            "Chào bạn,\n\n"
            f"Bạn gửi lại link repo và quyền truy cập cho mình trước {d(1)} nhé, mình cần "
            "để viết phần tài liệu kiến trúc.\n\n"
            "Cảm ơn bạn nhiều.",
        ),
        (
            "Lê Anh Đức",
            "Phản hồi giúp mình về lịch họp nhóm",
            "Hi bạn,\n\n"
            f"Bạn phản hồi giúp mình xem {t(2)} ngày {d(2)} họp nhóm được không. Mình cần "
            "chốt phòng trước khi đăng ký.\n\n"
            "Nếu bận thì báo mình dời sang đầu tuần sau.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM G — BẪY: CÓ NGÀY THÁNG NHƯNG KHÔNG PHẢI VIỆC PHẢI LÀM
        # → Q3. Đây là chỗ chứng minh bộ trích không nhận bừa mọi thứ có con số.
        # ══════════════════════════════════════════════════════════════════
        (
            "Nguyễn Hoàng Nam",
            f"Sinh nhật mình ngày {d(5)} nha",
            "Mình tổ chức nhỏ ở nhà thôi, hẹn gặp lại mọi người nha. Ai rảnh thì qua "
            "chơi, không cần mang gì cả.",
        ),
        (
            "Hệ thống HCMUS",
            f"Thông báo bảo trì hệ thống đêm {d(4)}",
            "Hệ thống sẽ tạm ngưng để bảo trì từ 23:00 đến 02:00. Trong thời gian này "
            "cổng thông tin không truy cập được. Thư này chỉ để thông báo.",
        ),
        # ══════════════════════════════════════════════════════════════════
        # NHÓM H — THƯ DÀI, GỬI CUỐI CÙNG nên là THƯ MỚI NHẤT
        # → Q9 "tóm tắt lá thư mới nhất"  · Q10 "tóm tắt thư này giúp tôi"
        # ĐỪNG ĐỔI CHỖ THƯ NÀY: câu hỏi bám vào việc nó đứng cuối.
        # ══════════════════════════════════════════════════════════════════
        (
            "Nguyễn Văn Sơn (GVHD)",
            "Biên bản họp hội đồng — những điểm nhóm cần sửa",
            "Chào các em,\n\n"
            "Thầy tóm tắt lại buổi họp hội đồng sáng nay để nhóm nắm.\n\n"
            "Thứ nhất, hội đồng đánh giá cao phần cổng xác nhận trước khi gửi thư. Đây là "
            "điểm nhóm nên nhấn mạnh khi bảo vệ, vì phần lớn các nhóm khác để mô hình gửi "
            "thẳng.\n\n"
            "Thứ hai, phần tài liệu kiến trúc còn mỏng. Hội đồng muốn thấy rõ ranh giới "
            "giữa phần nhóm tự viết và phần dùng thư viện, kèm lý do chọn từng thư viện. "
            "Các em bổ sung một sơ đồ thành phần và một đoạn giải thích quyết định thiết "
            "kế quan trọng nhất.\n\n"
            "Thứ ba, về kiểm thử: hội đồng hỏi khá kỹ chuyện đo độ phủ. Các em chuẩn bị "
            "số liệu thật, đừng nói chung chung. Nếu độ phủ chưa cao thì nói thẳng con số "
            "và giải thích phần nào chưa phủ được, như thế đáng tin hơn nhiều so với việc "
            "tránh câu hỏi.\n\n"
            "Cuối cùng, thầy nhắc lại là buổi bảo vệ chấm cả phần trả lời câu hỏi, không "
            "chỉ phần trình bày. Các em chia nhau nắm chắc từng phần để ai bị hỏi cũng "
            "trả lời được.\n\n"
            "Thầy Sơn",
        ),
    ]
