import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CalendarDays,
  Inbox,
  Send,
  FileEdit,
  Star,
  Archive,
  Trash2,
  Sparkles,
  ChevronsLeft,
  ChevronsRight,
  ShieldAlert,
  MoreHorizontal,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { LogoMark } from '@/components/logo'
import { AccountMenu } from '@/components/layout/account-menu'
import { SettingsDialog } from '@/components/layout/settings-dialog'
import { NotificationBell } from '@/components/layout/notification-bell'

type NavItem = { id: string; label: string; icon: React.ElementType; sangTrang?: string }

/* ══════════════════════════════════════════════════════════════════════════════
   BA MỤC CHÍNH, PHẦN CÒN LẠI GIẤU SAU MỘT NÚT

   Trước đây thanh này có tám mục ngang hàng nhau: Hộp thư, AI Agent, Lịch trình,
   Gắn sao, Đã gửi, Nháp, Lưu trữ, Thùng rác. Xếp ngang hàng nghĩa là nói với
   người dùng rằng "Thùng rác" quan trọng bằng "AI Agent" — mà đó là điều sai.

   MeoArc chỉ có ba thứ đáng gọi là trung tâm: đọc thư, nói chuyện với trợ lý, và
   giữ lịch trình. Sáu thư mục còn lại là chỗ để TÌM LẠI một lá thư — việc người
   ta làm vài lần một tuần, không phải vài lần một giờ. Chúng không xứng chiếm
   chỗ ngang hàng, và để chúng ở đó thì ba mục chính cũng mất luôn sức nặng.

   Nên: ba mục chính to hơn, luôn thấy. Phần còn lại nằm sau một nút mở, và vùng
   đó CUỘN ĐƯỢC — thêm thư mục về sau cũng không đẩy hỏng gì.
   ══════════════════════════════════════════════════════════════════════════════ */
const CHINH: NavItem[] = [
  { id: 'inbox', label: 'Hộp thư', icon: Inbox },
  { id: 'agent', label: 'Trợ lý', icon: Sparkles },
  { id: 'lich', label: 'Lịch trình', icon: CalendarDays, sangTrang: '/lich' },
]

/** Thư mục — chỗ TÌM LẠI thư, không phải chỗ làm việc hằng ngày. */
const PHU: NavItem[] = [
  { id: 'starred', label: 'Gắn sao', icon: Star },
  { id: 'sent', label: 'Đã gửi', icon: Send },
  { id: 'drafts', label: 'Nháp', icon: FileEdit },
  { id: 'archive', label: 'Lưu trữ', icon: Archive },
  // Spam TỪNG THIẾU hẳn, dù nó là thư mục người ta cần nhất khi một lá thư quan
  // trọng "biến mất" — và đó là lúc người dùng hoảng nhất.
  { id: 'spam', label: 'Thư rác', icon: ShieldAlert },
  { id: 'trash', label: 'Thùng rác', icon: Trash2 },
]


const COLLAPSE_KEY = 'meoarc:navCollapsed'
const MO_RONG_KEY = 'meoarc:navMoRong'

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
/** Một mục điều hướng. `to` = mục CHÍNH (to hơn, đậm hơn) hay mục phụ. */
function MucNav({
  item, collapsed, isActive, count, onBam, to,
}: {
  item: NavItem
  collapsed: boolean
  isActive: boolean
  count?: number
  onBam: () => void
  to: boolean
}) {
  const Icon = item.icon
  return (
    <button
      onClick={onBam}
      title={collapsed ? item.label : undefined}
      className={cn(
        'group press relative flex items-center rounded-2xl transition-all duration-200 ease-spring',
        collapsed ? 'justify-center' : 'gap-3 px-3',
        // Mục chính CAO HƠN và chữ ĐẬM HƠN. Thứ bậc phải đọc được bằng mắt chứ
        // không phải bằng cách suy ra từ vị trí.
        to ? (collapsed ? 'h-13 py-3' : 'py-3') : collapsed ? 'h-10 py-2' : 'py-2',
        isActive
          ? 'bg-secondary text-active glow-active border border-border/40'
          : 'text-muted-foreground hover:bg-secondary/40 hover:text-foreground',
      )}
    >
      {isActive && (
        <span className="absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full bg-active" />
      )}
      <span className="relative shrink-0">
        <Icon className={cn(to ? 'size-[22px]' : 'size-[18px]', isActive && 'stroke-[2.2px]')} />
        {count ? (
          <span className="cherry-dot absolute -right-2 -top-2 flex size-4 animate-pulse items-center justify-center rounded-full bg-spark text-[10px] font-semibold text-background">
            {count}
          </span>
        ) : null}
      </span>
      {!collapsed && (
        <span className={cn('truncate leading-none', to ? 'text-[15px] font-semibold' : 'text-sm font-medium')}>
          {item.label}
        </span>
      )}
    </button>
  )
}

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
    <div className="den-vien mx-2 rounded-lg px-3 py-2.5">
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
  const navigate = useNavigate()
  const [moRong, setMoRong] = useState(() => {
    try { return localStorage.getItem(MO_RONG_KEY) === '1' } catch { return false }
  })
  useEffect(() => {
    try { localStorage.setItem(MO_RONG_KEY, moRong ? '1' : '0') } catch { /* riêng tư */ }
  }, [moRong])
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(COLLAPSE_KEY) === '1',
  )
  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0')
  }, [collapsed])

  return (
    <nav
      className={cn(
        // KẺ SỌC DỌC ĐÃ BỎ (repeating-linear-gradient 20px, màu ghi cứng
        // rgba(239,217,210) — một màu kem còn sót từ bảng màu cũ, nên ở bản sáng
        // mới nó chỏi hẳn). Thay bằng kính mờ: sọc là hoa văn nên mắt luôn thấy
        // nó và nó tranh chỗ với nhãn điều hướng; kính mờ không có gì để nhìn.
        'kinh-mo den-noi-phai relative z-20 flex h-full shrink-0 flex-col bg-rail py-5 transition-[width] duration-300 ease-soft',
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
            'flex size-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground active:scale-95',
            !collapsed && 'ml-auto',
          )}
        >
          {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
        </button>
      </div>

      {/* ── BA MỤC CHÍNH — to hơn, luôn thấy ── */}
      <div className="flex shrink-0 flex-col gap-1.5 px-3">
        {CHINH.map((item) => (
          <MucNav
            key={item.id} item={item} collapsed={collapsed} to={true}
            isActive={item.id === 'agent' ? agentActive : activeId === item.id}
            count={badges[item.id]}
            onBam={() => (item.sangTrang ? navigate(item.sangTrang) : onSelect(item.id))}
          />
        ))}
      </div>

      {/* ── NÚT MỞ PHẦN CÒN LẠI ── */}
      <button
        onClick={() => setMoRong((v) => !v)}
        title={moRong ? 'Thu gọn thư mục' : 'Xem thêm thư mục'}
        aria-expanded={moRong}
        className={cn(
          'mx-3 mt-3 flex shrink-0 items-center rounded-xl py-2 text-muted-foreground',
          'transition-colors hover:bg-secondary/40 hover:text-foreground',
          collapsed ? 'justify-center' : 'gap-3 px-3',
        )}
      >
        <MoreHorizontal className={cn('size-5 shrink-0 transition-transform', moRong && 'rotate-90')} />
        {!collapsed && <span className="text-sm font-medium leading-none">Thư mục</span>}
      </button>

      {/* ── PHẦN CÒN LẠI — CUỘN ĐƯỢC.
          `min-h-0` ở đây là BẮT BUỘC: trong một flex-column, phần tử con mặc định
          không co nhỏ hơn nội dung, nên thiếu nó thì vùng này đẩy cụm đáy rơi ra
          ngoài màn hình thay vì tự cuộn. Đó đúng là lỗi đang có — đồng hồ đẩy tụt
          và xén mất icon cá nhân. */}
      {moRong && (
        <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto scrollbar-thin px-3 pt-1">
          {PHU.map((item) => (
            <MucNav
              key={item.id} item={item} collapsed={collapsed} to={false}
              isActive={activeId === item.id}
              count={badges[item.id]}
              onBam={() => onSelect(item.id)}
            />
          ))}
        </div>
      )}

      {/* Đẩy cụm đáy xuống khi phần thư mục đang đóng */}
      {!moRong && <div className="flex-1" />}

      {/* ── ĐÁY CỐ ĐỊNH: đồng hồ + ba nút. `shrink-0` để KHÔNG BAO GIỜ bị xén. ── */}
      <div className="shrink-0 border-t border-border/10 bg-secondary/5 px-3 pb-3 pt-3">
        <SystemStatus collapsed={collapsed} />
        <div className={cn('mt-2 flex gap-1.5', collapsed ? 'flex-col items-center' : 'items-center justify-between')}>
          <NotificationBell />
          <SettingsDialog />
          <AccountMenu />
        </div>
      </div>
    </nav>
  )
}