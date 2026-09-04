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
  'mail.searchTitle': { vi: 'Tìm kiếm', en: 'Search' },
  'mail.colTitle': { vi: 'Thư', en: 'Mail' },
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

  'act.keep': { vi: 'Giữ lại', en: 'Keep' },
  'act.replyDraft': { vi: 'Soạn trả lời', en: 'Draft a reply' },
  'act.star': { vi: 'Gắn sao', en: 'Star' },
  'auto.read': { vi: 'Đã đọc', en: 'Read' },
  'auto.replay': { vi: '— bấm để tua lại', en: '— click to replay' },
  'auto.sent': { vi: 'Đã gửi', en: 'Sent' },
  'chat.rewriteHint': { vi: 'Gợi ý: ngắn gọn hơn, trang trọng hơn…', en: 'Try: shorter, more formal…' },
  'chat.searchHistory': { vi: 'Tìm trong lịch sử…', en: 'Search history…' },
  'cmd.archiveHint': { vi: 'Dọn hộp thư', en: 'Tidy the inbox' },
  'cmd.archiveNews': { vi: 'Lưu trữ thư bản tin', en: 'Archive newsletters' },
  'cmd.autolabelHint': { vi: 'Gắn nhãn toàn bộ', en: 'Label everything' },
  'cmd.briefHint': { vi: 'Tóm tắt cuộc họp', en: 'Summarize the meeting' },
  'cmd.digest': { vi: 'Digest hôm nay', en: "Today's digest" },
  'cmd.digestHint': { vi: 'Báo cáo nhanh hộp thư', en: 'Quick inbox report' },
  'cmd.placeholder': { vi: 'Gõ lệnh hoặc hỏi trợ lý…', en: 'Type a command or ask…' },
  'cmd.sendToMeoarc': { vi: 'Gửi cho MeoArc xử lý', en: 'Send to MeoArc' },
  'cmd.summarize': { vi: 'Tóm tắt thư chưa đọc', en: 'Summarize unread' },
  'cmd.summarizeHint': { vi: 'Rút gọn nội dung', en: 'Condense the content' },
  'cmd.theme': { vi: 'Đổi theme', en: 'Switch theme' },
  'cmd.triage': { vi: 'Triage hộp thư', en: 'Triage inbox' },
  'cmd.triageHint': { vi: 'Phân loại theo ưu tiên', en: 'Sort by priority' },
  'flt.action': { vi: 'Cần xử lý', en: 'Needs action' },
  'flt.all': { vi: 'Tất cả', en: 'All' },
  'flt.attach': { vi: 'Đính kèm', en: 'Attachment' },
  'flt.done': { vi: 'Xong', en: 'Done' },
  'flt.unread': { vi: 'Chưa đọc', en: 'Unread' },
  'flt.waiting': { vi: 'Đang đợi', en: 'Waiting' },
  'mail.bodyPlaceholder': { vi: 'Nội dung email…', en: 'Email body…' },
  'mail.from': { vi: 'Từ', en: 'From' },
  'mail.orBrowse': { vi: 'hoặc bấm để chọn từ máy', en: 'or click to browse' },
  'mail.subject': { vi: 'Chủ đề', en: 'Subject' },
  'mail.to': { vi: 'Tới', en: 'To' },
  'mail.toLabel': { vi: 'Tới:', en: 'To:' },
  'mail.toPlaceholder': { vi: 'email người nhận', en: 'recipient email' },
  'nav.faq': { vi: 'Giải đáp', en: 'FAQ' },
  'nav.features': { vi: 'Tính năng', en: 'Features' },
  'nav.how': { vi: 'Cách vận hành', en: 'How it works' },
  'nav.pricing': { vi: 'Gói dịch vụ', en: 'Pricing' },
  'onb.d2': { vi: 'Cứ nhắn lời thường: “tóm tắt thư chưa đọc”, “lưu trữ thư bản tin”, “brief cuộc họp”…', en: 'Just talk normally: “summarize unread”, “archive newsletters”, “brief the meeting”…' },
  'onb.d4': { vi: '⌘K mở bảng lệnh · / tìm kiếm · j/k duyệt thư · Enter mở · c soạn thư.', en: '⌘K command palette · / search · j/k browse · Enter open · c compose.' },
  'onb.d1': { vi: 'Điều hướng trái · danh sách thư giữa · trợ lý AI phải. Kéo mép phải để chỉnh rộng.', en: 'Navigation left · mail list centre · AI assistant right. Drag the edge to resize.' },
  'onb.d3': { vi: 'Bấm mic để nói — trợ lý nghe, hiểu và đọc lại câu trả lời cho bạn.', en: 'Tap the mic and speak — the assistant listens, understands and reads its answer back.' },
  'onb.t1': { vi: 'Giao diện 3 cột', en: 'Three-column layout' },
  'onb.t2': { vi: 'Trợ lý ngôn ngữ tự nhiên', en: 'Natural-language assistant' },
  'onb.t3': { vi: 'Ra lệnh bằng giọng nói', en: 'Voice commands' },
  'onb.t4': { vi: 'Phím tắt nhanh', en: 'Keyboard shortcuts' },
  'plan.choose': { vi: 'Chọn gói', en: 'Choose a plan' },
  'pref.namePlaceholder': { vi: 'Anh Quân', en: 'e.g. Alex' },
  'scope.modify': { vi: 'Quản lý thư (modify/label/archive)', en: 'Manage mail (modify/label/archive)' },
  'scope.read': { vi: 'Đọc thư (read)', en: 'Read mail (read)' },
  'scope.send': { vi: 'Soạn & gửi (send)', en: 'Compose & send (send)' },
  'skill.autolabel': { vi: 'Phân loại tự động', en: 'Auto-label' },
  'skill.autopilot': { vi: 'Hộp thư tự lái', en: 'Autopilot inbox' },
  'skill.brief': { vi: 'Tóm lược cuộc họp', en: 'Meeting brief' },
  'skill.digest': { vi: 'Tóm tắt hôm nay', en: "Today's digest" },
  'skill.triage': { vi: 'Phân loại ưu tiên', en: 'Prioritize' },
  'st.pinned': { vi: 'Đã ghim', en: 'Pinned' },
  'sub.thisMonth': { vi: 'Tháng này', en: 'This month' },
  'sug.brief': { vi: 'Tạo Meeting Brief', en: 'Create a meeting brief' },
  'sug.cleanNews': { vi: 'Dọn thư bản tin tuần này', en: "Clear this week's newsletters" },
  'sug.digestAm': { vi: 'Tóm tắt hộp thư sáng nay', en: "Summarize this morning's inbox" },
  'sug.summarize': { vi: 'Tóm tắt thư này', en: 'Summarize this message' },
  'sug.tasks': { vi: 'Trích việc & deadline', en: 'Extract tasks & deadlines' },
  'theme.dark': { vi: 'Tối', en: 'Dark' },
  'theme.light': { vi: 'Sáng', en: 'Light' },

  'acct.switchTo': { vi: 'Chuyển sang', en: 'Switch to' },
  'acct.addAnother': { vi: 'Thêm tài khoản khác', en: 'Add another account' },
  'acct.logoutThis': { vi: 'Đăng xuất tài khoản này', en: 'Sign out of this account' },
  'acct.revoke': { vi: 'Thu hồi quyền Gmail', en: 'Revoke Gmail access' },
  'acct.revokeAsk': { vi: 'Thu hồi quyền Gmail?', en: 'Revoke Gmail access?' },
  'acct.revokeWarn': { vi: 'MeoArc sẽ mất toàn bộ quyền đọc & quản lý thư trên Gmail của bạn và bạn sẽ bị đăng xuất. Lần sau muốn dùng lại phải cấp quyền từ đầu.', en: 'MeoArc will lose all read & manage access to your Gmail and you will be signed out. Using it again means granting access from scratch.' },
  'acct.revokeGo': { vi: 'Thu hồi & đăng xuất', en: 'Revoke & sign out' },
  'act.cancel': { vi: 'Huỷ', en: 'Cancel' },

  'pref.instrPlaceholder': { vi: "Đừng dùng từ 'trân trọng'. Luôn hỏi lại trước khi hứa deadline.", en: "Don't use the word 'sincerely'. Always check with me before promising a deadline." },
  'voice.example': { vi: 'vd: “tóm tắt thư chưa đọc”', en: 'e.g. “summarize unread”' },

  'fld.inbox': { vi: 'Hộp thư', en: 'Inbox' },
  'fld.starred': { vi: 'Gắn sao', en: 'Starred' },
  'fld.sent': { vi: 'Đã gửi', en: 'Sent' },
  'fld.drafts': { vi: 'Nháp', en: 'Drafts' },
  'fld.archive': { vi: 'Lưu trữ', en: 'Archive' },
  'fld.trash': { vi: 'Thùng rác', en: 'Trash' },
  'toast.unstarred': { vi: 'Đã bỏ quan trọng', en: 'Removed from important' },
  'toast.starred': { vi: 'Đã đánh dấu quan trọng', en: 'Marked important' },
  'toast.markedRead': { vi: 'Đã đánh dấu {n} thư là đã đọc', en: 'Marked {n} messages as read' },
  'toast.markedUnread': { vi: 'Đã đánh dấu {n} thư là chưa đọc', en: 'Marked {n} messages as unread' },
  'toast.markedImportant': { vi: 'Đã đánh dấu {n} thư là quan trọng', en: 'Marked {n} messages as important' },
  'toast.deleted': { vi: 'Đã xoá {n} thư', en: 'Deleted {n} messages' },
  'toast.labelled': { vi: 'Đã gắn nhãn “{nhan}” cho {n} thư', en: 'Labelled {n} messages “{nhan}”' },
  'toast.labelledOne': { vi: 'Đã gắn nhãn “{nhan}”', en: 'Labelled “{nhan}”' },
  'toast.archived': { vi: 'Đã lưu trữ thư', en: 'Message archived' },
  'toast.markedUnreadOne': { vi: 'Đã đánh dấu chưa đọc', en: 'Marked as unread' },
  'mail.closeSearch': { vi: 'Đóng tìm kiếm', en: 'Close search' },
  'mail.unreadCount': { vi: '{n} thư chưa đọc', en: '{n} unread' },
  'mail.allRead': { vi: 'Đã đọc hết', en: 'All read' },
  'mail.phGmail': { vi: 'Tìm trên Gmail (vd: from:github, has:attachment)…', en: 'Search Gmail (e.g. from:github, has:attachment)…' },
  'mail.phNl': { vi: 'Hỏi: "thư chưa đọc có đính kèm"…', en: 'Ask: "unread with attachments"…' },
  'mail.phPlain': { vi: 'Tìm (phím / để focus)…', en: 'Search (press / to focus)…' },
  'mail.nlOff': { vi: 'Tắt tìm theo ngôn ngữ tự nhiên', en: 'Turn off natural-language search' },
  'mail.nlOn': { vi: 'Tìm bằng ngôn ngữ tự nhiên', en: 'Search in natural language' },
  'mail.tagsCollapse': { vi: 'Thu gọn nhãn', en: 'Collapse labels' },
  'mail.tagsExpand': { vi: 'Hiện đủ nhãn phân loại', en: 'Show all labels' },
  'mail.deselectAll': { vi: 'Bỏ chọn tất cả', en: 'Deselect all' },
  'mail.selectAll': { vi: 'Chọn tất cả', en: 'Select all' },
  'mail.loadMore': { vi: 'Tải thêm thư', en: 'Load more' },
  'mail.noResult': { vi: 'Không tìm thấy thư nào', en: 'No messages found' },
  'mail.folderEmpty': { vi: 'Mục “{ten}” đang trống', en: '“{ten}” is empty' },
  'mail.tryOther': { vi: 'Thử đổi từ khoá hoặc bỏ bớt bộ lọc đang áp dụng.', en: 'Try another keyword or drop a filter.' },
  'mail.nothingHere': { vi: 'Chưa có thư nào ở đây.', en: 'Nothing here yet.' },
  'mail.clearFilter': { vi: 'Xoá bộ lọc', en: 'Clear filters' },
  'mail.theseMsgs': { vi: 'Các thư', en: 'These messages' },
  'mail.thisMsg': { vi: 'Thư', en: 'Message' },
  'mail.prioTitle': { vi: 'Độ ưu tiên: {muc}', en: 'Priority: {muc}' },
  'det.unstar': { vi: 'Bỏ quan trọng', en: 'Unmark important' },
  'det.star': { vi: 'Đánh dấu quan trọng', en: 'Mark important' },
  'det.status': { vi: 'Trạng thái', en: 'Status' },
  'det.length': { vi: 'Độ dài', en: 'Length' },
  'det.words': { vi: '{n} chữ', en: '{n} words' },
  'det.readTime': { vi: 'Thời gian đọc', en: 'Reading time' },
  'det.minutes': { vi: '{n} phút', en: '{n} min' },
  'det.hideSummary': { vi: 'Ẩn tóm tắt', en: 'Hide summary' },
  'det.aiSummary': { vi: 'Tóm tắt với AI', en: 'Summarize with AI' },
  'det.fyi': { vi: 'Để biết', en: 'FYI' },
  'det.htmlNote': { vi: 'Thư này chủ yếu là nội dung HTML — xem bản đầy đủ bên dưới.', en: 'This message is mostly HTML — see the full version below.' },
  'nav.weekEmpty': { vi: 'tuần này trống', en: 'nothing this week' },
  'nav.ready': { vi: 'Trợ lý sẵn sàng · {gio}', en: 'Assistant ready · {gio}' },
  'nav.expand': { vi: 'Mở rộng thanh điều hướng', en: 'Expand navigation' },
  'nav.collapse': { vi: 'Thu gọn thanh điều hướng', en: 'Collapse navigation' },
  'nav.dayLoad': { vi: '{thu} — {n} việc, {gio} giờ', en: '{thu} — {n} tasks, {gio} h' },
  'sh.refresh': { vi: 'Làm mới', en: 'Refresh' },
  'sh.loadMore': { vi: 'Tải thêm', en: 'Load more' },
  'sh.expired': { vi: 'Phiên đăng nhập đã hết hạn. Đăng nhập lại để xem thư.', en: 'Your session has expired. Sign in again to see your mail.' },
  'sh.netFail': { vi: 'Không nạp được thư từ máy chủ. Kiểm tra kết nối rồi thử lại.', en: 'Could not load mail from the server. Check your connection and try again.' },
  'sh.syncing': { vi: 'Hộp thư đang đồng bộ', en: 'Mailbox syncing' },
  'al.hoursLeft': { vi: 'Còn {n} giờ · {ai} đang chờ', en: '{n} h left · {ai} is waiting' },
  'al.new': { vi: 'mới', en: 'new' },
  'al.newMail': { vi: '{ai} · thư mới', en: '{ai} · new message' },
  'ck.hours': { vi: '{n} giờ', en: '{n} h' },
  'ck.minutes': { vi: '{n} phút', en: '{n} min' },
  'ck.urgent': { vi: 'Gấp', en: 'Urgent' },
  'ck.todo': { vi: 'Chưa làm', en: 'To do' },
  'sub.viewPlans': { vi: 'Xem gói', en: 'View plans' },
  'sub.upgrade': { vi: 'Nâng cấp', en: 'Upgrade' },
  'tok.clickPlans': { vi: 'Bấm để xem các gói.', en: 'Click to see plans.' },
  'tok.out': { vi: 'Hết token', en: 'Out of tokens' },
  'tok.left': { vi: '{n} lượt', en: '{n} left' },
  'tok.today': { vi: 'hôm nay', en: 'today' },
  'tok.month': { vi: 'tháng này', en: 'this month' },
  'tok.dayGone': { vi: 'Hạn mức {n} token/ngày đã cạn. Chờ sang ngày mai hoặc nâng gói để hỏi tiếp.', en: 'The {n} tokens/day limit is used up. Wait until tomorrow or upgrade to keep asking.' },
  'tok.monthGone': { vi: 'Hạn mức {n} token/tháng đã cạn. Nâng gói để tiếp tục.', en: 'The {n} tokens/month limit is used up. Upgrade to continue.' },

  'tok.title': { vi: 'Gói {goi} — đã dùng {dung} / {tran} token hôm nay.\nTrợ lý đọc {ngay} ngày thư gần nhất; thư cũ hơn vẫn tìm được bằng từ khoá.\nBấm để xem các gói.', en: '{goi} plan — {dung} / {tran} tokens used today.\nThe assistant reads the last {ngay} days of mail; older mail is still searchable by keyword.\nClick to see plans.' },
  'tok.usedUp': { vi: 'Đã dùng hết token {khi} của gói {goi}', en: 'Out of {khi} tokens on the {goi} plan' },

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

/** Dịch ở BẤT KỲ đâu, kể cả ngoài component.
 *
 *  `thay` điền vào chỗ `{ten}` trong câu. Phải có nó vì rất nhiều câu là câu ghép
 *  ("Đã xoá 3 thư") mà TRẬT TỰ TỪ giữa hai thứ tiếng không giống nhau — nối chuỗi
 *  bằng `+` ở nơi gọi thì bản tiếng Anh mãi mãi kẹt theo trật tự tiếng Việt.
 *  Thiếu biến thì để nguyên `{ten}`: một chỗ trống nhìn thấy được thì sửa được,
 *  còn ném lỗi ở đây là làm vỡ cả màn hình chỉ vì một dòng chữ. */
export function t(khoa: string, thay?: Record<string, string | number>): string {
  const cau = TU_DIEN[khoa]?.[_ngonHienTai] ?? khoa
  if (!thay) return cau
  return cau.replace(/\{(\w+)\}/g, (nguyen, ten) =>
    ten in thay ? String(thay[ten]) : nguyen,
  )
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
  return (khoa: string, thay?: Record<string, string | number>): string => {
    const cau = TU_DIEN[khoa]?.[ngon] ?? khoa
    if (!thay) return cau
    return cau.replace(/\{(\w+)\}/g, (nguyen, ten) =>
      ten in thay ? String(thay[ten]) : nguyen,
    )
  }
}

/** Đọc/đổi ngôn ngữ hiện tại (dùng ở màn Cài đặt). */
export function useNgonNgu() {
  return useContext(Boi)
}
