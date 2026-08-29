import { flushSync } from 'react-dom'

/* ══════════════════════════════════════════════════════════════════════════════
   CHUYỂN CẢNH — bọc một thay đổi trạng thái để trình duyệt vẽ chuyển tiếp

   VÌ SAO CẦN. Đổi trang hay mở một khung trong React là một cú nhảy tức thì: nội
   dung cũ biến mất, nội dung mới xuất hiện trong CÙNG MỘT KHUNG HÌNH. Mắt người
   không có gì để bám nên mất một nhịp để định vị lại — cảm giác "giật" mà người
   dùng mô tả là "hiện ra một cái tức thì".

   View Transitions API giải quyết đúng chuyện đó: trình duyệt chụp ảnh trạng thái
   cũ, để React đổi DOM, chụp trạng thái mới, rồi nội suy giữa hai ảnh.

   BA CHI TIẾT DỄ SAI, ghi lại để khỏi vấp:

   1. `flushSync` là BẮT BUỘC. React 19 gom các cập nhật lại và chạy sau; nếu không
      ép đồng bộ trong callback thì trình duyệt chụp "ảnh mới" lúc DOM còn y nguyên
      ảnh cũ, và kết quả là không có chuyển tiếp nào cả — hoặc tệ hơn, ảnh chụp
      đứng che mất giao diện thật.

   2. Phải THOÁI LUI AN TOÀN. Safari cũ và Firefox chưa có API này; thiếu nhánh dự
      phòng thì nút bấm chết hẳn chứ không phải chỉ mất hiệu ứng.

   3. Phải tôn trọng `prefers-reduced-motion`. Chuyển cảnh toàn màn là đúng loại
      chuyển động gây khó chịu cho người nhạy cảm tiền đình.
   ══════════════════════════════════════════════════════════════════════════════ */

type CoTheChuyen = {
  startViewTransition?: (cb: () => void) => unknown
}

/** Chạy `fn` bên trong một chuyển cảnh, nếu trình duyệt và người dùng cho phép. */
export function chuyenCanh(fn: () => void): void {
  const giamChuyenDong = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const doc = document as unknown as CoTheChuyen
  if (giamChuyenDong || typeof doc.startViewTransition !== 'function') {
    fn()
    return
  }
  try {
    doc.startViewTransition(() => flushSync(fn))
  } catch {
    // Chuyển cảnh chỉ là lớp trang trí. Hỏng thì vẫn phải đổi được trạng thái —
    // nuốt lỗi ở đây là đúng, còn để nó nổi lên thì một hiệu ứng làm chết cả nút.
    fn()
  }
}
