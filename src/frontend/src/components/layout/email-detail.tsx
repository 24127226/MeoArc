import { useState, type CSSProperties } from 'react'
import {
  ArrowLeft,
  Archive,
  Trash2,
  Tag,
  Star,
  Mail,
  Paperclip,
  Download,
  Reply,
  Sparkles,
  CalendarClock,
  ListChecks,
  FileText,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
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
import { useToast } from '@/components/ui/toast'
import { CATEGORY } from '@/data/categories'
import type { Email } from '@/data/emails'
import type { EmailActions } from '@/lib/email-actions'

/** Nút hành động "đoán trước ý định" theo nội dung thư (UC016 + UC007). */
type ContextAction = { label: string; icon: React.ElementType; command: string }
function contextActions(email: Email): ContextAction[] {
  const text = `${email.subject} ${email.body.join(' ')}`.toLowerCase()
  const first = email.sender.split(' ').slice(-1)[0] || email.sender
  const acts: ContextAction[] = []
  if (/(họp|meeting|lịch|cuộc họp|\bhẹn\b)/.test(text)) {
    acts.push({ label: 'Tạo Meeting Brief', icon: CalendarClock, command: 'brief cuộc họp' })
  }
  if (/(deadline|hạn|nộp|trước \d|submit|báo cáo)/.test(text)) {
    acts.push({ label: 'Trích việc & deadline', icon: ListChecks, command: 'triage hộp thư' })
  }
  acts.push({ label: 'Tóm tắt thư này', icon: FileText, command: `tóm tắt thư từ ${first}` })
  acts.push({ label: 'Soạn trả lời', icon: Reply, command: `soạn trả lời ${first}` })
  return acts.slice(0, 3)
}

export function EmailDetail({
  email,
  onClose,
  actions,
  onAgentAction,
}: {
  email: Email
  onClose: () => void
  actions: EmailActions
  onAgentAction?: (command: string) => void
}) {
  const c = CATEGORY[email.category]
  const [labelOpen, setLabelOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [showSummary, setShowSummary] = useState(true)
  const id = email.id
  const toast = useToast()
  const actionsList = contextActions(email)

  return (
    <aside className="ai-panel-bg relative z-10 flex h-full flex-1 flex-col overflow-hidden border-l border-accent/30 shadow-soft duration-300 animate-in fade-in slide-in-from-right-4">
      {/* Adaptive accent — panel nhuốm sắc theo category của thư đang đọc */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-44"
        style={{
          background: `linear-gradient(to bottom, color-mix(in srgb, ${c.bar} 22%, transparent), transparent)`,
        }}
      />
      {/* Thanh hành động trên cùng */}
      <header className="flex items-center gap-1 border-b border-border/50 px-4 py-3">
        <button
          onClick={onClose}
          title="Quay lại trợ lý"
          className="flex items-center gap-2 rounded-xl px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Quay lại
        </button>
        <div className="ml-auto flex items-center gap-0.5">
          <ActionBtn
            icon={Mail}
            label="Đánh dấu chưa đọc"
            onClick={() => {
              actions.markRead([id], false)
              toast('Đã đánh dấu chưa đọc', 'success')
            }}
          />
          <ActionBtn
            icon={Archive}
            label="Lưu trữ"
            onClick={() => {
              actions.removeEmails([id])
              toast('Đã lưu trữ thư', 'success')
            }}
          />
          <ActionBtn icon={Tag} label="Gắn nhãn" onClick={() => setLabelOpen(true)} />
          <ActionBtn icon={Trash2} label="Xoá" onClick={() => setConfirmDelete(true)} />
          <button
            onClick={() => {
              actions.setImportant([id], !email.starred)
              toast(email.starred ? 'Đã bỏ quan trọng' : 'Đã đánh dấu quan trọng', 'success')
            }}
            aria-label={email.starred ? 'Bỏ quan trọng' : 'Đánh dấu quan trọng'}
            title={email.starred ? 'Bỏ quan trọng' : 'Đánh dấu quan trọng'}
            className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <Star className="size-4" style={email.starred ? { fill: c.bar, color: c.bar } : undefined} />
          </button>
        </div>
      </header>

      {/* Nội dung */}
      <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-5 py-5">
        {/* Thread Smart Card (UC004 + UC008) — bento mọng .ripe tóm tắt luồng thư */}
        <div
          style={{ ['--tint' as string]: c.bar }}
          className="ripe glass overflow-hidden rounded-2xl shadow-tint-lg edge-light"
        >
          <button
            onClick={() => setShowSummary((v) => !v)}
            className="flex w-full items-center gap-2 px-4 py-3 text-left"
          >
            <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-emphasis text-emphasis-foreground shadow-subtle">
              <Sparkles className="size-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-xs font-semibold uppercase tracking-wide text-foreground/80">
                Tóm tắt luồng thư · AI
              </span>
              {!showSummary && (
                <span className="block truncate text-xs text-muted-foreground">
                  {email.tldr ?? aiSummary(email)[0]}
                </span>
              )}
            </span>
            <ChevronDown
              className={cn(
                'size-4 shrink-0 text-muted-foreground transition-transform',
                showSummary && 'rotate-180',
              )}
            />
          </button>
          {showSummary && (
            <div className="space-y-2 px-4 pb-4">
              {email.tldr && (
                <p className="text-sm font-medium leading-relaxed text-foreground">{email.tldr}</p>
              )}
              <ul className="space-y-1">
                {aiSummary(email).map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm text-foreground/90">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-active" />
                    <span className="min-w-0">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Contextual Agent Actions (UC016) — nút "đoán trước ý định" */}
        {onAgentAction && (
          <div className="flex flex-wrap gap-2">
            {actionsList.map((a) => {
              const Icon = a.icon
              return (
                <button
                  key={a.label}
                  onClick={() => onAgentAction(a.command)}
                  className="group flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-foreground shadow-soft ring-1 ring-spark/40 transition-all duration-200 ease-spring glass hover:-translate-y-0.5 hover:shadow-float hover:ring-spark active:scale-95"
                >
                  <Icon className="size-4 text-spark" />
                  {a.label}
                </button>
              )
            })}
          </div>
        )}

        <div className="rounded-2xl p-5 shadow-soft edge-light glass">
          {/* Eyebrow: nhãn + thời gian (micro uppercase) */}
          <div className="mb-2.5 flex flex-wrap items-center gap-2 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            {email.label && (
              <span className="inline-flex items-center gap-1.5 text-foreground">
                <span className="size-1.5 rounded-full" style={{ backgroundColor: c.bar }} />
                {email.label}
              </span>
            )}
            {email.label && <span className="text-muted-foreground/50">/</span>}
            <span>{email.date}</span>
          </div>

          {/* Subject lớn editorial */}
          <h1 className="font-serif text-[28px] font-semibold leading-[1.12] text-foreground">
            {email.subject}
          </h1>

          {/* Người gửi */}
          <div className="mt-5 flex items-center gap-3">
            <div
              className="gloss flex size-11 shrink-0 items-center justify-center rounded-full font-serif text-base font-semibold ring-1 ring-inset"
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
            <div className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-foreground">
                {email.sender}
              </span>
              <p className="truncate text-xs text-muted-foreground">&lt;{email.senderEmail}&gt;</p>
            </div>
          </div>

          {/* Người nhận */}
          <p className="mt-3 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            <span className="text-foreground/75">Tới</span> · {email.to}
          </p>

          {/* Vạch ngăn */}
          <div className="my-4 h-px bg-border/60" />

          {/* Body */}
          <div className="space-y-3 text-sm leading-relaxed text-foreground">
            {email.body.map((p, i) => (
              <p key={i} className="whitespace-pre-line">
                {p}
              </p>
            ))}
          </div>

          {/* Tệp đính kèm */}
          {email.attachments && email.attachments.length > 0 && (
            <div className="mt-5">
              <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Paperclip className="size-3.5" />
                {email.attachments.length} tệp đính kèm
              </div>
              <div className="flex flex-wrap gap-2">
                {email.attachments.map((a) => (
                  <button
                    key={a.name}
                    className="group flex items-center gap-2.5 rounded-xl bg-popover px-3 py-2 text-left shadow-subtle transition-all hover:-translate-y-0.5 hover:shadow-soft"
                  >
                    <span
                      className="flex size-8 items-center justify-center rounded-lg text-[10px] font-bold uppercase"
                      style={{ backgroundColor: c.soft, color: c.ink }}
                    >
                      {a.name.split('.').pop()}
                    </span>
                    <span className="min-w-0">
                      <span className="block max-w-[160px] truncate text-xs font-medium text-popover-foreground">
                        {a.name}
                      </span>
                      <span className="block text-[11px] text-popover-foreground/60">{a.size}</span>
                    </span>
                    <Download className="size-4 text-popover-foreground/50 transition-colors group-hover:text-popover-foreground" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chân — trả lời */}
      <div className="flex items-center gap-2.5 border-t border-border/50 px-5 py-4">
        <Button
          variant="primary"
          onClick={() => onAgentAction?.(`soạn trả lời ${email.sender.split(' ').slice(-1)[0]}`)}
        >
          <Reply className="size-4" />
          Trả lời
        </Button>
        <Button variant="outline" onClick={() => setShowSummary((v) => !v)}>
          <Sparkles className="size-4" />
          {showSummary ? 'Ẩn tóm tắt' : 'Tóm tắt với AI'}
        </Button>
      </div>

      {/* Dialog gắn nhãn */}
      <LabelDialog
        open={labelOpen}
        onOpenChange={setLabelOpen}
        count={1}
        onPick={(category, label) => {
          actions.applyLabel([id], category, label)
          toast(`Đã gắn nhãn “${label}”`, 'success')
        }}
      />

      {/* Dialog xác nhận xoá */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="size-5 text-destructive" />
              Xoá thư này?
            </DialogTitle>
            <DialogDescription>
              Thư “{email.subject}” sẽ bị xoá khỏi hộp thư. Bạn không thể hoàn tác thao tác này.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              Huỷ
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                setConfirmDelete(false)
                actions.removeEmails([id])
                toast('Đã xoá thư', 'destructive')
              }}
            >
              <Trash2 className="size-4" />
              Xoá
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </aside>
  )
}

/** Tóm tắt mock từ nội dung email (UC008) — backend thật dùng LLM. */
function aiSummary(email: Email): string[] {
  const core = email.body
    .map((p) => p.replace(/\n/g, ' ').trim())
    .filter((p) => p.length > 24)
    .slice(0, 3)
    .map((p) => (p.length > 96 ? p.slice(0, 96).trimEnd() + '…' : p))
  return core.length ? core : [email.preview]
}

function ActionBtn({
  icon: Icon,
  label,
  onClick,
}: {
  icon: React.ElementType
  label: string
  onClick: () => void
}) {
  return (
    <button
      title={label}
      onClick={onClick}
      className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
    >
      <Icon className="size-4" />
    </button>
  )
}
