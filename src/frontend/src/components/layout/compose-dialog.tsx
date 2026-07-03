import { useEffect, useRef, useState } from 'react'
import {
  PenSquare,
  Send,
  CheckCircle2,
  ArrowLeft,
  Paperclip,
  X,
  Sparkles,
  Bold,
  Italic,
  Underline,
  List,
  Link2,
  Trash2,
  Files,
  UploadCloud,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api, apiBaseUrl } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

// id = mã tệp BE trả khi upload (http mode). Mock mode không có id (gửi giả).
type Attachment = { id?: string; name: string; size: string }

const fieldCls =
  'w-full bg-transparent text-sm text-popover-foreground outline-none placeholder:text-popover-foreground/40'

function ToolbarBtn({ icon: Icon }: { icon: React.ElementType }) {
  return (
    <button
      type="button"
      className="flex size-8 items-center justify-center rounded-lg text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground"
    >
      <Icon className="size-4" />
    </button>
  )
}

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}

/** UC010 — Soạn & gửi email (Gmail+): To/Cc/Bcc, định dạng, đính kèm file, xác nhận gửi. */
export function ComposeDialog() {
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState<'compose' | 'confirm' | 'sent'>('compose')
  const [to, setTo] = useState('')
  const [cc, setCc] = useState('')
  const [bcc, setBcc] = useState('')
  const [showCc, setShowCc] = useState(false)
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [files, setFiles] = useState<Attachment[]>([])
  const [dragging, setDragging] = useState(false)
  const [justDropped, setJustDropped] = useState(false) // bật vệt sáng chạy viền sau khi thả
  const [sending, setSending] = useState(false) // đang gọi backend gửi thư (khoá nút, chống gửi 2 lần)
  const [sendError, setSendError] = useState<string | null>(null) // báo lỗi nếu Gmail từ chối
  const fileRef = useRef<HTMLInputElement>(null)

  // #2 — phím tắt "c" mở soạn thư (khi không đang gõ ở ô nào)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey || open) return
      const el = document.activeElement as HTMLElement | null
      const typing =
        !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)
      if (e.key === 'c' && !typing) {
        e.preventDefault()
        setOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  // #9 — "Soạn với AI": stream chữ kiểu typewriter + ghost text + con trỏ bokeh
  const [aiTyping, setAiTyping] = useState(false)
  const [aiTarget, setAiTarget] = useState('')
  const [aiTyped, setAiTyped] = useState(0)
  const aiTimer = useRef<number | null>(null)
  const stopAi = () => {
    if (aiTimer.current) {
      clearInterval(aiTimer.current)
      aiTimer.current = null
    }
  }
  useEffect(() => () => stopAi(), [])
  // Khi gõ xong → chốt nội dung vào ô soạn
  useEffect(() => {
    if (aiTyping && aiTarget && aiTyped >= aiTarget.length) {
      stopAi()
      setBody(aiTarget)
      setAiTyping(false)
    }
  }, [aiTyped, aiTyping, aiTarget])

  const reset = () => {
    stopAi()
    setAiTyping(false)
    setAiTarget('')
    setAiTyped(0)
    setStep('compose')
    setTo('')
    setCc('')
    setBcc('')
    setShowCc(false)
    setSubject('')
    setBody('')
    setFiles([])
    setSending(false)
    setSendError(null)
  }

  // Thêm tệp: chế độ backend thật → UPLOAD lên server rồi lấy metadata trả về;
  // chế độ mock → chỉ thêm cục bộ như cũ.
  const addFiles = async (list: FileList | null) => {
    if (!list) return
    const arr = Array.from(list)
    if (apiBaseUrl) {
      for (const f of arr) {
        try {
          const r = await api.uploadFile(f)
          // GIỮ r.id để lúc gửi còn biết đính tệp nào (BE tra bytes theo id).
          setFiles((prev) => [...prev, { id: r.id, name: r.name, size: r.size }])
        } catch {
          setFiles((prev) => [...prev, { name: f.name, size: formatBytes(f.size) }])
        }
      }
    } else {
      setFiles((prev) => [...prev, ...arr.map((f) => ({ name: f.name, size: formatBytes(f.size) }))])
    }
  }

  // Khi THẢ tệp vào khung: bật vệt sáng chạy viền (~1.2s) rồi thêm tệp.
  const handleDrop = (list: FileList | null) => {
    setJustDropped(false)
    requestAnimationFrame(() => setJustDropped(true))
    window.setTimeout(() => setJustDropped(false), 1200)
    void addFiles(list)
  }

  const aiCompose = () => {
    // Đang gõ → bấm lần nữa để chốt ngay
    if (aiTyping) {
      stopAi()
      setBody(aiTarget)
      setAiTyping(false)
      return
    }
    const target = `Dạ em chào anh/chị,\n\nEm viết email này về việc "${subject || '...'}". Em xin trình bày ngắn gọn như sau:\n- ...\n- ...\n\nEm cảm ơn anh/chị đã dành thời gian. Mong sớm nhận phản hồi ạ.\n\nTrân trọng,\nAnh Quân`
    stopAi()
    setBody('')
    setAiTarget(target)
    setAiTyped(0)
    setAiTyping(true)
    aiTimer.current = window.setInterval(() => {
      setAiTyped((n) => Math.min(target.length, n + 2))
    }, 18)
  }

  const canSend = to.trim() && subject.trim()

  // Một ô Cc/Bcc có thể chứa NHIỀU email ngăn bởi dấu phẩy → tách thành mảng cho backend.
  const splitAddrs = (s: string): string[] | undefined => {
    const arr = s.split(',').map((x) => x.trim()).filter(Boolean)
    return arr.length ? arr : undefined // rỗng → undefined để khỏi gửi field thừa
  }

  // Bấm "Xác nhận gửi": chế độ backend thật → GỬI qua Gmail rồi mới sang bước 'sent';
  // chế độ mock → chỉ chuyển bước như demo cũ. Lỗi (vd token thiếu quyền) → hiện thông báo.
  const doSend = async () => {
    if (!apiBaseUrl) {
      setStep('sent')
      return
    }
    setSending(true)
    setSendError(null)
    try {
      await api.sendEmail({
        to: to.trim(),
        cc: splitAddrs(cc),
        bcc: splitAddrs(bcc),
        subject,
        body,
        // chỉ gửi các tệp ĐÃ upload thành công (có id); bỏ tệp fallback không id.
        attachmentIds: files.map((f) => f.id).filter((x): x is string => !!x),
      })
      setStep('sent')
    } catch (e) {
      setSendError(e instanceof Error ? e.message : 'Gửi thất bại, thử lại sau.')
    } finally {
      setSending(false)
    }
  }


  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) setTimeout(reset, 150)
      }}
    >
      <DialogTrigger asChild>
        <button
          title="Soạn thư mới"
          className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <PenSquare className="size-4" />
        </button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl">
        {step === 'compose' && (
          <>
            <DialogHeader>
              <DialogTitle>Soạn thư mới</DialogTitle>
            </DialogHeader>

            {/* Vùng form (chặn trình duyệt tự mở file nếu lỡ thả trượt ra ngoài khung) */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => e.preventDefault()}
              className="relative overflow-hidden rounded-xl border border-border/40"
            >

              {/* Người gửi */}
              <div className="flex items-center gap-2 border-b border-border/30 px-3.5 py-2 text-xs text-popover-foreground/60">
                <span className="text-popover-foreground/80">Từ</span>
                Anh Quân &lt;quanpta.meoarc@gmail.com&gt;
              </div>

              {/* Tới + Cc/Bcc toggle */}
              <div className="flex items-center gap-2 border-b border-border/30 px-3.5 py-2">
                <span className="w-7 shrink-0 text-xs text-popover-foreground/60">Tới</span>
                <input
                  className={fieldCls}
                  placeholder="email người nhận"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowCc((v) => !v)}
                  className="shrink-0 rounded-md px-1.5 text-xs font-medium text-popover-foreground/60 hover:text-popover-foreground"
                >
                  Cc/Bcc
                </button>
              </div>

              {showCc && (
                <>
                  <div className="flex items-center gap-2 border-b border-border/30 px-3.5 py-2">
                    <span className="w-7 shrink-0 text-xs text-popover-foreground/60">Cc</span>
                    <input className={fieldCls} value={cc} onChange={(e) => setCc(e.target.value)} />
                  </div>
                  <div className="flex items-center gap-2 border-b border-border/30 px-3.5 py-2">
                    <span className="w-7 shrink-0 text-xs text-popover-foreground/60">Bcc</span>
                    <input className={fieldCls} value={bcc} onChange={(e) => setBcc(e.target.value)} />
                  </div>
                </>
              )}

              {/* Chủ đề */}
              <div className="border-b border-border/30 px-3.5 py-2">
                <input
                  className={`${fieldCls} font-medium`}
                  placeholder="Chủ đề"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>

              {/* Thanh định dạng */}
              <div className="flex items-center gap-0.5 border-b border-border/30 px-2 py-1">
                <ToolbarBtn icon={Bold} />
                <ToolbarBtn icon={Italic} />
                <ToolbarBtn icon={Underline} />
                <span className="mx-1 h-5 w-px bg-border/40" />
                <ToolbarBtn icon={List} />
                <ToolbarBtn icon={Link2} />
                <button
                  type="button"
                  onClick={aiCompose}
                  className={cn(
                    'ml-auto flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium text-popover-foreground transition-colors',
                    aiTyping ? 'bg-active/30' : 'bg-active/20 hover:bg-active/30',
                  )}
                >
                  <Sparkles className={cn('size-3.5 text-active', aiTyping && 'animate-pulse')} />
                  {aiTyping ? 'Đang soạn… (bấm để chốt)' : 'Soạn với AI'}
                </button>
              </div>

              {/* Nội dung — khi AI đang soạn: hiện chữ gõ dần + ghost text + con trỏ bokeh */}
              {aiTyping ? (
                <div
                  className={`${fieldCls} min-h-44 whitespace-pre-wrap px-3.5 py-3 leading-relaxed`}
                  aria-live="polite"
                >
                  <span>{aiTarget.slice(0, aiTyped)}</span>
                  <span
                    className="mx-px inline-block h-4 w-0.5 -translate-y-0.5 animate-pulse rounded-full bg-active align-middle"
                    style={{ boxShadow: '0 0 8px 1px var(--active)' }}
                  />
                  <span className="text-popover-foreground/30">{aiTarget.slice(aiTyped)}</span>
                </div>
              ) : (
                <textarea
                  className={`${fieldCls} min-h-44 resize-none px-3.5 py-3 leading-relaxed`}
                  placeholder="Nội dung email…"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                />
              )}

              {/* Tệp đính kèm */}
              {files.length > 0 && (
                <div className="flex flex-wrap gap-2 border-t border-border/30 px-3.5 py-2.5">
                  {files.map((f, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-2 rounded-lg bg-popover-foreground/10 py-1 pl-2 pr-1 text-xs text-popover-foreground"
                    >
                      <span className="rounded bg-active/20 px-1 text-[9px] font-bold uppercase text-popover-foreground">
                        {f.name.split('.').pop()}
                      </span>
                      <span className="max-w-[160px] truncate">{f.name}</span>
                      <span className="text-popover-foreground/50">{f.size}</span>
                      <button
                        type="button"
                        onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                        className="flex size-5 items-center justify-center rounded text-popover-foreground/50 hover:bg-popover-foreground/10 hover:text-popover-foreground"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Khung kéo–thả tệp "xịn": glow khi rê vào · viền chạy sáng khi thả */}
            <div
              role="button"
              tabIndex={0}
              onClick={() => fileRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  fileRef.current?.click()
                }
              }}
              onDragOver={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setDragging(true)
              }}
              onDragLeave={(e) => {
                e.preventDefault()
                setDragging(false)
              }}
              onDrop={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setDragging(false)
                handleDrop(e.dataTransfer.files)
              }}
              className={cn('drop-zone', dragging && 'is-dragging', justDropped && 'border-run')}
            >
              <UploadCloud className={cn('dz-icon size-7', dragging && 'text-active')} />
              <span className="text-sm font-medium">
                {dragging ? 'Thả ra để đính kèm ✨' : 'Kéo & thả tệp vào đây'}
              </span>
              <span className="text-xs text-muted-foreground">hoặc bấm để chọn từ máy</span>
            </div>

            <input
              ref={fileRef}
              type="file"
              multiple
              hidden
              onChange={(e) => {
                addFiles(e.target.files)
                e.target.value = ''
              }}
            />

            <DialogFooter className="sm:justify-between">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  title="Đính kèm tệp"
                  className="flex size-9 items-center justify-center rounded-xl text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground"
                >
                  <Paperclip className="size-4" />
                </button>
                {files.length > 0 && (
                  <span className="flex items-center gap-1 text-xs text-popover-foreground/60">
                    <Files className="size-3.5" />
                    {files.length}
                  </span>
                )}
                <button
                  type="button"
                  onClick={reset}
                  title="Bỏ bản nháp"
                  className="flex size-9 items-center justify-center rounded-xl text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
              <Button variant="primary" disabled={!canSend} onClick={() => setStep('confirm')}>
                <Send className="size-4" />
                Gửi
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'confirm' && (
          <>
            <DialogHeader>
              <DialogTitle>Xác nhận gửi?</DialogTitle>
            </DialogHeader>
            <div className="space-y-2 rounded-xl bg-popover-foreground/5 p-3.5 text-sm text-popover-foreground">
              <p>
                <span className="text-popover-foreground/60">Tới:</span> {to}
              </p>
              {cc && (
                <p>
                  <span className="text-popover-foreground/60">Cc:</span> {cc}
                </p>
              )}
              <p>
                <span className="text-popover-foreground/60">Chủ đề:</span> {subject}
              </p>
              <p className="flex items-center gap-1.5 text-popover-foreground/70">
                <Paperclip className="size-3.5" />
                {files.length} tệp đính kèm
              </p>
            </div>
            {sendError && (
              <p className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
                {sendError}
              </p>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('compose')} disabled={sending}>
                <ArrowLeft className="size-4" />
                Quay lại
              </Button>
              <Button variant="primary" onClick={doSend} disabled={sending}>
                <Send className="size-4" />
                {sending ? 'Đang gửi…' : 'Xác nhận gửi'}
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'sent' && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle2 className="size-5 text-success" />
                Đã gửi thư
              </DialogTitle>
            </DialogHeader>
            {/* Hiệu ứng gửi: máy bay giấy bay đi + gợn sóng xác nhận */}
            <div className="relative mx-auto my-1 flex size-16 items-center justify-center">
              <span className="send-ripple absolute inset-0 rounded-full" />
              <Send className="send-plane size-7 text-active" />
            </div>
            <p className={cn('text-sm text-popover-foreground/75')}>
              Email tới {to} đã được gửi thành công{files.length ? ` kèm ${files.length} tệp` : ''}.
            </p>
            <DialogFooter>
              <Button variant="primary" onClick={() => setOpen(false)}>
                Đóng
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
