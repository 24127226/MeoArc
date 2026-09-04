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
  'settings.langNote': {
    vi: 'Đổi ngôn ngữ khung giao diện và ngôn ngữ trợ lý trả lời. Một số phần (thẻ kết quả, thông báo lỗi) hiện vẫn là tiếng Việt.',
    en: 'Changes the interface chrome and the language the assistant replies in. Some parts (result cards, error messages) are still in Vietnamese.',
  },
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

  return <Boi.Provider value={{ ngon, datNgon: setNgon }}>{children}</Boi.Provider>
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
