import type { Email } from '@/data/emails'

/* ══════════════════════════════════════════════════════════════════════════════
   THƯ DEMO CHO MÀN LỊCH TRÌNH — tháng 8 và 9

   Tách riêng khỏi `emails.ts` để bộ thư gốc (dùng cho các màn khác) không bị pha
   loãng, và để xoá bộ demo này đi chỉ cần bỏ đúng một dòng import.

   Bộ này cố ý phủ đủ BỐN tình huống mà bộ trích cam kết phải xử lý đúng — đó là
   thứ đáng cho người chấm thấy, chứ không phải "có vài lá thư cho đỡ trống":

     • ngày tuyệt đối          — "trước 17:00 ngày 5/9"
     • thứ trong tuần          — "8h thứ Ba tuần sau"
     • hạn phải TÍNH RA        — "trong vòng 3 ngày làm việc"
     • việc DÀI nhiều giờ      — báo cáo Testing → thẻ trải ngang nhiều ngày

   Và HAI thư KHÔNG phải cam kết dù có ngày tháng (thư sale 9/9, lời mời sinh
   nhật 15/9). Chúng ở đây để trả lời câu hỏi khó nhất khi trình bày — "làm sao
   nó biết cái nào là việc?" — bằng cách cho thấy bộ lọc BỎ QUA chúng.
   ══════════════════════════════════════════════════════════════════════════════ */

const TOI = 'Anh Quân <meoarc.hcmus@gmail.com>'

export const DEMO_LICH: Email[] = [
  {
    id: 'd1', sender: 'Phòng Đào tạo HCMUS', senderEmail: 'daotao@hcmus.edu.vn',
    senderInitial: 'P', to: TOI,
    subject: 'Đăng ký học phần HK1 2026-2027',
    preview: 'Sinh viên hoàn tất đăng ký học phần trước 17:00 ngày 5/9…',
    body: [
      'Chào các em,',
      'Sinh viên hoàn tất đăng ký học phần học kỳ 1 năm học 2026-2027 trên cổng thông tin trước 17:00 ngày 5/9. Sau thời hạn này hệ thống sẽ khoá, các trường hợp bổ sung phải làm đơn.',
      'Lưu ý kiểm tra kỹ số tín chỉ tối thiểu và các môn tiên quyết trước khi xác nhận.',
    ],
    time: '09:15', date: '20/08/2026', unread: true, starred: true,
    category: 'moss', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Hạn đăng ký học phần HK1: 17:00 ngày 5/9, sau đó hệ thống khoá.',
  },
  {
    id: 'd2', sender: 'GVHD Nguyễn Văn Sơn', senderEmail: 'nvson@fit.hcmus.edu.vn',
    senderInitial: 'S', to: TOI,
    subject: 'Lịch bảo vệ đồ án Nhập môn CNPM',
    preview: 'Nhóm 7 chuẩn bị slide và demo, bảo vệ 8h thứ Ba tuần sau…',
    body: [
      'Chào em Quân,',
      'Nhóm 7 chuẩn bị slide và bản demo chạy được. Buổi bảo vệ diễn ra lúc 8h thứ Ba tuần sau tại phòng I.53.',
      'Mỗi nhóm trình bày 15 phút, hỏi đáp 10 phút. Nhớ gửi slide cho thầy trước một ngày.',
    ],
    time: '14:30', date: '26/08/2026', unread: true, starred: true,
    category: 'sea', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Bảo vệ đồ án 8h thứ Ba tuần sau, phòng I.53. Gửi slide trước một ngày.',
  },
  {
    id: 'd3', sender: 'Ban tổ chức Hackathon', senderEmail: 'contact@vnhackathon.dev',
    senderInitial: 'B', to: TOI,
    subject: 'Xác nhận tham dự vòng chung kết 12/09',
    preview: 'Vui lòng xác nhận tham dự trong vòng 3 ngày làm việc…',
    body: [
      'Xin chào đội MeoArc,',
      'Đội của bạn đã lọt vào vòng chung kết ngày 12/09 tại Đà Nẵng. Vui lòng xác nhận tham dự trong vòng 3 ngày làm việc kể từ khi nhận thư này.',
      'Ban tổ chức hỗ trợ chi phí đi lại cho tối đa 3 thành viên mỗi đội.',
    ],
    time: '11:02', date: '28/08/2026', unread: true, starred: false,
    category: 'sun', label: 'Cá nhân', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Xác nhận dự chung kết Hackathon 12/09 — hạn trong 3 ngày làm việc.',
  },
  {
    id: 'd4', sender: 'Giáo vụ HCMUS', senderEmail: 'giaovu@fit.hcmus.edu.vn',
    senderInitial: 'G', to: TOI,
    subject: 'Nộp báo cáo Testing (PA3) — Nhóm 7',
    preview: 'Các nhóm nộp báo cáo Testing đầy đủ trước 23:59 ngày 18/9…',
    body: [
      'Chào các em,',
      'Các nhóm nộp báo cáo Testing (PA3) đầy đủ lên Moodle trước 23:59 ngày 18/9, kèm minh chứng chạy test và bảng phân công công việc của từng thành viên.',
      'Báo cáo cần có đủ: kế hoạch kiểm thử, đặc tả ca kiểm thử cho toàn bộ use case đã đăng ký, kết quả chạy thực tế, phần đánh giá độ phủ, và phụ lục minh chứng.',
      'Đây là hạng mục chiếm trọng số lớn nhất của học phần. Các em bố trí thời gian sớm, đừng để dồn vào tuần cuối.',
    ],
    time: '08:00', date: '02/09/2026', unread: true, starred: true,
    category: 'moss', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Hạn nộp báo cáo Testing PA3: 23:59 ngày 18/9, kèm minh chứng chạy test.',
  },
  {
    id: 'd5', sender: 'Trần Minh Khoa', senderEmail: 'khoa.tran@gmail.com',
    senderInitial: 'K', to: TOI,
    subject: 'Re: Chia việc phần backend tuần này',
    preview: 'Mình nhận phần MCP, bạn gửi lại đặc tả tool trước thứ Năm nhé…',
    body: [
      'Ok bạn,',
      'Mình nhận phần MCP server. Bạn gửi lại đặc tả tool trước thứ Năm để mình còn kịp làm.',
      'Phần confirm-gate mình thấy nên gom về một chỗ, tránh mỗi tool tự làm một kiểu rồi khó kiểm.',
    ],
    time: '20:41', date: '30/08/2026', unread: false, starred: false,
    category: 'cherry', label: 'Cá nhân', folder: 'inbox',
    priority: 'Medium', status: 'Todo',
    tldr: 'Gửi đặc tả tool MCP cho Khoa trước thứ Năm.',
  },
  {
    id: 'd6', sender: 'Phòng CTSV', senderEmail: 'ctsv@hcmus.edu.vn',
    senderInitial: 'C', to: TOI,
    subject: 'Đóng học phí học kỳ 1',
    preview: 'Sinh viên hoàn tất đóng học phí trước ngày 25/9…',
    body: [
      'Thông báo,',
      'Sinh viên hoàn tất đóng học phí học kỳ 1 trước ngày 25/9 qua cổng thanh toán của trường.',
      'Quá hạn sẽ bị khoá kết quả học tập cho tới khi hoàn tất nghĩa vụ tài chính.',
    ],
    time: '10:20', date: '05/09/2026', unread: true, starred: false,
    category: 'terra', label: 'Tài chính', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Hạn đóng học phí HK1: ngày 25/9, quá hạn bị khoá kết quả.',
  },

  /* ── BA VIỆC DỒN VÀO CÙNG MỘT NGÀY (10/9) ──
     Đây là tình huống làm vỡ mọi thiết kế lịch ẩu, nên phải có trong bộ demo:
     một ngày nhiều việc thì lưới có méo không, chữ có bị nuốt không, và người
     dùng có đọc được cái nào quan trọng hơn không. */
  {
    id: 'd9', sender: 'Nguyễn Hoàng Anh', senderEmail: 'hoanganh@fit.hcmus.edu.vn',
    senderInitial: 'H', to: TOI,
    subject: 'Bản vẽ kiến trúc hệ thống — hạn 10/9',
    preview: 'Nhóm nộp bản vẽ kiến trúc trước 23:59 ngày 10/9…',
    body: [
      'Chào nhóm 7,',
      'Nhóm nộp bản vẽ kiến trúc hệ thống trước 23:59 ngày 10/9, gồm sơ đồ thành phần, sơ đồ tuần tự cho ba luồng chính, và bản mô tả lựa chọn công nghệ kèm lý do.',
      'Phần mô tả lựa chọn công nghệ cần nói rõ vì sao chọn, đã cân nhắc phương án nào khác, và đánh đổi là gì. Đây là phần các nhóm hay làm sơ sài nhất.',
    ],
    time: '09:40', date: '04/09/2026', unread: true, starred: false,
    category: 'sea', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Nộp bản vẽ kiến trúc hệ thống trước 23:59 ngày 10/9.',
  },
  {
    id: 'd10', sender: 'CLB Học thuật', senderEmail: 'clb@fit.hcmus.edu.vn',
    senderInitial: 'C', to: TOI,
    subject: 'Seminar sáng 10/9 — gửi slide',
    preview: 'Bạn trình bày lúc 9h ngày 10/9, gửi slide trước…',
    body: [
      'Chào bạn, bạn trình bày lúc 9h ngày 10/9 tại phòng E203. Gửi slide cho ban tổ chức trước một hôm để chiếu thử.',
    ],
    time: '16:10', date: '05/09/2026', unread: false, starred: false,
    category: 'sky', label: 'Hoạt động', folder: 'inbox',
    priority: 'Medium', status: 'Todo',
    tldr: 'Trình bày seminar 9h ngày 10/9, gửi slide trước một hôm.',
  },
  {
    id: 'd11', sender: 'Trần Minh Khoa', senderEmail: 'khoa.tran@gmail.com',
    senderInitial: 'K', to: TOI,
    subject: 'Kiểm thử tích hợp — cần xong trước 10/9',
    preview: 'Mình cần bạn hoàn thành phần kiểm thử tích hợp trước ngày 10/9…',
    body: [
      'Bạn ơi,',
      'Mình cần bạn hoàn thành phần kiểm thử tích hợp trước ngày 10/9 để mình còn ghép vào bản báo cáo. Phần này gồm ca kiểm thử cho luồng đăng nhập, luồng đồng bộ thư, và luồng gọi agent.',
      'Mỗi luồng cần ít nhất một ca thuận và hai ca nghịch, kèm ảnh chụp kết quả chạy thật. Riêng luồng đồng bộ nhớ thêm ca mạng đứt giữa chừng, vì đó là chỗ hay hỏng nhất mà lại chưa ai kiểm.',
      'Nếu kẹt phần nào thì nhắn sớm, đừng để tới sát ngày. Tuần trước mình đã mất hai hôm chỉ để dựng lại môi trường chạy test nên biết nó tốn thời gian hơn mình tưởng.',
    ],
    time: '21:15', date: '03/09/2026', unread: true, starred: false,
    category: 'cherry', label: 'Công việc', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Hoàn thành kiểm thử tích hợp trước ngày 10/9 để Khoa ghép báo cáo.',
  },

  /* ── MỘT VIỆC KÉO DÀI NHIỀU NGÀY ──
     Thư dài + ưu tiên cao → ước lượng 480 phút → trải 3 ngày. Đây là thứ cuốn
     lịch thường vẽ thành MỘT CHẤM ở ngày hạn, và cũng chính là lý do người ta
     hay vỡ kế hoạch: nhìn thấy một chấm ở 16/9 thì tưởng đó là việc của 16/9. */
  {
    id: 'd12', sender: 'Giáo vụ HCMUS', senderEmail: 'giaovu@fit.hcmus.edu.vn',
    senderInitial: 'G', to: TOI,
    subject: 'Tài liệu SRS bản cuối — nộp trước 17:00 ngày 16/9',
    preview: 'Các nhóm nộp tài liệu SRS bản cuối trước 17:00 ngày 16/9…',
    body: [
      'Chào các em,',
      'Các nhóm nộp tài liệu SRS bản cuối trước 17:00 ngày 16/9. Đây là bản dùng để chấm, không nhận bản bổ sung sau thời hạn, nên các em kiểm tra kỹ trước khi nộp.',
      'Tài liệu cần đầy đủ các phần sau. Phần mở đầu gồm mục đích, phạm vi, định nghĩa thuật ngữ và tài liệu tham chiếu. Phần mô tả tổng quan gồm bối cảnh sản phẩm, các chức năng chính, đặc điểm người dùng, ràng buộc thiết kế, giả định và phụ thuộc.',
      'Phần đặc tả yêu cầu là phần nặng nhất và cũng là phần bị trừ điểm nhiều nhất. Mỗi use case phải có đủ tác nhân, tiền điều kiện, hậu điều kiện, luồng chính, luồng thay thế và luồng ngoại lệ. Luồng ngoại lệ là chỗ các nhóm hay bỏ trống, trong khi đó mới là chỗ thể hiện các em đã nghĩ tới trường hợp hỏng hay chưa.',
      'Yêu cầu phi chức năng phải đo được. Viết "hệ thống phải nhanh" là không chấp nhận được; phải viết thành ngưỡng cụ thể, ví dụ thời gian phản hồi trung bình dưới hai giây với một trăm người dùng đồng thời. Mỗi yêu cầu phi chức năng cần nói rõ đo bằng cách nào.',
      'Phần mô hình hoá cần sơ đồ use case tổng thể, sơ đồ lớp cho miền nghiệp vụ, và sơ đồ tuần tự cho ít nhất ba use case phức tạp nhất. Các sơ đồ phải khớp với phần đặc tả chữ; nhóm nào để sơ đồ nói một đằng chữ nói một nẻo sẽ bị trừ nặng.',
      'Cuối cùng là phụ lục gồm bảng phân công công việc theo từng thành viên, biên bản các buổi họp nhóm, và ảnh chụp giao diện đã dựng. Bảng phân công phải ghi rõ ai làm phần nào và chiếm bao nhiêu phần trăm khối lượng.',
      'Các em bắt đầu sớm. Kinh nghiệm các khoá trước cho thấy phần đặc tả use case tốn nhiều thời gian hơn mọi người dự tính, và dồn vào hai ngày cuối thì chất lượng rơi thấy rõ.',
      'Trân trọng, Phòng Giáo vụ',
    ],
    time: '07:50', date: '06/09/2026', unread: true, starred: true,
    category: 'moss', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Nộp SRS bản cuối trước 17:00 ngày 16/9 — bản dùng để chấm, không nhận bổ sung.',
  },

  /* ── MỘT ĐỢT KÉO DÀI NHIỀU TUẦN ──
     Khoảng ngày thư NÓI THẲNG ("từ ngày 7/9 đến ngày 25/9"), không phải suy ra từ
     ước lượng thời lượng. Đây là tình huống lưới tháng phải vẽ một đợt VẮT QUA BA
     HÀNG TUẦN: hàng đầu có góc bo trái và mang chữ, hai hàng sau mở bằng dấu "‹"
     và không bo trái, hàng cuối bo phải và mang giờ hạn. */
  {
    id: 'd13', sender: 'Phòng Quan hệ Doanh nghiệp', senderEmail: 'qhdn@fit.hcmus.edu.vn',
    senderInitial: 'Q', to: TOI,
    subject: 'Đợt thực tập doanh nghiệp 7/9 – 25/9',
    preview: 'Đợt thực tập diễn ra từ ngày 7/9 đến ngày 25/9…',
    body: [
      'Chào các em,',
      'Đợt thực tập doanh nghiệp diễn ra từ ngày 7/9 đến ngày 25/9. Các em có mặt tại đơn vị theo lịch đã đăng ký và nộp nhật ký thực tập hằng tuần cho giảng viên hướng dẫn.',
      'Cuối đợt nộp báo cáo thực tập có xác nhận của đơn vị tiếp nhận.',
    ],
    time: '08:30', date: '01/09/2026', unread: true, starred: true,
    category: 'sea', label: 'Học tập', folder: 'inbox',
    priority: 'High', status: 'Todo',
    tldr: 'Thực tập doanh nghiệp từ 7/9 đến 25/9, nộp nhật ký hằng tuần.',
  },

  /* ── MỘT NGÀY QUÁ TẢI (10/9) ──
     Bốn việc nữa dồn vào đúng ngày đã có ba việc, thành BẢY. Lưới chỉ vẽ được ba
     làn nên bốn cái còn lại phải đi đâu đó — đó chính là chỗ "+4" và bảng ngày
     tồn tại. Không có tình huống này trong bộ demo thì phần xử lý tràn không bao
     giờ được nhìn thấy, và cũng không ai kiểm được nó có đúng không. */
  {
    id: 'd14', sender: 'Thư viện HCMUS', senderEmail: 'thuvien@hcmus.edu.vn',
    senderInitial: 'T', to: TOI,
    subject: 'Trả sách mượn quá hạn',
    preview: 'Bạn hoàn tất trả sách trước ngày 10/9…',
    body: ['Bạn hoàn tất trả sách mượn trước ngày 10/9 để tránh phí phạt quá hạn.'],
    time: '08:05', date: '06/09/2026', unread: true, starred: false,
    category: 'terra', label: 'Hành chính', folder: 'inbox',
    priority: 'Low', status: 'Todo',
    tldr: 'Trả sách thư viện trước ngày 10/9.',
  },
  {
    id: 'd15', sender: 'Đoàn khoa CNTT', senderEmail: 'doankhoa@fit.hcmus.edu.vn',
    senderInitial: 'Đ', to: TOI,
    subject: 'Đăng ký hiến máu đợt tháng 9',
    preview: 'Đăng ký trước ngày 10/9 nếu tham gia…',
    body: ['Bạn đăng ký tham gia hiến máu trước ngày 10/9 qua biểu mẫu của Đoàn khoa.'],
    time: '14:20', date: '06/09/2026', unread: false, starred: false,
    category: 'cherry', label: 'Hoạt động', folder: 'inbox',
    priority: 'Low', status: 'Todo',
    tldr: 'Đăng ký hiến máu trước ngày 10/9.',
  },
  {
    id: 'd16', sender: 'Nguyễn Hoàng Anh', senderEmail: 'hoanganh@fit.hcmus.edu.vn',
    senderInitial: 'H', to: TOI,
    subject: 'Phản hồi bản nháp chương 3',
    preview: 'Gửi lại phản hồi cho mình trước 10/9…',
    body: [
      'Mình đã đọc bản nháp chương 3. Bạn gửi lại phản hồi cho mình trước ngày 10/9 để kịp gộp vào bản chung.',
      'Mấy chỗ mình đánh dấu vàng là chỗ cần bạn xác nhận lại số liệu.',
    ],
    time: '19:45', date: '07/09/2026', unread: true, starred: false,
    category: 'sea', label: 'Công việc', folder: 'inbox',
    priority: 'Medium', status: 'Todo',
    tldr: 'Gửi phản hồi bản nháp chương 3 trước ngày 10/9.',
  },
  {
    id: 'd17', sender: 'Phòng Công tác Sinh viên', senderEmail: 'ctsv@hcmus.edu.vn',
    senderInitial: 'C', to: TOI,
    subject: 'Nộp đơn xin xác nhận sinh viên',
    preview: 'Nộp đơn trước ngày 10/9 để kịp xử lý…',
    body: ['Sinh viên nộp đơn xin xác nhận trước ngày 10/9 để phòng kịp xử lý trong tuần.'],
    time: '10:00', date: '07/09/2026', unread: false, starred: false,
    category: 'moss', label: 'Hành chính', folder: 'inbox',
    priority: 'Low', status: 'Todo',
    tldr: 'Nộp đơn xin xác nhận sinh viên trước ngày 10/9.',
  },

  /* ── HAI THƯ KHÔNG PHẢI CAM KẾT ──
     Cả hai đều CÓ ngày tháng nhưng KHÔNG có nghĩa vụ nào. Bộ trích phải bỏ qua
     chúng, và đó chính là chỗ chứng minh nó không nhận bừa mọi thứ có con số. */
  {
    id: 'd7', sender: 'Shopee', senderEmail: 'no-reply@shopee.vn',
    senderInitial: 'S', to: TOI,
    subject: 'Sale 9.9 — giảm đến 50% ngày 9/9',
    preview: 'Đừng bỏ lỡ ngày hội mua sắm 9/9…',
    body: ['Đừng bỏ lỡ ngày hội mua sắm 9/9 với hàng ngàn ưu đãi giảm đến 50% toàn sàn.'],
    time: '07:00', date: '01/09/2026', unread: true, starred: false,
    category: 'wine', label: 'Mua sắm', folder: 'inbox',
  },
  {
    id: 'd8', sender: 'Lê Thu Hà', senderEmail: 'ha.le@gmail.com',
    senderInitial: 'H', to: TOI,
    subject: 'Sinh nhật mình 15/9 nhé',
    preview: 'Mình tổ chức nhỏ ở nhà, hẹn gặp lại mọi người ngày 15/9…',
    body: ['Mình tổ chức nhỏ ở nhà, hẹn gặp lại mọi người ngày 15/9 nha. Không cần mang gì đâu.'],
    time: '19:30', date: '03/09/2026', unread: false, starred: false,
    category: 'sky', label: 'Cá nhân', folder: 'inbox',
  },
]
