import { Sparkles, Zap, Crown } from 'lucide-react'
import type { SubscriptionStatus, TokenBucket } from '@/lib/api'
import { cn } from '@/lib/utils'
import { t } from '@/lib/ngon-ngu'

/* ══════════════════════════════════════════════════════════════════════════════
   KHỐI GÓI & HẠN MỨC TOKEN — nhúng trong menu tài khoản (UC013 mở rộng).

   Số liệu là thật: backend đếm token ở bảng subscriptions, cộng sau mỗi lượt agent.
   Trang chọn gói nằm riêng ở pricing-screen.tsx (chiếm trọn khung hình).
   ══════════════════════════════════════════════════════════════════════════════ */

const TIER_ICON: Record<string, React.ElementType> = { free: Sparkles, pro: Zap, max: Crown }

/** 1.234.567 → "1,2Tr" · 45.600 → "46K" — đọc nhanh hơn số đầy đủ. */
export function shortNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1).replace('.', ',')}Tr`
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`
  return String(n)
}

/** Thanh tiêu thụ token — đổi màu khi gần chạm trần. */
export function UsageBar({ bucket, label }: { bucket: TokenBucket; label: string }) {
  const pct = bucket.limit > 0 ? Math.min(100, (bucket.used / bucket.limit) * 100) : 0
  const level = pct >= 90 ? 'crit' : pct >= 70 ? 'warn' : 'ok'
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          {label}
        </span>
        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
          <span className={cn('font-semibold',
            level === 'crit' ? 'text-destructive' : level === 'warn' ? 'text-gold' : 'text-foreground')}>
            {shortNumber(bucket.used)}
          </span>
          {' / '}{shortNumber(bucket.limit)} token
        </span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-secondary">
        <div
          className={cn('h-full rounded-full transition-[width] duration-700 ease-soft',
            level === 'crit' ? 'bg-destructive' : level === 'warn' ? 'bg-gold' : 'bg-active')}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

/** Khối tóm tắt gói + mức dùng — nhúng trong menu tài khoản. */
export function UsageSummary({ status, onOpenPlans }: {
  status: SubscriptionStatus | null
  onOpenPlans: () => void
}) {
  if (!status) {
    return (
      <div className="rounded-2xl border border-border/60 bg-secondary/40 p-3.5">
        <div className="skeleton h-3 w-24 rounded" />
        <div className="skeleton mt-3 h-1.5 w-full rounded-full" />
      </div>
    )
  }
  const Icon = TIER_ICON[status.tier] ?? Sparkles
  const nearLimit = status.daily.limit > 0 && status.daily.used / status.daily.limit >= 0.8
  return (
    <div className="rounded-2xl border border-border/60 bg-secondary/40 p-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <span className="flex size-6 items-center justify-center rounded-lg bg-active/15 text-active">
            <Icon className="size-3.5" />
          </span>
          Gói {status.tierLabel}
        </span>
        <button
          onClick={onOpenPlans}
          className="rounded-full bg-active px-3 py-1 text-[11px] font-semibold text-active-foreground transition-transform active:scale-95"
        >
          {t(status.tier === 'max' ? 'sub.viewPlans' : 'sub.upgrade')}
        </button>
      </div>
      <div className="mt-3 space-y-2.5">
        <UsageBar bucket={status.daily} label={t('cal.today')} />
        <UsageBar bucket={status.monthly} label={t('sub.thisMonth')} />
      </div>
      {nearLimit && (
        <p className="mt-2.5 text-[11px] leading-relaxed text-gold">
          Sắp chạm hạn mức ngày. Hết token thì trợ lý tạm nghỉ tới ngày mai.
        </p>
      )}
    </div>
  )
}
