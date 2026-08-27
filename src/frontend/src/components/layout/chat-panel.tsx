import { Fragment, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import {
  Sparkles,
  Check,
  X,
  Send,
  Paperclip,
  ListChecks,
  Mail,
  AlertTriangle,
  CheckCircle2,
  FileText,
  History,
  SquarePen,
  Search,
  Loader2,
  CalendarClock,
  Users,
  CheckSquare,
  Square,
  Clock,
  BarChart3,
  Pin,
  PinOff,
  Pencil,
  Trash2,
  Mic,
  Volume2,
  VolumeX,
  ArrowUpRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { MeoMascot } from '@/components/meo-mascot'
import { LogoMark } from '@/components/logo'
import { VoiceMode } from '@/components/layout/voice-mode'
import { ChatAmbience } from '@/components/layout/chat-ambience'
import { KinhKhucXa, KinhKhucXaDefs } from '@/components/layout/glass-refraction'
import { type AgentReply, type PlanOp, type EmailRef } from '@/lib/agent'
import { AutopilotWidget, type AutopilotResult } from '@/components/layout/autopilot-widget'
import { api, apiBaseUrlDaCauHinh, type StoredMessage } from '@/lib/api'
import { useSubscription, isOutOfTokens } from '@/lib/subscription'
import { TokenMeter, QuotaBanner } from '@/components/layout/token-meter'
import { PricingScreen } from '@/components/layout/pricing-screen'
import { normalize } from '@/lib/search'
import type { EmailActions } from '@/lib/email-actions'
import type { Category, Email } from '@/data/emails'
import { CATEGORY, CATEGORY_OPTIONS } from '@/data/categories'

type Message =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'agent'; reply: AgentReply; resolved?: boolean }

/** Một phiên hội thoại đã lưu (UC011).
 *  `backendId` = id phiên trong DB (có khi đã lưu xuống backend); dùng để gọi API
 *  list/get/rename/delete + gửi kèm chat. Phiên mới chưa gửi thì chưa có backendId. */
type Session = {
  id: string
  title: string
  time: string
  messages: Message[]
  pinned?: boolean
  backendId?: string
}

const RENAME_MAX = 60

let counter = 0
const uid = () => `m${++counter}`

const WELCOME =
  'Chào Quân 👋 Mình là trợ lý MeoArc. Cứ nhắn bằng lời thường — mình giúp tóm tắt, dọn, phân loại hay soạn thư. Việc quan trọng mình luôn hỏi bạn duyệt trước.'

function initSessions(): Session[] {
  return [
    {
      id: 's0',
      title: 'Cuộc trò chuyện mới',
      time: 'Bây giờ',
      messages: [{ id: uid(), role: 'agent', reply: { kind: 'text', text: WELCOME } }],
    },
    {
      id: 'past1',
      title: 'Dọn thư bản tin tuần này',
      time: 'Hôm qua',
      messages: [
        { id: uid(), role: 'user', text: 'lưu trữ thư bản tin' },
        { id: uid(), role: 'agent', reply: { kind: 'done', text: 'Đã lưu trữ 1 thư. Hộp thư gọn hơn rồi ✨' } },
      ],
    },
    {
      id: 'past2',
      title: 'Tóm tắt hộp thư sáng nay',
      time: 'Thứ 4',
      messages: [
        { id: uid(), role: 'user', text: 'tóm tắt thư chưa đọc' },
        {
          id: uid(),
          role: 'agent',
          reply: {
            kind: 'result',
            title: 'Tóm tắt 2 thư chưa đọc',
            intro: 'Mình đã rút gọn:',
            lines: ['Giáo vụ HCMUS — Nhắc nộp báo cáo SRS', 'GitHub — PR #12 đã được review'],
          },
        },
      ],
    },
  ]
}

/* Gợi ý chip KHÔNG còn tĩnh — sinh theo ngữ cảnh hộp thư thật, xem memo
   `suggestions` trong ChatPanel (web "tư duy" đúng thời điểm). */

/** Kỹ năng AI (UC014/015/016/009) — gợi ý nổi bật trên canvas. */
const SKILLS = [
  { label: 'Hộp thư tự lái', prompt: 'tự lái hộp thư' },
  { label: 'Digest hôm nay', prompt: 'digest hôm nay' },
  { label: 'Triage hộp thư', prompt: 'triage hộp thư' },
  { label: 'Brief cuộc họp', prompt: 'brief cuộc họp' },
  { label: 'Phân loại tự động', prompt: 'phân loại tự động toàn bộ' },
]

/** Khuôn tin BE (StoredMessage) → Message của FE (thêm id cục bộ để React render). */
function toLocalMsg(m: StoredMessage): Message {
  return m.role === 'user'
    ? { id: uid(), role: 'user', text: m.text }
    : { id: uid(), role: 'agent', reply: m.reply }
}

/** ISO time (BE) → nhãn 'time' mà drawer hiểu (timeBucket đọc 'Hôm nay'/'Hôm qua'). */
function relTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const now = new Date()
  const y = new Date(now)
  y.setDate(now.getDate() - 1)
  const hhmm = d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
  if (d.toDateString() === now.toDateString()) return `Hôm nay ${hhmm}`
  if (d.toDateString() === y.toDateString()) return 'Hôm qua'
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

/** Dòng preview ngắn của 1 phiên (lấy tin cuối). */
function previewOf(s: Session): string {
  const last = s.messages[s.messages.length - 1]
  if (!last) return ''
  if (last.role === 'user') return last.text
  return 'text' in last.reply ? last.reply.text : 'Kết quả…'
}

/** Gom toàn bộ chữ của 1 phiên để tìm kiếm. */
function searchTextOf(s: Session): string {
  return [s.title, ...s.messages.map((m) => (m.role === 'user' ? m.text : 'text' in m.reply ? m.reply.text : ''))]
    .join(' ')
    .toLowerCase()
}

/** Nhóm phiên theo mốc thời gian (dựa trên nhãn time có sẵn). */
const TIME_ORDER = ['Hôm nay', 'Hôm qua', 'Trước đó'] as const
function timeBucket(t: string): (typeof TIME_ORDER)[number] {
  const low = t.toLowerCase()
  if (low.includes('bây giờ') || low.includes('hôm nay')) return 'Hôm nay'
  if (low.includes('hôm qua')) return 'Hôm qua'
  return 'Trước đó'
}

function doneText(op: PlanOp): string {
  switch (op.type) {
    case 'archive':
      return `Đã lưu trữ ${op.ids.length} thư. Hộp thư gọn hơn rồi ✨`
    case 'delete':
      return `Đã xoá ${op.ids.length} thư.`
    case 'markRead':
      return `Đã đánh dấu đã đọc ${op.ids.length} thư.`
    case 'label':
      return `Đã gắn nhãn “${op.label}” cho ${op.ids.length} thư.`
    case 'autoLabel':
      return `Đã phân loại ${op.items.length} thư theo nội dung.`
  }
}

/** Câu ngắn để TTS đọc cho từng loại phản hồi. */
function replyToSpeech(reply: AgentReply): string {
  if ('text' in reply) return reply.text
  if ('intro' in reply) return reply.intro
  return ''
}

/* ---------- Mảnh hiển thị ---------- */

function UserBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-end">
      <div className="gloss max-w-[85%] whitespace-pre-line break-words rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-sm text-primary-foreground shadow-soft">
        {children}
      </div>
    </div>
  )
}

function AgentRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-emphasis text-emphasis-foreground shadow-subtle">
        <Sparkles className="size-3.5" />
      </div>
      <div className="min-w-0 flex-1 space-y-2.5">{children}</div>
    </div>
  )
}

/* (#3) Chữ "giải mã": ký tự random rồi định hình dần về câu thật.
   Tốc độ co theo độ dài (câu dài vẫn xong ~1.4s). Reduced-motion → hiện thẳng. */
const SCRAMBLE_CH = 'ABCDEF#@%&*0123456789▓▒░'
function scrambleAll(t: string): string {
  let out = ''
  for (const c of t) out += c === ' ' || c === '\n' ? c : SCRAMBLE_CH[(Math.random() * SCRAMBLE_CH.length) | 0]
  return out
}
function ScrambleText({ text }: { text: string }) {
  const reduce =
    typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const [display, setDisplay] = useState(() => (reduce ? text : scrambleAll(text)))
  useEffect(() => {
    if (reduce) {
      setDisplay(text)
      return
    }
    let i = 0
    const step = Math.max(0.5, text.length / 22) // câu dài → lộ nhanh hơn để khỏi lê thê
    const id = window.setInterval(() => {
      let out = ''
      for (let k = 0; k < text.length; k++) {
        const c = text[k]
        out += c === ' ' || c === '\n' || k < i ? c : SCRAMBLE_CH[(Math.random() * SCRAMBLE_CH.length) | 0]
      }
      setDisplay(out)
      i += step
      if (i >= text.length) {
        window.clearInterval(id)
        setDisplay(text) // chốt câu thật, sạch sẽ
      }
    }, 32)
    return () => window.clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text])
  return <>{display}</>
}

function AgentText({ children }: { children: React.ReactNode }) {
  return (
    // whitespace-pre-line: GIỮ xuống dòng + gạch đầu dòng của AI → câu trả lời có bố cục,
    // không bị dồn thành một đoạn dài (trông chỉn chu hơn hẳn).
    <div className="max-w-[88%] whitespace-pre-line break-words rounded-2xl rounded-tl-md px-4 py-2.5 text-sm leading-relaxed text-foreground shadow-soft edge-light rose-glass">
      {/* Chỉ "giải mã" khi nội dung là chuỗi (text/intro của AI) */}
      {typeof children === 'string' ? <ScrambleText text={children} /> : children}
    </div>
  )
}

function ThinkingDots() {
  return (
    <div className="flex items-start gap-2.5">
      <MeoMascot thinking className="size-9 shrink-0" />
      <div className="min-w-0 flex-1 space-y-2.5">
        <div className="inline-flex items-center gap-1 rounded-2xl rounded-tl-md px-4 py-3 shadow-soft glass">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="size-1.5 animate-bounce rounded-full bg-foreground/60"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
        {/* Skeleton morphing — khung kết quả đang hình thành */}
        <div className="max-w-[88%] space-y-2.5 rounded-2xl p-3.5 shadow-soft glass">
          <div className="skeleton h-3 w-1/3 rounded" />
          <div className="grid grid-cols-2 gap-2">
            <div className="skeleton h-12 rounded-lg" />
            <div className="skeleton h-12 rounded-lg" />
          </div>
          <div className="skeleton h-2.5 w-3/4 rounded" />
          <div className="skeleton h-2.5 w-1/2 rounded" />
        </div>
      </div>
    </div>
  )
}

/* ---------- Generative widgets (UC014/015/016) ---------- */

/** Nút hành động nhỏ trên mỗi phiên lịch sử (Pin/Rename/Delete). */
function HistAction({
  icon: Icon,
  title,
  onClick,
  danger,
}: {
  icon: React.ElementType
  title: string
  onClick: () => void
  danger?: boolean
}) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      title={title}
      aria-label={title}
      className={cn(
        'flex size-7 items-center justify-center rounded-md text-popover-foreground/60 transition-colors active:scale-90',
        danger
          ? 'hover:bg-destructive hover:text-destructive-foreground'
          : 'hover:bg-popover-foreground/10 hover:text-popover-foreground',
      )}
    >
      <Icon className="size-3.5" />
    </button>
  )
}

/** Avatar tròn nhỏ với chữ cái đầu. */
function MiniAvatar({ initial }: { initial: string }) {
  return (
    <span className="gloss flex size-7 shrink-0 items-center justify-center rounded-full bg-emphasis font-serif text-xs font-semibold text-emphasis-foreground ring-1 ring-inset ring-accent/40">
      {initial}
    </span>
  )
}

/** Danh sách thư THẬT (bấm để mở thẳng thư) — dùng dưới kết quả AI. UI/UX: mỗi thư 1 hàng
 *  avatar + người gửi + tiêu đề + snippet + chấm chưa đọc; bấm → onOpen(id) mở chi tiết. */
function EmailRefList({ emails, onOpen }: { emails: EmailRef[]; onOpen?: (id: string) => void }) {
  return (
    <div className="mt-2 space-y-1.5">
      {emails.map((e) => (
        <button
          key={e.id}
          type="button"
          onClick={() => onOpen?.(e.id)}
          disabled={!onOpen}
          className="group/mail flex w-full items-center gap-2.5 rounded-xl bg-[#452216]/5 dark:bg-white/5 p-2 text-left transition-colors hover:bg-[#452216]/10 dark:hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
        >
          <MiniAvatar initial={e.initial} />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 truncate text-sm font-medium text-foreground">
              {e.unread && <span className="size-1.5 shrink-0 rounded-full cherry-dot" />}
              <span className="truncate">{e.sender}</span>
            </p>
            <p className="truncate text-xs text-muted-foreground">{e.subject}</p>
            {e.snippet && (
              <p className="truncate text-[11px] text-muted-foreground/70">{e.snippet}</p>
            )}
          </div>
          {onOpen && (
            <ArrowUpRight className="size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover/mail:opacity-100" />
          )}
        </button>
      ))}
    </div>
  )
}

/** Meeting Brief — bento: thời gian/deadline · người tham gia · checklist · điểm chính. */
function BriefWidget({ reply }: { reply: Extract<AgentReply, { kind: 'brief' }> }) {
  const [done, setDone] = useState<Set<number>>(new Set())
  const toggle = (i: number) =>
    setDone((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  return (
    <Card className="overflow-hidden rose-glass shadow-float">
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <CalendarClock className="size-4 text-primary" />
          {reply.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-2">
        {/* Hàng bento: thời gian · người tham gia */}
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-[#452216]/5 dark:bg-white/5 p-3">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <Clock className="size-3.5" />
              Thời gian
            </p>
            <p className="mt-1 text-sm font-medium text-foreground">{reply.when}</p>
            {reply.deadline && (
              <p className="mt-1 inline-flex rounded-full bg-spark/20 px-2 py-0.5 text-[11px] font-semibold text-foreground">
                {reply.deadline}
              </p>
            )}
          </div>
          <div className="rounded-xl bg-[#452216]/5 dark:bg-white/5 p-3">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <Users className="size-3.5" />
              Tham gia
            </p>
            <div className="mt-1.5 space-y-1.5">
              {reply.attendees.map((a) => (
                <div key={a.name} className="flex items-center gap-2">
                  <MiniAvatar initial={a.initial} />
                  <span className="truncate text-xs text-foreground">{a.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Checklist action items (tick được) */}
        <div>
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Việc cần làm · {done.size}/{reply.actions.length}
          </p>
          <div className="space-y-1">
            {reply.actions.map((a, i) => {
              const checked = done.has(i)
              return (
                <button
                  key={i}
                  onClick={() => toggle(i)}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ease-spring hover:bg-popover-foreground/5 active:scale-[0.99]"
                >
                  <span
                    className={cn(
                      'flex size-5 shrink-0 items-center justify-center rounded-md ring-1 ring-inset transition-colors',
                      checked
                        ? 'ripe-pulse bg-success text-success-foreground ring-transparent'
                        : 'text-transparent ring-border',
                    )}
                  >
                    <Check className="size-3.5" />
                  </span>
                  <span
                    className={cn(
                      'min-w-0 flex-1',
                      checked ? 'text-muted-foreground line-through' : 'text-foreground',
                    )}
                  >
                    {a}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Điểm chính */}
        <div className="space-y-1 border-t border-border/40 pt-2.5">
          {reply.points.map((p, i) => (
            <div key={i} className="flex gap-2 text-sm text-foreground/90">
              <span className="mt-1 size-1.5 shrink-0 rounded-full bg-active" />
              <span className="min-w-0">{p}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/** Triage — nhóm theo ưu tiên, mỗi thư có gợi ý hành động + tick "đã xử lý". */
function TriageWidget({ reply }: { reply: Extract<AgentReply, { kind: 'triage' }> }) {
  const [done, setDone] = useState<Set<string>>(new Set())
  const toggle = (k: string) =>
    setDone((prev) => {
      const next = new Set(prev)
      if (next.has(k)) next.delete(k)
      else next.add(k)
      return next
    })
  return (
    <Card className="overflow-hidden rose-glass shadow-float">
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <ListChecks className="size-4 text-primary" />
          {reply.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-2">
        {reply.groups.map((g) => (
          <div key={g.label}>
            <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <span
                className={cn(
                  'size-2 rounded-full',
                  g.level === 'high' ? 'cherry-dot' : 'bg-muted-foreground/50',
                )}
              />
              {g.label} · {g.items.length}
            </p>
            <div className="space-y-1.5">
              {g.items.map((it, i) => {
                const key = `${g.label}-${i}`
                const checked = done.has(key)
                return (
                  <div
                    key={key}
                    className={cn(
                      'flex items-center gap-2.5 rounded-xl bg-popover-foreground/5 p-2 transition-opacity',
                      checked && 'opacity-50',
                    )}
                  >
                    <MiniAvatar initial={it.initial} />
                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          'truncate text-sm font-medium text-foreground',
                          checked && 'line-through',
                        )}
                      >
                        {it.sender}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">{it.subject}</p>
                    </div>
                    <span className="hidden shrink-0 rounded-full bg-active/15 px-2 py-0.5 text-[10px] font-semibold text-foreground sm:inline">
                      {it.suggest}
                    </span>
                    <button
                      onClick={() => toggle(key)}
                      title={checked ? 'Bỏ đánh dấu' : 'Đánh dấu đã xử lý'}
                      className="flex size-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-popover-foreground/10 hover:text-foreground active:scale-90"
                    >
                      {checked ? (
                        <CheckSquare className="size-4 text-success" />
                      ) : (
                        <Square className="size-4" />
                      )}
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

/** Daily Digest — bento số liệu + phân bổ theo nhãn (mini-bar) + nổi bật. */
function DigestWidget({ reply }: { reply: Extract<AgentReply, { kind: 'digest' }> }) {
  const max = Math.max(1, ...reply.breakdown.map((b) => b.count))
  return (
    <Card className="overflow-hidden rose-glass shadow-float">
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <BarChart3 className="size-4 text-primary" />
          {reply.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-2">
        {/* Tiles số liệu */}
        <div className="grid grid-cols-3 gap-2">
          {reply.stats.map((s) => (
            <div
              key={s.label}
              className="ripe rounded-xl bg-popover-foreground/5 p-2.5 text-center"
              style={{ ['--tint' as string]: 'var(--spark)' }}
            >
              <p className="font-serif text-2xl font-semibold text-foreground">{s.value}</p>
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
        {/* Phân bổ theo nhãn */}
        {reply.breakdown.length > 0 && (
          <div className="space-y-1.5">
            {reply.breakdown.map((b) => (
              <div key={b.label} className="flex items-center gap-2 text-xs">
                <span className="w-20 shrink-0 truncate text-muted-foreground">{b.label}</span>
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-popover-foreground/10">
                  <span
                    className="block h-full rounded-full bg-active transition-all"
                    style={{ width: `${(b.count / max) * 100}%` }}
                  />
                </span>
                <span className="w-4 shrink-0 text-right font-semibold text-foreground">
                  {b.count}
                </span>
              </div>
            ))}
          </div>
        )}
        {/* Nổi bật */}
        {reply.highlights.length > 0 && (
          <div className="space-y-1 border-t border-border/40 pt-2.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Nổi bật
            </p>
            {reply.highlights.map((h, i) => (
              <div key={i} className="flex gap-2 text-sm text-foreground/90">
                <span className="mt-1 size-1.5 shrink-0 cherry-dot rounded-full" />
                <span className="min-w-0 truncate">{h}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/* ---------- Panel ---------- */

/* ĐÃ XOÁ hai thành phần MeltingWave (sơn tan chảy) và WaterDivider (mặt hồ
   gợn sóng) cùng dữ liệu đi kèm. Xem giải thích ở chỗ chúng từng được gắn.
   Lịch sử vẫn còn trong git nếu cần dựng lại. */

/** Đoạn phim bong bóng xà phòng — nguồn để khối kính khúc xạ.
 *
 *  TỰ HOST, không trỏ thẳng vào CDN ngoài. Bản gốc trên CloudFront tải được
 *  (HTTP 200, 2 MB) nhưng phát tới giữa chừng thì đứt: `PIPELINE_ERROR_DISCONNECTED`.
 *  Đây là thứ không kiểm soát được từ phía mình — CDN, chính sách nội dung của
 *  trình duyệt, hay mạng của người dùng đều có thể cắt. Mà khối kính thì KHÔNG
 *  CÓ GÌ ĐỂ KHÚC XẠ nếu đoạn phim chết, nên phụ thuộc bên ngoài ở đây là phụ
 *  thuộc vào đúng thứ dễ hỏng nhất.
 *
 *  Đặt cùng chỗ với 4 đoạn phim sẵn có của trang giới thiệu. Cùng origin nên
 *  canvas cũng không bị "nhiễm bẩn" — tiện thể bỏ luôn một lo lắng. */
const PHIM_BONG_BONG = '/landing/soap-bubble.mp4'

export function ChatPanel({
  emails,
  actions,
  injectedCommand,
  onInjectConsumed,
  onOpenEmail,
  focusSignal,
  onClose,
}: {
  emails: Email[]
  actions: EmailActions
  injectedCommand?: string | null
  onInjectConsumed?: () => void
  /** Mở 1 thư (chuyển panel phải sang chi tiết) — dùng khi bấm thư trong kết quả AI. */
  onOpenEmail?: (id: string) => void
  /** Tăng lên mỗi khi bấm tab "AI Agent" ở nav → bung composer + focus ô chat. */
  focusSignal?: number
  /** Đóng panel AI → trả Hộp thư về full-width (nút X trên header + tab AI Agent). */
  onClose?: () => void
}) {
  const [sessions, setSessions] = useState<Session[]>(initSessions)
  const [currentId, setCurrentId] = useState('s0')
  const [input, setInput] = useState('')
  // Composer THU GỌN: mặc định chỉ là 1 nút; bấm mới bung ô nhập + gợi ý (chừa chỗ cho
  // khung chat). Bấm ra ngoài (khi ô rỗng) → tự co lại. composerRef để phát hiện click ngoài.
  const [composerOpen, setComposerOpen] = useState(false)
  const composerRef = useRef<HTMLDivElement>(null)
  const [thinking, setThinking] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyQuery, setHistoryQuery] = useState('')
  const [voiceOpen, setVoiceOpen] = useState(false)
  // Gói + hạn mức token: hiện cạnh ô nhập, chặn gửi khi cạn, mở trang nâng cấp.
  const { status: sub, refresh: refreshSub, setStatus: setSub } = useSubscription()
  const [pricingOpen, setPricingOpen] = useState(false)
  /** Đoạn phim nền + cờ báo hỏng để rơi về bong bóng dựng bằng CSS. */
  const videoNenRef = useRef<HTMLVideoElement>(null)
  const [phimHong, setPhimHong] = useState(false)
  const [ttsOn, setTtsOn] = useState(true) // đọc lại câu trả lời khi dùng voice
  const [speaking, setSpeaking] = useState(false) // agent đang đọc → nút loa nhấp nháy
  // UC011 — đổi tên / xoá phiên
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  // #7 — tiến trình thực thi plan: { id phiên message, số bước đã xong }
  const [exec, setExec] = useState<{ id: string; current: number } | null>(null)
  const [executedIds, setExecutedIds] = useState<Set<string>>(new Set())
  // #3 — luồng sáng viền panel khi vừa hoàn tất tác vụ
  const [flash, setFlash] = useState(false)
  const flashTimer = useRef<number | null>(null)
  const triggerFlash = () => {
    setFlash(false)
    window.requestAnimationFrame(() => setFlash(true))
    if (flashTimer.current) clearTimeout(flashTimer.current)
    flashTimer.current = window.setTimeout(() => setFlash(false), 1100)
  }
  const scrollRef = useRef<HTMLDivElement>(null)

  const messages = useMemo(
    () => sessions.find((s) => s.id === currentId)?.messages ?? [],
    [sessions, currentId],
  )

  // (#AI-native) GỢI Ý THEO NGỮ CẢNH — web "tư duy" từ tình trạng hộp thư thật:
  // thư quan trọng chưa đọc → gợi ý trả lời ĐÍCH DANH người gửi; có thư chưa đọc
  // → tóm tắt đúng số lượng; có thư khuyến mãi → gợi ý dọn; nhiều thư chưa nhãn
  // → gợi ý phân loại. Câu chữ bám đúng intent parser (lib/agent.ts) để bấm phát
  // là agent hiểu và chạy đúng việc. Tối đa 3 chip, ưu tiên việc gấp trước.
  const suggestions = useMemo(() => {
    const inbox = emails.filter((e) => (e.folder ?? 'inbox') === 'inbox')
    const out: string[] = []
    const urgent = inbox.find((e) => e.unread && e.status === 'Todo')
    if (urgent) out.push(`Soạn trả lời ${urgent.sender}`)
    const unread = inbox.filter((e) => e.unread).length
    if (unread > 0) out.push(`Tóm tắt ${unread} thư chưa đọc`)
    const promo = inbox.filter((e) => e.category === 'terra').length
    if (promo > 0) out.push(`Dọn ${promo} thư khuyến mãi`)
    if (out.length < 3) {
      const unlabeled = inbox.filter((e) => !e.label).length
      if (unlabeled >= 2) out.push('Phân loại tự động thư chưa nhãn')
    }
    if (out.length < 3) {
      const waiting = inbox.find((e) => e.status === 'Waiting')
      if (waiting) out.push(`Tóm tắt thư của ${waiting.sender}`)
    }
    if (out.length === 0) out.push('Tóm tắt hộp thư hôm nay')
    return out.slice(0, 3)
  }, [emails])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  // Composer vừa bung → focus ô nhập ngay cho gõ liền.
  useEffect(() => {
    if (composerOpen) document.getElementById('meoarc-composer-input')?.focus()
  }, [composerOpen])

  // Bấm RA NGOÀI composer (khi ô đang RỖNG) → tự co lại thành nút → chừa chỗ cho khung chat.
  // Còn chữ trong ô thì KHÔNG co (khỏi mất bản nháp đang gõ dở).
  useEffect(() => {
    if (!composerOpen) return
    const onDown = (e: PointerEvent) => {
      if (composerRef.current?.contains(e.target as Node)) return
      if (input.trim()) return
      setComposerOpen(false)
    }
    document.addEventListener('pointerdown', onDown)
    return () => document.removeEventListener('pointerdown', onDown)
  }, [composerOpen, input])

  // Esc để đóng drawer lịch sử
  useEffect(() => {
    if (!historyOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setHistoryOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [historyOpen])

  // Lọc + nhóm lịch sử: phiên đã ghim lên đầu, phần còn lại theo mốc thời gian (UC011)
  const historyGroups = useMemo(() => {
    const q = historyQuery.trim().toLowerCase()
    const filtered = q ? sessions.filter((s) => searchTextOf(s).includes(q)) : sessions
    const pinned = filtered.filter((s) => s.pinned)
    const rest = filtered.filter((s) => !s.pinned)
    const map = new Map<string, Session[]>()
    rest.forEach((s) => {
      const b = timeBucket(s.time)
      if (!map.has(b)) map.set(b, [])
      map.get(b)!.push(s)
    })
    const groups: { label: string; items: Session[]; pinned?: boolean }[] = []
    if (pinned.length) groups.push({ label: 'Đã ghim', items: pinned, pinned: true })
    TIME_ORDER.filter((o) => map.has(o)).forEach((o) => groups.push({ label: o, items: map.get(o)! }))
    return groups
  }, [sessions, historyQuery])

  // Cập nhật messages của phiên hiện tại
  const updateMessages = (fn: (m: Message[]) => Message[]) =>
    setSessions((prev) =>
      prev.map((s) => (s.id === currentId ? { ...s, messages: fn(s.messages) } : s)),
    )
  const push = (m: Message) => updateMessages((prev) => [...prev, m])

  const freshSession = (): Session => ({
    id: uid(),
    title: 'Cuộc trò chuyện mới',
    time: 'Bây giờ',
    messages: [{ id: uid(), role: 'agent', reply: { kind: 'text', text: WELCOME } }],
  })

  const newChat = () => {
    const s = freshSession()
    setSessions((prev) => [s, ...prev])
    setCurrentId(s.id)
  }

  // UC011: nạp lịch sử phiên ĐÃ LƯU từ backend (chế độ HTTP). Mock trả [] → giữ initSessions (demo SRS).
  // Phiên tải về chỉ có metadata (messages rỗng) — mở phiên nào thì mới getConversation phiên đó.
  useEffect(() => {
    let alive = true
    api
      .listConversations()
      .then((list) => {
        if (!alive || list.length === 0) return
        const loaded: Session[] = list.map((c) => ({
          id: c.id,
          backendId: c.id,
          title: c.title,
          time: relTime(c.updatedAt),
          pinned: c.pinned,
          messages: [],
        }))
        const fresh = freshSession()
        setSessions([fresh, ...loaded]) // thêm 1 phiên mới ở đầu để chat ngay
        setCurrentId(fresh.id)
      })
      .catch(() => {}) // lỗi mạng/chưa đăng nhập → cứ giữ initSessions, không vỡ UI
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---- UC011: Mở / Pin / Rename / Delete (đều LƯU xuống backend nếu phiên đã có backendId) ----
  // Mở 1 phiên ở drawer: chuyển sang phiên đó; nếu mới có metadata (messages rỗng) thì tải đầy đủ.
  const openSession = (s: Session) => {
    setCurrentId(s.id)
    setHistoryOpen(false)
    if (s.backendId && s.messages.length === 0) {
      api
        .getConversation(s.backendId)
        .then((detail) => {
          setSessions((prev) =>
            prev.map((x) => (x.id === s.id ? { ...x, messages: detail.messages.map(toLocalMsg) } : x)),
          )
        })
        .catch(() => {})
    }
  }

  const togglePin = (id: string) => {
    const s = sessions.find((x) => x.id === id)
    const next = !s?.pinned
    setSessions((prev) => prev.map((x) => (x.id === id ? { ...x, pinned: next } : x)))
    if (s?.backendId) api.updateConversation(s.backendId, { pinned: next }).catch(() => {})
  }

  const startRename = (s: Session) => {
    setRenamingId(s.id)
    setRenameValue(s.title)
  }
  const commitRename = () => {
    const title = renameValue.trim()
    if (!title || title.length > RENAME_MAX) return // A4 — rename không hợp lệ: giữ ô mở
    const s = sessions.find((x) => x.id === renamingId)
    setSessions((prev) => prev.map((x) => (x.id === renamingId ? { ...x, title } : x)))
    if (s?.backendId) api.updateConversation(s.backendId, { title }).catch(() => {})
    setRenamingId(null)
  }

  const deleteSession = (id: string) => {
    const s = sessions.find((x) => x.id === id)
    if (s?.backendId) api.deleteConversation(s.backendId).catch(() => {})
    const next = sessions.filter((x) => x.id !== id)
    if (next.length === 0) {
      const fresh = freshSession()
      setSessions([fresh])
      setCurrentId(fresh.id)
    } else {
      setSessions(next)
      if (id === currentId) setCurrentId(next[0].id)
    }
    setDeletingId(null)
  }

  // Đọc to câu trả lời (SpeechSynthesis, vi-VN) — dùng khi tương tác bằng giọng nói
  const speak = (txt: string) => {
    if (!ttsOn || !txt || typeof window === 'undefined' || !('speechSynthesis' in window)) return
    try {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(txt)
      u.lang = 'vi-VN'
      u.rate = 1.02
      u.onstart = () => setSpeaking(true)
      u.onend = () => setSpeaking(false)
      u.onerror = () => setSpeaking(false)
      window.speechSynthesis.speak(u)
    } catch {
      /* noop */
    }
  }

  const send = (raw: string, viaVoice = false) => {
    const text = raw.trim()
    if (!text || thinking) return
    // Cạn hạn mức token → chặn ngay ở client, khỏi gọi backend chỉ để nhận lỗi.
    if (isOutOfTokens(sub)) {
      setPricingOpen(true)
      return
    }
    // Thêm tin user + đặt tiêu đề phiên nếu là tin đầu tiên
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== currentId) return s
        const firstUser = !s.messages.some((m) => m.role === 'user')
        return {
          ...s,
          time: 'Bây giờ',
          title: firstUser ? (text.length > 40 ? text.slice(0, 40) + '…' : text) : s.title,
          messages: [...s.messages, { id: uid(), role: 'user', text }],
        }
      }),
    )
    setInput('')
    setThinking(true)
    // Gửi kèm backendId của phiên hiện tại (nếu đã lưu) để agent NHỚ đúng cuộc trò chuyện (UC011).
    const sid = currentId
    const backendId = sessions.find((s) => s.id === sid)?.backendId
    // Qua lớp adapter (UC007): mock trả interpretCommand; backend thật gọi POST /agent/chat.
    api
      .sendAgentMessage(text, { emails }, { viaVoice, sessionId: backendId })
      .then((reply) => {
        setThinking(false)
        // Lần đầu của phiên mới: BE trả conversationId → gắn vào phiên để các lượt sau bám đúng.
        if (reply.conversationId) {
          setSessions((prev) =>
            prev.map((s) => (s.id === sid ? { ...s, backendId: reply.conversationId } : s)),
          )
        }
        push({ id: uid(), role: 'agent', reply })
        if (viaVoice) speak(replyToSpeech(reply))
        void refreshSub() // lượt vừa rồi đã tiêu token → cập nhật lại đồng hồ
      })
      .catch(() => {
        setThinking(false)
        push({
          id: uid(),
          role: 'agent',
          reply: { kind: 'text', text: 'Có lỗi khi xử lý yêu cầu. Bạn thử lại giúp mình nhé.' },
        })
      })
  }

  // Lệnh từ nút ngữ cảnh (UC016) — tự gửi khi app-shell đẩy vào
  useEffect(() => {
    if (!injectedCommand) return
    send(injectedCommand)
    onInjectConsumed?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [injectedCommand])

  // Bấm tab "AI Agent" ở nav → bung ô nhập (nếu đang thu gọn) + focus con trỏ vào chat
  // + cuộn xuống cuối. Nhờ vậy nút không còn "vô tác dụng" khi chat đã hiển thị sẵn.
  useEffect(() => {
    if (!focusSignal) return
    setComposerOpen(true)
    const t = window.setTimeout(() => {
      const el = document.getElementById('meoarc-composer-input') as HTMLTextAreaElement | null
      el?.focus()
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
    }, 60)
    return () => window.clearTimeout(t)
  }, [focusSignal])

  const markResolved = (id: string) =>
    updateMessages((prev) =>
      prev.map((m) => (m.id === id && m.role === 'agent' ? { ...m, resolved: true } : m)),
    )

  const execOp = (op: PlanOp) => {
    if (op.type === 'archive' || op.type === 'delete') actions.removeEmails(op.ids, op.type)
    else if (op.type === 'markRead') actions.markRead(op.ids, op.read)
    else if (op.type === 'label') actions.applyLabel(op.ids, op.category, op.label)
    else if (op.type === 'autoLabel')
      op.items.forEach((it) => actions.applyLabel([it.id], it.category, it.label))
  }

  // #7 — duyệt plan: chạy từng bước (skeleton → ripe-pulse) rồi mới thực thi
  const approvePlan = (id: string, op: PlanOp, stepCount: number) => {
    const total = Math.max(1, stepCount)
    setExec({ id, current: 0 })
    let i = 0
    const tick = () => {
      i += 1
      if (i < total) {
        setExec({ id, current: i })
        window.setTimeout(tick, 550)
      } else {
        setExec(null)
        setExecutedIds((prev) => new Set(prev).add(id))
        execOp(op)
        markResolved(id)
        push({ id: uid(), role: 'agent', reply: { kind: 'done', text: doneText(op) } })
        triggerFlash()
      }
    }
    window.setTimeout(tick, 550)
  }

  const rejectPlan = (id: string) => {
    markResolved(id)
    push({
      id: uid(),
      role: 'agent',
      reply: { kind: 'text', text: 'Đã huỷ kế hoạch. Bạn muốn điều chỉnh lại thế nào?' },
    })
  }

  // UC010 — GỬI THẬT bản nháp sau khi user duyệt trên DraftCard (human-in-the-loop):
  // draft thường → POST /emails/send; draft TRẢ LỜI (replyToId) → POST /emails/{id}/reply
  // (giữ đúng luồng thư). Mock mode: adapter giả trả ok — UX như cũ. Trả true/false để
  // DraftCard biết đóng thẻ hay GIỮ LẠI cho user sửa/bấm gửi lại khi lỗi. Nhờ gửi qua
  // endpoint tất định (không qua LLM) nên "Đã gửi ✓" = thư THẬT SỰ đã đi.
  const sendDraft = async (
    id: string,
    draft: { to: string; subject: string; body: string; replyToId?: string; confirmationId?: string },
  ): Promise<boolean> => {
    try {
      if (draft.confirmationId) {
        // Đường CHUẨN: máy chủ giữ trạng thái yêu cầu duyệt, nên bấm hai lần vẫn chỉ
        // gửi một lần (PA2 §1.3.5). Trước đây nút này gọi thẳng lệnh gửi — mở lại hội
        // thoại cũ rồi bấm lại là thư đi lần nữa.
        await api.approveConfirmation(draft.confirmationId)
      } else if (draft.replyToId) {
        await api.replyEmail(draft.replyToId, draft.body)
      } else {
        // "Tên <email>" → chỉ gửi phần địa chỉ cho backend
        const addr = (draft.to.match(/<([^>]+)>/)?.[1] ?? draft.to).trim()
        await api.sendEmail({ to: addr, subject: draft.subject, body: draft.body })
      }
      markResolved(id)
      push({
        id: uid(),
        role: 'agent',
        reply: {
          kind: 'done',
          text: draft.replyToId
            ? 'Đã gửi trả lời trong đúng luồng thư ✓'
            : `Đã gửi email tới ${draft.to.split('<')[0].trim()}.`,
        },
      })
      triggerFlash()
      return true
    } catch {
      push({
        id: uid(),
        role: 'agent',
        reply: {
          kind: 'text',
          text: 'Gửi KHÔNG thành công (mạng hoặc quyền Gmail). Thư CHƯA được gửi — bạn kiểm tra lại người nhận rồi bấm gửi lần nữa nhé.',
        },
      })
      return false
    }
  }

  // UC010 — "Viết lại": nhờ AGENT soạn lại ĐÚNG bản nháp này (giữ người nhận + chủ đề),
  // KHÔNG tạo email mới. Neo theo chủ đề/người nhận để agent không lạc đề (fix bug rewrite
  // ra email khác hẳn). Agent trả về 1 thẻ nháp mới đã viết lại.
  const rewriteDraft = (
    draft: { to: string; subject: string; body: string; replyToId?: string; confirmationId?: string },
    instruction: string,
  ) => {
    const instr = instruction.trim()
    send(
      `Viết lại bản nháp email vừa rồi (chủ đề “${draft.subject}”, gửi ${draft.to})` +
        `${instr ? ` theo yêu cầu: “${instr}”` : ''}. ` +
        `Giữ NGUYÊN người nhận và chủ đề, chỉ đổi cách hành văn — tuyệt đối không đổi chủ đề.`,
    )
  }

  // UC017 — áp dụng kết quả tự lái vào hộp thư thật
  const applyAutopilot = (id: string, r: AutopilotResult) => {
    if (r.archive.length) actions.removeEmails(r.archive, 'archive')
    if (r.markRead.length) actions.markRead(r.markRead, true)
    if (r.flag.length) actions.setImportant(r.flag, true)
    markResolved(id)
    const parts: string[] = []
    if (r.counts.archive) parts.push(`lưu trữ ${r.counts.archive}`)
    if (r.counts.markRead) parts.push(`đánh dấu đã đọc ${r.counts.markRead}`)
    if (r.counts.flag) parts.push(`gắn sao ${r.counts.flag}`)
    if (r.counts.replied) parts.push(`gửi ${r.counts.replied} trả lời`)
    const summary = parts.length ? parts.join(', ') : 'không thay đổi gì'
    push({
      id: uid(),
      role: 'agent',
      reply: { kind: 'done', text: `Mèo đã tự lái xong: ${summary}. Hộp thư gọn hơn rồi ✨` },
    })
    triggerFlash()
  }

  // UC009 — áp dụng nhãn sau khi user chỉnh checklist
  const applyCategorize = (
    id: string,
    items: { id: string; category: Category; label: string }[],
  ) => {
    items.forEach((it) => actions.applyLabel([it.id], it.category, it.label))
    markResolved(id)
    push({
      id: uid(),
      role: 'agent',
      reply: { kind: 'done', text: `Đã phân loại ${items.length} thư theo nhãn bạn chọn.` },
    })
    triggerFlash()
  }

  // #8 — phát hiện confirmation đang chờ (plan/draft cuối chưa xử lý) để spotlight
  const lastMsg = messages[messages.length - 1]
  const pendingConfirmId =
    lastMsg &&
    lastMsg.role === 'agent' &&
    !lastMsg.resolved &&
    !exec &&
    (lastMsg.reply.kind === 'plan' || lastMsg.reply.kind === 'draft')
      ? lastMsg.id
      : null

  return (
    <aside className="ai-panel-bg relative z-10 flex h-full flex-1 flex-col overflow-hidden border-l border-accent/30 shadow-soft duration-300 animate-in fade-in">
      {/* ĐOẠN PHIM NỀN — nguồn để khối kính khúc xạ, và nó PHẢI ĂN NHẬP VỚI NỀN, KHÔNG PHẢI DÁN LÊN NỀN.
          Bản thô là một bong bóng TRẮNG LOÁ trên nền studio sáng. Đặt nguyên nó
          lên nền #05060D thì nó không thuộc về căn phòng ấy — nó là một tấm ảnh
          dán lên tường tối, và mắt đọc ra ngay.

          Thử `mix-blend-mode: screen` trước và nó KHÔNG ăn thua, vì một lý do đáng
          ghi lại: screen lấy giá trị sáng hơn của hai lớp, mà nền ở đây là #05060D
          — gần như đen tuyệt đối. Screen với đen chính là phép đồng nhất, nên nó
          không đổi được gì cả. Vẫn giữ screen vì ở những chỗ nền không thuần đen
          nó có tác dụng, nhưng nó không phải đòn bẩy.

          Đòn bẩy là `filter`. Ghì brightness xuống 0.38 để nền studio trắng của
          đoạn phim tụt xuống ngang tầm nền tối của mình, rồi đẩy contrast và
          saturate lên bù lại — làm thế thì chỉ những vân ngũ sắc rực nhất mới
          sống sót, đúng những thứ đáng giữ. hue-rotate kéo phổ về phía tím/hồng
          của thương hiệu để đoạn phim không mang một hệ màu riêng.

          Bản gốc dặn "không phủ lớp làm tối nào lên phim" — vẫn giữ đúng: đây
          không phải lớp phủ, đây là cách chính đoạn phim hoà vào nền. Riêng
          phần mờ dần về đáy thì cần, vì dưới đó là chip gợi ý và ô nhập, chữ
          phải đọc được. */}
      <video
        ref={videoNenRef}
        className="phim-nen"
        aria-hidden
        autoPlay muted loop playsInline preload="auto"
        src={PHIM_BONG_BONG}
        onError={() => setPhimHong(true)}
      />
      {/* Định nghĩa bộ lọc khúc xạ — gắn một lần, các khối kính trỏ tới bằng id */}
      <KinhKhucXaDefs />
      {/* Bong bóng dựng bằng CSS: nền dự phòng khi đoạn phim không tải được
          (mạng chặn, CDN hỏng). Không có nó thì panel thành một mảng đen trơn. */}
      {phimHong && <ChatAmbience />}
      {/* Watermark maison — Phiên bản SÁNG BÓNG ÁNH KIM cho Dark Mode, chốt hạ bài toán tàng hình */}
      <div aria-hidden className="maison-watermark relative z-[2]">
        <style>{`
          .wm-title {
            font-family: var(--font-display);
            font-weight: 900;
            letter-spacing: 0.12em;
            /* Light Mode: Giữ độ nét thanh lịch, xám Champagne dập khối tinh tế */
            color: color-mix(in srgb, var(--foreground) 16%, transparent);
            text-shadow: 1px 1px 0px rgba(255, 255, 255, 0.45);
            transition: all 0.3s ease;
          }
          
          .dark .wm-title {
            /* HẠ từ 38% xuống 12%. Đây là HÌNH NỀN, không phải nội dung: khung trợ lý
               giờ mở sẵn nên chữ này nằm ngay sau mọi cuộc hội thoại. Ở 38% nó tranh
               chỗ với thứ người dùng đang đọc; ở 12% nó làm đúng việc của hình nền. */
            color: color-mix(in srgb, var(--foreground) 12%, transparent);
            /* Quầng sáng neon bóng bẩy hắt ra từ lòng chữ, giả lập hiệu ứng kim loại bóng loáng phản quang dưới ánh đèn */
            text-shadow: 
              0 0 1px rgba(255, 255, 255, 0.6),
              0 0 8px color-mix(in srgb, var(--active) 30%, transparent),
              1px 2px 3px rgba(0, 0, 0, 0.7);
          }

          .wm-sign span {
            font-family: var(--font-serif);
            font-style: italic;
            color: color-mix(in srgb, var(--foreground) 18%, transparent);
            text-shadow: 1px 1px 0px rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
          }
          
          .dark .wm-sign span {
            /* Chữ ký phụ cũng được tráng bạc nhạt mờ ảo để không bị chìm nghỉm */
            color: color-mix(in srgb, var(--foreground) 24%, #ffffff);
            text-shadow: 0 0 4px rgba(255, 255, 255, 0.2), 1px 1px 2px rgba(0, 0, 0, 0.5);
          }
        `}</style>

        {/* Chữ ký tác giả ĐÃ GỠ khỏi mặt sản phẩm.
            Khung trợ lý giờ mở sẵn nên đây là thứ ĐẦU TIÊN người dùng nhìn thấy — chỗ đó
            phải nói sản phẩm làm được gì, không phải ai làm ra nó. Tên tác giả thuộc về
            trang giới thiệu và tài liệu, không thuộc về nền màn hình làm việc.
            Giữ lại chữ MEOARC mờ làm hình nền, hạ độ mờ để không tranh chỗ với hội thoại. */}
        <div className="wm-title">MEOARC</div>
      </div>
      {/* Luồng sáng viền khi hoàn tất tác vụ (#3) */}
      {flash && <span aria-hidden className="panel-flash pointer-events-none absolute inset-0 z-30" />}
      {/* Voice mode (mở rộng UC007) — nói → STT → gửi cho agent */}
      <VoiceMode open={voiceOpen} onClose={() => setVoiceOpen(false)} onResult={(t) => send(t, true)} />

      {/* Trang chọn gói — chiếm trọn khung hình */}
      <PricingScreen
        open={pricingOpen}
        onClose={() => setPricingOpen(false)}
        status={sub}
        onChanged={setSub}
      />
      
      {/* [HAUTE COUTURE] Khung tiêu đề Hollywood với thanh phân cách dập rãnh cơ khí 3D tách khối tuyệt đối */}
      {/* Khung tiêu đề: nền KÍNH SỌC (fluted glass).
          Kính sọc là tấm kính đúc thành nhiều gân bán trụ dọc; mỗi gân là một
          thấu kính trụ nên ảnh phía sau bị nén ngang và vỡ thành dải — thấy có
          gì đó ở sau nhưng không đọc được là gì. Đúng vai của một thanh tiêu đề:
          phải tách khỏi nội dung bên dưới, nhưng không được là một mảng đặc chặn
          hết mọi thứ. Bong bóng phía sau vẫn thấp thoáng qua các gân. */}
      {/* Thanh tiêu đề: ĐÈN NEON CHIẾU VÀO, không phải một bề mặt được trang trí.
          Ống đèn nằm ở mép trên, chùm sáng đổ xuống, và thứ nhìn thấy là chùm ấy
          chạm vào không khí trong khối. Khác hẳn kính sọc trước đó — sọc là hoa
          văn nên mắt luôn thấy nó và nó tranh chỗ với nội dung; ánh sáng thì
          không có hoa văn nào để nhìn, nó chỉ làm khối này sáng lên.

          CHỮ ĐÃ BỎ, thay bằng dấu hiệu thương hiệu. Dòng "Trợ lý MeoArc" không
          nói thêm được gì: người dùng vừa tự tay mở khung này, họ biết thừa nó
          là gì. Một chữ ở chỗ trang trọng nhất mà không mang thông tin thì chỉ
          là chỗ trống được lấp. Dấu hiệu thì nhận ra tức thì, không phải đọc, và
          nó chừa lại khoảng thở cho chùm sáng. */}
      <header data-cat-perch="bottom" className="den-neon relative z-20 shrink-0 overflow-hidden px-6 pb-5 pt-5">
        
        {/* THANH PHÂN CÁCH CƠ KHÍ 3D (RECESSED GROOVE): Tạo khe hở ánh sáng và bóng lún tách lớp */}
        <div className="absolute bottom-0 left-0 right-0 pointer-events-none z-10 flex flex-col">
          {/* Đường hairline trắng gắt giả lập ánh sáng khúc xạ qua khe cắt kính */}
          <div className="w-full h-[1px] bg-background/50 border-t border-white/[0.08]" />
          {/* Rãnh cắt tối dập chìm, hắt bóng xuống lòng khung chat bên dưới */}
          <div className="w-full h-[1px] bg-[#000000]/40 shadow-[0_1px_3px_rgba(0,0,0,0.4)]" />
        </div>

        {/* Lưới mảnh + vệt sáng: ngôn ngữ bảng điều khiển, thay cho dải sơn huy hiệu Pháp.
            Dải cũ (navy/trắng/đỏ + serif + "Maison de L'intellect") nói về thư quán thế kỷ 19,
            trong khi thứ đang chạy bên dưới là một agent. Hai câu chuyện chỏi nhau ngay trên
            cùng một màn hình, và người xem cảm nhận được dù không gọi tên ra được. */}
        {/* Lưới mảnh ĐÃ BỎ: gân kính đã lo phần "cấu trúc nền", chồng thêm một
            lưới nữa thì hai hoa văn đánh nhau. */}

        {/* BỐ CỤC NỘI DUNG: CHỮ HOLLYWOOD DI SẢN CĂN GIỮA TUYỆT ĐỐI */}
        <div className="relative flex items-center justify-between w-full z-10">
          {/* Logo mèo đã BỎ — linh hồn mèo giờ là WanderingCat chạy rong khắp app;
              giữ khối đệm trống cho tiêu đề căn giữa cân với nút bên phải */}
          <div className="size-9 shrink-0 ml-12" />

          {/* VIÊN KÍNH KHÚC XẠ — hẹp so với đoạn phim, và đó là điều kiện bắt buộc.
              Bản gốc ghi rõ một hiện tượng cố hữu của bộ lọc: khi khối kính rộng
              gần bằng nguồn, mép của nó rơi vào vùng mặt nạ 45px và lộ ra dải
              tách kênh màu gắt chạy dọc cạnh. Thanh tiêu đề tràn viền rơi đúng
              vào bẫy đó — đã thử và đúng là bị. Thu lại thành viên nổi hẹp thì
              mép ra khỏi vùng ấy, chỉ còn lại phần khúc xạ sạch.
              Tiện thể nó cũng đúng hơn về mặt hình: một tấm kính có bốn cạnh
              nhìn thấy được thì mới đọc ra là VẬT đặt lên trên đoạn phim; tràn
              viền thì chỉ đọc là một mảng nền. */}
          <KinhKhucXa
            videoRef={videoNenRef}
            co="nho"
            className="kkx pointer-events-none absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 select-none items-center justify-center overflow-hidden rounded-full border border-white/[0.16] p-3.5">
            {/* Dấu hiệu, không phải chữ. Phát sáng bằng drop-shadow theo đúng màu
                đèn đang rọi — cùng một nguồn sáng thì mọi vật trong khối phải
                nhận cùng một màu, nếu không khối mất tính nhất quán. */}
            <LogoMark className="relative size-6 text-foreground drop-shadow-[0_0_10px_var(--den)]" />
            <span className="sr-only">Trợ lý MeoArc</span>
          </KinhKhucXa>

          <div className="flex items-center gap-1 shrink-0 mr-12">
            <button
              onClick={() => setHistoryOpen((v) => !v)}
              title="Kích hoạt dải phím thao tác"
              className={cn(
                "flex size-9 items-center justify-center rounded-xl border border-foreground/[0.08] bg-background/50 backdrop-blur-md text-muted-foreground transition-all duration-300 active:scale-90 hover:border-gold/40 hover:text-foreground shadow-sm",
                historyOpen && "bg-foreground text-background border-transparent scale-95 rotate-90"
              )}
            >
              <Sparkles className="size-4" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                title="Đóng trợ lý — về Hộp thư"
                aria-label="Đóng trợ lý AI"
                className="flex size-9 items-center justify-center rounded-xl border border-foreground/[0.08] bg-background/50 backdrop-blur-md text-muted-foreground transition-all duration-300 active:scale-90 hover:border-destructive/40 hover:text-foreground shadow-sm"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        </div>

        {/* KHAY CHỨA NÚT CƠ KHÍ: Trượt lướt mượt mà khi được kích hoạt */}
        <div 
          className={cn(
            "relative z-10 flex items-center justify-center gap-4 w-full border-t border-foreground/[0.04] bg-foreground/[0.01] mt-4 pt-3 transition-all duration-500 ease-soft",
            historyOpen 
              ? "max-h-12 opacity-100 translate-y-0" 
              : "max-h-0 opacity-0 -translate-y-4 pointer-events-none overflow-hidden mt-0 pt-0 border-t-0"
          )}
        >
          <div className="flex items-center gap-2 px-4 py-1 rounded-full bg-background/60 backdrop-blur-md border border-foreground/[0.05] shadow-inner">
            <kbd className="hidden items-center gap-0.5 rounded-md border border-foreground/[0.08] bg-background px-1.5 py-0.5 text-[9px] font-mono font-medium text-muted-foreground/70 lg:flex">
              ⌘K
            </kbd>

            <button
              onClick={() => {
                setTtsOn((v) => {
                  if (v && 'speechSynthesis' in window) window.speechSynthesis.cancel()
                  setSpeaking(false)
                  return !v
                })
              }}
              title={ttsOn ? 'Tắt đọc câu trả lời' : 'Bật đọc câu trả lời'}
              className={cn(
                'flex size-8 items-center justify-center rounded-lg transition-colors',
                ttsOn ? 'text-active bg-background shadow-sm' : 'text-muted-foreground hover:bg-background/40 hover:text-foreground',
                speaking && 'animate-pulse', // agent đang đọc → loa nhấp nháy thay mèo mấp máy
              )}
            >
              {ttsOn ? <Volume2 className="size-3.5" /> : <VolumeX className="size-3.5" />}
            </button>

            <button
              onClick={newChat}
              title="Cuộc trò chuyện mới"
              className="flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-background/40 hover:text-foreground"
            >
              <SquarePen className="size-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* ĐÃ GỠ dải sơn nhớt (navy/trắng ngà/đỏ mận) tan chảy tràn mép header.
          Nó là một mảng công phu và đẹp, nhưng nó kể sai chuyện: sơn chảy là ẩn dụ
          của chất lỏng, của thủ công, của thứ diễn ra chậm. Bên dưới nó là một
          agent đọc vài trăm lá thư trong vài giây. Hai câu chuyện chỏi nhau ngay
          trên cùng một màn hình.
          Thay bằng một VẠCH SÁNG mảnh có tán sắc — cùng vai trò phân cách, nhưng
          nói bằng ngôn ngữ ánh sáng. */}
      <div aria-hidden className="relative z-10 h-px shrink-0">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[var(--spark)] to-transparent opacity-80" />
        <div className="absolute inset-x-0 top-0 h-px translate-y-[0.5px] bg-gradient-to-r from-transparent via-[#F042FF] to-transparent opacity-40 blur-[1.5px]" />
      </div>

      {/* Canvas hội thoại */}
      <div
        ref={scrollRef}
        className="scrollbar-thin fade-y relative z-[1] flex-1 space-y-5 overflow-y-auto px-6 py-6"
      >
        {messages.map((m) => {
          return (
            <div key={m.id} className="msg-pop">
              {m.role === 'user' ? (
                <UserBubble>{m.text}</UserBubble>
              ) : (
                <AgentMessage
                  message={m}
                  exec={exec}
                  executed={executedIds.has(m.id)}
                  spotlight={pendingConfirmId === m.id}
                  onApprove={approvePlan}
                  onReject={rejectPlan}
                  onSendDraft={sendDraft}
                  onRewrite={rewriteDraft}
                  onResolve={markResolved}
                  onApplyCategorize={applyCategorize}
                  onAutopilotApply={applyAutopilot}
                  onOpenEmail={onOpenEmail}
                />
              )}
            </div>
          )
        })}
        {thinking && (
          <div className="duration-300 animate-in fade-in slide-in-from-bottom-2">
            <ThinkingDots />
          </div>
        )}
      </div>

      {/* Khu nhập liệu — .roof-ledge = dải phân cách "mặt hồ" (WaterDivider) nơi giọt
          sơn đáp xuống; mèo lang thang đậu được (data-cat-perch). THU GỌN được:
          mặc định là 1 nút, bấm mới bung; bấm ra ngoài (ô rỗng) tự co → chừa chỗ chat.
          composer co/giãn thì --roof-y tự đo lại (ResizeObserver) → mặt hồ + giọt vẫn khớp. */}
      <div
        ref={composerRef}
        data-cat-perch="top"
        className="roof-ledge relative px-6 py-4"
      >
        {/* ĐÃ GỠ mặt hồ gợn sóng champagne. Sóng nước là đường cong hữu cơ, mềm —
            đúng thứ khiến cả panel đọc ra là "mặt phẳng mượt". Thay bằng một
            đường chân trời phát sáng: cùng nhiệm vụ ngăn khung chat với ô nhập,
            nhưng là một CẠNH sắc, thứ mà ánh sáng bám được vào. */}
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0">
          <div className="h-px w-full bg-gradient-to-r from-transparent via-[var(--active)] to-transparent" />
          <div className="h-px w-full -translate-y-px bg-gradient-to-r from-transparent via-[var(--spark)] to-transparent opacity-70 blur-[2px]" />
          {/* Quầng hắt lên từ đường kẻ — cho biết nó phát sáng chứ không phải một nét vẽ */}
          <div className="h-10 w-full bg-[radial-gradient(60%_100%_at_50%_0%,color-mix(in_srgb,var(--active)_22%,transparent),transparent_72%)]" />
        </div>

        {/* Cạn hạn mức → nói rõ lý do trợ lý ngừng trả lời + lối nâng cấp */}
        <QuotaBanner status={sub} onUpgrade={() => setPricingOpen(true)} />

        {/* Kỹ năng AI — LUÔN hiện (không thu gọn) */}
        <div className="mb-2 flex flex-wrap gap-2">
          {SKILLS.map((s) => (
            <button
              key={s.label}
              onClick={() => send(s.prompt)}
              className="flex items-center gap-1.5 rounded-full bg-active/20 px-3 py-1.5 text-xs font-medium text-foreground shadow-subtle transition-all duration-200 ease-spring hover:-translate-y-0.5 active:scale-95"
            >
              <Sparkles className="size-3.5 text-active" />
              {s.label}
            </button>
          ))}
        </div>
        {/* Gợi ý theo ngữ cảnh — LUÔN hiện */}
        <div className="mb-3 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full px-3.5 py-1.5 text-xs text-foreground/80 shadow-subtle transition-all duration-200 ease-spring glass hover:-translate-y-0.5 hover:text-foreground active:scale-95"
            >
              {s}
            </button>
          ))}
        </div>

        {/* CHỈ Ô NHẬP LIỆU thu gọn: mặc định là 1 nút, bấm mới bung; bấm ra ngoài
            (ô rỗng) tự co lại → chừa chỗ cho khung chat. Tag phía trên GIỮ NGUYÊN. */}
        {composerOpen ? (
          <div className="duration-200 animate-in fade-in slide-in-from-bottom-1">
            <div className="flex items-end gap-2 rounded-2xl p-2.5 shadow-soft transition-shadow glass focus-within:shadow-float focus-within:ring-2 focus-within:ring-ring/40">
              <button className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                <Paperclip className="size-4" />
              </button>
              <button
                onClick={() => setVoiceOpen(true)}
                title="Nói với trợ lý (voice mode)"
                aria-label="Bật voice mode"
                className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors ease-spring hover:bg-secondary hover:text-foreground active:scale-90"
              >
                <Mic className="size-4" />
              </button>
              <Textarea
                id="meoarc-composer-input"
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    send(input)
                  } else if (e.key === 'Escape' && !input.trim()) {
                    setComposerOpen(false)
                  }
                }}
                placeholder={
                  isOutOfTokens(sub)
                    ? 'Đã hết token — nâng gói để hỏi tiếp…'
                    : "Nhắn cho trợ lý... vd: 'lưu trữ thư bản tin'"
                }
                disabled={isOutOfTokens(sub)}
                className="max-h-32 min-h-0 flex-1 resize-none border-0 bg-transparent py-1.5 shadow-none focus-visible:ring-0 disabled:opacity-60"
              />
              {/* Đồng hồ token — luôn nằm cạnh ô nhập như các trợ lý AI khác */}
              <TokenMeter status={sub} onUpgrade={() => setPricingOpen(true)} />
              <Button
                size="icon"
                variant="primary"
                className="rounded-xl"
                disabled={isOutOfTokens(sub)}
                onClick={() => send(input)}
              >
                <Send className="size-4" />
              </Button>
            </div>
            <p className="mt-2 text-center text-[11px] text-muted-foreground">
              Mọi hành động không thể hoàn tác đều cần bạn xác nhận trước.
            </p>
          </div>
        ) : (
          /* Ô nhập THU GỌN — pill mời gõ, bấm là bung ô nhập đầy đủ */
          <button
            onClick={() => setComposerOpen(true)}
            className="gloss gloss-sweep flex w-full items-center gap-3 rounded-2xl px-3.5 py-2.5 text-left shadow-soft transition-all duration-200 ease-spring glass hover:-translate-y-0.5 hover:shadow-float active:scale-[0.99]"
          >
            <span className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-emphasis text-emphasis-foreground shadow-subtle">
              <Sparkles className="size-4" />
            </span>
            <span className="flex-1 truncate text-sm text-muted-foreground">Nhắn cho trợ lý MeoArc…</span>
            <span className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Send className="size-4" />
            </span>
          </button>
        )}
      </div>

      {/* Lịch sử trò chuyện (UC011) — drawer trượt từ phải */}
      <div
        aria-hidden
        onClick={() => setHistoryOpen(false)}
        className={cn(
          'fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300',
          historyOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />
      <div
        role="dialog"
        aria-label="Lịch sử trò chuyện"
        aria-modal={historyOpen || undefined}
        aria-hidden={!historyOpen}
        className={cn(
          'fixed inset-y-0 right-0 z-50 flex w-[min(360px,92vw)] flex-col border-l border-accent/30 bg-popover text-popover-foreground shadow-float transition-transform duration-300 ease-out',
          historyOpen ? 'translate-x-0' : 'translate-x-full',
        )}
      >
        <div className="flex items-center gap-3 border-b border-border/40 px-5 py-4">
          <span className="bokeh flex size-9 shrink-0 items-center justify-center rounded-xl bg-emphasis text-emphasis-foreground shadow-subtle">
            <History className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="font-serif text-base font-semibold text-popover-foreground">
              Lịch sử trò chuyện
            </h3>
            <p className="truncate text-xs text-popover-foreground/55">
              {sessions.length} cuộc trò chuyện đã lưu
            </p>
          </div>
          <button
            onClick={() => setHistoryOpen(false)}
            title="Đóng"
            aria-label="Đóng"
            className="flex size-8 shrink-0 items-center justify-center rounded-lg text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground active:scale-95"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="space-y-2.5 px-5 py-3">
          <button
            onClick={() => {
              newChat()
              setHistoryOpen(false)
            }}
            className="gloss gloss-sweep flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-3 py-2.5 text-sm font-semibold text-primary-foreground shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:shadow-float active:scale-[0.98]"
          >
            <SquarePen className="size-4" />
            Cuộc trò chuyện mới
          </button>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-popover-foreground/45" />
            <input
              value={historyQuery}
              onChange={(e) => setHistoryQuery(e.target.value)}
              placeholder="Tìm trong lịch sử…"
              className="w-full rounded-xl border border-border/40 bg-popover-foreground/5 py-2 pl-9 pr-3 text-sm text-popover-foreground outline-none transition-shadow placeholder:text-popover-foreground/40 focus-visible:ring-2 focus-visible:ring-ring/40"
            />
          </div>
        </div>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-3 pb-4">
          {historyGroups.length === 0 ? (
            <div className="mt-14 flex flex-col items-center gap-3 px-6 text-center">
              <span className="bokeh flex size-16 items-center justify-center">
                <MeoMascot className="size-14" />
              </span>
              <p className="text-sm font-medium text-popover-foreground/80">
                Không có cuộc trò chuyện nào khớp
              </p>
              <p className="text-xs text-popover-foreground/50">Thử từ khoá khác nhé.</p>
            </div>
          ) : (
            historyGroups.map((g) => (
              <div key={g.label} className="mb-1">
                <p className="px-2 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-popover-foreground/40">
                  {g.label}
                </p>
                <div className="space-y-1">
                  {g.items.map((s) => {
                    const active = s.id === currentId
                    const renaming = renamingId === s.id

                    if (deletingId === s.id) {
                      return (
                        <div
                          key={s.id}
                          className="rounded-xl bg-destructive/10 px-3 py-2.5 ring-1 ring-destructive/30"
                        >
                          <p className="text-xs text-popover-foreground/80">
                            Xoá phiên “{s.title}”? Không thể hoàn tác.
                          </p>
                          <div className="mt-2 flex justify-end gap-1.5">
                            <button
                              onClick={() => setDeletingId(null)}
                              className="rounded-lg px-2.5 py-1 text-xs text-popover-foreground/70 transition-colors hover:bg-popover-foreground/10"
                            >
                              Huỷ
                            </button>
                            <button
                              onClick={() => deleteSession(s.id)}
                              className="flex items-center gap-1 rounded-lg bg-destructive px-2.5 py-1 text-xs font-semibold text-destructive-foreground transition-transform active:scale-95"
                            >
                              <Trash2 className="size-3.5" />
                              Xoá
                            </button>
                          </div>
                        </div>
                      )
                    }

                    return (
                      <div
                        key={s.id}
                        className={cn(
                          'group relative flex items-start gap-3 overflow-hidden rounded-xl py-2.5 pl-4 pr-3 transition-colors',
                          active ? 'bg-popover-foreground/10' : 'hover:bg-popover-foreground/[0.06]',
                        )}
                      >
                        {active && (
                          <span className="absolute inset-y-1.5 left-0 w-1 rounded-r-full bg-active" />
                        )}
                        <span className="mt-1 flex size-2 shrink-0 items-center justify-center">
                          {s.pinned ? (
                            <Pin className="size-3 text-active" />
                          ) : (
                            <span
                              className={cn(
                                'block size-2 rounded-full',
                                active ? 'cherry-dot' : 'bg-popover-foreground/25',
                              )}
                            />
                          )}
                        </span>

                        <div className="min-w-0 flex-1">
                          {renaming ? (
                            <input
                              autoFocus
                              value={renameValue}
                              maxLength={RENAME_MAX}
                              onChange={(e) => setRenameValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault()
                                  commitRename()
                                } else if (e.key === 'Escape') {
                                  setRenamingId(null)
                                }
                              }}
                              onBlur={commitRename}
                              className="w-full rounded-md border border-border/50 bg-popover-foreground/5 px-2 py-1 text-sm text-popover-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                            />
                          ) : (
                            <button
                              onClick={() => openSession(s)}
                              className="block w-full text-left"
                            >
                              <span className="flex items-center gap-2">
                                <span className="min-w-0 flex-1 truncate text-sm font-medium text-popover-foreground">
                                  {s.title}
                                </span>
                                <span className="shrink-0 text-[11px] text-popover-foreground/45 transition-opacity group-hover:opacity-0">
                                  {s.time}
                                </span>
                              </span>
                              <span className="mt-0.5 block truncate text-xs text-popover-foreground/55">
                                {previewOf(s)}
                              </span>
                            </button>
                          )}
                        </div>

                        {!renaming && (
                          <div className="absolute right-2 top-1.5 hidden items-center gap-0.5 rounded-lg bg-popover/90 px-0.5 shadow-subtle backdrop-blur-sm group-hover:flex">
                            <HistAction
                              icon={s.pinned ? PinOff : Pin}
                              title={s.pinned ? 'Bỏ ghim' : 'Ghim'}
                              onClick={() => togglePin(s.id)}
                            />
                            <HistAction icon={Pencil} title="Đổi tên" onClick={() => startRename(s)} />
                            <HistAction
                              icon={Trash2}
                              title="Xoá"
                              danger
                              onClick={() => setDeletingId(s.id)}
                            />
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  )
}

// MOCK viết lại (chỉ dùng khi CHƯA nối backend). Nguyên tắc: GIỮ nội dung/chủ đề gốc,
// chỉ khoác văn phong theo yêu cầu — KHÔNG trả email mẫu cứng lạc đề. Bản thật do agent viết lại.
function rewriteVariant(base: string, instr: string): string {
  const body = base.trim()
  const i = normalize(instr)
  if (/(trang trong|formal|lich su)/.test(i))
    return `Kính gửi anh/chị,\n\n${body}\n\nEm xin chân thành cảm ơn.\nTrân trọng.`
  if (/(than thien|friendly|gan gui)/.test(i))
    return `Chào anh/chị,\n\n${body}\n\nCảm ơn anh/chị nhiều nhé!`
  if (/(ngan|short|gon|suc tich)/.test(i)) {
    const lines = body.split(/\n+/).map((s) => s.trim()).filter(Boolean)
    return lines.slice(0, 2).join('\n\n')
  }
  return instr ? `${body}\n\n(Đã điều chỉnh theo: “${instr}”.)` : `${body}\n\n(Đã viết lại.)`
}

function DraftCard({
  reply,
  resolved,
  spotCls,
  id,
  onSendDraft,
  onRewrite,
  onResolve,
}: {
  reply: Extract<AgentReply, { kind: 'draft' }>
  resolved?: boolean
  spotCls: string
  id: string
  onSendDraft: (
    id: string,
    draft: { to: string; subject: string; body: string; replyToId?: string; confirmationId?: string },
  ) => Promise<boolean>
  onRewrite?: (draft: { to: string; subject: string; body: string; replyToId?: string }, instruction: string) => void
  onResolve: (id: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [rwOpen, setRwOpen] = useState(false)
  const [rwText, setRwText] = useState('')
  const [rewriting, setRewriting] = useState(false)
  const [to, setTo] = useState(reply.to)
  const [subject, setSubject] = useState(reply.subject)
  const [body, setBody] = useState(reply.body)
  const [done, setDone] = useState<null | 'sent' | 'cancelled'>(null)
  const [sendingNow, setSendingNow] = useState(false) // đang gọi API gửi thật

  const fieldCls =
    'w-full rounded-lg border border-border/50 bg-popover-foreground/5 px-2.5 py-1.5 text-sm text-popover-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring/40'

  const doRewrite = () => {
    const instr = rwText.trim()
    setRwOpen(false)
    // Backend thật: nhờ AGENT viết lại đúng bản nháp này (giữ chủ đề + người nhận).
    // Mock/demo (chưa nối backend): biến thể cục bộ GIỮ nội dung gốc, không lạc đề.
    if (apiBaseUrlDaCauHinh && onRewrite) {
      onRewrite({ to, subject, body, replyToId: reply.replyToId }, instr)
      setRwText('')
      return
    }
    setRewriting(true)
    window.setTimeout(() => {
      setBody((b) => rewriteVariant(b, instr))
      setRwText('')
      setRewriting(false)
    }, 650)
  }

  if (done || resolved) {
    return (
      <Card className="rose-glass shadow-float overflow-hidden relative">
        {done === 'sent' && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 flex size-12 items-center justify-center rounded-full bg-active text-active-foreground font-serif font-bold text-lg border-2 border-accent/40 shadow-md rotate-[-12deg] opacity-85 animate-in fade-in zoom-in duration-500">
            M
            <div className="absolute inset-0.5 rounded-full border border-dashed border-active-foreground/30" />
          </div>
        )}
        <CardHeader>
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Mail className="size-4 text-primary" />
            Bản nháp trả lời
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-2 pr-20">
          <span className="text-xs font-serif font-semibold uppercase tracking-wider text-foreground/80">
            {done === 'cancelled' ? 'Đã huỷ thư' : 'Đã niêm phong mật thư ✓'}
          </span>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('rose-glass shadow-float transition-all overflow-hidden', spotCls)}>
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Mail className="size-4 text-primary" />
          {editing ? 'Chỉnh sửa bản nháp' : 'Bản nháp trả lời'}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5 pt-2 text-sm">
        {editing ? (
          <div className="space-y-1.5">
            <input className={fieldCls} value={to} onChange={(e) => setTo(e.target.value)} />
            <input
              className={fieldCls}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            <textarea
              className={cn(fieldCls, 'min-h-28 resize-none font-serif leading-relaxed bg-elevated text-foreground shadow-inner')}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </div>
        ) : (
          <>
            <p className="text-muted-foreground text-xs">
              <span className="text-foreground font-medium">Tới:</span> {to}
            </p>
            <p className="text-muted-foreground text-xs">
              <span className="text-foreground font-medium">Chủ đề:</span> {subject}
            </p>
            {rewriting ? (
              <div className="mt-2 space-y-2 rounded-xl bg-popover px-3.5 py-3 shadow-subtle">
                <div className="skeleton h-3 w-3/4 rounded" />
                <div className="skeleton h-3 w-full rounded" />
                <div className="skeleton h-3 w-2/3 rounded" />
              </div>
            ) : (
              /* Bản nháp thư. Trước đây khối này là NỀN KEM #f7ebd9 + MỰC NÂU
                 #3e1717 + viền ngà — tức là giả một tờ giấy da. Đây là thứ "cổ
                 điển" lộ liễu nhất trong toàn ứng dụng, lại nằm đúng chỗ người
                 dùng nhìn lâu nhất: lúc đọc lại thư trước khi bấm gửi.

                 Hai màu đó còn được ghi cứng nên ở theme tối chúng đứng im —
                 một mảng kem chói giữa nền gần đen.

                 Giờ là một khối kính có viền phát sáng, chữ dùng token nên theo
                 theme. Vẫn tách khỏi nền để biết "đây là nội dung thư", nhưng
                 tách bằng ÁNH SÁNG chứ không bằng cách giả vật liệu giấy. */
              <div className="neon-edge mt-2 whitespace-pre-line rounded-xl bg-elevated/70 px-4 py-3.5 text-[14px] leading-relaxed text-foreground backdrop-blur-sm"
                style={{ ['--tint' as string]: 'var(--spark)' }}>
                {body}
              </div>
            )}
          </>
        )}

        {rwOpen && (
          <div className="flex items-center gap-1.5 pt-1">
            <input
              autoFocus
              value={rwText}
              onChange={(e) => setRwText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doRewrite()}
              placeholder="Gợi ý: ngắn gọn hơn, trang trọng hơn…"
              className={fieldCls}
            />
            <Button size="sm" variant="accent" onClick={doRewrite}>
              Tạo lại
            </Button>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex-wrap gap-2 border-t border-border/10 pt-3 mt-2">
        <Button
          variant="primary"
          size="sm"
          disabled={rewriting || sendingNow}
          onClick={async () => {
            // GỬI THẬT rồi mới đóng thẻ — thất bại thì giữ thẻ cho user sửa/gửi lại
            setSendingNow(true)
            const ok = await onSendDraft(id, { to, subject, body, replyToId: reply.replyToId, confirmationId: reply.confirmationId })
            setSendingNow(false)
            if (ok) setDone('sent')
          }}
          className="relative overflow-hidden group/btn"
        >
          {sendingNow ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Đang gửi…
            </>
          ) : (
            <>
              <Send className="size-4 transition-transform group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5" />
              Niêm phong &amp; Gửi
            </>
          )}
        </Button>
        <Button variant="outline" size="sm" onClick={() => setEditing((v) => !v)}>
          <Pencil className="size-4" />
          {editing ? 'Xong' : 'Chỉnh sửa'}
        </Button>
        <Button variant="outline" size="sm" disabled={rewriting} onClick={() => setRwOpen((v) => !v)}>
          <Sparkles className="size-4" />
          Viết lại
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setDone('cancelled')
            onResolve(id)
          }}
        >
          Huỷ
        </Button>
      </CardFooter>
    </Card>
  )
}

function CategorizeWidget({
  reply,
  resolved,
  spotCls,
  id,
  onApply,
  onReject,
}: {
  reply: Extract<AgentReply, { kind: 'categorize' }>
  resolved?: boolean
  spotCls: string
  id: string
  onApply: (id: string, items: { id: string; category: Category; label: string }[]) => void
  onReject: (id: string) => void
}) {
  const [rows, setRows] = useState(reply.items.map((it) => ({ ...it })))
  const [excluded, setExcluded] = useState<Set<string>>(new Set())

  const cycleLabel = (rid: string) =>
    setRows((prev) =>
      prev.map((r) => {
        if (r.id !== rid) return r
        const idx = CATEGORY_OPTIONS.findIndex((o) => o.key === r.category)
        const next = CATEGORY_OPTIONS[(idx + 1) % CATEGORY_OPTIONS.length]
        return { ...r, category: next.key, label: next.label }
      }),
    )
  const toggle = (rid: string) =>
    setExcluded((prev) => {
      const n = new Set(prev)
      if (n.has(rid)) n.delete(rid)
      else n.add(rid)
      return n
    })

  const included = rows.filter((r) => !excluded.has(r.id))

  return (
    <Card className={cn('overflow-hidden rose-glass shadow-float transition-all', spotCls)}>
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <ListChecks className="size-4 text-primary" />
          {reply.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5 pt-2">
        {rows.map((r) => {
          const c = CATEGORY[r.category]
          const off = excluded.has(r.id)
          return (
            <div
              key={r.id}
              className={cn(
                'flex items-center gap-2.5 rounded-xl bg-popover-foreground/5 p-2 transition-opacity',
                off && 'opacity-45',
              )}
            >
              <button
                onClick={() => toggle(r.id)}
                title={off ? 'Bao gồm lại' : 'Bỏ qua thư này'}
                className="flex size-6 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-popover-foreground/10 active:scale-90"
              >
                {off ? <Square className="size-4" /> : <CheckSquare className="size-4 text-success" />}
              </button>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{r.sender}</p>
                <p className="truncate text-xs text-muted-foreground">{r.subject}</p>
              </div>
              <button
                onClick={() => cycleLabel(r.id)}
                disabled={resolved || off}
                title="Bấm để đổi nhãn"
                className="flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold text-[#1b1b2c] dark:text-[#E6E8F5] ring-1 ring-inset transition-transform active:scale-95 disabled:opacity-60"
                style={
                  {
                    // Pha màu nhãn với nền của theme hiện tại để chip không bị đục
                    backgroundColor: `color-mix(in srgb, ${c.bar} 70%, var(--background))`,
                    ['--tw-ring-color']: c.bar, // Viền đặc màu nhãn không loãng
                  } as CSSProperties
                }
              >
                <span className="size-1.5 rounded-full" style={{ backgroundColor: c.bar }} />
                {r.label}
              </button>
            </div>
          )
        })}
      </CardContent>
      <CardFooter>
        {resolved ? (
          <span className="text-xs font-medium text-muted-foreground">Đã xử lý ✓</span>
        ) : (
          <>
            <Button
              variant="primary"
              size="sm"
              disabled={included.length === 0}
              onClick={() =>
                onApply(
                  id,
                  included.map((r) => ({ id: r.id, category: r.category, label: r.label })),
                )
              }
            >
              <Check className="size-4" />
              Áp dụng ({included.length})
            </Button>
            <Button variant="outline" size="sm" onClick={() => onReject(id)}>
              <X className="size-4" />
              Từ chối
            </Button>
          </>
        )}
      </CardFooter>
    </Card>
  )
}

/* ---------- Render 1 phản hồi agent ---------- */

function AgentMessage({
  message,
  exec,
  executed,
  spotlight,
  onApprove,
  onReject,
  onSendDraft,
  onRewrite,
  onResolve,
  onApplyCategorize,
  onAutopilotApply,
  onOpenEmail,
}: {
  message: Extract<Message, { role: 'agent' }>
  exec: { id: string; current: number } | null
  executed: boolean
  spotlight: boolean
  onApprove: (id: string, op: PlanOp, stepCount: number) => void
  onReject: (id: string) => void
  onSendDraft: (
    id: string,
    draft: { to: string; subject: string; body: string; replyToId?: string; confirmationId?: string },
  ) => Promise<boolean>
  onRewrite: (draft: { to: string; subject: string; body: string; replyToId?: string }, instruction: string) => void
  onResolve: (id: string) => void
  onApplyCategorize: (id: string, items: { id: string; category: Category; label: string }[]) => void
  onAutopilotApply: (id: string, result: AutopilotResult) => void
  onOpenEmail?: (id: string) => void
}) {
  const { reply, resolved } = message
  const running = exec?.id === message.id
  const spotCls = spotlight ? 'ring-2 ring-spark/50 shadow-float' : ''

  if (reply.kind === 'text') {
    return (
      <AgentRow>
        <AgentText>{reply.text}</AgentText>
        {reply.emails && reply.emails.length > 0 && (
          <EmailRefList emails={reply.emails} onOpen={onOpenEmail} />
        )}
      </AgentRow>
    )
  }

  if (reply.kind === 'done') {
    return (
      <AgentRow>
        <div className="ripe-pulse flex items-center gap-2.5 rounded-2xl rounded-tl-md px-4 py-3 text-sm font-medium text-foreground shadow-soft edge-light glass">
          <CheckCircle2 className="size-5 shrink-0 text-success" />
          {reply.text}
        </div>
      </AgentRow>
    )
  }

  if (reply.kind === 'result') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <Card className="rose-glass shadow-float">
          <CardHeader>
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <FileText className="size-4 text-primary" />
              {reply.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2">
            {reply.emails && reply.emails.length > 0 ? (
              <EmailRefList emails={reply.emails} onOpen={onOpenEmail} />
            ) : (
              <div className="space-y-2">
                {reply.lines.map((l, i) => (
                  <div key={i} className="flex min-w-0 gap-2 text-sm text-foreground">
                    <span className="text-muted-foreground">•</span>
                    <span className="min-w-0 break-words">{l}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </AgentRow>
    )
  }

  if (reply.kind === 'brief') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <BriefWidget reply={reply} />
      </AgentRow>
    )
  }

  if (reply.kind === 'triage') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <TriageWidget reply={reply} />
      </AgentRow>
    )
  }

  if (reply.kind === 'digest') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <DigestWidget reply={reply} />
      </AgentRow>
    )
  }

  if (reply.kind === 'categorize') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <CategorizeWidget
          reply={reply}
          resolved={resolved}
          spotCls={spotCls}
          id={message.id}
          onApply={onApplyCategorize}
          onReject={onReject}
        />
      </AgentRow>
    )
  }

  if (reply.kind === 'autopilot') {
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <AutopilotWidget
          reply={reply}
          resolved={resolved}
          id={message.id}
          onApply={onAutopilotApply}
        />
      </AgentRow>
    )
  }

  if (reply.kind === 'plan') {
    const stepStatus = (i: number): 'done' | 'running' | 'pending' => {
      if (running) {
        if (i < exec!.current) return 'done'
        if (i === exec!.current) return 'running'
        return 'pending'
      }
      return executed ? 'done' : 'pending'
    }
    return (
      <AgentRow>
        <AgentText>{reply.intro}</AgentText>
        <Card className={cn('rose-glass shadow-float transition-all', spotCls)}>
          <CardHeader>
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <ListChecks className="size-4 text-primary" />
              {running ? 'Đang thực thi…' : 'Kế hoạch đề xuất'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {reply.steps.length > 1 && (
              <div className="flex items-center px-1 pb-1">
                {reply.steps.map((_s, i) => {
                  const st = stepStatus(i)
                  return (
                    <Fragment key={i}>
                      <span
                        className={cn(
                          'flex size-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold ring-1 ring-inset transition-colors',
                          st === 'done'
                            ? 'ripe-pulse bg-success text-success-foreground ring-transparent'
                            : st === 'running'
                              ? 'bg-active text-active-foreground ring-transparent'
                              : 'bg-transparent text-muted-foreground ring-border',
                        )}
                      >
                        {st === 'done' ? (
                          <Check className="size-3" />
                        ) : st === 'running' ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : (
                          i + 1
                        )}
                      </span>
                      {i < reply.steps.length - 1 && (
                        <span
                          className={cn(
                            'h-px flex-1 border-t border-dashed transition-colors',
                            stepStatus(i) === 'done' ? 'border-success/60' : 'border-border/60',
                          )}
                        />
                      )}
                    </Fragment>
                  )
                })}
              </div>
            )}
            <ol className="space-y-2">
              {reply.steps.map((s, i) => {
                const st = stepStatus(i)
                return (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-foreground">
                    <span
                      className={cn(
                        'mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold transition-colors',
                        st === 'done'
                          ? 'ripe-pulse bg-success text-success-foreground'
                          : st === 'running'
                            ? 'bg-active text-active-foreground'
                            : 'bg-accent text-accent-foreground',
                      )}
                    >
                      {st === 'done' ? (
                        <Check className="size-3" />
                      ) : st === 'running' ? (
                        <Loader2 className="size-3 animate-spin" />
                      ) : (
                        i + 1
                      )}
                    </span>
                    <span className={cn('min-w-0', st === 'running' && 'text-foreground')}>
                      {st === 'running' ? (
                        <span className="skeleton inline-block w-full rounded text-transparent">
                          {s}
                        </span>
                      ) : (
                        s
                      )}
                    </span>
                  </li>
                )
              })}
            </ol>
            {reply.warn && !running && (
              <div className="flex items-start gap-2 rounded-xl bg-accent px-3 py-2 text-xs text-accent-foreground">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                {reply.warn}
              </div>
            )}
          </CardContent>
          <CardFooter>
            {running ? (
              <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" />
                Agent đang xử lý từng bước…
              </span>
            ) : resolved ? (
              <span className="text-xs font-medium text-muted-foreground">Đã xử lý ✓</span>
            ) : (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onApprove(message.id, reply.op, reply.steps.length)}
                >
                  <Check className="size-4" />
                  {reply.confirmLabel}
                </Button>
                <Button variant="outline" size="sm" onClick={() => onReject(message.id)}>
                  <X className="size-4" />
                  Từ chối
                </Button>
              </>
            )}
          </CardFooter>
        </Card>
      </AgentRow>
    )
  }

  return (
    <AgentRow>
      <AgentText>{reply.intro}</AgentText>
      <DraftCard
        reply={reply}
        resolved={resolved}
        spotCls={spotCls}
        id={message.id}
        onSendDraft={onSendDraft}
        onRewrite={onRewrite}
        onResolve={onResolve}
      />
    </AgentRow>
  )
}