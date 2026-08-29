import type { Category, Email, Priority } from '@/data/emails'

/* ══════════════════════════════════════════════════════════════════════════════
   BỘ THƯ DÀY — để nhìn thấy màn Lịch trình DƯỚI TẢI THẬT

   Bộ demo thường có 17 việc rải đều, nên ba cơ chế xử lý quá tải gần như không
   bao giờ chạy: xếp làn, chip "+N", và bảng ngày. Không nhìn thấy chúng chạy thì
   cũng không biết chúng có đúng không — mà đó lại chính là chỗ mọi thiết kế lịch
   ẩu vỡ ra.

   Bộ này cố ý dồn cục: vài ngày có 8–10 việc, vài đợt kéo dài nhiều tuần chồng
   lên nhau, xen giữa những ngày trống để còn thấy tương phản.

   ── TẮT ĐI ──
   Sửa `BAT` thành `false` (hoặc bỏ dòng nhập ở `emails.ts`). Để bật khi trình
   bày phần xử lý quá tải, tắt khi trình bày luồng thường.
   ══════════════════════════════════════════════════════════════════════════════ */

export const BAT = true

/** [ngày/tháng, giờ hạn, người gửi, động từ + việc, ưu tiên, nhãn, màu] */
type Dong = [string, string, string, string, Priority, string, Category]

const VIEC: Dong[] = [
  // ── Tuần 7–13/9 ─────────────────────────────────────────────────────────
  ['7/9', '17:00', 'Giáo vụ HCMUS', 'nộp danh sách nhóm đồ án', 'High', 'Học tập', 'moss'],
  ['7/9', '23:59', 'Nguyễn Hoàng Anh', 'gửi bản vẽ use case cho nhóm', 'Medium', 'Công việc', 'sea'],
  ['8/9', '09:00', 'GVHD Nguyễn Văn Sơn', 'trình bày tiến độ tuần 2', 'High', 'Học tập', 'sea'],
  ['8/9', '17:00', 'Phòng Đào tạo HCMUS', 'xác nhận lịch thi giữa kỳ', 'Medium', 'Học tập', 'moss'],
  ['8/9', '23:59', 'Trần Minh Khoa', 'gửi đặc tả API cho backend', 'High', 'Công việc', 'cherry'],
  ['8/9', '23:59', 'CLB Học thuật', 'đăng ký suất trình bày seminar', 'Low', 'Hoạt động', 'sky'],
  ['9/9', '12:00', 'Thư viện HCMUS', 'gia hạn sách mượn', 'Low', 'Hành chính', 'terra'],
  ['9/9', '17:00', 'Lê Thu Hà', 'phản hồi bản thiết kế giao diện', 'Medium', 'Công việc', 'wine'],
  ['9/9', '23:59', 'Giáo vụ HCMUS', 'nộp biên bản họp nhóm tuần 2', 'Medium', 'Học tập', 'moss'],
  ['11/9', '08:00', 'Phòng CTSV', 'nộp đơn xin miễn giảm học phí', 'High', 'Hành chính', 'terra'],
  ['11/9', '17:00', 'Nguyễn Hoàng Anh', 'gửi số liệu đo hiệu năng', 'Medium', 'Công việc', 'sea'],
  ['11/9', '23:59', 'Ban tổ chức Hackathon', 'xác nhận danh sách thành viên dự thi', 'High', 'Cá nhân', 'sun'],
  ['11/9', '23:59', 'Trần Minh Khoa', 'trả lời góp ý pull request #48', 'Medium', 'Công việc', 'cherry'],
  ['11/9', '23:59', 'Đoàn khoa CNTT', 'đăng ký tham gia ngày hội việc làm', 'Low', 'Hoạt động', 'sky'],

  // ── Tuần 14–20/9: ĐỈNH ĐIỂM ─────────────────────────────────────────────
  ['14/9', '09:00', 'GVHD Nguyễn Văn Sơn', 'trình bày tiến độ tuần 3', 'High', 'Học tập', 'sea'],
  ['14/9', '17:00', 'Giáo vụ HCMUS', 'nộp phiếu tự đánh giá giữa kỳ', 'High', 'Học tập', 'moss'],
  ['14/9', '23:59', 'Lê Thu Hà', 'gửi bản dịch phần tài liệu tiếng Anh', 'Medium', 'Công việc', 'wine'],
  ['14/9', '23:59', 'Phòng Đào tạo HCMUS', 'đăng ký môn học bổ sung', 'Medium', 'Học tập', 'moss'],
  ['14/9', '23:59', 'Thư viện HCMUS', 'trả sách quá hạn đợt hai', 'Low', 'Hành chính', 'terra'],
  ['15/9', '08:30', 'Phòng Quan hệ Doanh nghiệp', 'nộp nhật ký thực tập tuần 1', 'High', 'Học tập', 'sea'],
  ['15/9', '10:00', 'Nguyễn Hoàng Anh', 'trình bày phần kiến trúc cho nhóm', 'High', 'Công việc', 'sea'],
  ['15/9', '15:00', 'Trần Minh Khoa', 'gửi kết quả chạy kiểm thử tích hợp', 'High', 'Công việc', 'cherry'],
  ['15/9', '17:00', 'Giáo vụ HCMUS', 'nộp bản mô tả ca kiểm thử', 'High', 'Học tập', 'moss'],
  ['15/9', '17:00', 'Phòng CTSV', 'xác nhận thông tin bảo hiểm y tế', 'Medium', 'Hành chính', 'terra'],
  ['15/9', '23:59', 'CLB Học thuật', 'gửi slide buổi chia sẻ kỹ thuật', 'Medium', 'Hoạt động', 'sky'],
  ['15/9', '23:59', 'Lê Thu Hà', 'phản hồi bản nháp phần mở đầu', 'Low', 'Công việc', 'wine'],
  ['15/9', '23:59', 'Đoàn khoa CNTT', 'đăng ký ca trực hỗ trợ tân sinh viên', 'Low', 'Hoạt động', 'sky'],
  ['17/9', '09:00', 'GVHD Nguyễn Văn Sơn', 'bảo vệ tiến độ giữa kỳ', 'High', 'Học tập', 'sea'],
  ['17/9', '14:00', 'Ban tổ chức Hackathon', 'trình bày sản phẩm vòng loại', 'High', 'Cá nhân', 'sun'],
  ['17/9', '17:00', 'Nguyễn Hoàng Anh', 'gửi bản cập nhật sơ đồ lớp', 'Medium', 'Công việc', 'sea'],
  ['17/9', '23:59', 'Trần Minh Khoa', 'hoàn thành phần tài liệu triển khai', 'Medium', 'Công việc', 'cherry'],
  ['17/9', '23:59', 'Phòng Đào tạo HCMUS', 'xác nhận đăng ký thi lại', 'Low', 'Học tập', 'moss'],
  ['17/9', '23:59', 'Thư viện HCMUS', 'thanh toán phí phạt quá hạn', 'Low', 'Hành chính', 'terra'],
  ['18/9', '08:00', 'Phòng Quan hệ Doanh nghiệp', 'nộp nhật ký thực tập tuần 2', 'High', 'Học tập', 'sea'],
  ['18/9', '10:00', 'Giáo vụ HCMUS', 'nộp phụ lục minh chứng kiểm thử', 'High', 'Học tập', 'moss'],
  ['18/9', '15:00', 'Lê Thu Hà', 'gửi ảnh chụp giao diện đã dựng', 'Medium', 'Công việc', 'wine'],
  ['18/9', '17:00', 'Nguyễn Hoàng Anh', 'phản hồi bảng phân công công việc', 'Medium', 'Công việc', 'sea'],
  ['18/9', '23:59', 'Trần Minh Khoa', 'gửi bản ghi buổi họp nhóm', 'Low', 'Công việc', 'cherry'],
  ['18/9', '23:59', 'CLB Học thuật', 'xác nhận tham dự buổi tổng kết', 'Low', 'Hoạt động', 'sky'],
  ['18/9', '23:59', 'Phòng CTSV', 'nộp đơn xin xác nhận thực tập', 'Medium', 'Hành chính', 'terra'],

  // ── Tuần 21–27/9 ────────────────────────────────────────────────────────
  ['22/9', '09:00', 'GVHD Nguyễn Văn Sơn', 'trình bày tiến độ tuần 4', 'High', 'Học tập', 'sea'],
  ['22/9', '17:00', 'Giáo vụ HCMUS', 'nộp bản chỉnh sửa theo góp ý', 'High', 'Học tập', 'moss'],
  ['22/9', '23:59', 'Nguyễn Hoàng Anh', 'gửi phần đánh giá độ phủ kiểm thử', 'Medium', 'Công việc', 'sea'],
  ['23/9', '17:00', 'Phòng Quan hệ Doanh nghiệp', 'nộp nhật ký thực tập tuần 3', 'High', 'Học tập', 'sea'],
  ['23/9', '23:59', 'Trần Minh Khoa', 'hoàn tất phần hướng dẫn cài đặt', 'Medium', 'Công việc', 'cherry'],
  ['24/9', '10:00', 'Ban tổ chức Hackathon', 'xác nhận tham dự lễ trao giải', 'Medium', 'Cá nhân', 'sun'],
  ['24/9', '17:00', 'Lê Thu Hà', 'gửi bản in màu để nộp cứng', 'Low', 'Công việc', 'wine'],
  ['24/9', '23:59', 'Phòng Đào tạo HCMUS', 'đăng ký học phần học kỳ 2', 'High', 'Học tập', 'moss'],
]

/** Đợt kéo dài nhiều tuần — dạng "từ … đến …", tức khoảng NÓI THẲNG.
 *  [id, người gửi, tên đợt, từ, đến, ưu tiên, nhãn, màu] */
type Dot = [string, string, string, string, string, Priority, string, Category]

const DOT: Dot[] = [
  ['qt-dot1', 'Phòng Khảo thí', 'Đợt kiểm tra giữa kỳ toàn khoa',
    '14/9', '19/9', 'High', 'Học tập', 'moss'],
  ['qt-dot2', 'Nhóm 7 — Anh Quân', 'Giai đoạn hoàn thiện tài liệu PA3',
    '9/9', '22/9', 'Medium', 'Công việc', 'cherry'],
]

const TOI = 'Anh Quân <meoarc.hcmus@gmail.com>'

/** Ngày thư ĐẾN — vài ngày trước hạn, để trông như hộp thư thật chứ không phải
 *  một lô dữ liệu sinh cùng lúc. */
function ngayDen(hanNgay: number, lech: number): string {
  const d = Math.max(1, hanNgay - lech)
  return `${String(d).padStart(2, '0')}/09/2026`
}

function hoa(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const thuTuViec: Email[] = VIEC.map(([ngay, gio, nguoiGui, viec, uuTien, nhan, mau], i) => {
  const soNgay = Number(ngay.split('/')[0])
  const cauChinh = `Bạn ${viec} trước ${gio} ngày ${ngay}.`
  return {
    id: `qt-${i}`,
    sender: nguoiGui,
    senderEmail: `${nguoiGui.split(' ').pop()?.toLowerCase() ?? 'nguoi'}@hcmus.edu.vn`,
    senderInitial: nguoiGui.charAt(0),
    to: TOI,
    subject: `${hoa(viec)} — hạn ${ngay}`,
    preview: `${cauChinh.slice(0, 60)}…`,
    body: [
      'Chào bạn,',
      cauChinh,
      'Nếu có vướng mắc thì báo lại sớm để còn kịp xử lý trong tuần.',
    ],
    time: gio,
    date: ngayDen(soNgay, 3 + (i % 4)),
    unread: i % 3 !== 0,
    starred: uuTien === 'High' && i % 5 === 0,
    category: mau,
    label: nhan,
    folder: 'inbox',
    priority: uuTien,
    status: 'Todo',
    tldr: `${hoa(viec)} trước ${gio} ngày ${ngay}.`,
  }
})

const thuTuDot: Email[] = DOT.map(([id, nguoiGui, ten, tu, den, uuTien, nhan, mau]) => ({
  id,
  sender: nguoiGui,
  senderEmail: 'thongbao@hcmus.edu.vn',
  senderInitial: nguoiGui.charAt(0),
  to: TOI,
  subject: `${ten} (${tu} – ${den})`,
  preview: `Đợt diễn ra từ ngày ${tu} đến ngày ${den}…`,
  body: [
    'Thông báo,',
    `${ten} diễn ra từ ngày ${tu} đến ngày ${den}. Bạn hoàn thành các đầu việc được giao trong suốt đợt và nộp kết quả vào cuối đợt.`,
    'Lịch chi tiết từng ngày xem trong tệp đính kèm của thông báo gốc.',
  ],
  time: '08:00',
  date: '05/09/2026',
  unread: true,
  starred: true,
  category: mau,
  label: nhan,
  folder: 'inbox',
  priority: uuTien,
  status: 'Todo',
  tldr: `${ten}: từ ngày ${tu} đến ngày ${den}.`,
}))

export const DEMO_QUA_TAI: Email[] = BAT ? [...thuTuViec, ...thuTuDot] : []
