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
  UserCog,
  Eye,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api, type Preferences, type PreferenceFields } from '@/lib/api'
import { useTheme } from '@/components/theme-provider'
import { t, useNgonNgu } from '@/lib/ngon-ngu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'


/* Nhãn tiếng Việt cho từng giọng văn. Khoá do backend định nghĩa (nguồn sự thật
   duy nhất ở app/models/user_preference.py); ở đây chỉ dịch để hiển thị. */
const TONE_LABEL: Record<string, string> = {
  formal: 'Trang trọng',
  friendly: 'Thân thiện',
  concise: 'Ngắn gọn',
  warm: 'Ấm áp',
}

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

/* ─────────────────── Tab "Cá nhân hoá" — PA2 §1.5.2 ───────────────────
   Đây là chỗ người dùng DẠY trợ lý cách viết thư thay mình. Ba nguyên tắc:
   • Lưu khi rời ô (blur), không phải mỗi lần gõ — gõ tới đâu gọi API tới đó là
     đốt request vô ích và dễ dẫm chân nhau.
   • Chỉ gửi trường vừa đổi, không gửi cả object — backend dùng PATCH nên gửi
     thừa sẽ xoá mất trường khác.
   • Luôn hiện khung XEM TRƯỚC đúng đoạn văn trợ lý sẽ đọc. Không có nó thì
     người dùng gõ vào một ô rồi đoán xem có tác dụng gì.                      */
function PersonalTab() {
  const [pref, setPref] = useState<Preferences | null>(null)
  const [saving, setSaving] = useState<string | null>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.preferences().then(setPref).catch(() => setErr('Không tải được thiết lập.'))
  }, [])

  const save = async (patch: Partial<PreferenceFields>) => {
    const key = Object.keys(patch)[0]
    setSaving(key)
    setErr('')
    try {
      setPref(await api.updatePreferences(patch))
    } catch {
      setErr('Chưa lưu được. Thử lại nhé.')
    } finally {
      setSaving(null)
    }
  }

  if (err && !pref) return <p className="py-6 text-sm text-popover-foreground/60">{err}</p>
  if (!pref) return <div className="skeleton h-40 rounded-xl" />

  return (
    <div className="space-y-5 text-popover-foreground">
      <p className="text-xs leading-relaxed text-popover-foreground/60">
        Những thiết lập này đi thẳng vào lời dặn của trợ lý. Trợ lý sẽ soạn thư theo đúng
        giọng và chữ ký bạn đặt ở đây.
      </p>

      {/* Tên xưng hô */}
      <div>
        <label className="mb-1.5 block text-sm font-semibold">{t('pref.callYou')}</label>
        <input
          defaultValue={pref.displayName ?? ''}
          onBlur={(e) => {
            const v = e.target.value.trim()
            if (v !== (pref.displayName ?? '')) save({ displayName: v || null })
          }}
          placeholder="Anh Quân"
          className="w-full rounded-xl border border-border/40 bg-popover-foreground/5 px-3 py-2 text-sm outline-none transition-colors focus-visible:border-spark/60"
        />
      </div>

      {/* Giọng văn */}
      <div>
        <p className="mb-2 text-sm font-semibold">{t('pref.tone')}</p>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(pref.availableTones).map(([key, desc]) => {
            const active = pref.tonePreference === key
            return (
              <button
                key={key}
                title={desc}
                onClick={() => save({ tonePreference: key })}
                className={cn(
                  'rounded-xl border px-3 py-2 text-left text-sm transition-colors',
                  active
                    ? 'border-spark/60 bg-spark/10 font-medium'
                    : 'border-border/40 bg-popover-foreground/5 hover:bg-popover-foreground/10',
                )}
              >
                {TONE_LABEL[key] ?? key}
                <span className="mt-0.5 block text-[11px] leading-snug text-popover-foreground/50">
                  {desc.split(',')[0]}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Chữ ký */}
      <div>
        <label className="mb-1.5 block text-sm font-semibold">{t('pref.signature')}</label>
        <textarea
          defaultValue={pref.signatureNote ?? ''}
          onBlur={(e) => {
            const v = e.target.value.trim()
            if (v !== (pref.signatureNote ?? '')) save({ signatureNote: v || null })
          }}
          rows={3}
          maxLength={500}
          placeholder={'Phạm Trần Anh Quân\nNhóm 7 — HCMUS'}
          className="w-full resize-none rounded-xl border border-border/40 bg-popover-foreground/5 px-3 py-2 text-sm outline-none transition-colors focus-visible:border-spark/60"
        />
      </div>

      {/* Dặn dò tự do */}
      <div>
        <label className="mb-1.5 block text-sm font-semibold">{t('pref.instruction')}</label>
        <textarea
          defaultValue={pref.customInstruction ?? ''}
          onBlur={(e) => {
            const v = e.target.value.trim()
            if (v !== (pref.customInstruction ?? '')) save({ customInstruction: v || null })
          }}
          rows={2}
          maxLength={1000}
          placeholder="Đừng dùng từ 'trân trọng'. Luôn hỏi lại trước khi hứa deadline."
          className="w-full resize-none rounded-xl border border-border/40 bg-popover-foreground/5 px-3 py-2 text-sm outline-none transition-colors focus-visible:border-spark/60"
        />
      </div>

      {/* Xem trước — đúng thứ trợ lý đọc, không phải bản diễn giải */}
      <div>
        <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-popover-foreground/50">
          <Eye className="size-3.5" />
          Trợ lý sẽ đọc
        </p>
        {pref.promptPreview ? (
          <pre className="whitespace-pre-wrap rounded-xl border border-border/40 bg-popover-foreground/5 px-3 py-2 font-sans text-xs leading-relaxed text-popover-foreground/80">
            {pref.promptPreview}
          </pre>
        ) : (
          <p className="rounded-xl border border-dashed border-border/40 px-3 py-3 text-xs text-popover-foreground/50">
            Chưa đặt gì — trợ lý dùng giọng mặc định. Điền một ô bất kỳ ở trên để thấy
            phần này thay đổi.
          </p>
        )}
      </div>

      <p className="h-4 text-xs text-popover-foreground/50">
        {saving ? 'Đang lưu…' : err || 'Tự lưu khi bạn rời khỏi ô.'}
      </p>
    </div>
  )
}

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
          title={t('act.copy')}
        >
          {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
        </button>
      </div>
    </div>
  )
}

export function SettingsDialog() {
  const { theme, setTheme } = useTheme()
  const [tab, setTab] = useState<'general' | 'personal' | 'mcp'>('general')
  // NGÔN NGỮ do lớp dịch dùng chung giữ (src/lib/ngon-ngu.tsx), không phải state
  // riêng của hộp thoại này — nếu không thì đổi xong đóng hộp thoại là mất, và thanh
  // điều hướng bên ngoài cũng không biết gì để mà đổi theo.
  const { ngon: lang, datNgon: setLang } = useNgonNgu()

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          title={t('nav.settings')}
          className="flex size-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <Settings className="size-5" />
        </button>
      </DialogTrigger>

      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t('nav.settings')}</DialogTitle>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-1 rounded-xl bg-popover-foreground/5 p-1">
          {[
            { key: 'general', label: 'Chung', icon: Settings },
            { key: 'personal', label: 'Cá nhân hoá', icon: UserCog },
            { key: 'mcp', label: 'MCP', icon: Plug },
          ].map((t) => {
            const Icon = t.icon
            const active = tab === t.key
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key as 'general' | 'personal' | 'mcp')}
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
              <p className="mb-2 text-sm font-semibold">{t('settings.appearance')}</p>
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
                      onClick={() => {
                        const v = opt.key as 'vi' | 'en'
                        setLang(v)
                        // LƯU LÊN MÁY CHỦ, không chỉ localStorage.
                        //
                        // Trợ lý đọc `language` từ bảng user_preference để biết trả lời
                        // bằng tiếng gì (xem to_prompt_context). Chỉ lưu ở trình duyệt
                        // thì nút này đổi được mỗi thuộc tính `lang` của thẻ <html> —
                        // tức là một nút không làm gì, thứ tệ hơn không có nút.
                        //
                        // Nuốt lỗi: đổi ngôn ngữ hiển thị vẫn phải chạy dù mạng hỏng.
                        void api.updatePreferences({ language: v }).catch(() => {})
                      }}
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
              {/* NÓI THẲNG PHẠM VI. Bản này dịch phần KHUNG và đổi ngôn ngữ trợ lý trả
                  lời; thẻ kết quả và thông báo lỗi vẫn tiếng Việt. Người dùng bấm xong
                  thấy một nửa đổi một nửa không mà không được báo trước thì họ nghĩ là
                  hỏng — nói trước thì đó là một giới hạn đã biết. */}
              <p className="mt-2 text-[11.5px] leading-relaxed text-popover-foreground/55">
                {t('settings.langNote')}
              </p>
            </div>
          </div>
        ) : tab === 'personal' ? (
          <PersonalTab />
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
