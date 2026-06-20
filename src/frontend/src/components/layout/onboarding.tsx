import { useState } from 'react'
import { Inbox, Sparkles, Mic, Command } from 'lucide-react'
import { MeoMascot } from '@/components/meo-mascot'

const KEY = 'meoarc:onboarded'

const TIPS = [
  {
    icon: Inbox,
    title: 'Giao diện 3 cột',
    desc: 'Điều hướng trái · danh sách thư giữa · trợ lý AI phải. Kéo mép phải để chỉnh rộng.',
  },
  {
    icon: Sparkles,
    title: 'Trợ lý ngôn ngữ tự nhiên',
    desc: 'Cứ nhắn lời thường: “tóm tắt thư chưa đọc”, “lưu trữ thư bản tin”, “brief cuộc họp”…',
  },
  {
    icon: Mic,
    title: 'Ra lệnh bằng giọng nói',
    desc: 'Bấm mic để nói — trợ lý nghe, hiểu và đọc lại câu trả lời cho bạn.',
  },
  {
    icon: Command,
    title: 'Phím tắt nhanh',
    desc: '⌘K mở bảng lệnh · / tìm kiếm · j/k duyệt thư · Enter mở · c soạn thư.',
  },
]

/** Onboarding coachmark — thẻ chào mừng + mẹo dùng, chỉ hiện LẦN ĐẦU (nhớ localStorage). */
export function Onboarding() {
  const [open, setOpen] = useState(() => localStorage.getItem(KEY) !== '1')
  if (!open) return null

  const dismiss = () => {
    localStorage.setItem(KEY, '1')
    setOpen(false)
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
      <div aria-hidden onClick={dismiss} className="absolute inset-0 bg-black/55 backdrop-blur-sm duration-300 animate-in fade-in" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Chào mừng đến MeoArc"
        className="glass edge-light relative z-10 w-full max-w-md overflow-hidden rounded-3xl border border-accent/30 p-7 shadow-float duration-300 animate-in fade-in zoom-in-95"
      >
        {/* Mèo chào */}
        <div className="flex flex-col items-center text-center">
          <span className="bokeh flex size-20 items-center justify-center">
            <MeoMascot mood="happy" className="size-20 drop-shadow-xl" />
          </span>
          <h2 className="mt-3 font-serif text-2xl font-semibold text-foreground">
            Chào mừng đến MeoArc
          </h2>
          <p className="mt-1 text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Email Intelligence · quản lý Gmail bằng AI
          </p>
        </div>

        {/* Mẹo dùng */}
        <div className="mt-6 space-y-2.5">
          {TIPS.map((t) => {
            const Icon = t.icon
            return (
              <div key={t.title} className="flex items-start gap-3 rounded-2xl bg-popover-foreground/5 p-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-emphasis text-emphasis-foreground shadow-subtle">
                  <Icon className="size-4" />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground">{t.title}</p>
                  <p className="text-xs leading-relaxed text-muted-foreground">{t.desc}</p>
                </div>
              </div>
            )
          })}
        </div>

        <button
          onClick={dismiss}
          className="gloss gloss-sweep mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-soft transition-all ease-spring hover:-translate-y-0.5 hover:shadow-float active:scale-[0.98]"
        >
          <Sparkles className="size-4" />
          Bắt đầu khám phá
        </button>
      </div>
    </div>
  )
}
