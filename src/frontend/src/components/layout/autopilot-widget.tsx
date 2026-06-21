import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import {
  Archive,
  MailOpen,
  Star,
  Send,
  Inbox,
  Check,
  X,
  Undo2,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  Clock,
  History,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { MeoMascot } from '@/components/meo-mascot'
import { CATEGORY } from '@/data/categories'
import type { AutopilotAction, AutopilotStep, AgentReply } from '@/lib/agent'

/** Kết quả tự lái gửi về ChatPanel để áp dụng thật qua EmailActions. */
export type AutopilotResult = {
  archive: string[]
  markRead: string[]
  flag: string[]
  counts: { archive: number; markRead: number; flag: number; replied: number; kept: number }
}

type Tone = 'safe' | 'risk' | 'hold'

const ACTION_META: Record<AutopilotAction, { icon: React.ElementType; label: string; tone: Tone }> =
  {
    archive: { icon: Archive, label: 'Lưu trữ', tone: 'safe' },
    markRead: { icon: MailOpen, label: 'Đánh dấu đã đọc', tone: 'safe' },
    flag: { icon: Star, label: 'Gắn sao', tone: 'safe' },
    reply: { icon: Send, label: 'Soạn trả lời', tone: 'risk' },
    keep: { icon: Inbox, label: 'Giữ lại', tone: 'hold' },
  }

const TONE_CHIP: Record<Tone, string> = {
  safe: 'bg-success/15 text-success ring-success/30',
  risk: 'bg-spark/25 text-foreground ring-spark/50',
  hold: 'bg-popover-foreground/10 text-muted-foreground ring-border',
}

const TONE_DOT: Record<Tone, string> = {
  safe: 'bg-success',
  risk: 'bg-spark',
  hold: 'bg-muted-foreground/40',
}

const STEP_MS = 1050

/** Avatar nhuốm màu category của thư. */
function CatAvatar({ initial, category, size = 'md' }: { initial: string; category: AutopilotStep['category']; size?: 'sm' | 'md' }) {
  const c = CATEGORY[category]
  return (
    <span
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full font-serif font-semibold ring-1 ring-inset',
        size === 'md' ? 'size-9 text-sm' : 'size-7 text-xs',
      )}
      style={
        {
          backgroundColor: `color-mix(in srgb, ${c.bar} 22%, transparent)`,
          color: c.ink,
          ['--tw-ring-color']: `color-mix(in srgb, ${c.bar} 45%, transparent)`,
        } as CSSProperties
      }
    >
      {initial}
    </span>
  )
}

function ActionChip({ action, className }: { action: AutopilotAction; className?: string }) {
  const m = ACTION_META[action]
  const Icon = m.icon
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset',
        TONE_CHIP[m.tone],
        className,
      )}
    >
      <Icon className="size-3.5" />
      {m.label}
    </span>
  )
}

/** Inbox Autopilot (UC017) — hộp thư tự lái, ambient + reversible. */
export function AutopilotWidget({
  reply,
  resolved,
  id,
  onApply,
}: {
  reply: Extract<AgentReply, { kind: 'autopilot' }>
  resolved?: boolean
  id: string
  onApply: (id: string, result: AutopilotResult) => void
}) {
  const plan = reply.plan
  const N = plan.length

  const [phase, setPhase] = useState<'running' | 'paused' | 'done'>(resolved ? 'done' : 'running')
  const [cursor, setCursor] = useState(resolved ? N : 0) // số thư đã lướt qua
  const [viewAt, setViewAt] = useState<number | null>(null) // đang tua xem lại bước nào
  const [overrides, setOverrides] = useState<Record<string, true>>({}) // bước bị hoàn tác → 'keep'
  const [approved, setApproved] = useState<Set<string>>(new Set()) // thư rủi ro đã duyệt gửi
  const [applied, setApplied] = useState(!!resolved)

  // Tự lướt từng thư khi đang chạy (dừng nếu đang tua xem lại)
  useEffect(() => {
    if (phase !== 'running' || viewAt !== null) return
    if (cursor >= N) {
      setPhase('done')
      return
    }
    const t = window.setTimeout(() => setCursor((c) => c + 1), cursor === 0 ? 650 : STEP_MS)
    return () => window.clearTimeout(t)
  }, [phase, viewAt, cursor, N])

  const effAction = (s: AutopilotStep): AutopilotAction => (overrides[s.id] ? 'keep' : s.action)
  const isPending = (s: AutopilotStep) => s.risky && !approved.has(s.id) && !overrides[s.id]

  const activeIndex = viewAt ?? Math.min(cursor, N - 1)
  const activeStep = plan[activeIndex]
  const processed = useMemo(
    () => plan.map((s, i) => ({ s, i })).filter(({ i }) => i < cursor),
    [plan, cursor],
  )
  const pendingCount = plan.filter((s, i) => i < cursor && isPending(s)).length

  const result = useMemo<AutopilotResult>(() => {
    const pick = (a: AutopilotAction) => plan.filter((s) => effAction(s) === a).map((s) => s.id)
    const archive = pick('archive')
    const markRead = pick('markRead')
    const flag = pick('flag')
    const replied = plan.filter((s) => s.risky && approved.has(s.id) && !overrides[s.id]).length
    const kept = N - archive.length - markRead.length - flag.length - replied
    return { archive, markRead, flag, counts: { archive: archive.length, markRead: markRead.length, flag: flag.length, replied, kept } }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan, overrides, approved, N])

  const restart = () => {
    setOverrides({})
    setApproved(new Set())
    setCursor(0)
    setViewAt(null)
    setPhase('running')
  }
  const undoStep = (sid: string) => setOverrides((p) => ({ ...p, [sid]: true }))
  const redoStep = (sid: string) =>
    setOverrides((p) => {
      const n = { ...p }
      delete n[sid]
      return n
    })
  const approve = (sid: string) => setApproved((p) => new Set(p).add(sid))

  const headTint = activeStep ? CATEGORY[activeStep.category].bar : 'var(--spark)'

  return (
    <div
      className={cn(
        'overflow-hidden rounded-3xl shadow-float glass',
        phase === 'done' && !applied && 'ripe-pulse',
      )}
    >
      {/* Cockpit — mèo phi công + tiến trình */}
      <div className="stars-faint relative flex items-center gap-3 border-b border-border/40 px-4 py-3.5">
        <span className="bokeh flex size-11 shrink-0 items-center justify-center">
          <MeoMascot
            thinking={phase === 'running' && viewAt === null}
            mood={phase === 'done' ? 'happy' : phase === 'running' ? 'thinking' : 'idle'}
            className="size-11"
          />
        </span>
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 font-serif text-[15px] font-semibold leading-tight text-foreground">
            <Sparkles className="size-3.5 text-active" />
            {phase === 'done' ? 'Mèo đã lái xong hộp thư' : 'Mèo đang tự lái hộp thư'}
          </p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {Math.min(cursor, N)}/{N} thư ·{' '}
            {viewAt !== null ? 'đang xem lại' : phase === 'running' ? 'đang chạy' : phase === 'paused' ? 'tạm dừng' : 'hoàn tất'}
          </p>
        </div>
        {phase !== 'done' ? (
          <button
            onClick={() => {
              if (phase === 'running') setPhase('paused')
              else {
                setViewAt(null)
                setPhase(cursor >= N ? 'done' : 'running')
              }
            }}
            title={phase === 'running' ? 'Tạm dừng' : 'Tiếp tục'}
            aria-label={phase === 'running' ? 'Tạm dừng' : 'Tiếp tục'}
            className="flex size-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-colors ease-spring hover:bg-secondary hover:text-foreground active:scale-90"
          >
            {phase === 'running' ? <Pause className="size-4" /> : <Play className="size-4" />}
          </button>
        ) : (
          <button
            onClick={restart}
            title="Chạy lại"
            aria-label="Chạy lại"
            className="flex size-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-colors ease-spring hover:bg-secondary hover:text-foreground active:scale-90"
          >
            <RotateCcw className="size-4" />
          </button>
        )}
      </div>

      {/* Thanh tiến trình mọng */}
      <div className="h-1 w-full bg-popover-foreground/10">
        <div
          className="h-full rounded-r-full bg-active transition-[width] duration-500 ease-soft"
          style={{ width: `${Math.round((Math.min(cursor, N) / N) * 100)}%` }}
        />
      </div>

      <div className="space-y-3.5 p-4">
        {/* Thẻ thư hero — nhuốm màu category, đổi theo thư đang xử lý/xem lại */}
        {activeStep && (
          <div
            key={activeIndex}
            className="ripe shadow-tint duration-300 animate-in fade-in slide-in-from-bottom-2 rounded-2xl p-3.5"
            style={{ ['--tint' as string]: headTint }}
          >
            <div className="flex items-start gap-3">
              <CatAvatar initial={activeStep.initial} category={activeStep.category} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="min-w-0 flex-1 truncate text-sm font-semibold text-foreground">
                    {activeStep.sender}
                  </p>
                  {viewAt !== null && (
                    <span className="flex shrink-0 items-center gap-1 rounded-full bg-popover-foreground/10 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                      <History className="size-3" />
                      bước {viewAt + 1}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{activeStep.subject}</p>
              </div>
            </div>

            {/* TL;DR Mèo đọc được */}
            <p className="mt-2.5 line-clamp-2 border-l-2 border-active/40 pl-2.5 text-xs italic leading-relaxed text-foreground/75">
              {activeStep.tldr}
            </p>

            {/* Quyết định + lý do (pop khi đổi thư) */}
            <div
              key={`d${activeIndex}-${effAction(activeStep)}`}
              className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1.5 duration-300 animate-in fade-in slide-in-from-bottom-1"
            >
              <ActionChip action={effAction(activeStep)} />
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <ChevronRight className="size-3.5 shrink-0 text-active" />
                {overrides[activeStep.id] ? 'Bạn đã hoàn tác — giữ lại thư này' : activeStep.reason}
              </span>
            </div>

            {/* Hàng nút theo ngữ cảnh */}
            <div className="mt-3 flex flex-wrap gap-2">
              {viewAt !== null && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setViewAt(null)
                    setPhase(cursor >= N ? 'done' : 'running')
                  }}
                >
                  <Play className="size-4" />
                  Về hiện tại
                </Button>
              )}
              {isPending(activeStep) ? (
                <>
                  <Button size="sm" variant="primary" onClick={() => approve(activeStep.id)}>
                    <Check className="size-4" />
                    Duyệt &amp; gửi
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => undoStep(activeStep.id)}>
                    <X className="size-4" />
                    Bỏ qua
                  </Button>
                </>
              ) : (
                effAction(activeStep) !== 'keep' && (
                  <Button size="sm" variant="ghost" onClick={() => undoStep(activeStep.id)}>
                    <Undo2 className="size-4" />
                    Hoàn tác bước này
                  </Button>
                )
              )}
              {overrides[activeStep.id] && (
                <Button size="sm" variant="ghost" onClick={() => redoStep(activeStep.id)}>
                  <RotateCcw className="size-4" />
                  Khôi phục đề xuất
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Cỗ máy thời gian — tua lại từng thao tác */}
        <div>
          <div className="mb-2 flex items-center gap-1.5">
            <History className="size-3.5 text-muted-foreground" />
            <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Cỗ máy thời gian
            </span>
            <span className="text-[11px] text-muted-foreground/70">— bấm để tua lại</span>
          </div>
          <div className="flex items-center px-0.5">
            {plan.map((s, i) => {
              const state = i < cursor ? 'done' : i === cursor ? 'current' : 'pending'
              const tone = ACTION_META[effAction(s)].tone
              const isActive = i === activeIndex
              return (
                <div key={s.id} className="flex flex-1 items-center last:flex-none">
                  <button
                    onClick={() => {
                      if (i >= cursor) return
                      setViewAt(i)
                      setPhase('paused')
                    }}
                    disabled={i >= cursor}
                    title={`${s.sender} · ${ACTION_META[effAction(s)].label}`}
                    aria-label={`Tua về ${s.sender}`}
                    className={cn(
                      'flex size-4 shrink-0 items-center justify-center rounded-full transition-transform ease-spring',
                      i < cursor && 'hover:scale-125 active:scale-95',
                      isActive && 'scale-125',
                    )}
                  >
                    <span
                      className={cn(
                        'block rounded-full',
                        state === 'current'
                          ? 'cherry-dot size-3'
                          : state === 'done'
                            ? cn('size-2.5', TONE_DOT[tone], isActive && 'ring-2 ring-inset ring-foreground/30')
                            : 'size-2 bg-border',
                      )}
                    />
                  </button>
                  {i < N - 1 && (
                    <span
                      className={cn(
                        'h-px flex-1 border-t border-dashed transition-colors',
                        i < cursor - 1 ? 'border-active/40' : 'border-border/50',
                      )}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Sổ nhật ký — các thư đã xử lý, có thể hoàn tác / duyệt */}
        {processed.length > 0 && (
          <div className="space-y-1.5 border-t border-border/40 pt-3">
            {processed
              .slice()
              .reverse()
              .filter(({ i }) => i !== activeIndex)
              .map(({ s }) => {
                const act = effAction(s)
                const pending = isPending(s)
                return (
                  <div
                    key={s.id}
                    className="flex items-center gap-2.5 rounded-xl bg-popover-foreground/5 p-2"
                  >
                    <CatAvatar initial={s.initial} category={s.category} size="sm" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium text-foreground">{s.sender}</p>
                      <p className="truncate text-[11px] text-muted-foreground">{s.subject}</p>
                    </div>
                    {pending ? (
                      <div className="flex shrink-0 items-center gap-1">
                        <span className="hidden rounded-full bg-spark/25 px-2 py-0.5 text-[10px] font-semibold text-foreground ring-1 ring-inset ring-spark/50 sm:inline">
                          chờ duyệt
                        </span>
                        <button
                          onClick={() => approve(s.id)}
                          title="Duyệt & gửi"
                          aria-label="Duyệt và gửi"
                          className="flex size-7 items-center justify-center rounded-lg text-success transition-colors hover:bg-success/15 active:scale-90"
                        >
                          <Check className="size-4" />
                        </button>
                        <button
                          onClick={() => undoStep(s.id)}
                          title="Bỏ qua"
                          aria-label="Bỏ qua"
                          className="flex size-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-popover-foreground/10 hover:text-foreground active:scale-90"
                        >
                          <X className="size-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex shrink-0 items-center gap-1">
                        {s.risky && approved.has(s.id) ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-success/15 px-2.5 py-1 text-[11px] font-semibold text-success ring-1 ring-inset ring-success/30">
                            <Send className="size-3.5" />
                            Đã duyệt gửi
                          </span>
                        ) : (
                          <ActionChip action={act} />
                        )}
                        <button
                          onClick={() => (overrides[s.id] ? redoStep(s.id) : undoStep(s.id))}
                          title={overrides[s.id] ? 'Khôi phục đề xuất' : 'Hoàn tác'}
                          aria-label={overrides[s.id] ? 'Khôi phục' : 'Hoàn tác'}
                          className="flex size-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-popover-foreground/10 hover:text-foreground active:scale-90"
                        >
                          {overrides[s.id] ? <RotateCcw className="size-4" /> : <Undo2 className="size-4" />}
                        </button>
                      </div>
                    )}
                  </div>
                )
              })}
          </div>
        )}

        {/* Tổng kết + áp dụng (khi xong) */}
        {phase === 'done' && (
          <div className="space-y-3 border-t border-border/40 pt-3 duration-300 animate-in fade-in slide-in-from-bottom-2">
            <div className="grid grid-cols-4 gap-2">
              {[
                { label: 'Lưu trữ', value: result.counts.archive },
                { label: 'Đã đọc', value: result.counts.markRead },
                { label: 'Gắn sao', value: result.counts.flag },
                { label: 'Đã gửi', value: result.counts.replied },
              ].map((t) => (
                <div
                  key={t.label}
                  className="ripe rounded-xl bg-popover-foreground/5 p-2 text-center"
                  style={{ ['--tint' as string]: 'var(--spark)' }}
                >
                  <p className="font-serif text-xl font-semibold text-foreground">{t.value}</p>
                  <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{t.label}</p>
                </div>
              ))}
            </div>

            {pendingCount > 0 && (
              <p className="flex items-center gap-1.5 rounded-xl bg-spark/15 px-3 py-2 text-xs text-foreground">
                <Clock className="size-3.5 shrink-0 text-active" />
                Còn {pendingCount} thư cần bạn duyệt trước khi gửi — chọn ✓ ở danh sách trên.
              </p>
            )}

            {applied || resolved ? (
              <span className="flex items-center gap-2 text-xs font-medium text-success">
                <Check className="size-4" />
                Đã áp dụng vào hộp thư
              </span>
            ) : (
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                onClick={() => {
                  setApplied(true)
                  onApply(id, result)
                }}
              >
                <Check className="size-4" />
                Áp dụng vào hộp thư
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
