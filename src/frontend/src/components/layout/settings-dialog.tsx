import { useEffect, useState } from 'react'
import {
  Settings,
  Sun,
  Moon,
  Languages,
  Plug,
  Copy,
  Check,
  ShieldCheck,
  Wrench,
  Server,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/components/theme-provider'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

const LANG_KEY = 'meoarc-lang'

const MCP_TOOLS = [
  'search_emails',
  'summarize',
  'draft_reply',
  'send_email',
  'reply_email',
  'bulk_manage',
  'extract_tasks',
]

const SCOPES = [
  { label: 'Đọc thư (read)', on: true },
  { label: 'Quản lý thư (modify/label/archive)', on: true },
  { label: 'Soạn & gửi (send)', on: true },
]

function CopyRow({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard?.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1400)
  }
  return (
    <div>
      <p className="mb-1 text-xs text-popover-foreground/60">{label}</p>
      <div className="flex items-center gap-2 rounded-xl border border-border/40 bg-popover-foreground/5 px-3 py-2">
        <code className="min-w-0 flex-1 truncate text-xs text-popover-foreground">{value}</code>
        <button
          onClick={copy}
          className="flex size-7 shrink-0 items-center justify-center rounded-lg text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground"
          title="Sao chép"
        >
          {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
        </button>
      </div>
    </div>
  )
}

export function SettingsDialog() {
  const { theme, setTheme } = useTheme()
  const [tab, setTab] = useState<'general' | 'mcp'>('general')
  const [lang, setLang] = useState<'vi' | 'en'>(
    () => (localStorage.getItem(LANG_KEY) as 'vi' | 'en') || 'vi',
  )

  useEffect(() => {
    localStorage.setItem(LANG_KEY, lang)
    document.documentElement.lang = lang
  }, [lang])

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          title="Cài đặt"
          className="flex size-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <Settings className="size-5" />
        </button>
      </DialogTrigger>

      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Cài đặt</DialogTitle>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-1 rounded-xl bg-popover-foreground/5 p-1">
          {[
            { key: 'general', label: 'Chung', icon: Settings },
            { key: 'mcp', label: 'MCP', icon: Plug },
          ].map((t) => {
            const Icon = t.icon
            const active = tab === t.key
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key as 'general' | 'mcp')}
                className={cn(
                  'flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                  active
                    ? 'bg-popover-foreground/10 text-popover-foreground'
                    : 'text-popover-foreground/60 hover:text-popover-foreground',
                )}
              >
                <Icon className="size-4" />
                {t.label}
              </button>
            )
          })}
        </div>

        {tab === 'general' ? (
          <div className="space-y-5 text-popover-foreground">
            {/* Giao diện */}
            <div>
              <p className="mb-2 text-sm font-semibold">Giao diện</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'light', label: 'Sáng', icon: Sun },
                  { key: 'dark', label: 'Tối', icon: Moon },
                ].map((opt) => {
                  const Icon = opt.icon
                  const active = theme === opt.key
                  return (
                    <button
                      key={opt.key}
                      onClick={() => setTheme(opt.key as 'light' | 'dark')}
                      className={cn(
                        'flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-medium transition-colors',
                        active
                          ? 'border-active bg-active/15 text-popover-foreground'
                          : 'border-border/40 text-popover-foreground/70 hover:bg-popover-foreground/5',
                      )}
                    >
                      <Icon className="size-4" />
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Ngôn ngữ */}
            <div>
              <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                <Languages className="size-4" />
                Ngôn ngữ hiển thị
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'vi', label: 'Tiếng Việt' },
                  { key: 'en', label: 'English' },
                ].map((opt) => {
                  const active = lang === opt.key
                  return (
                    <button
                      key={opt.key}
                      onClick={() => setLang(opt.key as 'vi' | 'en')}
                      className={cn(
                        'rounded-xl border px-3 py-2.5 text-sm font-medium transition-colors',
                        active
                          ? 'border-active bg-active/15 text-popover-foreground'
                          : 'border-border/40 text-popover-foreground/70 hover:bg-popover-foreground/5',
                      )}
                    >
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 text-popover-foreground">
            <p className="flex items-start gap-2 text-xs text-popover-foreground/70">
              <Server className="mt-0.5 size-4 shrink-0 text-active" />
              Kết nối AI Agent ngoài (Claude Desktop / Codex) tới hộp thư của bạn qua MCP — gọi
              trực tiếp các tool trong phạm vi quyền đã cấp.
            </p>

            <CopyRow label="MCP Server endpoint" value="https://mcp.meoarc.dev/sse" />
            <CopyRow label="Access token" value="mcp_sk_••••••••••••3f9a" />

            {/* Scopes */}
            <div>
              <p className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold">
                <ShieldCheck className="size-4" />
                Phạm vi quyền đã cấp
              </p>
              <div className="space-y-1.5">
                {SCOPES.map((s) => (
                  <div key={s.label} className="flex items-center gap-2 text-sm text-popover-foreground/80">
                    <Check className="size-4 text-success" />
                    {s.label}
                  </div>
                ))}
              </div>
            </div>

            {/* Tools */}
            <div>
              <p className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold">
                <Wrench className="size-4" />
                Tool khả dụng
              </p>
              <div className="flex flex-wrap gap-1.5">
                {MCP_TOOLS.map((t) => (
                  <code
                    key={t}
                    className="rounded-lg bg-popover-foreground/10 px-2 py-1 text-[11px] text-popover-foreground"
                  >
                    {t}
                  </code>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-xl bg-success/15 px-3 py-2 text-xs text-popover-foreground">
              <span className="size-2 rounded-full bg-success" />
              Trạng thái: đã kết nối · 1 client đang hoạt động
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
