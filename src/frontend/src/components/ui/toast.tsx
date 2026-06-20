import { createContext, useCallback, useContext, useState } from 'react'
import { CheckCircle2, Info, AlertTriangle, X } from 'lucide-react'

type Tone = 'default' | 'success' | 'destructive'
type Toast = { id: number; message: string; tone: Tone }

type ToastContextValue = { show: (message: string, tone?: Tone) => void }

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

let toastId = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const DURATION = 2800
  const show = useCallback(
    (message: string, tone: Tone = 'default') => {
      const id = ++toastId
      setToasts((prev) => [...prev, { id, message, tone }])
      window.setTimeout(() => remove(id), DURATION)
    },
    [remove],
  )

  const toneColor = (t: Tone) =>
    t === 'success' ? 'var(--success)' : t === 'destructive' ? 'var(--destructive)' : 'var(--active)'

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      {/* Lớp hiển thị toast */}
      <div className="pointer-events-none fixed bottom-5 left-1/2 z-[70] flex -translate-x-1/2 flex-col items-center gap-2">
        {toasts.map((t) => {
          const Icon =
            t.tone === 'success' ? CheckCircle2 : t.tone === 'destructive' ? AlertTriangle : Info
          const color = toneColor(t.tone)
          return (
            <div
              key={t.id}
              className="gloss pointer-events-auto relative flex items-center gap-2.5 overflow-hidden rounded-2xl border border-border/50 bg-popover py-2.5 pl-3 pr-2 text-sm text-popover-foreground shadow-float duration-300 ease-spring animate-in fade-in zoom-in-95 slide-in-from-bottom-3"
            >
              {/* Icon trong ô tint theo tone */}
              <span
                className="flex size-7 shrink-0 items-center justify-center rounded-lg"
                style={{ backgroundColor: `color-mix(in srgb, ${color} 20%, transparent)` }}
              >
                <Icon className="size-4" style={{ color }} />
              </span>
              <span className="pr-1 font-medium">{t.message}</span>
              <button
                onClick={() => remove(t.id)}
                aria-label="Đóng thông báo"
                className="flex size-6 shrink-0 items-center justify-center rounded-md text-popover-foreground/50 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground active:scale-90"
              >
                <X className="size-3.5" />
              </button>
              {/* Thanh đếm giờ tự tắt */}
              <span aria-hidden className="absolute inset-x-0 bottom-0 h-[3px] bg-popover-foreground/10">
                <span
                  className="block h-full origin-left"
                  style={{ backgroundColor: color, animation: `toast-bar ${DURATION}ms linear forwards` }}
                />
              </span>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast phải dùng trong <ToastProvider>')
  return ctx.show
}
