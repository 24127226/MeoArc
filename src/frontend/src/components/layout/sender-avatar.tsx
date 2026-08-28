import { useState } from 'react'
import { cn } from '@/lib/utils'
import { duongDanApi, apiBaseUrlDaCauHinh } from '@/lib/api'

/**
 * SenderAvatar — ảnh đại diện người gửi.
 *
 * Tổ chức (github.com, vercel.com, hcmus.edu.vn…) hiện BIỂU TƯỢNG NHẬN DIỆN của
 * họ; cá nhân dùng hộp thư phổ thông giữ chữ cái đầu.
 *
 * ── CHỮ CÁI ĐẦU KHÔNG PHẢI GIẢI PHÁP TẠM ──
 * Nó là câu trả lời đúng khi không có gì thật để hiển thị. Cái sai của bản trước
 * không phải "dùng chữ cái" mà là dùng chữ cái CẢ KHI có thứ tốt hơn: thư từ
 * GitHub, Google Cloud, Vercel đều có biểu tượng ai cũng nhận ra trong một phần
 * mười giây, trong khi chữ "G" thì chung cho Google, GitHub, Grab, Groq.
 *
 * ── VÌ SAO KHÔNG CÓ ẢNH GOOGLE CỦA CÁ NHÂN ──
 * Gmail API không trả ảnh người gửi. Muốn có phải dùng People API, mà nó chỉ trả
 * ảnh của người NẰM TRONG DANH BẠ và đòi thêm quyền `contacts.readonly`. Xin
 * quyền đọc toàn bộ danh bạ chỉ để vẽ một hình tròn là cái giá quá đắt, và trái
 * với điều trang giới thiệu đang hứa — xin ít quyền nhất có thể. Xem thêm phần
 * giải thích ở `app/api/avatar.py`.
 *
 * Lấy biểu tượng qua BACKEND chứ không gọi thẳng: gọi thẳng thì mỗi lần hiển thị
 * hộp thư, trình duyệt gửi cho bên thứ ba danh sách tên miền người dùng đang
 * liên hệ. Đó là rò rỉ quan hệ, và nó xảy ra âm thầm sau mỗi lần cuộn.
 */
export function SenderAvatar({
  email,
  initial,
  className,
  style,
}: {
  /** Địa chỉ thư người gửi — dùng để lấy tên miền. */
  email?: string
  /** Chữ cái đầu, dùng khi không có biểu tượng. */
  initial: string
  className?: string
  style?: React.CSSProperties
}) {
  const [hong, setHong] = useState(false)
  const tenMien = (email ?? '').split('@')[1]?.trim().toLowerCase()

  // Không có backend (chế độ mock) thì đừng gọi — sẽ 404 và nháy một nhịp trống.
  const coTheThu = apiBaseUrlDaCauHinh && !!tenMien && !hong

  return (
    <div className={cn('relative overflow-hidden', className)} style={style}>
      {/* Chữ cái LUÔN được vẽ, nằm dưới. Nhờ vậy lúc ảnh đang tải, hoặc khi không
          có ảnh, ô vẫn đầy — không có khoảnh khắc nào hiện ra một hình tròn rỗng. */}
      <span className="absolute inset-0 flex items-center justify-center">{initial}</span>
      {coTheThu && (
        <img
          src={duongDanApi(`/avatars/${encodeURIComponent(tenMien)}`)}
          alt=""
          aria-hidden
          loading="lazy"
          decoding="async"
          onError={() => setHong(true)}
          className="relative size-full object-contain p-1.5"
        />
      )}
    </div>
  )
}
