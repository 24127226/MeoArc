/* ── LỚP DỊCH TỐI GIẢN ────────────────────────────────────────────────────────
   Nút "English" ở màn Cài đặt trước đây chỉ ghi vào localStorage và đặt thuộc tính
   `lang` của thẻ <html> — KHÔNG có chỗ nào đọc nó, nên bấm xong giao diện không đổi
   một chữ. Một nút hứa một việc rồi không làm thì tệ hơn không có nút.

   ── VÌ SAO TỰ VIẾT, KHÔNG DÙNG THƯ VIỆN ──
   `react-i18next` kéo theo ~40KB, một hệ thống namespace, và cách nạp bất đồng bộ —
   toàn thứ đáng giá khi có hàng nghìn chuỗi và nhiều người dịch. Ở đây phạm vi là vài
   chục chuỗi KHUNG (thanh điều hướng, tiêu đề cột, nút chính). Một `Record` phẳng cộng
   một hook đọc hết trong ba mươi giây, và không ai phải học gì để thêm chuỗi mới.

   ── PHẠM VI CÓ CHỦ Ý, VÀ NÓI THẲNG RA ──
   Bản này dịch phần KHUNG, không dịch thẻ trả lời của trợ lý hay thông báo lỗi. Toàn
   bộ khoảng 300–400 chuỗi; dịch dở dang thì giao diện nửa Việt nửa Anh, tệ hơn là để
   nguyên tiếng Việt. Nên phần chưa dịch được để nguyên MỘT CÁCH NHẤT QUÁN thay vì rải
   rác — và ngôn ngữ TRẢ LỜI của trợ lý thì đổi thật (xem
   `user_preference.to_prompt_context`), vì đó mới là chỗ người dùng đọc nhiều nhất.

   Thiếu khoá thì trả về CHÍNH KHOÁ đó chứ không phải chuỗi rỗng: một nhãn hiện ra
   "nav.inbox" là lỗi nhìn thấy ngay và sửa được, còn một nhãn trống thì trông như
   giao diện hỏng và không ai đoán ra thiếu gì. */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type Ngon = 'vi' | 'en'

const KHOA_LUU = 'meoarc-lang'

/** Từ điển. Khoá đặt theo `khu-vuc.ten` để tìm bằng mắt được. */
const TU_DIEN: Record<string, { vi: string; en: string }> = {
  // Thanh điều hướng
  'nav.inbox': { vi: 'Hộp thư', en: 'Inbox' },
  'nav.schedule': { vi: 'Lịch trình', en: 'Schedule' },
  'nav.assistant': { vi: 'Trợ lý', en: 'Assistant' },
  'nav.starred': { vi: 'Gắn sao', en: 'Starred' },
  'nav.sent': { vi: 'Đã gửi', en: 'Sent' },
  'nav.drafts': { vi: 'Nháp', en: 'Drafts' },
  'nav.archive': { vi: 'Lưu trữ', en: 'Archive' },
  'nav.spam': { vi: 'Thư rác', en: 'Spam' },
  'nav.trash': { vi: 'Thùng rác', en: 'Trash' },
  'nav.settings': { vi: 'Cài đặt', en: 'Settings' },
  'nav.notifications': { vi: 'Thông báo', en: 'Notifications' },

  // Cột thư
  'mail.title': { vi: 'Hộp thư', en: 'Inbox' },
  'mail.search': { vi: 'Tìm trong thư…', en: 'Search mail…' },
  'mail.compose': { vi: 'Soạn thư', en: 'Compose' },
  'mail.refresh': { vi: 'Làm mới', en: 'Refresh' },
  'mail.unread': { vi: 'chưa đọc', en: 'unread' },
  'mail.empty': { vi: 'Không có thư nào.', en: 'No messages.' },

  // Khung trợ lý
  'chat.title': { vi: 'Trợ lý MeoArc', en: 'MeoArc Assistant' },
  'chat.placeholder': { vi: 'Nhắn cho trợ lý…', en: 'Message the assistant…' },
  'chat.send': { vi: 'Gửi', en: 'Send' },
  'chat.approve': { vi: 'Duyệt', en: 'Approve' },
  'chat.reject': { vi: 'Từ chối', en: 'Reject' },
  'chat.openMail': { vi: 'Mở thư', en: 'Open' },
  'chat.reply': { vi: 'Trả lời', en: 'Reply' },

  // Cài đặt
  'settings.title': { vi: 'Cài đặt', en: 'Settings' },
  'settings.appearance': { vi: 'Giao diện', en: 'Appearance' },
  'settings.personal': { vi: 'Cá nhân hoá', en: 'Personalisation' },
  'settings.theme': { vi: 'Chủ đề', en: 'Theme' },
  'settings.language': { vi: 'Ngôn ngữ', en: 'Language' },
  'act.approveSend': { vi: 'Duyệt & gửi', en: 'Approve & send' },
  'act.archive': { vi: 'Lưu trữ', en: 'Archive' },
  'act.attach': { vi: 'Đính kèm tệp', en: 'Attach file' },
  'act.clear': { vi: 'Bỏ chọn', en: 'Clear selection' },
  'act.close': { vi: 'Đóng', en: 'Close' },
  'act.compose': { vi: 'Soạn thư mới', en: 'New message' },
  'act.copy': { vi: 'Sao chép', en: 'Copy' },
  'act.delete': { vi: 'Xoá', en: 'Delete' },
  'act.discardDraft': { vi: 'Bỏ bản nháp', en: 'Discard draft' },
  'act.filter': { vi: 'Bộ lọc theo tiêu chí', en: 'Filter by criteria' },
  'act.important': { vi: 'Quan trọng', en: 'Important' },
  'act.label': { vi: 'Gắn nhãn', en: 'Label' },
  'act.markImportant': { vi: 'Đánh dấu quan trọng', en: 'Mark as important' },
  'act.markRead': { vi: 'Đánh dấu đã đọc', en: 'Mark as read' },
  'act.markUnread': { vi: 'Đánh dấu chưa đọc', en: 'Mark as unread' },
  'act.refresh': { vi: 'Làm mới', en: 'Refresh' },
  'act.rename': { vi: 'Đổi tên', en: 'Rename' },
  'act.rerun': { vi: 'Chạy lại', en: 'Run again' },
  'act.skip': { vi: 'Bỏ qua', en: 'Skip' },
  'auth.login': { vi: 'Đăng nhập MeoArc', en: 'Sign in to MeoArc' },
  'auth.retry': { vi: 'Thử lại, hoặc dùng tài khoản Google.', en: 'Try again, or use a Google account.' },
  'auth.scope': { vi: 'đọc &amp; quản lý thư', en: 'read &amp; manage mail' },
  'cal.day': { vi: 'NGÀY', en: 'DAY' },
  'cal.month': { vi: 'THÁNG', en: 'MONTH' },
  'cal.next': { vi: 'Tháng sau', en: 'Next month' },
  'cal.prev': { vi: 'Tháng trước', en: 'Previous month' },
  'cal.today': { vi: 'Hôm nay', en: 'Today' },
  'chat.attachHint': { vi: 'Đính kèm tệp để trợ lý gửi đi', en: 'Attach a file for the assistant to send' },
  'chat.clearCtx': { vi: 'Bỏ bối cảnh', en: 'Clear context' },
  'chat.new': { vi: 'Cuộc trò chuyện mới', en: 'New conversation' },
  'mail.askAssistant': { vi: 'Hỏi trợ lý về việc này', en: 'Ask the assistant about this' },
  'mail.body': { vi: 'Nội dung email', en: 'Email body' },
  'mail.confirmSend': { vi: 'Xác nhận gửi?', en: 'Confirm send?' },
  'mail.dragWidth': { vi: 'Kéo để chỉnh độ rộng dải hộp thư', en: 'Drag to resize the mail column' },
  'mail.dragWidthLong': { vi: 'Kéo để chỉnh độ rộng · double-click để khôi phục', en: 'Drag to resize · double-click to reset' },
  'mail.enableKeys': { vi: 'Kích hoạt dải phím thao tác', en: 'Enable shortcut bar' },
  'mail.openThis': { vi: 'Mở lá thư này', en: 'Open this message' },
  'mail.refreshBox': { vi: 'Làm mới hộp thư', en: 'Refresh mailbox' },
  'mail.replyThis': { vi: 'Soạn trả lời thư này', en: 'Draft a reply' },
  'mail.subjectLabel': { vi: 'Chủ đề:', en: 'Subject:' },
  'mail.tapChangeLabel': { vi: 'Bấm để đổi nhãn', en: 'Tap to change label' },
  'mail.toggleSearch': { vi: 'Bật/tắt ô tìm kiếm', en: 'Toggle search box' },
  'mail.viewOriginal': { vi: 'Xem thư gốc', en: 'View original' },
  'nav.account': { vi: 'Tài khoản', en: 'Account' },
  'nav.backAssistant': { vi: 'Quay lại trợ lý', en: 'Back to assistant' },
  'nav.backInbox': { vi: 'Về hộp thư', en: 'Back to inbox' },
  'nav.closeAssistant': { vi: 'Đóng trợ lý AI', en: 'Close AI assistant' },
  'nav.closeToInbox': { vi: 'Đóng trợ lý — về Hộp thư', en: 'Close assistant — back to Inbox' },
  'nav.history': { vi: 'Lịch sử trò chuyện', en: 'Chat history' },
  'nav.openAssistant': { vi: 'Mở trợ lý MeoArc', en: 'Open MeoArc Assistant' },
  'nav.palette': { vi: 'Bảng lệnh', en: 'Command palette' },
  'nav.travel': { vi: 'Tra cứu chỗ đi lại', en: 'Travel lookup' },
  'nav.travelLong': { vi: 'Tra cứu chuyến bay và phòng', en: 'Look up flights and rooms' },
  'notif.close': { vi: 'Đóng thông báo', en: 'Dismiss notification' },
  'onb.welcome': { vi: 'Chào mừng đến MeoArc', en: 'Welcome to MeoArc' },
  'plan.close': { vi: 'Đóng trang nâng cấp', en: 'Close upgrade page' },
  'plan.perDay': { vi: 'lượt hỏi / ngày', en: 'questions / day' },
  'plan.perMonth': { vi: '/tháng', en: '/month' },
  'pref.callYou': { vi: 'Trợ lý gọi bạn là', en: 'The assistant calls you' },
  'pref.instruction': { vi: 'Dặn riêng cho trợ lý', en: 'Custom instruction' },
  'pref.session': { vi: 'Phiên đăng nhập Google hiện tại của bạn.', en: 'Your current Google session.' },
  'pref.signature': { vi: 'Chữ ký cuối thư', en: 'Email signature' },
  'pref.tone': { vi: 'Giọng văn khi soạn thư', en: 'Writing tone' },
  'st.arrowSelect': { vi: '↑↓ chọn', en: '↑↓ select' },
  'st.askingAbout': { vi: 'Đang hỏi về:', en: 'Asking about:' },
  'st.enterRun': { vi: '↵ chạy', en: '↵ run' },
  'st.escClose': { vi: 'esc đóng', en: 'esc to close' },
  'st.handled': { vi: 'Đã xử lý ✓', en: 'Handled ✓' },
  'st.inferredDue': { vi: 'hạn tự tính', en: 'inferred due date' },
  'st.loading': { vi: 'Đang tải…', en: 'Loading…' },
  'st.multiSelect': { vi: 'Được chọn nhiều', en: 'Multi-select' },
  'st.noBooking': { vi: 'không đặt chỗ', en: 'no booking' },
  'st.noNotif': { vi: 'Chưa có thông báo', en: 'No notifications' },
  'st.noTasks': { vi: 'Chưa có việc nào.', en: 'No tasks yet.' },
  'st.noTasksRange': { vi: 'Không có việc nào trong khoảng này.', en: 'No tasks in this range.' },
  'st.on': { vi: 'đang bật', en: 'on' },
  'st.tryOtherKeyword': { vi: 'Thử từ khoá khác nhé.', en: 'Try another keyword.' },
  'travel.clearFilter': { vi: 'Bỏ lọc', en: 'Clear filters' },
  'travel.googleDetail': { vi: 'Xem chi tiết chuyến bay này trên Google', en: 'See this flight on Google' },
  'travel.hotelNote': { vi: 'Tên, hạng sao và vị trí là thật — giá phòng là số mô phỏng', en: 'Name, star rating and location are real — the price is simulated' },
  'travel.noPrice': { vi: 'Nguồn này cung cấp lịch bay, không bán vé nên không có giá', en: 'This source provides schedules, not tickets — so no price' },
  'travel.real': { vi: 'thật', en: 'real' },
  'travel.viewFlight': { vi: 'Xem chuyến bay', en: 'View flight' },
  'voice.off': { vi: 'Đóng voice mode', en: 'Close voice mode' },
  'voice.on': { vi: 'Bật voice mode', en: 'Start voice mode' },
  'voice.speak': { vi: 'Nói với trợ lý (voice mode)', en: 'Talk to the assistant (voice mode)' },

  'settings.langNote': {
    vi: 'Đổi ngôn ngữ khung giao diện và ngôn ngữ trợ lý trả lời. Một số phần (thẻ kết quả, thông báo lỗi) hiện vẫn là tiếng Việt.',
    en: 'Changes the interface chrome and the language the assistant replies in. Some parts (result cards, error messages) are still in Vietnamese.',
  },
}

/* ── VÌ SAO CÓ `t()` Ở TẦNG MODULE, KHÔNG CHỈ HOOK ──────────────────────────
   `useT()` là hook nên chỉ gọi được TRONG component. Nhưng chuỗi cần dịch nằm rải
   rác ở những chỗ hook với tới không được: mảng hằng số ở đầu file (`SKILLS`,
   `NAV_ITEMS`), component con lồng sâu chưa nhận context, hàm tiện ích thuần.
   Ép mọi chỗ đó thành component chỉ để gọi hook được là bẻ cong cấu trúc mã vì một
   giới hạn kỹ thuật — cái giá trả bằng khả năng đọc, cho một thứ không ai thấy.

   Nên giữ MỘT biến ở tầng module, và cho `t()` đọc nó. Đổi ngôn ngữ thì provider vừa
   cập nhật biến vừa gắn `key` mới cho cây con → React dựng lại toàn bộ, và mọi `t()`
   chạy lại với giá trị mới. Dựng lại làm mất state cục bộ (ô đang gõ dở, tab đang
   mở) — chấp nhận được, vì đổi ngôn ngữ là việc hiếm và người dùng cũng mong đợi
   màn hình vẽ lại. */
let _ngonHienTai: Ngon = 'vi'

/** Dịch ở BẤT KỲ đâu, kể cả ngoài component. */
export function t(khoa: string): string {
  return TU_DIEN[khoa]?.[_ngonHienTai] ?? khoa
}

const Boi = createContext<{ ngon: Ngon; datNgon: (n: Ngon) => void }>({
  ngon: 'vi',
  datNgon: () => {},
})

export function NhaCungCapNgonNgu({ children }: { children: ReactNode }) {
  const [ngon, setNgon] = useState<Ngon>(() => {
    try {
      return (localStorage.getItem(KHOA_LUU) as Ngon) || 'vi'
    } catch {
      // Cửa sổ ẩn danh hoặc trình duyệt chặn lưu trữ: về mặc định, đừng để vỡ app.
      return 'vi'
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(KHOA_LUU, ngon)
    } catch {
      /* không lưu được thì thôi — lần sau mở lại về tiếng Việt, không phải lỗi chặn dùng */
    }
    document.documentElement.lang = ngon
  }, [ngon])

  // Cập nhật biến module TRƯỚC khi vẽ, để `t()` trong lần vẽ này đã đúng ngôn ngữ.
  _ngonHienTai = ngon

  return (
    <Boi.Provider value={{ ngon, datNgon: setNgon }}>
      {/* `key` đổi → React dựng lại cả cây. Không có nó thì `children` giữ nguyên
          tham chiếu nên React bỏ qua, và mọi `t()` ở tầng module vẫn trả chữ cũ. */}
      <div key={ngon} className="contents">
        {children}
      </div>
    </Boi.Provider>
  )
}

/** `const t = useT()` rồi `t('nav.inbox')`. */
export function useT() {
  const { ngon } = useContext(Boi)
  return (khoa: string): string => TU_DIEN[khoa]?.[ngon] ?? khoa
}

/** Đọc/đổi ngôn ngữ hiện tại (dùng ở màn Cài đặt). */
export function useNgonNgu() {
  return useContext(Boi)
}
