import { useEffect, useState, type CSSProperties } from 'react'
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

/** Đồng hồ CƠ Quiet Luxury — Trả lại mặt nền dìm khối và inset shadow nguyên bản của Claude */
function MechanicalClock({ collapsed }: { collapsed: boolean }) {
  const [delays] = useState(() => {
    const now = new Date()
    const s = now.getSeconds() + now.getMilliseconds() / 1000
    const m = now.getMinutes() * 60 + s
    const h = (now.getHours() % 12) * 3600 + m
    return { second: -s, minute: -m, hour: -h }
  })

  const face = collapsed ? 40 : 52
  const center = face / 2

  return (
    <div className="flex flex-col items-center gap-1.5 border-t border-border/20 pt-4 mt-auto mb-2 w-full transition-all duration-300">
      <div
        className="relative flex items-center justify-center select-none rounded-full border border-gold/40 shadow-[inset_0_0_8px_rgba(0,0,0,0.5)] transition-all duration-300"
        style={{ 
          width: face, 
          height: face,
          // Mix màu rail với gỗ mun sẫm chuẩn bài phối màu trong index.css
          background: 'color-mix(in srgb, var(--rail) 72%, #0a130d)' 
        }}
        role="img"
        aria-label="Đồng hồ"
        title={new Date().toLocaleTimeString('vi-VN')}
      >
        <svg width={face} height={face} viewBox={`0 0 ${face} ${face}`} className="overflow-visible bg-transparent">
          
          {/* 12 Vạch số gold mảnh truyền thống */}
          {Array.from({ length: 12 }).map((_, i) => (
            <line
              key={i}
              x1={center}
              y1={collapsed ? 3 : 5}
              x2={center}
              y2={collapsed ? 5.5 : 8.5}
              stroke="var(--gold)"
              strokeWidth={collapsed ? 0.8 : 1.2}
              opacity="0.75"
              transform={`rotate(${i * 30} ${center} ${center})`}
            />
          ))}

          {/* Kim Giờ (Baton mảnh) */}
          <line
            x1={center}
            y1={center}
            x2={center}
            y2={collapsed ? center - 7 : center - 11}
            stroke="var(--foreground)"
            strokeWidth={1.8}
            strokeLinecap="round"
            style={{
              transformOrigin: `${center}px ${center}px`,
              animation: 'clock-sweep 43200s linear infinite',
              animationDelay: `${delays.hour}s`,
            } as CSSProperties}
          />

          {/* Kim Phút (Baton mảnh chỉ) */}
          <line
            x1={center}
            y1={center}
            x2={center}
            y2={collapsed ? center - 11 : center - 17}
            stroke="var(--foreground)"
            strokeWidth={1.2}
            strokeLinecap="round"
            opacity="0.9"
            style={{
              transformOrigin: `${center}px ${center}px`,
              animation: 'clock-sweep 3600s linear infinite',
              animationDelay: `${delays.minute}s`,
            } as CSSProperties}
          />

          {/* Kim Giây (Kim quét cơ khí màu hồng cherry mảnh dẻ) */}
          <line
            x1={center}
            y1={center}
            x2={center}
            y2={collapsed ? center - 13 : center - 20}
            stroke="var(--spark)"
            strokeWidth={0.8}
            strokeLinecap="round"
            style={{
              transformOrigin: `${center}px ${center}px`,
              animation: 'clock-sweep 60s linear infinite',
              animationDelay: `${delays.second}s`,
            } as CSSProperties}
          />

          {/* Chốt kim loại gold đồng tâm ở tâm máy */}
          <circle cx={center} cy={center} r={collapsed ? 1.2 : 1.8} fill="var(--gold)" />
        </svg>
      </div>
      {!collapsed && (
        <span className="text-[9px] uppercase font-mono tracking-[0.25em] text-muted-foreground/40 animate-in fade-in duration-500">
          Chronomètre
        </span>
      )}
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
      <MechanicalClock collapsed={collapsed} />

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