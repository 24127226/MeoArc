import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import {
  Search,
  Star,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  X,
  SearchX,
  Check,
  MailOpen,
  Mail,
  Tag,
  Trash2,
  CheckSquare,
  Square,
  Archive,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { LabelDialog } from '@/components/layout/label-dialog'
import { ComposeDialog } from '@/components/layout/compose-dialog'
import { MeoMascot } from '@/components/meo-mascot'
import { useToast } from '@/components/ui/toast'
import { emailHaystack, interpretNL, matchText } from '@/lib/search'
import type { EmailActions } from '@/lib/email-actions'
import { CATEGORY } from '@/data/categories'
import type { Category, Email } from '@/data/emails'

/* Chip lọc theo category — khoe đủ sắc palette */
const FILTERS: { key: Category | 'all'; label: string }[] = [
  { key: 'all', label: 'Tất cả' },
  { key: 'moss', label: 'Học tập' },
  { key: 'sea', label: 'Dev' },
  { key: 'cherry', label: 'Cá nhân' },
  { key: 'sky', label: 'Deploy' },
]

/* AI Triage badge (UC015) — chỉ hiện cho action/waiting; fyi để yên cho gọn.
   Dùng token cherry/active nên tự đổi theo theme. */
const PRIORITY: Record<'action' | 'waiting', { label: string; cls: string; dot: string }> = {
  action: { label: 'Cần xử lý', cls: 'bg-spark/20 text-foreground', dot: 'cherry-dot' },
  waiting: { label: 'Đang đợi', cls: 'bg-active/20 text-foreground', dot: 'bg-active' },
}

/* Bộ lọc nhanh theo tiêu chí (UC005) */
const QUICK = [
  { key: 'unread', label: 'Chưa đọc' },
  { key: 'starred', label: 'Gắn sao' },
  { key: 'attachment', label: 'Đính kèm' },
] as const
type QuickKey = (typeof QUICK)[number]['key']

/* #4 — số đếm trượt mượt khi giá trị đổi */
function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(value)
  const fromRef = useRef(value)
  const rafRef = useRef<number | null>(null)
  useEffect(() => {
    const from = fromRef.current
    const to = value
    if (from === to) return
    const start = performance.now()
    const dur = 420
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur)
      const eased = 1 - (1 - t) * (1 - t)
      setDisplay(Math.round(from + (to - from) * eased))
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
      else fromRef.current = to
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [value])
  return <>{display}</>
}

/* #3 — nút thao tác nhanh hiện khi hover thẻ (span role=button để không lồng <button>) */
function CardAction({
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
    <span
      role="button"
      tabIndex={-1}
      title={title}
      aria-label={title}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      className={cn(
        'flex size-7 cursor-pointer items-center justify-center rounded-lg text-muted-foreground transition-colors active:scale-90',
        danger
          ? 'hover:bg-destructive hover:text-destructive-foreground'
          : 'hover:bg-secondary hover:text-foreground',
      )}
    >
      <Icon className="size-3.5" />
    </span>
  )
}

/* Nút icon cho thanh thao tác hàng loạt (UC006) */
function IconBtn({
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
      title={title}
      onClick={onClick}
      className={cn(
        'flex size-9 items-center justify-center rounded-xl transition-colors',
        danger
          ? 'text-muted-foreground hover:bg-destructive hover:text-destructive-foreground'
          : 'text-muted-foreground hover:bg-secondary hover:text-foreground',
      )}
    >
      <Icon className="size-4" />
    </button>
  )
}

function EmailCard({
  email,
  selected,
  checked,
  selectionActive,
  kbActive,
  index,
  onSelect,
  onToggleCheck,
  onArchive,
  onStar,
  onDelete,
}: {
  email: Email
  selected: boolean
  checked: boolean
  selectionActive: boolean
  kbActive: boolean
  index: number
  onSelect: () => void
  onToggleCheck: () => void
  onArchive: () => void
  onStar: () => void
  onDelete: () => void
}) {
  const c = CATEGORY[email.category]

  // Kính NHUỐM màu category: lớp gradient màu phủ lên nền kính tối của .glass
  const cardStyle: CSSProperties = {
    backgroundImage: `linear-gradient(135deg, ${c.bar}40, ${c.bar}14)`,
  }
  // --tint: màu category → colored shadow (specular ambient occlusion)
  ;(cardStyle as Record<string, string>)['--tint'] = c.bar
  if (selected) (cardStyle as Record<string, string>)['--tw-ring-color'] = c.bar

  return (
    <button
      onClick={onSelect}
      data-idx={index}
      style={cardStyle}
      className={cn(
        'group relative w-full overflow-hidden rounded-2xl p-4 pl-5 text-left transition-all duration-300 ease-soft ripe bloom-hover glass active:scale-[0.985]',
        selected
          ? 'shadow-tint-lg ring-2'
          : kbActive
            ? 'shadow-tint-lg ring-2 ring-active'
            : 'shadow-tint hover:-translate-y-1 hover:scale-[1.01] hover:shadow-tint-lg',
      )}
    >
      {/* Sọc category bên trái — bóng như thanh kẹo */}
      <span
        aria-hidden
        className="absolute inset-y-0 left-0 w-1.5 rounded-r-full"
        style={{
          backgroundColor: c.bar,
          backgroundImage: 'linear-gradient(180deg, rgba(255,255,255,0.45), transparent 45%)',
        }}
      />

      {/* #3 — thao tác nhanh khi hover (ẩn khi đang ở chế độ chọn nhiều) */}
      {!selectionActive && (
        <span className="absolute right-2 top-2 z-10 hidden items-center gap-0.5 rounded-lg bg-popover/85 p-0.5 shadow-subtle backdrop-blur-sm group-hover:flex">
          <CardAction icon={Archive} title="Lưu trữ" onClick={onArchive} />
          <CardAction icon={Star} title="Quan trọng" onClick={onStar} />
          <CardAction icon={Trash2} title="Xoá" danger onClick={onDelete} />
        </span>
      )}

      <div className="flex items-start gap-3.5">
        {/* Avatar + checkbox chọn (hiện khi hover hoặc đang chọn) */}
        <div className="relative size-9 shrink-0">
          <div
            className="gloss flex size-9 items-center justify-center rounded-full font-serif text-sm font-semibold ring-1 ring-inset"
            style={
              {
                backgroundColor: 'rgba(251, 240, 226, 0.92)',
                color: c.ink,
                ['--tw-ring-color' as string]: c.bar,
              } as CSSProperties
            }
          >
            {email.senderInitial}
          </div>
          <span
            role="checkbox"
            aria-checked={checked}
            onClick={(e) => {
              e.stopPropagation()
              onToggleCheck()
            }}
            className={cn(
              'absolute inset-0 flex cursor-pointer items-center justify-center rounded-full transition-opacity',
              checked || selectionActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
            )}
          >
            <span
              className={cn(
                'flex size-9 items-center justify-center rounded-full ring-1 ring-inset',
                checked
                  ? 'bg-active text-active-foreground ring-transparent'
                  : 'bg-popover/80 text-transparent ring-border backdrop-blur-sm',
              )}
            >
              <Check className="size-4" />
            </span>
          </span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'truncate text-sm',
                email.unread ? 'font-semibold text-foreground' : 'font-medium text-foreground/80',
              )}
            >
              {email.sender}
            </span>
            <span className="ml-auto shrink-0 text-xs text-muted-foreground">{email.time}</span>
          </div>

          <div className="mt-0.5 flex items-center gap-1.5">
            {email.unread && <span className="cherry-dot size-2 shrink-0 rounded-full" />}
            <span
              className={cn(
                'truncate text-sm',
                email.unread ? 'font-medium text-foreground' : 'text-muted-foreground',
              )}
            >
              {email.subject}
            </span>
            {email.starred && (
              <Star className="ml-auto size-3.5 shrink-0" style={{ fill: c.bar, color: c.bar }} />
            )}
          </div>

          <p className="mt-1 truncate text-xs text-muted-foreground">{email.preview}</p>

          {(email.label || (email.priority && email.priority !== 'fyi')) && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {email.priority && email.priority !== 'fyi' && (
                <span
                  className={cn(
                    'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold',
                    PRIORITY[email.priority].cls,
                  )}
                >
                  <span className={cn('size-1.5 rounded-full', PRIORITY[email.priority].dot)} />
                  {PRIORITY[email.priority].label}
                </span>
              )}
              {email.label && (
                <span
                  className="inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold"
                  style={{ backgroundColor: c.soft, color: c.ink }}
                >
                  {email.label}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

/* Co giãn độ rộng dải hộp thư — kẹp trong khoảng hợp lý, nhớ qua localStorage */
const MIN_W = 300
const MAX_W = 560
const DEFAULT_W = 384
const WIDTH_KEY = 'meoarc:listWidth'
const clampW = (n: number) => Math.min(MAX_W, Math.max(MIN_W, Math.round(n)))

/* Tên thư mục để hiển thị tiêu đề cột */
const FOLDER_TITLES: Record<string, string> = {
  inbox: 'Hộp thư',
  starred: 'Gắn sao',
  sent: 'Đã gửi',
  drafts: 'Nháp',
  archive: 'Lưu trữ',
  trash: 'Thùng rác',
}

export function EmailList({
  emails,
  folder = 'inbox',
  openedId,
  onOpen,
  actions,
  onSearch,
  onLoadMore,
  loadingMore,
  onRefresh,
  refreshing,
}: {
  emails: Email[]
  folder?: string
  openedId: string | null
  onOpen: (id: string) => void
  actions: EmailActions
  /** Có hàm này = chế độ backend thật → tìm kiếm chạy trên Gmail (server). */
  onSearch?: (q: string) => void
  /** Có hàm này = còn thư để tải thêm (phân trang server). */
  onLoadMore?: () => void
  loadingMore?: boolean
  /** Có hàm này = nút "Làm mới" nạp lại từ Gmail (bỏ qua cache). */
  onRefresh?: () => void
  refreshing?: boolean
}) {
  const [filter, setFilter] = useState<Category | 'all'>('all')
  const [query, setQuery] = useState('')
  const [nlMode, setNlMode] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [quick, setQuick] = useState<Record<QuickKey, boolean>>({
    unread: false,
    starred: false,
    attachment: false,
  })

  // Lựa chọn nhiều (UC006)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [labelOpen, setLabelOpen] = useState(false)
  const [deleteIds, setDeleteIds] = useState<string[] | null>(null) // xác nhận xoá (bulk hoặc 1 thư)
  const [loading, setLoading] = useState(false)
  const [kbActive, setKbActive] = useState(-1) // #2 — chỉ mục đang chọn bằng phím
  const listRef = useRef<HTMLDivElement>(null)
  const toast = useToast()

  // ---- Co giãn độ rộng (drag handle ở mép phải) ----
  const sectionRef = useRef<HTMLElement>(null)
  const dragging = useRef(false)
  const [width, setWidth] = useState<number>(() => {
    const saved = Number(localStorage.getItem(WIDTH_KEY))
    return Number.isFinite(saved) && saved >= MIN_W && saved <= MAX_W ? saved : DEFAULT_W
  })
  useEffect(() => {
    localStorage.setItem(WIDTH_KEY, String(width))
  }, [width])

  const startDrag = (e: React.PointerEvent) => {
    dragging.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    document.body.style.userSelect = 'none'
  }
  const onDrag = (e: React.PointerEvent) => {
    if (!dragging.current || !sectionRef.current) return
    const left = sectionRef.current.getBoundingClientRect().left
    setWidth(clampW(e.clientX - left))
  }
  const endDrag = (e: React.PointerEvent) => {
    dragging.current = false
    e.currentTarget.releasePointerCapture?.(e.pointerId)
    document.body.style.userSelect = ''
  }

  const refresh = () => {
    // Backend thật → nạp lại từ Gmail (bỏ qua cache). Mock → giả lập quay 700ms như cũ.
    if (onRefresh) {
      onRefresh()
      return
    }
    setLoading(true)
    window.setTimeout(() => setLoading(false), 700)
  }

  // serverMode = đang nối backend thật → việc tìm kiếm do Gmail (server) làm,
  // nên KHÔNG lọc theo chữ ở phía trình duyệt nữa (tránh lọc 2 lần, mất kết quả).
  const serverMode = !!onSearch
  const nl = nlMode && query.trim() ? interpretNL(query) : null

  // UC005 — chế độ server: tự gửi từ khoá sang Gmail sau khi NGỪNG GÕ ~0.45s (debounce)
  // → khỏi cần nhấn Enter, và không gọi mạng mỗi ký tự. Bỏ qua lần đầu (ô còn trống).
  const firstSearch = useRef(true)
  useEffect(() => {
    if (!serverMode) return
    if (firstSearch.current) {
      firstSearch.current = false
      return
    }
    const t = window.setTimeout(() => onSearch?.(query.trim()), 450)
    return () => window.clearTimeout(t) // gõ tiếp trong 0.45s → huỷ lần gọi cũ
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, serverMode])

  // Lọc theo thư mục nav (starred = thư gắn sao, trừ thùng rác)
  const folderEmails = useMemo(
    () =>
      emails.filter((e) => {
        const f = e.folder ?? 'inbox'
        if (folder === 'starred') return e.starred && f !== 'trash'
        return f === folder
      }),
    [emails, folder],
  )

  const results = useMemo(() => {
    const text = nl ? nl.text : query
    return folderEmails.filter((e) => {
      if (filter !== 'all' && e.category !== filter) return false
      if ((quick.unread || nl?.unread) && !e.unread) return false
      if ((quick.starred || nl?.starred) && !e.starred) return false
      if ((quick.attachment || nl?.attachment) && !e.attachments?.length) return false
      if (!serverMode && text.trim() && !matchText(emailHaystack(e), text)) return false
      return true
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderEmails, filter, query, nlMode, quick])

  const unreadCount = folderEmails.filter((e) => e.unread).length

  // #2 — phím tắt: / focus tìm kiếm · j/k duyệt · Enter mở · Esc bỏ chọn
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return
      const el = document.activeElement as HTMLElement | null
      const typing =
        !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)
      if (e.key === '/' && !typing) {
        e.preventDefault()
        document.getElementById('meoarc-search')?.focus()
        return
      }
      if (typing) return
      if (e.key === 'j') {
        e.preventDefault()
        setKbActive((i) => Math.min(results.length - 1, i + 1))
      } else if (e.key === 'k') {
        e.preventDefault()
        setKbActive((i) => Math.max(0, (i < 0 ? 0 : i) - 1))
      } else if (e.key === 'Enter') {
        if (kbActive >= 0 && results[kbActive]) onOpen(results[kbActive].id)
      } else if (e.key === 'Escape') {
        setKbActive(-1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [results, kbActive, onOpen])

  // Cuộn thẻ đang chọn (phím) vào tầm nhìn; kẹp lại nếu danh sách đổi
  useEffect(() => {
    if (kbActive >= results.length) setKbActive(results.length ? results.length - 1 : -1)
  }, [results.length, kbActive])
  useEffect(() => {
    if (kbActive < 0) return
    const node = listRef.current?.querySelector(`[data-idx="${kbActive}"]`) as HTMLElement | null
    node?.scrollIntoView({ block: 'nearest' })
  }, [kbActive])

  // #3 — thao tác nhanh trên 1 thư
  const quickArchive = (id: string) => {
    actions.removeEmails([id], 'archive') // lưu trữ = bỏ nhãn INBOX (khác xoá)
    toast('Đã lưu trữ thư', 'success')
  }
  const quickStar = (e: Email) => {
    actions.setImportant([e.id], !e.starred)
    toast(e.starred ? 'Đã bỏ quan trọng' : 'Đã đánh dấu quan trọng', 'success')
  }

  const isFiltering =
    !!query.trim() || filter !== 'all' || quick.unread || quick.starred || quick.attachment

  const clearAll = () => {
    setQuery('')
    setFilter('all')
    setQuick({ unread: false, starred: false, attachment: false })
  }

  // ---- Selection helpers ----
  const ids = Array.from(selected)
  const clearSel = () => setSelected(new Set())
  const toggleOne = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  const allSelected = results.length > 0 && results.every((e) => selected.has(e.id))
  const toggleSelectAll = () =>
    setSelected(allSelected ? new Set() : new Set(results.map((e) => e.id)))

  const doMarkRead = (read: boolean) => {
    actions.markRead(ids, read)
    toast(`Đã đánh dấu ${ids.length} thư là ${read ? 'đã đọc' : 'chưa đọc'}`, 'success')
    clearSel()
  }
  const doImportant = () => {
    actions.setImportant(ids, true)
    toast(`Đã đánh dấu ${ids.length} thư là quan trọng`, 'success')
    clearSel()
  }
  const doDelete = () => {
    if (!deleteIds) return
    const n = deleteIds.length
    actions.removeEmails(deleteIds, 'delete') // xoá = chuyển vào thùng rác
    setDeleteIds(null)
    toast(`Đã xoá ${n} thư`, 'destructive')
    clearSel()
  }

  return (
    <section
      ref={sectionRef}
      style={{ width }}
      className="relative z-10 flex h-full shrink-0 flex-col bg-list"
    >
      {/* Header */}
      <header className="flex flex-col gap-4 border-b border-border/60 px-6 py-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-serif text-[27px] font-semibold leading-none text-foreground">
              {FOLDER_TITLES[folder] ?? 'Hộp thư'}
            </h1>
            <p className="mt-1.5 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              {isFiltering ? (
                <>
                  <AnimatedNumber value={results.length} /> kết quả
                </>
              ) : folder === 'inbox' ? (
                <>
                  <AnimatedNumber value={unreadCount} /> thư chưa đọc · MeoArc
                </>
              ) : (
                <>
                  <AnimatedNumber value={folderEmails.length} /> thư
                </>
              )}
            </p>
          </div>
          <div className="flex items-center gap-1">
            <ComposeDialog />
            <button
              title="Làm mới"
              aria-label="Làm mới hộp thư"
              onClick={refresh}
              className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <RefreshCw className={cn('size-4', (loading || refreshing) && 'animate-spin')} />
            </button>
            <button
              title="Bộ lọc theo tiêu chí"
              onClick={() => setShowFilters((v) => !v)}
              className={cn(
                'flex size-9 items-center justify-center rounded-xl transition-colors',
                showFilters
                  ? 'bg-foreground text-background'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground',
              )}
            >
              <SlidersHorizontal className="size-4" />
            </button>
          </div>
        </div>

        {/* Ô tìm kiếm + nút bật chế độ ngôn ngữ tự nhiên */}
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 z-10 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="meoarc-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              serverMode
                ? 'Tìm trên Gmail (vd: from:github, has:attachment)…'
                : nlMode
                  ? 'Hỏi: "thư chưa đọc có đính kèm"…'
                  : 'Tìm (phím / để focus)…'
            }
            className="border-0 bg-transparent pl-9 pr-10 text-foreground shadow-none glass placeholder:text-foreground/60"
          />
          <button
            onClick={() => setNlMode((v) => !v)}
            title={nlMode ? 'Tắt tìm theo ngôn ngữ tự nhiên' : 'Tìm bằng ngôn ngữ tự nhiên'}
            className={cn(
              'absolute right-2 top-1/2 z-10 flex size-7 -translate-y-1/2 items-center justify-center rounded-lg transition-colors',
              nlMode ? 'bg-active text-active-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            <Sparkles className="size-4" />
          </button>
        </div>

        {/* Tiêu chí NL đã "hiểu" */}
        {nl && nl.criteria.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
            <span>Đã hiểu:</span>
            {nl.criteria.map((c) => (
              <span key={c} className="rounded-full bg-active/20 px-2 py-0.5 font-medium text-foreground">
                {c}
              </span>
            ))}
          </div>
        )}

        {/* Chip lọc theo category */}
        <div className="scrollbar-thin -mx-1 flex gap-2 overflow-x-auto px-1 pb-0.5">
          {FILTERS.map((f) => {
            const active = filter === f.key
            const dot = f.key === 'all' ? undefined : CATEGORY[f.key].bar
            return (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={cn(
                  'flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all duration-200',
                  active
                    ? 'bg-foreground text-background shadow-subtle'
                    : 'glass text-foreground/80 shadow-subtle hover:text-foreground',
                )}
              >
                {dot && <span className="size-2 rounded-full" style={{ backgroundColor: dot }} />}
                {f.label}
              </button>
            )
          })}
        </div>

        {/* Bộ lọc nhanh theo tiêu chí */}
        {showFilters && (
          <div className="flex flex-wrap gap-2">
            {QUICK.map((q) => {
              const active = quick[q.key]
              return (
                <button
                  key={q.key}
                  onClick={() => setQuick((s) => ({ ...s, [q.key]: !s[q.key] }))}
                  className={cn(
                    'flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all duration-200',
                    active
                      ? 'bg-accent text-accent-foreground shadow-subtle'
                      : 'glass text-foreground/80 shadow-subtle hover:text-foreground',
                  )}
                >
                  {q.label}
                </button>
              )
            })}
          </div>
        )}
      </header>

      {/* Thanh thao tác hàng loạt (UC006) */}
      {selected.size > 0 && (
        <div className="flex items-center gap-2 border-b border-border/60 px-4 py-2.5">
          <button
            onClick={toggleSelectAll}
            title={allSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
            className="flex size-8 items-center justify-center rounded-lg text-active transition-colors hover:bg-secondary"
          >
            {allSelected ? <CheckSquare className="size-5" /> : <Square className="size-5" />}
          </button>
          <span className="text-sm font-semibold text-foreground">{selected.size} đã chọn</span>
          <div className="ml-auto flex items-center gap-0.5">
            <IconBtn icon={MailOpen} title="Đánh dấu đã đọc" onClick={() => doMarkRead(true)} />
            <IconBtn icon={Mail} title="Đánh dấu chưa đọc" onClick={() => doMarkRead(false)} />
            <IconBtn icon={Star} title="Đánh dấu quan trọng" onClick={doImportant} />
            <IconBtn icon={Tag} title="Gắn nhãn" onClick={() => setLabelOpen(true)} />
            <IconBtn icon={Trash2} title="Xoá" onClick={() => setDeleteIds(ids)} danger />
            <IconBtn icon={X} title="Bỏ chọn" onClick={clearSel} />
          </div>
        </div>
      )}

      {/* Danh sách card / trạng thái rỗng */}
      <div ref={listRef} className="scrollbar-thin fade-y flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {loading ? (
          // Skeleton khi làm mới
          [0, 1, 2, 3].map((i) => (
            <div key={i} className="rounded-2xl glass p-4 pl-5 shadow-soft">
              <div className="flex items-start gap-3.5">
                <div className="skeleton size-9 shrink-0 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-3.5 w-2/5 rounded" />
                  <div className="skeleton h-3 w-4/5 rounded" />
                  <div className="skeleton h-2.5 w-3/5 rounded" />
                </div>
              </div>
            </div>
          ))
        ) : results.length > 0 ? (
          <>
            {results.map((email, i) => (
              <EmailCard
                key={email.id}
                email={email}
                index={i}
                selected={openedId === email.id}
                checked={selected.has(email.id)}
                selectionActive={selected.size > 0}
                kbActive={kbActive === i}
                onSelect={() => onOpen(email.id)}
                onToggleCheck={() => toggleOne(email.id)}
                onArchive={() => quickArchive(email.id)}
                onStar={() => quickStar(email)}
                onDelete={() => setDeleteIds([email.id])}
              />
            ))}
            {/* Còn thư trên Gmail (onLoadMore có giá trị) → nút tải trang kế */}
            {onLoadMore && (
              <button
                onClick={onLoadMore}
                disabled={loadingMore}
                className="mt-1 w-full rounded-xl glass py-2.5 text-xs font-medium text-foreground shadow-subtle transition-all hover:-translate-y-0.5 disabled:opacity-60"
              >
                {loadingMore ? 'Đang tải…' : 'Tải thêm thư'}
              </button>
            )}
          </>
        ) : (
          <div className="mt-10 flex flex-col items-center gap-3 px-6 text-center">
            <div className="relative flex size-20 items-center justify-center">
              <span className="bokeh flex size-16 items-center justify-center">
                <MeoMascot className="size-16" />
              </span>
              <span className="absolute bottom-0 right-0 flex size-7 items-center justify-center rounded-full glass text-muted-foreground shadow-subtle">
                <SearchX className="size-3.5" />
              </span>
            </div>
            <p className="text-sm font-medium text-foreground">
              {isFiltering ? 'Không tìm thấy thư nào' : `Mục “${FOLDER_TITLES[folder] ?? ''}” đang trống`}
            </p>
            <p className="text-xs text-muted-foreground">
              {isFiltering
                ? 'Thử đổi từ khoá hoặc bỏ bớt bộ lọc đang áp dụng.'
                : 'Chưa có thư nào ở đây.'}
            </p>
            {isFiltering && (
              <button
                onClick={clearAll}
                className="mt-1 flex items-center gap-1.5 rounded-full glass px-3 py-1 text-xs font-medium text-foreground shadow-subtle hover:-translate-y-0.5"
              >
                <X className="size-3.5" />
                Xoá bộ lọc
              </button>
            )}
          </div>
        )}
      </div>

      {/* Dialog gắn nhãn */}
      <LabelDialog
        open={labelOpen}
        onOpenChange={setLabelOpen}
        count={selected.size}
        onPick={(category, label) => {
          actions.applyLabel(ids, category, label)
          toast(`Đã gắn nhãn “${label}” cho ${ids.length} thư`, 'success')
          clearSel()
        }}
      />

      {/* Dialog xác nhận xoá (bulk hoặc 1 thư khi hover) */}
      <Dialog open={deleteIds !== null} onOpenChange={(o) => !o && setDeleteIds(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="size-5 text-destructive" />
              Xoá {deleteIds?.length ?? 0} thư?
            </DialogTitle>
            <DialogDescription>
              {(deleteIds?.length ?? 0) > 1 ? 'Các thư' : 'Thư'} sẽ bị xoá khỏi hộp thư. Bạn không thể
              hoàn tác thao tác này.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteIds(null)}>
              Huỷ
            </Button>
            <Button variant="destructive" onClick={doDelete}>
              <Trash2 className="size-4" />
              Xoá
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Tay nắm kéo giãn độ rộng — đường mảnh + grip hạt cherry khi hover/focus */}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Kéo để chỉnh độ rộng dải hộp thư"
        aria-valuenow={width}
        aria-valuemin={MIN_W}
        aria-valuemax={MAX_W}
        tabIndex={0}
        onPointerDown={startDrag}
        onPointerMove={onDrag}
        onPointerUp={endDrag}
        onDoubleClick={() => setWidth(DEFAULT_W)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') {
            e.preventDefault()
            setWidth((w) => clampW(w - 16))
          } else if (e.key === 'ArrowRight') {
            e.preventDefault()
            setWidth((w) => clampW(w + 16))
          }
        }}
        title="Kéo để chỉnh độ rộng · double-click để khôi phục"
        className="group absolute inset-y-0 -right-2 z-30 flex w-4 cursor-col-resize touch-none items-center justify-center"
      >
        <span className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-border/50 transition-colors group-hover:bg-active group-focus-visible:bg-active" />
        <span className="cherry-dot relative h-10 w-1.5 rounded-full opacity-0 shadow-subtle transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100" />
      </div>
    </section>
  )
}
