/** Category màu của inbox — tên màu lấy từ palette "Provence Meadow".
 *  Bảng màu cụ thể nằm ở email-list.tsx (CATEGORY) để giữ một nguồn duy nhất. */
export type Category = 'moss' | 'sea' | 'sun' | 'cherry' | 'sky' | 'terra' | 'wine'

export type Attachment = { name: string; size: string }

/** Độ ưu tiên do AI Triage (UC015) gán sẵn — hiển thị badge trên card. */
export type Priority = 'action' | 'waiting' | 'fyi'

export type Email = {
  id: string
  sender: string
  senderEmail: string
  senderInitial: string
  to: string
  subject: string
  preview: string
  body: string[]
  time: string
  date: string
  unread: boolean
  starred: boolean
  category: Category
  label?: string
  attachments?: Attachment[]
  /** AI Triage (UC015): action=cần bạn xử lý · waiting=đang đợi · fyi=để biết */
  priority?: Priority
  /** Tóm tắt 1 dòng do AI quét sẵn (UC008) — TL;DR cho card & smart card. */
  tldr?: string
  /** Thư mục (mặc định inbox) — cho nav trái lọc thật. */
  folder?: 'inbox' | 'sent' | 'drafts' | 'archive' | 'trash'
}

const ME = 'Anh Quân <quanpta.meoarc@gmail.com>'

export const emails: Email[] = [
  {
    id: '1',
    sender: 'Giáo vụ HCMUS',
    senderEmail: 'giaovu@fit.hcmus.edu.vn',
    senderInitial: 'G',
    to: ME,
    subject: 'Nhắc nộp báo cáo SRS — Nhóm 7',
    preview: 'Các nhóm vui lòng nộp bản SRS hoàn chỉnh trước 23:59 thứ Sáu tuần này...',
    body: [
      'Chào các em,',
      'Các nhóm vui lòng nộp bản SRS hoàn chỉnh (PDF + bản Word) lên hệ thống Moodle trước 23:59 thứ Sáu tuần này. Lưu ý đặt tên file theo định dạng Nhom07_SRS_v1.pdf.',
      'Bản nộp cần đầy đủ: danh sách Use Case, đặc tả Main/Alternative Scenario, sơ đồ Use Case, và mockup giao diện minh hoạ.',
      'Trân trọng,\nPhòng Giáo vụ — Khoa CNTT, HCMUS',
    ],
    time: '08:42',
    date: 'Hôm nay, 08:42',
    unread: true,
    starred: true,
    category: 'moss',
    label: 'Học tập',
    priority: 'action',
    tldr: 'Hạn nộp SRS hoàn chỉnh: 23:59 thứ Sáu, đặt tên Nhom07_SRS_v1.pdf.',
    attachments: [
      { name: 'Mau_SRS_Intro2SE.docx', size: '248 KB' },
      { name: 'Lich_nop_baocao.pdf', size: '96 KB' },
    ],
  },
  {
    id: '2',
    sender: 'GitHub',
    senderEmail: 'notifications@github.com',
    senderInitial: 'G',
    to: ME,
    subject: '[meoarc-frontend] PR #12 đã được review',
    preview: 'quanpta đã yêu cầu thay đổi trên pull request: "feat: add chat canvas"...',
    body: [
      'quanpta đã review pull request #12 — "feat: add chat canvas".',
      'Trạng thái: Changes requested. 2 bình luận mới ở src/components/layout/chat-panel.tsx.',
      'Mở pull request trên GitHub để xem chi tiết và phản hồi.',
    ],
    time: '08:10',
    date: 'Hôm nay, 08:10',
    unread: true,
    starred: false,
    category: 'sea',
    label: 'Dev',
    priority: 'action',
    tldr: 'PR #12 bị "Changes requested" — 2 bình luận cần bạn xử lý.',
  },
  {
    id: '3',
    sender: 'Google Cloud',
    senderEmail: 'cloud-noreply@google.com',
    senderInitial: 'C',
    to: ME,
    subject: 'Gemini API — hạn mức tháng này',
    preview: 'Dự án của bạn đã dùng 64% hạn mức request. Xem chi tiết sử dụng...',
    body: [
      'Xin chào,',
      'Dự án meoarc-prod đã sử dụng 64% hạn mức request của Gemini API trong chu kỳ thanh toán này.',
      'Bạn có thể xem chi tiết mức sử dụng theo từng model và thiết lập cảnh báo ngân sách trong Google Cloud Console.',
    ],
    time: 'Hôm qua',
    date: 'Hôm qua, 19:20',
    unread: false,
    starred: false,
    category: 'sun',
    label: 'Hệ thống',
    priority: 'fyi',
    tldr: 'Đã dùng 64% hạn mức Gemini API tháng này — chưa cần hành động.',
  },
  {
    id: '4',
    sender: 'Trần Minh Khoa',
    senderEmail: 'khoa.tran@gmail.com',
    senderInitial: 'K',
    to: ME,
    subject: 'Re: Phân chia use case backend',
    preview: 'Ok bạn, mình nhận UC005 với UC006 nhé. Còn phần MCP để cuối tuần họp...',
    body: [
      'Ok bạn,',
      'Mình nhận UC005 (Search & Filter) với UC006 (Manage Emails) nhé. Phần MCP (UC012) để cuối tuần họp rồi chia tiếp.',
      'Tối nay mình push nhánh feat/search, bạn review giúp nha.',
    ],
    time: 'Hôm qua',
    date: 'Hôm qua, 16:05',
    unread: false,
    starred: true,
    category: 'cherry',
    label: 'Cá nhân',
    priority: 'waiting',
    tldr: 'Khoa nhận UC005/UC006; tối nay push nhánh feat/search chờ bạn review. Có hẹn cuối tuần họp chia phần MCP.',
  },
  {
    id: '5',
    sender: 'Vercel',
    senderEmail: 'noreply@vercel.com',
    senderInitial: 'V',
    to: ME,
    subject: 'Deployment sẵn sàng để preview',
    preview: 'Bản preview cho nhánh main đã build thành công và sẵn sàng xem thử...',
    body: [
      'Deployment cho meoarc-frontend đã hoàn tất.',
      'Nhánh: main · Trạng thái: Ready · Thời gian build: 38s.',
      'Mở bản preview để kiểm tra trước khi promote lên production.',
    ],
    time: 'T4',
    date: 'Thứ 4, 11:48',
    unread: false,
    starred: false,
    category: 'sky',
    label: 'Deploy',
    priority: 'fyi',
    tldr: 'Preview nhánh main build xong (38s) — sẵn sàng kiểm tra trước khi promote.',
  },
  {
    id: '6',
    sender: 'Newsletter UX',
    senderEmail: 'hello@uxweekly.com',
    senderInitial: 'N',
    to: ME,
    subject: 'Xu hướng thiết kế "quiet luxury" 2026',
    preview: 'Tuần này: bảng màu ấm, typography serif, và sự trở lại của old-money...',
    body: [
      'Chào bạn,',
      'Số tuần này: bảng màu ấm, typography serif có trọng lượng, và sự trở lại của thẩm mỹ "old-money" trong sản phẩm số.',
      'Đọc bản đầy đủ trên web để xem các case study kèm ảnh minh hoạ.',
    ],
    time: 'T3',
    date: 'Thứ 3, 09:15',
    unread: false,
    starred: false,
    category: 'terra',
    label: 'Bản tin',
    priority: 'fyi',
    tldr: 'Bản tin UX: màu ấm, serif có trọng lượng, thẩm mỹ "old-money" lên ngôi 2026.',
  },

  /* ----- Đã gửi ----- */
  {
    id: 's1',
    sender: 'Giáo vụ HCMUS',
    senderEmail: 'giaovu@fit.hcmus.edu.vn',
    senderInitial: 'G',
    to: 'giaovu@fit.hcmus.edu.vn',
    subject: 'Re: Nhắc nộp báo cáo SRS — Nhóm 7',
    preview: 'Dạ em chào thầy/cô, nhóm 7 sẽ nộp bản SRS đúng hạn ạ...',
    body: [
      'Dạ em chào thầy/cô,',
      'Nhóm 7 đã nắm thông tin và sẽ nộp bản SRS hoàn chỉnh trước hạn. Em cảm ơn ạ.',
      'Trân trọng,\nAnh Quân',
    ],
    time: '09:02',
    date: 'Hôm nay, 09:02',
    unread: false,
    starred: false,
    category: 'moss',
    label: 'Học tập',
    folder: 'sent',
  },
  {
    id: 's2',
    sender: 'Trần Minh Khoa',
    senderEmail: 'khoa.tran@gmail.com',
    senderInitial: 'K',
    to: 'khoa.tran@gmail.com',
    subject: 'Re: Phân chia use case backend',
    preview: 'Ok bạn, mình review nhánh feat/search tối nay nhé...',
    body: ['Ok bạn,', 'Mình review nhánh feat/search tối nay nhé. Cảm ơn!', 'Quân'],
    time: 'Hôm qua',
    date: 'Hôm qua, 17:10',
    unread: false,
    starred: false,
    category: 'cherry',
    label: 'Cá nhân',
    folder: 'sent',
  },

  /* ----- Nháp ----- */
  {
    id: 'd1',
    sender: 'Nháp',
    senderEmail: '',
    senderInitial: '✎',
    to: 'cloud-noreply@google.com',
    subject: 'Hỏi về hạn mức Gemini API',
    preview: 'Dạ cho em hỏi về cách nâng hạn mức request...',
    body: ['Dạ cho em hỏi về cách nâng hạn mức request cho dự án meoarc-prod ạ.', '(đang soạn…)'],
    time: 'Hôm qua',
    date: 'Hôm qua, 20:05',
    unread: false,
    starred: false,
    category: 'sun',
    folder: 'drafts',
  },

  /* ----- Thùng rác ----- */
  {
    id: 't1',
    sender: 'Promo Shopee',
    senderEmail: 'no-reply@shopee.vn',
    senderInitial: 'S',
    to: ME,
    subject: 'Sale 12.12 — giảm đến 50%',
    preview: 'Săn deal khủng ngày đôi, mã freeship toàn sàn...',
    body: ['Săn deal khủng ngày đôi!', 'Mã freeship toàn sàn, áp dụng hôm nay.'],
    time: 'T2',
    date: 'Thứ 2, 08:00',
    unread: false,
    starred: false,
    category: 'terra',
    label: 'Bản tin',
    folder: 'trash',
  },
]
