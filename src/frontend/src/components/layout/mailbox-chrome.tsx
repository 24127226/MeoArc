import type { ReactNode } from 'react'
import { t } from '@/lib/ngon-ngu'

/**
 * MailboxChrome — thanh đầu cột Hộp thư.
 *
 * Bản trước dựng theo lối "thư quán Pháp": dải sơn polygon navy/ngà/đỏ kiểu huy hiệu,
 * tiêu đề serif giãn chữ, phụ đề "Maison de la Correspondance". Rất đẹp, nhưng nó nói
 * SAI về sản phẩm — người dùng vừa rời trang giới thiệu vũ trụ/neon thì rơi vào một
 * tiệm văn phòng phẩm thế kỷ 19, và não đọc ngay ra là hai phần do hai nơi làm.
 *
 * Bản này nói đúng thứ đang chạy: một thanh trạng thái kỹ thuật — nhãn micro chữ hoa,
 * số đếm dạng monospace, một chấm nhịp báo hệ thống đang sống, và một đường quét sáng
 * mảnh ở đáy. Ngôn ngữ của bảng điều khiển, không phải của giấy viết thư.
 */
export function MailboxChrome({
  title,
  subtitle = t('sh.syncing'),
  count,
  right,
}: {
  title: string
  subtitle?: string
  /** Số thư chưa đọc — hiện dạng monospace, thứ ngôn ngữ kỹ thuật quen thuộc. */
  count?: number
  right?: ReactNode
}) {
  return (
    <div className="relative shrink-0 overflow-hidden px-5 pb-4 pt-5">
      {/* Lưới mảnh phía sau — mắt không nhìn ra, nhưng não đọc được là "môi trường kỹ thuật" */}
      {/* Lưới kẻ ĐÃ BỎ, thay bằng kính mờ. Sọc/lưới là hoa văn: nó lặp lại nên
          mắt luôn thấy nó, và đặt sau chữ thì nó tranh chỗ với chữ. Kính mờ
          không có hoa văn nào để nhìn — mắt lướt qua, đúng việc của một cái nền. */}
      <div className="kinh-mo pointer-events-none absolute inset-0 z-0" />

      {/* Đường quét sáng ở đáy: một sợi neon mảnh thay cho rãnh cơ khí cũ */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 z-10">
        <div className="h-px w-full bg-gradient-to-r from-transparent via-[var(--spark)]/45 to-transparent" />
      </div>

      <div className="relative z-10 flex w-full items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-baseline gap-2.5">
            <h2 className="truncate text-[19px] font-semibold leading-none tracking-tight text-foreground">
              {title}
            </h2>
            {count != null && (
              <span className="font-mono text-[12px] tabular-nums text-[var(--spark)]">
                {String(count).padStart(2, '0')}
              </span>
            )}
          </div>
          <p className="mt-2 flex items-center gap-1.5 text-[9.5px] uppercase tracking-[0.18em] text-muted-foreground/60">
            {/* Chấm nhịp — dấu hiệu duy nhất cần thiết để nói "hệ thống đang sống" */}
            <span className="pulse-dot" aria-hidden />
            {subtitle}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-0.5">{right}</div>
      </div>
    </div>
  )
}
