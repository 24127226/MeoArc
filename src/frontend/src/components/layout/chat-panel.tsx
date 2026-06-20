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
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { MeoMascot } from '@/components/meo-mascot'
import { VoiceMode } from '@/components/layout/voice-mode'
import { interpretCommand, type AgentReply, type PlanOp } from '@/lib/agent'
import { normalize } from '@/lib/search'
import type { EmailActions } from '@/lib/email-actions'
import type { Category, Email } from '@/data/emails'
import { CATEGORY, CATEGORY_OPTIONS } from '@/data/categories'

type Message =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'agent'; reply: AgentReply; resolved?: boolean }

/** Một phiên hội thoại đã lưu (UC011). */
type Session = { id: string; title: string; time: string; messages: Message[]; pinned?: boolean }

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

const SUGGESTIONS = ['Tóm tắt thư chưa đọc', 'Lưu trữ thư bản tin', 'Soạn trả lời giáo vụ']

/** Kỹ năng AI (UC014/015/016/009) — gợi ý nổi bật trên canvas. */
const SKILLS = [
  { label: 'Digest hôm nay', prompt: 'digest hôm nay' },
  { label: 'Triage hộp thư', prompt: 'triage hộp thư' },
  { label: 'Brief cuộc họp', prompt: 'brief cuộc họp' },
  { label: 'Phân loại tự động', prompt: 'phân loại tự động toàn bộ' },
]

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

function AgentText({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-[88%] break-words rounded-2xl rounded-tl-md px-4 py-2.5 text-sm leading-relaxed text-foreground shadow-soft edge-light glass">
      {children}
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
    <Card className="overflow-hidden bg-transparent shadow-float glass">
      <CardHeader>
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <CalendarClock className="size-4 text-primary" />
          {reply.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-2">
        {/* Hàng bento: thời gian · người tham gia */}
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-xl bg-popover-foreground/5 p-3">
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
          <div className="rounded-xl bg-popover-foreground/5 p-3">
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
    <Card className="overflow-hidden bg-transparent shadow-float glass">
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
    <Card className="overflow-hidden bg-transparent shadow-float glass">
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

export function ChatPanel({
  emails,
  actions,
  injectedCommand,
  onInjectConsumed,
}: {
  emails: Email[]
  actions: EmailActions
  injectedCommand?: string | null
  onInjectConsumed?: () => void
}) {
  const [sessions, setSessions] = useState<Session[]>(initSessions)
  const [currentId, setCurrentId] = useState('s0')
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyQuery, setHistoryQuery] = useState('')
  const [voiceOpen, setVoiceOpen] = useState(false)
  const [ttsOn, setTtsOn] = useState(true) // đọc lại câu trả lời khi dùng voice
  const [speaking, setSpeaking] = useState(false) // agent đang đọc → mèo mấp máy
  const [mood, setMood] = useState<'idle' | 'happy'>('idle') // mèo đổi biểu cảm khi xong việc
  const moodTimer = useRef<number | null>(null)
  const celebrate = () => {
    setMood('happy')
    if (moodTimer.current) clearTimeout(moodTimer.current)
    moodTimer.current = window.setTimeout(() => setMood('idle'), 2600)
  }
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
    celebrate() // mèo cười khi xong việc
  }
  const scrollRef = useRef<HTMLDivElement>(null)

  const messages = useMemo(
    () => sessions.find((s) => s.id === currentId)?.messages ?? [],
    [sessions, currentId],
  )

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

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

  // ---- UC011: Pin / Rename / Delete ----
  const togglePin = (id: string) =>
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, pinned: !s.pinned } : s)))

  const startRename = (s: Session) => {
    setRenamingId(s.id)
    setRenameValue(s.title)
  }
  const commitRename = () => {
    const title = renameValue.trim()
    if (!title || title.length > RENAME_MAX) return // A4 — rename không hợp lệ: giữ ô mở
    setSessions((prev) => prev.map((s) => (s.id === renamingId ? { ...s, title } : s)))
    setRenamingId(null)
  }

  const deleteSession = (id: string) => {
    const next = sessions.filter((s) => s.id !== id)
    if (next.length === 0) {
      const s = freshSession()
      setSessions([s])
      setCurrentId(s.id)
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
    const snapshot = emails
    window.setTimeout(() => {
      const reply = interpretCommand(text, snapshot)
      setThinking(false)
      push({ id: uid(), role: 'agent', reply })
      if (viaVoice) speak(replyToSpeech(reply))
    }, 700)
  }

  // Lệnh từ nút ngữ cảnh (UC016) — tự gửi khi app-shell đẩy vào
  useEffect(() => {
    if (!injectedCommand) return
    send(injectedCommand)
    onInjectConsumed?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [injectedCommand])

  const markResolved = (id: string) =>
    updateMessages((prev) =>
      prev.map((m) => (m.id === id && m.role === 'agent' ? { ...m, resolved: true } : m)),
    )

  const execOp = (op: PlanOp) => {
    if (op.type === 'archive' || op.type === 'delete') actions.removeEmails(op.ids)
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

  const sendDraft = (id: string, to: string) => {
    markResolved(id)
    push({
      id: uid(),
      role: 'agent',
      reply: { kind: 'done', text: `Đã gửi email tới ${to.split('<')[0].trim()}.` },
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

  // Mèo "lo" khi có plan cảnh báo không hoàn tác (xoá) đang chờ duyệt
  const worried =
    !!lastMsg &&
    lastMsg.role === 'agent' &&
    !lastMsg.resolved &&
    !exec &&
    lastMsg.reply.kind === 'plan' &&
    !!lastMsg.reply.warn

  return (
    <aside className="ai-panel-bg relative z-10 flex h-full flex-1 flex-col border-l border-accent/30 shadow-soft duration-300 animate-in fade-in">
      {/* Luồng sáng viền khi hoàn tất tác vụ (#3) */}
      {flash && <span aria-hidden className="panel-flash pointer-events-none absolute inset-0 z-30" />}
      {/* Voice mode (mở rộng UC007) — nói → STT → gửi cho agent */}
      <VoiceMode open={voiceOpen} onClose={() => setVoiceOpen(false)} onResult={(t) => send(t, true)} />
      {/* Header */}
      <header className="stars-faint flex items-center gap-3 border-b border-border/50 px-6 py-5">
        <span className="bokeh flex size-11 shrink-0 items-center justify-center">
          <MeoMascot
            thinking={thinking || speaking}
            mood={thinking || speaking ? 'thinking' : worried ? 'worry' : mood}
            className="size-11"
          />
        </span>
        <div className="min-w-0">
          <h2 className="font-serif text-[22px] font-semibold leading-none text-foreground">
            Trợ lý MeoArc
          </h2>
          <p className="mt-1.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            <span className="size-1.5 shrink-0 rounded-full bg-success" />
            Sẵn sàng · ngôn ngữ tự nhiên
          </p>
        </div>
        <div className="ml-auto flex items-center gap-0.5">
          <kbd
            title="Mở bảng lệnh"
            className="mr-1 hidden items-center gap-0.5 rounded-md border border-border/50 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground lg:flex"
          >
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
            aria-label={ttsOn ? 'Tắt giọng đọc' : 'Bật giọng đọc'}
            className={cn(
              'flex size-9 items-center justify-center rounded-xl transition-colors hover:bg-secondary',
              ttsOn ? 'text-active' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {ttsOn ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
          </button>
          <button
            onClick={newChat}
            title="Cuộc trò chuyện mới"
            className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <SquarePen className="size-4" />
          </button>
          <button
            onClick={() => setHistoryOpen(true)}
            title="Lịch sử trò chuyện"
            className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <History className="size-4" />
          </button>
        </div>
      </header>

      {/* Canvas hội thoại */}
      <div
        ref={scrollRef}
        className="scrollbar-thin fade-y flex-1 space-y-5 overflow-y-auto px-6 py-6"
      >
        {messages.map((m) => {
          return (
            <div
              key={m.id}
              className="transition-all duration-300 animate-in fade-in slide-in-from-bottom-2"
            >
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
                  onResolve={markResolved}
                  onApplyCategorize={applyCategorize}
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

      {/* Khu nhập liệu */}
      <div className="border-t border-border/50 px-6 py-5">
        {/* Kỹ năng AI */}
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
        <div className="mb-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full px-3.5 py-1.5 text-xs text-foreground/80 shadow-subtle transition-all duration-200 ease-spring glass hover:-translate-y-0.5 hover:text-foreground active:scale-95"
            >
              {s}
            </button>
          ))}
        </div>
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
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send(input)
              }
            }}
            placeholder="Nhắn cho trợ lý... vd: 'lưu trữ thư bản tin'"
            className="max-h-32 min-h-0 flex-1 resize-none border-0 bg-transparent py-1.5 shadow-none focus-visible:ring-0"
          />
          <Button size="icon" variant="primary" className="rounded-xl" onClick={() => send(input)}>
            <Send className="size-4" />
          </Button>
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Mọi hành động không thể hoàn tác đều cần bạn xác nhận trước.
        </p>
      </div>

      {/* Lịch sử trò chuyện (UC011) — drawer trượt từ phải */}
      {/* Lớp nền mờ */}
      <div
        aria-hidden
        onClick={() => setHistoryOpen(false)}
        className={cn(
          'fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity duration-300',
          historyOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />
      {/* Ngăn kéo */}
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
        {/* Header */}
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

        {/* Tạo mới + tìm kiếm */}
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

        {/* Danh sách theo nhóm thời gian */}
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

                    // Dải xác nhận xoá (hành động không hoàn tác — UC011 bước 6)
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
                        {/* Ghim hoặc hạt cherry/chấm mờ */}
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
                              onClick={() => {
                                setCurrentId(s.id)
                                setHistoryOpen(false)
                              }}
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

                        {/* Hành động hiện khi hover (UC011: Pin · Rename · Delete) */}
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

/** Mock "viết lại" draft theo gợi ý (backend thật dùng LLM). */
function rewriteVariant(base: string, instr: string): string {
  const i = normalize(instr)
  if (/(ngan|short|gon|suc tich)/.test(i))
    return 'Dạ em chào,\n\nEm đã nhận được email và sẽ phản hồi sớm ạ. Em cảm ơn.\n\nTrân trọng,\nAnh Quân'
  if (/(trang trong|formal|lich su)/.test(i))
    return 'Kính gửi Quý Thầy/Cô,\n\nEm xin trân trọng phản hồi về nội dung email và sẽ hoàn tất, cập nhật trong thời gian sớm nhất.\n\nEm xin chân thành cảm ơn.\nTrân trọng,\nPhạm Trần Anh Quân'
  if (/(than thien|friendly|gan gui)/.test(i))
    return 'Chào anh/chị,\n\nEm nhận được mail rồi nhé, em xử lý sớm rồi báo lại liền ạ. Cảm ơn anh/chị nhiều!\n\nAnh Quân'
  return `${base}${instr ? `\n\n(Đã điều chỉnh theo: “${instr}”.)` : '\n\n(Đã viết lại.)'}`
}

/** Bản nháp trả lời (UC010) — 4 hành động: Gửi · Chỉnh sửa (inline) · Viết lại · Huỷ. */
function DraftCard({
  reply,
  resolved,
  spotCls,
  id,
  onSendDraft,
  onResolve,
}: {
  reply: Extract<AgentReply, { kind: 'draft' }>
  resolved?: boolean
  spotCls: string
  id: string
  onSendDraft: (id: string, to: string) => void
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

  const fieldCls =
    'w-full rounded-lg border border-border/50 bg-popover-foreground/5 px-2.5 py-1.5 text-sm text-popover-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring/40'

  const doRewrite = () => {
    setRwOpen(false)
    setRewriting(true)
    window.setTimeout(() => {
      setBody((b) => rewriteVariant(b, rwText))
      setRwText('')
      setRewriting(false)
    }, 650)
  }

  if (done || resolved) {
    return (
      <Card className="bg-transparent shadow-float glass">
        <CardHeader>
          <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Mail className="size-4 text-primary" />
            Bản nháp trả lời
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-2">
          <span className="text-xs font-medium text-muted-foreground">
            {done === 'cancelled' ? 'Đã huỷ' : 'Đã gửi ✓'}
          </span>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('bg-transparent shadow-float glass transition-all', spotCls)}>
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
              className={cn(fieldCls, 'min-h-28 resize-none leading-relaxed')}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </div>
        ) : (
          <>
            <p className="text-muted-foreground">
              <span className="text-foreground">Tới:</span> {to}
            </p>
            <p className="text-muted-foreground">
              <span className="text-foreground">Chủ đề:</span> {subject}
            </p>
            {rewriting ? (
              <div className="mt-2 space-y-2 rounded-xl bg-popover px-3.5 py-3 shadow-subtle">
                <div className="skeleton h-3 w-3/4 rounded" />
                <div className="skeleton h-3 w-full rounded" />
                <div className="skeleton h-3 w-2/3 rounded" />
              </div>
            ) : (
              <div className="mt-2 whitespace-pre-line rounded-xl bg-popover px-3.5 py-3 leading-relaxed text-popover-foreground shadow-subtle">
                {body}
              </div>
            )}
          </>
        )}

        {/* Ô gợi ý "viết lại" */}
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
      <CardFooter className="flex-wrap gap-2">
        <Button
          variant="primary"
          size="sm"
          disabled={rewriting}
          onClick={() => {
            setDone('sent')
            onSendDraft(id, to)
          }}
        >
          <Send className="size-4" />
          Gửi
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

/** Categorize (UC009) — checklist: chỉnh nhãn từng thư + bỏ chọn, rồi mới áp dụng. */
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
    <Card className={cn('overflow-hidden bg-transparent shadow-float glass transition-all', spotCls)}>
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
                className="flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold text-foreground ring-1 ring-inset transition-transform active:scale-95 disabled:opacity-60"
                style={
                  {
                    backgroundColor: `color-mix(in srgb, ${c.bar} 24%, transparent)`,
                    ['--tw-ring-color']: `color-mix(in srgb, ${c.bar} 50%, transparent)`,
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
  onResolve,
  onApplyCategorize,
}: {
  message: Extract<Message, { role: 'agent' }>
  exec: { id: string; current: number } | null
  executed: boolean
  spotlight: boolean
  onApprove: (id: string, op: PlanOp, stepCount: number) => void
  onReject: (id: string) => void
  onSendDraft: (id: string, to: string) => void
  onResolve: (id: string) => void
  onApplyCategorize: (id: string, items: { id: string; category: Category; label: string }[]) => void
}) {
  const { reply, resolved } = message
  const running = exec?.id === message.id
  // Lớp nhấn khi card đang là confirmation chờ duyệt (#8)
  const spotCls = spotlight ? 'ring-2 ring-spark/50 shadow-float' : ''

  if (reply.kind === 'text') {
    return (
      <AgentRow>
        <AgentText>{reply.text}</AgentText>
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
        <Card className="bg-transparent shadow-float glass">
          <CardHeader>
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <FileText className="size-4 text-primary" />
              {reply.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 pt-2">
            {reply.lines.map((l, i) => (
              <div key={i} className="flex min-w-0 gap-2 text-sm text-foreground">
                <span className="text-muted-foreground">•</span>
                <span className="min-w-0 break-words">{l}</span>
              </div>
            ))}
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

  if (reply.kind === 'plan') {
    // Trạng thái từng bước: done / running / pending (#7)
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
        <Card className={cn('bg-transparent shadow-float glass transition-all', spotCls)}>
          <CardHeader>
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <ListChecks className="size-4 text-primary" />
              {running ? 'Đang thực thi…' : 'Kế hoạch đề xuất'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {/* Thought-map: sơ đồ node tiến trình của agent (#3) */}
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

  // draft
  return (
    <AgentRow>
      <AgentText>{reply.intro}</AgentText>
      <DraftCard
        reply={reply}
        resolved={resolved}
        spotCls={spotCls}
        id={message.id}
        onSendDraft={onSendDraft}
        onResolve={onResolve}
      />
    </AgentRow>
  )
}
