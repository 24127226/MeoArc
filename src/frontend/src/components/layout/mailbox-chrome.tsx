import type { ReactNode } from 'react'

/**
 * MailboxChrome — KHUNG header thanh lịch tái hiện đúng "khung Trợ lý MeoArc" của ChatPanel
 * (dải sơn polygon navy/ngà/đỏ + rãnh cơ khí + tiêu đề serif giãn chữ căn giữa), nhưng dùng
 * cho HỘP THƯ khi tắt AI. Nhận `right` = khay công cụ (tìm/lọc/soạn/làm mới) nép phải.
 * Tách riêng để KHÔNG đụng ChatPanel (giữ nguyên hiệu ứng sơn tan chảy của nó).
 */
export function MailboxChrome({
  title,
  subtitle = 'Maison de la Correspondance',
  right,
}: {
  title: string
  subtitle?: string
  right?: ReactNode
}) {
  return (
    <div className="group relative shrink-0 overflow-hidden bg-gradient-to-b from-foreground/[0.04] to-foreground/[0.01] px-6 pb-5 pt-6 backdrop-blur-xl">
      {/* Rãnh cơ khí 3D ở đáy — khe sáng + bóng lún tách lớp với danh sách bên dưới */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 z-10 flex flex-col">
        <div className="h-[1px] w-full border-t border-white/[0.08] bg-background/50" />
        <div className="h-[1px] w-full bg-black/40 shadow-[0_1px_3px_rgba(0,0,0,0.4)]" />
      </div>

      {/* Dải sơn polygon 2 cánh đối xứng (đồng bộ với header Trợ lý MeoArc) */}
      <div className="pointer-events-none absolute inset-0 z-0">
        <svg
          className="h-full w-full"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
          viewBox="0 0 320 90"
          aria-hidden
        >
          <defs>
            <linearGradient id="mbx-glow-left" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="color-mix(in srgb, var(--active) 35%, transparent)" />
              <stop offset="100%" stopColor="transparent" />
            </linearGradient>
            <linearGradient id="mbx-glow-right" x1="100%" y1="0%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="color-mix(in srgb, var(--active) 35%, transparent)" />
              <stop offset="100%" stopColor="transparent" />
            </linearGradient>
          </defs>
          <path d="M 0,0 L 25,0 L 75,90 L 0,90 Z" fill="#0b1d3a" opacity="0.95" />
          <path d="M 25,0 L 60,0 L 110,90 L 75,90 Z" fill="#ffffff" opacity="1" />
          <path d="M 60,0 L 95,0 L 145,90 L 110,90 Z" fill="#a62b2b" opacity="0.95" />
          <path d="M 95,0 L 115,0 L 165,90 L 145,90 Z" fill="url(#mbx-glow-left)" opacity="0.35" />
          <path d="M 320,0 L 295,0 L 245,90 L 320,90 Z" fill="#0b1d3a" opacity="0.95" />
          <path d="M 295,0 L 260,0 L 210,90 L 245,90 Z" fill="#ffffff" opacity="1" />
          <path d="M 260,0 L 225,0 L 175,90 L 210,90 Z" fill="#a62b2b" opacity="0.95" />
          <path d="M 225,0 L 205,0 L 155,90 L 175,90 Z" fill="url(#mbx-glow-right)" opacity="0.35" />
        </svg>
      </div>

      {/* Tiêu đề căn giữa tuyệt đối + khay công cụ nép phải */}
      <div className="relative z-10 flex w-full items-center justify-between">
        <div className="ml-12 size-9 shrink-0" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 select-none text-center">
          <h2
            className="font-serif text-[22px] font-black uppercase leading-none tracking-[0.38em] text-foreground transition-all duration-700 group-hover:tracking-[0.42em]"
            style={{ textShadow: '0 1px 1px rgba(255,255,255,0.22)', letterSpacing: '0.38em' }}
          >
            {title}
          </h2>
          <p className="mt-2 font-serif text-[8.5px] italic tracking-[0.28em] text-muted-foreground/50">
            {subtitle}
          </p>
        </div>
        <div className="relative z-10 flex shrink-0 items-center gap-0.5">{right}</div>
      </div>
    </div>
  )
}
