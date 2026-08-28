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
