import { useEffect, useState } from 'react'
import {
  Inbox,
  Send,
  FileEdit,
  Star,
  Archive,
  Trash2,
  Sparkles,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { LogoMark } from '@/components/logo'
import { AccountMenu } from '@/components/layout/account-menu'
import { SettingsDialog } from '@/components/layout/settings-dialog'
import { NotificationBell } from '@/components/layout/notification-bell'

type NavItem = { id: string; label: string; icon: React.ElementType }

const items: NavItem[] = [
  { id: 'inbox', label: 'Hộp thư', icon: Inbox },
  { id: 'agent', label: 'AI Agent', icon: Sparkles },
  { id: 'starred', label: 'Gắn sao', icon: Star },
  { id: 'sent', label: 'Đã gửi', icon: Send },
  { id: 'drafts', label: 'Nháp', icon: FileEdit },
  { id: 'archive', label: 'Lưu trữ', icon: Archive },
  { id: 'trash', label: 'Thùng rác', icon: Trash2 },
]

const COLLAPSE_KEY = 'meoarc:navCollapsed'

/** Ô trạng thái hệ thống — thay cho đồng hồ cơ mạ vàng ở bản trước.
 *
 *  Đồng hồ đó là món chế tác đẹp, nhưng nó nói "xưởng đồng hồ Thuỵ Sĩ" trong khi sản
 *  phẩm là một agent. Đổi nhãn không cứu được: hình dáng mặt số cơ khí và ánh vàng
 *  tự nó đã kể sai câu chuyện.
 *
 *  Ô này giữ nguyên vị trí và vai trò (thông tin nền, cuối thanh điều hướng) nhưng nói
 *  đúng thứ đang chạy: trợ lý còn sống, và giờ hiện tại — dạng monospace, thứ chữ mà
 *  bảng điều khiển nào cũng dùng.
 */
function SystemStatus({ collapsed }: { collapsed: boolean }) {
  const [gio, setGio] = useState(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setGio(new Date()), 30_000)
    return () => clearInterval(t)
  }, [])
  const hhmm = gio.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false })

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-1.5 py-2" title={`Trợ lý sẵn sàng · ${hhmm}`}>
        <span className="pulse-dot" aria-hidden />
        <span className="font-mono text-[9px] tabular-nums text-muted-foreground/45">{hhmm}</span>
      </div>
    )
  }

  return (
    <div className="mx-2 rounded-lg border border-foreground/[0.06] px-3 py-2.5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-[9px] uppercase tracking-[0.2em] text-muted-foreground/55">
          <span className="pulse-dot" aria-hidden />
          Trực tuyến
        </span>
        <span className="font-mono text-[11px] tabular-nums text-[var(--spark)]">{hhmm}</span>
      </div>
      <p className="mt-1.5 text-[9px] uppercase tracking-[0.16em] text-muted-foreground/35">
        Trợ lý sẵn sàng
      </p>
    </div>
  )
}

export function NavRail({
  activeId,
  onSelect,
  badges = {},
  agentActive = false,
}: {
  activeId: string
  onSelect: (id: string) => void
  badges?: Record<string, number>
  /** Nút "AI Agent" là công tắc → sáng theo trạng thái panel chat, không theo thư mục. */
  agentActive?: boolean
}) {
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(COLLAPSE_KEY) === '1',
  )
  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0')
  }, [collapsed])

  return (
    <nav
      className={cn(
        'relative z-20 flex h-full shrink-0 flex-col bg-rail py-5 border-r border-border/40 transition-[width] duration-300 ease-soft',
        collapsed ? 'w-[76px]' : 'w-[212px]',
      )}
      style={{
        backgroundImage: `repeating-linear-gradient(90deg, transparent, transparent 19px, rgba(239, 217, 210, 0.12) 19px, rgba(239, 217, 210, 0.12) 20px)`
      }}
    >
      {/* Logo + nút thu/mở */}
      <div
        className={cn(
          'mb-6 flex items-center px-3',
          collapsed ? 'flex-col gap-3' : 'gap-2',
        )}
      >
        <div className="flex min-w-0 items-center gap-2">
          <LogoMark className="size-9 shrink-0 text-emphasis" />
          {!collapsed && (
            <span className="font-serif text-base font-semibold tracking-wide text-foreground">
              MeoArc
            </span>
          )}
        </div>
        <button
          onClick={() => setCollapsed((v) => !v)}
          title={collapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng'}
          aria-label={collapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng'}
          className={cn(
            'flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground active:scale-95',
            !collapsed && 'ml-auto',
          )}
        >
          {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
        </button>
      </div>

      {/* Items */}
      <div className="flex flex-1 flex-col gap-1 px-3">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = item.id === 'agent' ? agentActive : activeId === item.id
          const count = badges[item.id]
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              title={collapsed ? item.label : undefined}
              className={cn(
                'group relative flex items-center rounded-2xl transition-all duration-200 ease-spring press',
                collapsed ? 'h-12 justify-center' : 'gap-3 px-3 py-2.5',
                isActive
                  ? 'bg-secondary text-active glow-active border border-border/40'
                  : 'text-muted-foreground hover:bg-secondary/40 hover:text-foreground',
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full bg-active" />
              )}
              <span className="relative shrink-0">
                <Icon className={cn('size-5', isActive && 'stroke-[2.2px]')} />
                {count ? (
                  <span className="absolute -right-2 -top-2 flex size-4 items-center justify-center rounded-full bg-spark text-[10px] font-semibold text-background cherry-dot animate-pulse">
                    {count}
                  </span>
                ) : null}
              </span>
              {!collapsed && (
                <span className="truncate text-sm font-medium leading-none">{item.label}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Gọi đồng hồ cơ thấu quang an toàn */}
      <SystemStatus collapsed={collapsed} />

      {/* Đáy: cài đặt + tài khoản */}
      <div className="space-y-2 px-3 border-t border-border/10 pt-4 bg-secondary/5">
        <div className={cn('flex gap-1.5', collapsed ? 'flex-col items-center' : 'items-center justify-between')}>
          <NotificationBell />
          <SettingsDialog />
          <AccountMenu />
        </div>
      </div>
    </nav>
  )
}