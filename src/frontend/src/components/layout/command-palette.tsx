import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Search,
  Sparkles,
  ListChecks,
  CalendarClock,
  FileText,
  Archive,
  Tag,
  Sun,
  Moon,
  CornerDownLeft,
  MessageSquare,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { t } from '@/lib/ngon-ngu'
import { normalize } from '@/lib/search'

type Cmd = { id: string; label: string; hint: string; icon: React.ElementType; run: () => void }

/** Command Palette (⌘K) — gõ lệnh tự nhiên / nhảy nhanh tới skill, đổi theme.
 *  Dấu ấn power-user kiểu Linear/Raycast, đồng bộ chất liệu cherry. */
export function CommandPalette({
  open,
  onOpenChange,
  onRun,
  theme,
  onToggleTheme,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  onRun: (command: string) => void
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}) {
  const [query, setQuery] = useState('')
  const [sel, setSel] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const close = () => onOpenChange(false)
  const ask = (command: string) => {
    onRun(command)
    close()
  }

  // Lệnh tĩnh — phần lớn đẩy NL sang agent (UC007)
  const commands = useMemo<Cmd[]>(
    () => [
      { id: 'digest', label: t('cmd.digest'), hint: t('cmd.digestHint'), icon: Sparkles, run: () => ask('digest hôm nay') },
      { id: 'triage', label: t('cmd.triage'), hint: t('cmd.triageHint'), icon: ListChecks, run: () => ask('triage hộp thư') },
      { id: 'brief', label: 'Meeting Brief', hint: t('cmd.briefHint'), icon: CalendarClock, run: () => ask('brief cuộc họp') },
      { id: 'summarize', label: t('cmd.summarize'), hint: t('cmd.summarizeHint'), icon: FileText, run: () => ask('tóm tắt thư chưa đọc') },
      { id: 'autolabel', label: t('skill.autolabel'), hint: t('cmd.autolabelHint'), icon: Tag, run: () => ask('phân loại tự động toàn bộ') },
      { id: 'archive', label: t('cmd.archiveNews'), hint: t('cmd.archiveHint'), icon: Archive, run: () => ask('lưu trữ thư bản tin') },
      {
        id: 'theme',
        label: theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối',
        hint: t('cmd.theme'),
        icon: theme === 'dark' ? Sun : Moon,
        run: () => {
          onToggleTheme()
          close()
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [theme],
  )

  // Lọc theo từ khoá (bỏ dấu) + thêm "Hỏi trợ lý: …" khi có chữ
  const list = useMemo<Cmd[]>(() => {
    const q = normalize(query)
    const filtered = q ? commands.filter((c) => normalize(c.label).includes(q) || normalize(c.hint).includes(q)) : commands
    if (query.trim()) {
      return [
        {
          id: 'ask',
          label: `Hỏi trợ lý: “${query.trim()}”`,
          hint: t('cmd.sendToMeoarc'),
          icon: MessageSquare,
          run: () => ask(query.trim()),
        },
        ...filtered,
      ]
    }
    return filtered
  }, [query, commands])

  // Reset + focus khi mở
  useEffect(() => {
    if (open) {
      setQuery('')
      setSel(0)
      const t = setTimeout(() => inputRef.current?.focus(), 40)
      return () => clearTimeout(t)
    }
  }, [open])

  useEffect(() => {
    setSel((s) => Math.min(s, Math.max(0, list.length - 1)))
  }, [list.length])

  if (!open) return null

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSel((s) => (s + 1) % list.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSel((s) => (s - 1 + list.length) % list.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      list[sel]?.run()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      close()
    }
  }

  return (
    <>
      {/* Nền mờ */}
      <div
        aria-hidden
        onClick={close}
        className="fixed inset-0 z-[60] bg-black/45 backdrop-blur-sm duration-200 animate-in fade-in"
      />
      {/* Hộp lệnh */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={t('nav.palette')}
        className="fixed left-1/2 top-[18%] z-[61] w-[min(560px,92vw)] -translate-x-1/2 overflow-hidden rounded-2xl border border-accent/30 bg-popover text-popover-foreground shadow-float duration-200 animate-in fade-in zoom-in-95"
      >
        {/* Ô nhập */}
        <div className="flex items-center gap-2.5 border-b border-border/40 px-4 py-3">
          <Search className="size-4 shrink-0 text-popover-foreground/50" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={t('cmd.placeholder')}
            className="w-full bg-transparent text-sm text-popover-foreground outline-none placeholder:text-popover-foreground/40"
          />
          <kbd className="hidden shrink-0 rounded-md border border-border/50 px-1.5 py-0.5 text-[10px] font-medium text-popover-foreground/50 sm:block">
            ESC
          </kbd>
        </div>

        {/* Danh sách */}
        <div className="scrollbar-thin max-h-[320px] overflow-y-auto p-1.5">
          {list.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-popover-foreground/55">
              Không có lệnh nào khớp.
            </p>
          ) : (
            list.map((c, i) => {
              const Icon = c.icon
              const active = i === sel
              return (
                <button
                  key={c.id}
                  onMouseEnter={() => setSel(i)}
                  onClick={c.run}
                  className={cn(
                    'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ease-spring',
                    active ? 'bg-popover-foreground/10' : 'hover:bg-popover-foreground/[0.06]',
                  )}
                >
                  <span
                    className={cn(
                      'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors',
                      active
                        ? 'bg-emphasis text-emphasis-foreground'
                        : 'bg-popover-foreground/10 text-popover-foreground/70',
                    )}
                  >
                    <Icon className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-popover-foreground">
                      {c.label}
                    </span>
                    <span className="block truncate text-xs text-popover-foreground/55">
                      {c.hint}
                    </span>
                  </span>
                  {active && (
                    <CornerDownLeft className="size-4 shrink-0 text-popover-foreground/50" />
                  )}
                </button>
              )
            })
          )}
        </div>

        {/* Chân */}
        <div className="flex items-center gap-3 border-t border-border/40 px-4 py-2 text-[11px] text-popover-foreground/45">
          <span>{t('st.arrowSelect')}</span>
          <span>{t('st.enterRun')}</span>
          <span>{t('st.escClose')}</span>
          <span className="ml-auto flex items-center gap-1">
            <Sparkles className="size-3 text-active" />
            MeoArc
          </span>
        </div>
      </div>
    </>
  )
}
