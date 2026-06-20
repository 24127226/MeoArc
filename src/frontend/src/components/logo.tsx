import { cn } from '@/lib/utils'

/**
 * Logo MeoArc: con mèo cuộn nằm trên hòm thư, đuôi là một nét cung brass-gold mảnh.
 * Dùng currentColor cho thân mèo/hòm thư + accent (brass-gold) cho đuôi & khe thư.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      className={cn('size-9', className)}
      aria-hidden="true"
    >
      {/* Hòm thư */}
      <rect
        x="9"
        y="24"
        width="30"
        height="16"
        rx="5"
        fill="currentColor"
        opacity="0.12"
      />
      <rect
        x="9"
        y="24"
        width="30"
        height="16"
        rx="5"
        stroke="currentColor"
        strokeWidth="2"
      />
      {/* Khe bỏ thư — brass gold */}
      <rect x="19" y="30" width="10" height="2.4" rx="1.2" fill="var(--accent)" />

      {/* Thân mèo cuộn tròn */}
      <path
        d="M16 24c-1.5-6 2.5-11 8-11s9.5 5 8 11"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        fill="currentColor"
        fillOpacity="0.06"
      />
      {/* Hai tai */}
      <path d="M17.5 15.5l-1.2-3.2 3 1.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M30.5 15.5l1.2-3.2-3 1.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

      {/* Đuôi — nét cung brass-gold mảnh */}
      <path
        d="M31.5 22c4.5-1 7.5 2 6.5 6.5"
        stroke="var(--accent)"
        strokeWidth="2.4"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  )
}

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string
  showWordmark?: boolean
}) {
  return (
    <div className={cn('flex flex-col items-center gap-1', className)}>
      <LogoMark className="text-emphasis" />
      {showWordmark && (
        <span className="font-serif text-sm font-semibold tracking-wide text-foreground">
          MeoArc
        </span>
      )}
    </div>
  )
}
