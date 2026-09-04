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
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { t } from '@/lib/ngon-ngu'
import { LogoMark } from '@/components/logo'
import { AccountMenu } from '@/components/layout/account-menu'
import { SettingsDialog } from '@/components/layout/settings-dialog'
import { NotificationBell } from '@/components/layout/notification-bell'
import { chuyenCanh } from '@/lib/chuyen-canh'

type NavItem = { id: string; label: string; icon: React.ElementType; sangTrang?: string }

/* ══════════════════════════════════════════════════════════════════════════════
   BA MỤC CHÍNH TO, THƯ MỤC THÀNH LƯỚI Ô VUÔNG

   Bản đầu: tám mục ngang hàng nhau (Hộp thư, Trợ lý, Lịch trình, Gắn sao, Đã gửi,
   Nháp, Lưu trữ, Thùng rác). Xếp ngang hàng nghĩa là nói với người dùng rằng
   "Thùng rác" quan trọng bằng "Trợ lý" — điều đó sai.

   Bản hai: ba mục chính to, sáu thư mục giấu sau nút "Thư mục". Sửa được thứ bậc
   nhưng đẻ ra hai vấn đề mới — một khoảng trống cao gần 350px ở giữa thanh (đo
   thật trên khung 1440×900), và thêm một cú bấm mới tới được Thư rác.

   Bản này: ba mục chính giữ nguyên, sáu thư mục thành LƯỚI Ô VUÔNG luôn hiện.
   Ô nhỏ, nhãn cực nhỏ nên chúng không tranh sức nặng với ba mục trên; mà vì luôn
   hiện nên không còn cú bấm ở giữa, và đúng phần trống kia được lấp.

   Phần trống còn lại lấp bằng DẢI ÁP LỰC 7 NGÀY — thông tin thật, không phải hoạ
   tiết. Không có dữ liệu thì không vẽ: thà trống còn hơn một cái khung rỗng.
   ══════════════════════════════════════════════════════════════════════════════ */
const CHINH: NavItem[] = [
  // `label` gio la KHOA DICH, khong phai chu hien ra. Doi thang chuoi o day thi
  // nut do khong bao gio dich duoc — xem src/lib/ngon-ngu.tsx.
  { id: 'inbox', label: 'nav.inbox', icon: Inbox },
  { id: 'agent', label: 'nav.assistant', icon: Sparkles },
  { id: 'lich', label: 'nav.schedule', icon: CalendarDays, sangTrang: '/lich' },
]

/** Thư mục — chỗ TÌM LẠI thư, không phải chỗ làm việc hằng ngày. */
const PHU: NavItem[] = [
  { id: 'starred', label: 'nav.starred', icon: Star },
  { id: 'sent', label: 'nav.sent', icon: Send },
  { id: 'drafts', label: 'nav.drafts', icon: FileEdit },
  { id: 'archive', label: 'nav.archive', icon: Archive },
  // Spam TỪNG THIẾU hẳn, dù nó là thư mục người ta cần nhất khi một lá thư quan
  // trọng "biến mất" — và đó là lúc người dùng hoảng nhất.
  { id: 'spam', label: 'nav.spam', icon: ShieldAlert },
  { id: 'trash', label: 'nav.trash', icon: Trash2 },
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
      title={collapsed ? t(item.label) : undefined}
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
          {t(item.label)}
        </span>
      )}
    </button>
  )
}

/** Một thư mục dưới dạng ô VUÔNG có góc cắt.
 *
 *  Vuông chứ không tròn: góc cắt chéo là ngôn ngữ hình đã dùng xuyên suốt app
 *  (ô ngày trong lịch, thẻ cam kết, nút hành động). Thêm một hình tròn vào đây là
 *  thêm một thứ tiếng thứ hai cho cùng một câu. */
function OThuMuc({
  item, collapsed, isActive, count, onBam,
}: {
  item: NavItem
  collapsed: boolean
  isActive: boolean
  count?: number
  onBam: () => void
}) {
  const Icon = item.icon
  return (
    <button
      onClick={onBam}
      title={t(item.label)}
      aria-label={t(item.label)}
      aria-current={isActive ? 'page' : undefined}
      className={cn(
        'goc-cat-nho goc-cat nhay-bat group relative flex flex-col items-center justify-center gap-1',
        'transition-[box-shadow,background,color] duration-200 ease-spring',
        collapsed ? 'h-9' : 'h-[52px]',
        isActive
          ? 'den-vien-chon bg-secondary text-active'
          : 'den-vien text-muted-foreground hover:bg-secondary/40 hover:text-foreground',
      )}
    >
      <span className="relative">
        <Icon className={cn(collapsed ? 'size-[17px]' : 'size-[18px]', isActive && 'stroke-[2.2px]')} />
        {count ? (
          <span className="cherry-dot absolute -right-1.5 -top-1.5 flex size-3.5 items-center justify-center rounded-full bg-spark text-[9px] font-semibold text-background">
            {count}
          </span>
        ) : null}
      </span>
      {!collapsed && (
        // Nhãn cực nhỏ, chữ hoa giãn — đủ để đọc mà không tranh sức nặng với ba
        // mục chính ở trên. Bỏ hẳn nhãn thì thành một hàng icon đố chữ.
        <span className="max-w-full truncate px-0.5 font-mono text-[7.5px] uppercase leading-none tracking-[0.08em]">
          {t(item.label)}
        </span>
      )}
    </button>
  )
}

/** Áp lực 7 ngày tới — bảy cột, cao theo số phút việc dồn vào ngày đó.
 *
 *  Đây là thông tin, không phải hoạ tiết lấp chỗ. Nó trả lời đúng câu người ta hỏi
 *  khi liếc sang thanh bên — "tuần này có nặng không" — mà không phải mở trang
 *  lịch. Cột vượt trần đổi màu, vì đó là thứ duy nhất đáng phải hành động. */
function DaiApLuc({
  apLuc, collapsed,
}: {
  apLuc: { ngay: Date; phut: number; soViec: number }[]
  collapsed: boolean
}) {
  const CHU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  const tran = 360 // TRAN_MOI_NGAY — giữ số ở đây để nav không phải phụ thuộc cam-ket
  // THANG TUYỆT ĐỐI, cố ý. Co thang theo tuần thì một tuần nhẹ trông y hệt một
  // tuần nặng, và cái duy nhất người ta cần biết — "tuần này có gánh nổi không" —
  // biến mất. Giá phải trả là tuần nhẹ cho cột thấp; bù lại bằng dòng SỐ bên dưới,
  // vốn đọc chính xác hơn mọi cột.
  const dinh = Math.max(tran, ...apLuc.map((x) => x.phut))
  const bay = apLuc.slice(0, 7)
  const tongPhut = bay.reduce((s, x) => s + x.phut, 0)
  const tongViec = new Set(bay.flatMap((x) => (x.soViec > 0 ? [x.ngay.toDateString()] : []))).size
  const soGio = Math.round(tongPhut / 6) / 10
  const ngayQuaTai = bay.filter((x) => x.phut > tran).length

  return (
    <div className={cn('mt-4 shrink-0', collapsed ? 'px-2' : 'px-3')}>
      {!collapsed && (
        <p className="mb-1.5 px-1 font-mono text-[8.5px] uppercase tracking-[0.22em] text-muted-foreground/40">
          Áp lực 7 ngày
        </p>
      )}
      <div className={cn('den-vien goc-cat-nho goc-cat relative px-2 pb-1.5 pt-2')}>
        <div className="flex items-end justify-between gap-[3px]">
          {bay.map((x) => {
            const ty = dinh > 0 ? x.phut / dinh : 0
            const qua = x.phut > tran
            return (
              <span
                key={x.ngay.toISOString()}
                className="relative flex min-w-0 flex-1 flex-col items-center gap-1"
                title={t('nav.dayLoad', { thu: CHU[x.ngay.getDay()], n: x.soViec, gio: Math.round(x.phut / 6) / 10 })}
              >
                <span className="flex h-6 w-full items-end">
                  <span
                    className={cn(
                      'w-full rounded-[1px] transition-[height] duration-500 ease-soft',
                      x.phut === 0
                        // Ngày rảnh vẫn phải có một vạch mảnh: mất hẳn thì mắt đếm
                        // nhầm cột và đọc lệch cả tuần.
                        ? 'bg-foreground/10'
                        : qua ? 'bg-[var(--ut-gap)]' : 'bg-[var(--ut-quan)]',
                    )}
                    style={{ height: x.phut === 0 ? 2 : `${Math.max(14, ty * 100)}%` }}
                  />
                </span>
                {!collapsed && (
                  <span className="font-mono text-[7px] uppercase leading-none text-muted-foreground/45">
                    {CHU[x.ngay.getDay()]}
                  </span>
                )}
              </span>
            )
          })}
        </div>

        {/* Dòng số — thứ đọc được kể cả khi cột quá thấp để so bằng mắt. */}
        {!collapsed && (
          <p className="mt-1.5 border-t border-border/15 pt-1 text-center font-mono text-[8px] uppercase tracking-[0.1em] text-muted-foreground/55">
            {tongViec === 0 ? (
              t('nav.weekEmpty')
            ) : ngayQuaTai > 0 ? (
              <span className="text-[var(--ut-gap)]">{ngayQuaTai} ngày quá tải · {soGio} giờ</span>
            ) : (
              <>{tongViec} ngày có việc · {soGio} giờ</>
            )}
          </p>
        )}
      </div>
    </div>
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
      <div className="flex flex-col items-center gap-1.5 py-2" title={t('nav.ready', { gio: hhmm })}>
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
  apLuc,
}: {
  activeId: string
  onSelect: (id: string) => void
  badges?: Record<string, number>
  /** Nút "AI Agent" là công tắc → sáng theo trạng thái panel chat, không theo thư mục. */
  agentActive?: boolean
  /** Áp lực 7 ngày tới, do nơi gọi tính sẵn. Không truyền thì dải này không vẽ —
   *  giữ nav rail KHÔNG phụ thuộc vào tầng dữ liệu lịch trình, để nó còn dùng
   *  lại được ở màn khác. */
  apLuc?: { ngay: Date; phut: number; soViec: number }[]
}) {
  const navigate = useNavigate()
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
          title={collapsed ? 'nav.expand' : 'nav.collapse'}
          aria-label={collapsed ? 'nav.expand' : 'nav.collapse'}
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
            onBam={() => (item.sangTrang
              // Đổi TRANG là cú nhảy lớn nhất trong app — không bọc chuyển cảnh thì
              // cả màn hình thay trong đúng một khung hình và mắt mất chỗ bám.
              ? chuyenCanh(() => navigate(item.sangTrang as string))
              : onSelect(item.id))}
          />
        ))}
      </div>

      {/* ── THƯ MỤC — LƯỚI NÚT VUÔNG, LUÔN HIỆN ──
          Trước đây sáu thư mục nằm sau một nút "Thư mục" phải bấm mới mở. Kết quả
          là thanh này có một khoảng trống cao gần 350px ở giữa — đo thật trên khung
          1440×900 — và người dùng vẫn phải bấm thêm một lần mới tới được Thư rác.
          Vừa phí chỗ vừa tốn thao tác, tức là chẳng được gì cả.

          Lưới vuông giải quyết cả hai: sáu ô icon chiếm đúng phần trống đó, và
          không còn cú bấm nào ở giữa. Vẫn giữ nguyên thứ bậc — ô vuông nhỏ, không
          nhãn to, nên chúng không tranh chỗ với ba mục chính ở trên. */}
      {/* PHẦN GIỮA PHẢI CUỘN ĐƯỢC.
          `min-h-0` là bắt buộc: trong flex-column, con mặc định KHÔNG co nhỏ hơn
          nội dung của nó, nên thiếu nó thì phần này đẩy cụm đáy rơi khỏi màn hình
          thay vì tự cuộn. Đó đúng là lỗi vừa đo được ở chế độ thu gọn — nội dung
          cao 820px trong khung 804px, và nút hồ sơ cá nhân có đáy ở 808px, tức
          nằm ngoài màn hình. Cụm đáy chứa hồ sơ, cài đặt, thông báo: ba thứ KHÔNG
          bao giờ được phép biến mất. */}
      <div className={cn(
        'flex min-h-0 flex-1 flex-col overflow-y-auto scrollbar-thin',
        collapsed ? 'px-2' : 'px-3',
      )}>
        <div className="mt-4 shrink-0">
          {!collapsed && (
            <p className="mb-1.5 px-1 font-mono text-[8.5px] uppercase tracking-[0.22em] text-muted-foreground/40">
              Thư mục
            </p>
          )}
          <div className={cn('grid gap-1.5', collapsed ? 'grid-cols-1' : 'grid-cols-3')}>
            {PHU.map((item) => (
              <OThuMuc
                key={item.id}
                item={item}
                collapsed={collapsed}
                isActive={activeId === item.id}
                count={badges[item.id]}
                onBam={() => onSelect(item.id)}
              />
            ))}
          </div>
        </div>

        {/* ── ÁP LỰC 7 NGÀY TỚI ──
            Phần trống được lấp bằng THÔNG TIN, không phải hoạ tiết. Dải này trả
            lời câu người dùng thật sự hỏi khi liếc sang thanh bên: "tuần này có
            nặng không".

            CHỈ VẼ KHI ĐANG MỞ. Thu gọn còn 76px thì bảy cột chỉ còn ~7px mỗi cột,
            không nhãn, không số — không đọc được gì mà vẫn ăn 64px chiều cao,
            đúng phần đã đẩy nút hồ sơ ra khỏi màn hình. Thu gọn nghĩa là người
            dùng đang muốn dồn chỗ cho nội dung; nhồi thêm biểu đồ vào đó là đi
            ngược lại điều họ vừa yêu cầu. */}
        {!collapsed && apLuc && apLuc.length > 0 && (
          <DaiApLuc apLuc={apLuc} collapsed={false} />
        )}

        <div className="min-h-2 flex-1" />
      </div>

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