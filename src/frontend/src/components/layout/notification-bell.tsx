import { useCallback, useEffect, useRef, useState } from 'react'
import { Bell, CheckCircle2, AlertTriangle, Info, CheckCheck, MonitorSmartphone } from 'lucide-react'
import { api, type NotificationItem } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { t } from '@/lib/ngon-ngu'

// Biểu tượng + tông màu theo loại (dùng token/utility, KHÔNG hardcode hex).
const META: Record<string, { icon: React.ElementType; ring: string; dot: string }> = {
  success: { icon: CheckCircle2, ring: 'bg-active/15 text-active', dot: 'bg-active' },
  warning: { icon: AlertTriangle, ring: 'bg-destructive/15 text-destructive', dot: 'bg-destructive' },
  info: { icon: Info, ring: 'bg-accent/20 text-accent-foreground', dot: 'bg-spark' },
}

function relTime(iso: string | null): string {
  if (!iso) return ''
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return 'vừa xong'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m} phút trước`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} giờ trước`
  return `${Math.floor(h / 24)} ngày trước`
}

function isToday(iso: string | null): boolean {
  if (!iso) return false
  const d = new Date(iso)
  const n = new Date()
  return d.getDate() === n.getDate() && d.getMonth() === n.getMonth() && d.getFullYear() === n.getFullYear()
}

const canDesktop = typeof window !== 'undefined' && 'Notification' in window
const POLL_MS = 25_000

/**
 * Chuông thông báo (accountability) — badge chưa đọc + panel sang, và BẮN THÔNG BÁO
 * DESKTOP (Web Notifications API) khi có thông báo mới: hiện ngay cả khi người dùng đang
 * ở tab/ứng dụng khác, miễn còn 1 tab MeoArc mở. (Đóng hẳn trình duyệt cần Service Worker
 * + Web Push — bước nâng cấp sau.)
 */
export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(false)
  const [perm, setPerm] = useState<NotificationPermission | 'unsupported'>(
    canDesktop ? Notification.permission : 'unsupported',
  )
  const seen = useRef<Set<number> | null>(null) // id đã biết (để chỉ báo desktop cho thư MỚI)

  const fireDesktop = useCallback((n: NotificationItem) => {
    if (!canDesktop || Notification.permission !== 'granted') return
    try {
      const notif = new Notification('MeoArc — thông báo', { body: n.message, tag: `meoarc-${n.id}` })
      notif.onclick = () => {
        window.focus()
        notif.close()
      }
    } catch {
      /* một số trình duyệt chặn tạo Notification ngoài user-gesture → bỏ qua */
    }
  }, [])

  // Poll danh sách: cập nhật badge + phát hiện thông báo MỚI để bắn desktop.
  const poll = useCallback(async () => {
    try {
      const res = await api.listNotifications(50)
      setItems(res.items)
      setUnread(res.unread)
      const ids = new Set(res.items.map((n) => n.id))
      if (seen.current === null) {
        seen.current = ids // lần đầu: coi mọi thứ là "đã biết", KHÔNG bắn cho thông báo cũ
      } else {
        res.items
          .filter((n) => !n.read && !seen.current!.has(n.id))
          .slice(0, 3)
          .forEach(fireDesktop)
        seen.current = ids
      }
    } catch {
      /* chưa đăng nhập / offline → im lặng */
    }
  }, [fireDesktop])

  useEffect(() => {
    poll()
    const t = setInterval(poll, POLL_MS)
    return () => clearInterval(t)
  }, [poll])

  const loadList = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.listNotifications(50)
      setItems(res.items)
      setUnread(res.unread)
      seen.current = new Set(res.items.map((n) => n.id))
    } catch {
      /* offline */
    } finally {
      setLoading(false)
    }
  }, [])

  const onOpenChange = (o: boolean) => {
    setOpen(o)
    if (o) {
      loadList()
      // Xin quyền desktop ngay trong cử chỉ mở panel (yêu cầu của trình duyệt).
      if (canDesktop && Notification.permission === 'default') {
        Notification.requestPermission().then((p) => setPerm(p))
      }
    }
  }

  const askDesktop = () => {
    if (canDesktop) Notification.requestPermission().then((p) => setPerm(p))
  }

  const markOne = async (n: NotificationItem) => {
    if (n.read) return
    setItems((xs) => xs.map((x) => (x.id === n.id ? { ...x, read: true } : x)))
    setUnread((u) => Math.max(0, u - 1))
    try {
      await api.markNotificationRead(n.id)
    } catch {
      /* ignore */
    }
  }

  const markAll = async () => {
    setItems((xs) => xs.map((x) => ({ ...x, read: true })))
    setUnread(0)
    try {
      await api.markAllNotificationsRead()
    } catch {
      /* ignore */
    }
  }

  const today = items.filter((n) => isToday(n.createdAt))
  const earlier = items.filter((n) => !isToday(n.createdAt))

  const renderItem = (n: NotificationItem, i: number) => {
    const meta = META[n.type] ?? META.info
    const Icon = meta.icon
    return (
      <li
        key={n.id}
        className="animate-in fade-in slide-in-from-top-1 fill-mode-both"
        style={{ animationDelay: `${Math.min(i, 8) * 28}ms` }}
      >
        <button
          onClick={() => markOne(n)}
          className={cn(
            'group relative flex w-full items-start gap-3 rounded-2xl px-3 py-2.5 text-left transition-all duration-200 ease-spring hover:-translate-y-px hover:bg-secondary/60',
            !n.read && 'bg-secondary/40',
          )}
        >
          {/* Vạch cherry mép trái cho thư CHƯA đọc */}
          {!n.read && <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-spark" />}
          <span className={cn('mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl', meta.ring)}>
            <Icon className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className={cn('text-sm leading-snug text-popover-foreground', !n.read && 'font-semibold')}>
              {n.message}
            </p>
            <p className="mt-1 text-[11px] uppercase tracking-[0.08em] text-muted-foreground/80">
              {relTime(n.createdAt)}
            </p>
          </div>
          {!n.read && <span className={cn('mt-1.5 size-2 shrink-0 rounded-full cherry-dot', meta.dot)} />}
        </button>
      </li>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <button
          title={t('nav.notifications')}
          aria-label={unread ? `Thông báo (${unread} chưa đọc)` : 'Thông báo'}
          className="relative flex size-9 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground active:scale-95"
        >
          <Bell className={cn('size-5', unread > 0 && 'text-foreground')} />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-spark px-1 text-[10px] font-semibold text-background cherry-dot">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>
      </DialogTrigger>

      <DialogContent className="glass edge-light max-w-sm gap-0 overflow-hidden p-0">
        {/* Đầu panel — tiêu đề serif + pill chưa đọc + đọc tất cả */}
        <DialogHeader className="space-y-0 border-b border-border/40 bg-gradient-to-b from-secondary/40 to-transparent px-5 pb-4 pt-5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-left">
              <span className="flex size-9 items-center justify-center rounded-xl bg-emphasis/10 text-emphasis">
                <Bell className="size-[18px]" />
              </span>
              <div>
                <DialogTitle className="font-serif text-lg">{t('nav.notifications')}</DialogTitle>
                <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  {unread ? `${unread} chưa đọc` : 'Đã xem hết'}
                </p>
              </div>
            </div>
            {unread > 0 && (
              <button
                onClick={markAll}
                className="flex shrink-0 items-center gap-1.5 rounded-full border border-border/50 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              >
                <CheckCheck className="size-3.5" />
                Đọc tất cả
              </button>
            )}
          </div>
        </DialogHeader>

        {/* Danh sách */}
        <div className="fade-y max-h-[56vh] overflow-y-auto px-2.5 py-2">
          {loading && items.length === 0 ? (
            <p className="px-3 py-10 text-center text-sm text-muted-foreground">{t('st.loading')}</p>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center gap-3 px-3 py-12 text-center">
              <span className="bokeh flex size-14 items-center justify-center rounded-full bg-secondary/40">
                <Bell className="size-6 text-muted-foreground/50" />
              </span>
              <div>
                <p className="text-sm font-medium text-foreground">{t('st.noNotif')}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Gửi thư, gắn nhãn hay dọn hộp thư — hoạt động sẽ hiện ở đây.
                </p>
              </div>
            </div>
          ) : (
            <>
              {today.length > 0 && (
                <>
                  <p className="px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/60">
                    Hôm nay
                  </p>
                  <ul className="space-y-0.5">{today.map(renderItem)}</ul>
                </>
              )}
              {earlier.length > 0 && (
                <>
                  <p className="px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/60">
                    Trước đó
                  </p>
                  <ul className="space-y-0.5">{earlier.map((n, i) => renderItem(n, today.length + i))}</ul>
                </>
              )}
            </>
          )}
        </div>

        {/* Chân panel — điều khiển thông báo desktop toàn màn hình */}
        {perm !== 'unsupported' && (
          <div className="flex items-center gap-2 border-t border-border/40 bg-secondary/20 px-4 py-2.5">
            <MonitorSmartphone className="size-4 shrink-0 text-muted-foreground" />
            {perm === 'granted' ? (
              <p className="text-[11px] text-muted-foreground">
                Thông báo màn hình <span className="font-medium text-active">{t('st.on')}</span> — hiện cả khi bạn ở tab khác.
              </p>
            ) : perm === 'denied' ? (
              <p className="text-[11px] text-muted-foreground">
                Bạn đã chặn thông báo màn hình. Bật lại trong cài đặt trình duyệt (biểu tượng 🔒 cạnh URL).
              </p>
            ) : (
              <button onClick={askDesktop} className="text-[11px] font-medium text-emphasis hover:underline">
                Bật thông báo trên màn hình (kể cả khi ở tab khác)
              </button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
