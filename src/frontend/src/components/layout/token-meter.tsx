import { Zap, AlertTriangle } from 'lucide-react'
import type { SubscriptionStatus } from '@/lib/api'
import { cn } from '@/lib/utils'
import { dailyRatio, isOutOfTokens, turnsLeft } from '@/lib/subscription'

/* ══════════════════════════════════════════════════════════════════════════════
   ĐỒNG HỒ TOKEN — chip nhỏ nằm ngay cạnh ô nhập chat.

   Mục đích: người dùng luôn thấy mình còn bao nhiêu lượt hỏi, và khi hết thì hiểu
   ngay vì sao trợ lý ngừng trả lời (thay vì tưởng web hỏng).
   Quy token ra "lượt hỏi" cho dễ hình dung; số token đầy đủ nằm ở tooltip.
   ══════════════════════════════════════════════════════════════════════════════ */

function shortNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace('.', ',')}Tr`
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`
  return String(n)
}

export function TokenMeter({ status, onUpgrade, compact = false }: {
  status: SubscriptionStatus | null
  onUpgrade: () => void
  compact?: boolean
}) {
  if (!status) return null

  const ratio = dailyRatio(status)
  const left = turnsLeft(status)
  const out = isOutOfTokens(status)
  const low = !out && ratio >= 0.8

  const tone = out ? 'text-destructive' : low ? 'text-gold' : 'text-muted-foreground'
  const barTone = out ? 'bg-destructive' : low ? 'bg-gold' : 'bg-active'

  return (
    <button
      onClick={onUpgrade}
      title={`Gói ${status.tierLabel} — đã dùng ${status.daily.used.toLocaleString('vi-VN')} / ${status.daily.limit.toLocaleString('vi-VN')} token hôm nay. Bấm để xem các gói.`}
      className={cn(
        'group flex shrink-0 items-center gap-2 rounded-xl border border-border/60 bg-secondary/40 px-2.5 py-1.5',
        'transition-all hover:border-active/50 hover:bg-secondary active:scale-95',
        compact && 'px-2 py-1',
      )}
    >
      {out ? (
        <AlertTriangle className="size-3.5 shrink-0 text-destructive" />
      ) : (
        <Zap className={cn('size-3.5 shrink-0', low ? 'text-gold' : 'text-active')} />
      )}

      <span className="flex flex-col items-start gap-1">
        <span className={cn('font-mono text-[10.5px] font-semibold leading-none tabular-nums', tone)}>
          {out ? 'Hết token' : `${left} lượt`}
        </span>
        {!compact && (
          <span className="h-1 w-14 overflow-hidden rounded-full bg-border/70">
            <span
              className={cn('block h-full rounded-full transition-[width] duration-700 ease-soft', barTone)}
              style={{ width: `${Math.max(2, ratio * 100)}%` }}
            />
          </span>
        )}
      </span>

      <span className="hidden text-[10px] font-medium uppercase tracking-wider text-muted-foreground group-hover:text-active sm:inline">
        {status.tierLabel}
      </span>
    </button>
  )
}

/** Băng cảnh báo khi đã cạn hạn mức — hiện ngay trên ô nhập, kèm lối nâng cấp. */
export function QuotaBanner({ status, onUpgrade }: {
  status: SubscriptionStatus | null
  onUpgrade: () => void
}) {
  if (!status || !isOutOfTokens(status)) return null
  const daily = status.daily.remaining <= 0
  return (
    <div className="mb-2 flex items-center gap-3 rounded-2xl border border-destructive/35 bg-destructive/10 px-3.5 py-2.5">
      <AlertTriangle className="size-4 shrink-0 text-destructive" />
      <div className="min-w-0 flex-1">
        <p className="text-[12.5px] font-semibold text-foreground">
          Đã dùng hết token {daily ? 'hôm nay' : 'tháng này'} của gói {status.tierLabel}
        </p>
        <p className="mt-0.5 text-[11.5px] leading-relaxed text-muted-foreground">
          {daily
            ? `Hạn mức ${shortNum(status.daily.limit)} token/ngày đã cạn. Chờ sang ngày mai hoặc nâng gói để hỏi tiếp.`
            : `Hạn mức ${shortNum(status.monthly.limit)} token/tháng đã cạn. Nâng gói để tiếp tục.`}
        </p>
      </div>
      <button
        onClick={onUpgrade}
        className="shrink-0 rounded-xl bg-active px-3 py-1.5 text-[12px] font-semibold text-active-foreground transition-transform active:scale-95"
      >
        Nâng cấp
      </button>
    </div>
  )
}
