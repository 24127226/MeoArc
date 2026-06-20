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

export function NavRail({
  activeId,
  onSelect,
  badges = {},
}: {
  activeId: string
  onSelect: (id: string) => void
  badges?: Record<string, number>
}) {
  // Trạng thái thu/mở — nhớ qua localStorage để lần sau giữ nguyên
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(COLLAPSE_KEY) === '1',
  )
  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0')
  }, [collapsed])

  return (
    <nav
      className={cn(
        'relative z-20 flex h-full shrink-0 flex-col bg-rail py-5 shadow-float transition-[width] duration-300 ease-soft',
        collapsed ? 'w-[76px]' : 'w-[212px]',
      )}
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
            'flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-elevated/60 hover:text-foreground active:scale-95',
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
          const isActive = activeId === item.id
          const count = badges[item.id]
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              title={collapsed ? item.label : undefined}
              className={cn(
                'group relative flex items-center rounded-2xl transition-all duration-200 ease-spring',
                collapsed ? 'h-12 justify-center' : 'gap-3 px-3 py-2.5',
                isActive
                  ? 'bg-elevated text-active shadow-subtle edge-light glow-active'
                  : 'text-muted-foreground hover:-translate-y-0.5 hover:bg-elevated/60 hover:text-foreground',
              )}
            >
              {/* Thanh nhấn màu active bên trái */}
              {isActive && (
                <span className="absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full bg-active" />
              )}
              <span className="relative shrink-0">
                <Icon className="size-5" />
                {count ? (
                  <span className="absolute -right-2 -top-2 flex size-4 items-center justify-center rounded-full bg-accent text-[10px] font-semibold text-accent-foreground">
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

      {/* Đáy: cài đặt (UC013/UC012 — đổi theme ở đây) + tài khoản (UC002) */}
      <div
        className={cn(
          'mt-2 flex gap-1.5 px-3',
          collapsed ? 'flex-col items-center' : 'items-center justify-between',
        )}
      >
        <SettingsDialog />
        <AccountMenu />
      </div>
    </nav>
  )
}
