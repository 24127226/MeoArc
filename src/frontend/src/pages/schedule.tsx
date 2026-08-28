import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft, ChevronLeft, ChevronRight, Clock, Mail,
  MessageSquare, Sparkles, X,
} from 'lucide-react'
import { emails as seedEmails, type Email } from '@/data/emails'
import { api, apiBaseUrlDaCauHinh } from '@/lib/api'
import {
  trichCamKet, gomTheoNgay, luoiThang, khoaNgay, viTriTrongDot, TRAN_MOI_NGAY, type CamKet,
} from '@/lib/cam-ket'
import { ChatPanel } from '@/components/layout/chat-panel'
import { EmailDetail } from '@/components/layout/email-detail'
import type { EmailActions } from '@/lib/email-actions'
import { AlertOverlay } from '@/components/layout/alert-overlay'
import { LogoMark } from '@/components/logo'
import { cn } from '@/lib/utils'

/**
 * SchedulePage — trang lịch trình.
 *
 * ── BỐ CỤC: HAI KHUNG, KHÔNG PHẢI MỘT KHUNG RỒI CUỘN ──
 * Bản trước là một cuốn lịch to rồi bên dưới là phần tóm tắt — nghĩa là muốn xem
 * đủ thì phải cuộn, mà cuộn trong một trang lịch là hỏng: người ta mở lịch để
 * NHÌN THẤY CẢ BỨC TRANH, không phải để đọc lần lượt.
 *
 * Nay chia đôi theo chiều ngang: cột trái là lịch nhỏ + danh sách sắp tới (phần
 * tóm tắt), cột phải là khung lớn chứa các thẻ lịch trình. Hai thứ nằm cạnh nhau
 * nên thấy cùng lúc, không phải cuộn.
 *
 * ── VÌ SAO THẺ, KHÔNG PHẢI CHẤM ──
 * Một hạn nộp thứ Sáu KHÔNG phải một việc của thứ Sáu: nếu nó cần sáu tiếng thì
 * nó là việc của cả thứ Tư và thứ Năm. Cuốn lịch thường vẽ nó thành một chấm ở
 * thứ Sáu, và đó chính là lý do người ta hay vỡ kế hoạch — họ nhìn thấy một chấm,
 * không nhìn thấy khối lượng. Thẻ TRẢI DÀI qua đúng số ngày cần làm.
 *
 * ── XẾP LỚP KHI NHIỀU ──
 * Một ngày có bốn việc mà vẽ bốn thẻ đầy đủ thì ô đó cao gấp bốn ô khác và cả
 * lưới méo. Xếp chồng lệch vài pixel thì vẫn thấy "ở đây có nhiều việc", vẫn giữ
 * lưới đều, và thẻ ƯU TIÊN CAO NHẤT nằm trên cùng — thứ người ta cần thấy trước.
 * Rê chuột thì cả chồng xoè ra.
 */
export function SchedulePage() {
  const [emails, setEmails] = useState<Email[]>(apiBaseUrlDaCauHinh ? [] : seedEmails)
  const homNay = useMemo(() => new Date(), [])
  const [thang, setThang] = useState(() => new Date(homNay.getFullYear(), homNay.getMonth(), 1))
  const [lenh, setLenh] = useState<string | null>(null)
  const [chatMo, setChatMo] = useState(false)
  /** Thẻ vừa bấm → hiện khung hỏi "xem thư hay hỏi AI". */
  const [dangHoi, setDangHoi] = useState<{ ck: CamKet; x: number; y: number } | null>(null)
  /** Thư đang mở toàn màn — bấm quay lại là về đúng lịch, không mất chỗ. */
  const [thuMo, setThuMo] = useState<string | null>(null)

  useEffect(() => {
    if (!apiBaseUrlDaCauHinh) return
    api.listEmails({ folder: 'inbox' }).then((r) => setEmails(r.items)).catch(() => {})
  }, [])

  const camKet = useMemo(() => trichCamKet(emails), [emails])
  const theoNgay = useMemo(() => gomTheoNgay(camKet), [camKet])
  const o = useMemo(() => luoiThang(thang.getFullYear(), thang.getMonth()), [thang])
  const sapToi = useMemo(
    () => camKet.filter((c) => c.trangThai !== 'xong').slice(0, 6),
    [camKet],
  )
  const emailDangMo = thuMo ? emails.find((e) => e.id === thuMo) : null

  const hoiAI = (ck: CamKet) => {
    setDangHoi(null)
    setChatMo(true)
    setLenh(`Về việc "${ck.noiDung}" (${ck.nguoiCho} đang chờ) — giúp mình sắp xếp thời gian làm.`)
  }

  // Thư mở toàn màn: che hẳn lịch. Quay lại là về đúng chỗ cũ vì lịch không
  // bị unmount — state tháng, thẻ, chat đều còn nguyên.
  if (emailDangMo) {
    return (
      <div className="giao-dien-app flex h-screen w-full overflow-hidden bg-background text-foreground">
        <EmailDetail
          email={emailDangMo}
          onClose={() => setThuMo(null)}
          actions={KHONG_LAM_GI}
          onAgentAction={(c) => { setThuMo(null); setChatMo(true); setLenh(c) }}
        />
      </div>
    )
  }

  return (
    <div className="giao-dien-app relative flex h-screen w-full overflow-hidden bg-background text-foreground">
      <AlertOverlay emails={emails} />

      {/* ══ CỘT TRÁI — lịch nhỏ + sắp tới. Đây là phần "tóm tắt" ══ */}
      <aside className="den-noi-phai flex w-[268px] shrink-0 flex-col overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-4">
          <Link to="/app" className="o-icon size-8 shrink-0" aria-label="Về hộp thư">
            <ArrowLeft className="size-4" />
          </Link>
          <span className="text-[15px] font-semibold tracking-tight">Lịch trình</span>
          <LogoMark className="ml-auto size-5 text-foreground/35" />
        </div>

        <LichNho thang={thang} homNay={homNay} theoNgay={theoNgay} onDoiThang={setThang} />

        <div className="mt-1 flex min-h-0 flex-1 flex-col overflow-y-auto scrollbar-thin px-3 pb-3">
          <p className="px-1 py-2 font-mono text-[9.5px] uppercase tracking-[0.2em] text-muted-foreground/60">
            Sắp tới
          </p>
          {sapToi.length === 0 ? (
            <p className="px-1 text-[12.5px] text-muted-foreground">Chưa có việc nào.</p>
          ) : (
            sapToi.map((c) => (
              <button
                key={c.id}
                onClick={(e) => setDangHoi({ ck: c, x: e.clientX, y: e.clientY })}
                className="group flex items-start gap-2.5 rounded-lg px-1 py-2 text-left transition-colors hover:bg-foreground/[0.04]"
              >
                <span className={cn('cham-rr mt-1.5', `c${c.mucRuiRo}`)} aria-hidden />
                <span className="flex min-w-0 flex-col">
                  <span className="truncate text-[12.5px] font-medium">{c.noiDung}</span>
                  <span className="truncate text-[11px] text-muted-foreground">
                    {c.han ? nhanNgay(c.han, homNay) : 'Không có hạn'} · {c.nguoiCho}
                  </span>
                </span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* ══ KHUNG LỚN — lịch thẻ ══ */}
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="den-noi-duoi flex shrink-0 items-center gap-3 px-5 py-3.5">
          <h2 className="text-[17px] font-semibold tracking-tight">
            Tháng {thang.getMonth() + 1}/{thang.getFullYear()}
          </h2>
          <span className="font-mono text-[11px] tabular-nums text-[var(--spark)]">
            {String(camKet.filter((c) => c.trangThai !== 'xong').length).padStart(2, '0')} việc
          </span>
          <div className="ml-auto flex items-center gap-1.5">
            <button onClick={() => setThang((t) => new Date(t.getFullYear(), t.getMonth() - 1, 1))}
              className="o-icon size-8" aria-label="Tháng trước"><ChevronLeft className="size-4" /></button>
            <button onClick={() => setThang(new Date(homNay.getFullYear(), homNay.getMonth(), 1))}
              className="nut-ky-thuat px-3 py-1.5 text-[11.5px] font-medium">Hôm nay</button>
            <button onClick={() => setThang((t) => new Date(t.getFullYear(), t.getMonth() + 1, 1))}
              className="o-icon size-8" aria-label="Tháng sau"><ChevronRight className="size-4" /></button>
          </div>
        </header>

        {/* Chat mở → lịch NHỎ LẠI và ưu tiên danh sách. Người dùng vừa mở chat là
            họ đang muốn BÀN về lịch, không phải ngắm lưới tháng. */}
        {chatMo ? (
          <DanhSachViec camKet={camKet} homNay={homNay} onBamThe={setDangHoi} />
        ) : (
          <LuoiThe o={o} thang={thang} homNay={homNay} theoNgay={theoNgay} onBamThe={setDangHoi} />
        )}
      </main>

      {/* ══ CHAT — nút tượng trưng góc dưới phải, bấm mới hiện ══ */}
      {chatMo ? (
        <div className="den-noi-trai flex w-[400px] shrink-0 flex-col">
          <ChatPanel
            emails={emails}
            actions={KHONG_LAM_GI}
            injectedCommand={lenh}
            onInjectConsumed={() => setLenh(null)}
            onClose={() => setChatMo(false)}
          />
        </div>
      ) : (
        <button
          onClick={() => setChatMo(true)}
          aria-label="Mở trợ lý MeoArc"
          // `position` ghi NỘI TUYẾN: `.goc-cat` đặt position:relative và nó thắng
          // tiện ích `fixed` của Tailwind (CSS tự viết nằm ngoài @layer). Dùng class
          // thì nút rơi lên góc trên phải — đã dính đúng vậy.
          style={{ position: 'fixed', bottom: 24, right: 24 }}
          className="den-vien-chon goc-cat z-40 flex size-14 items-center justify-center
                     bg-[var(--elevated)]/92 backdrop-blur-md transition-transform
                     hover:scale-105 active:scale-95"
        >
          <Sparkles className="size-6 text-[var(--spark)]" />
        </button>
      )}

      {/* ══ KHUNG HỎI khi bấm một thẻ ══ */}
      {dangHoi && (
        <KhungHoi
          ck={dangHoi.ck} x={dangHoi.x} y={dangHoi.y}
          onDong={() => setDangHoi(null)}
          onXemThu={() => { setThuMo(dangHoi.ck.emailId); setDangHoi(null) }}
          onHoiAI={() => hoiAI(dangHoi.ck)}
        />
      )}
    </div>
  )
}

/** Trang lịch KHÔNG thao tác trên thư — người dùng ở đây đang nghĩ về thời gian. */
const KHONG_LAM_GI: EmailActions = {
  markRead: () => {},
  setImportant: () => {},
  applyLabel: () => {},
  removeEmails: () => {},
}

/* ── Lịch nhỏ ở cột trái ─────────────────────────────────────────────────── */
function LichNho({
  thang, homNay, theoNgay, onDoiThang,
}: {
  thang: Date
  homNay: Date
  theoNgay: Map<string, CamKet[]>
  onDoiThang: (d: Date) => void
}) {
  const o = useMemo(() => luoiThang(thang.getFullYear(), thang.getMonth()), [thang])
  return (
    <div className="shrink-0 px-3">
      <div className="mb-1.5 flex items-center justify-between px-1">
        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
          Th {thang.getMonth() + 1}/{thang.getFullYear()}
        </span>
        <span className="flex gap-0.5">
          <button onClick={() => onDoiThang(new Date(thang.getFullYear(), thang.getMonth() - 1, 1))}
            className="o-icon size-6" aria-label="Tháng trước"><ChevronLeft className="size-3" /></button>
          <button onClick={() => onDoiThang(new Date(thang.getFullYear(), thang.getMonth() + 1, 1))}
            className="o-icon size-6" aria-label="Tháng sau"><ChevronRight className="size-3" /></button>
        </span>
      </div>
      <div className="grid grid-cols-7 gap-px">
        {['2', '3', '4', '5', '6', '7', 'C'].map((t) => (
          <span key={t} className="pb-1 text-center font-mono text-[9px] text-muted-foreground/50">{t}</span>
        ))}
        {o.map((d) => {
          const co = (theoNgay.get(khoaNgay(d)) ?? []).length
          return (
            <span key={d.toISOString()}
              className={cn(
                'relative flex h-7 items-center justify-center font-mono text-[10.5px] tabular-nums',
                d.getMonth() === thang.getMonth() ? 'text-foreground/75' : 'text-foreground/20',
                khoaNgay(d) === khoaNgay(homNay) && 'font-bold text-[var(--spark)]',
              )}
            >
              {d.getDate()}
              {co > 0 && (
                <i className="absolute bottom-0.5 size-1 rounded-full bg-[var(--rr-hoan)]" />
              )}
            </span>
          )
        })}
      </div>
    </div>
  )
}

/* ── Lưới tháng với THẺ ──────────────────────────────────────────────────── */
function LuoiThe({
  o, thang, homNay, theoNgay, onBamThe,
}: {
  o: Date[]
  thang: Date
  homNay: Date
  theoNgay: Map<string, CamKet[]>
  onBamThe: (v: { ck: CamKet; x: number; y: number }) => void
}) {
  return (
    <div className="grid min-h-0 flex-1 grid-cols-7 grid-rows-[auto_repeat(6,1fr)] gap-1 p-3">
      {['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((t) => (
        <div key={t} className="pb-0.5 text-center font-mono text-[9.5px] uppercase tracking-[0.16em] text-muted-foreground/55">
          {t}
        </div>
      ))}
      {o.map((d) => {
        const viec = theoNgay.get(khoaNgay(d)) ?? []
        const trongThang = d.getMonth() === thang.getMonth()
        return (
          <ONgay
            key={d.toISOString()}
            ngay={d}
            trongThang={trongThang}
            laHomNay={khoaNgay(d) === khoaNgay(homNay)}
            viec={viec}
            onBamThe={onBamThe}
          />
        )
      })}
    </div>
  )
}

function ONgay({
  ngay, trongThang, laHomNay, viec, onBamThe,
}: {
  ngay: Date
  trongThang: boolean
  laHomNay: boolean
  viec: CamKet[]
  onBamThe: (v: { ck: CamKet; x: number; y: number }) => void
}) {
  const [xoe, setXoe] = useState(false)
  // Ưu tiên cao nhất lên TRÊN CÙNG của chồng — thứ người ta cần thấy trước.
  const xep = useMemo(
    () => [...viec].sort((a, b) => b.mucRuiRo - a.mucRuiRo || b.uocLuongPhut - a.uocLuongPhut),
    [viec],
  )
  const phut = viec.reduce((s, c) => s + c.uocLuongPhut, 0)
  const quaTai = phut > TRAN_MOI_NGAY

  return (
    <div
      onMouseEnter={() => setXoe(true)}
      onMouseLeave={() => setXoe(false)}
      className={cn(
        'goc-cat-nho goc-cat relative flex min-h-0 flex-col p-1.5',
        laHomNay ? 'den-vien-chon' : 'den-vien',
        !trongThang && 'opacity-30',
        // Chồng thẻ xoè ra thì cần thoát khỏi ô — nâng z-index để nó không bị ô
        // bên cạnh cắt mất.
        xoe && viec.length > 1 && 'z-20',
      )}
    >
      <span className="flex shrink-0 items-center justify-between">
        <span className={cn(
          'font-mono text-[11px] tabular-nums',
          laHomNay ? 'font-bold text-[var(--spark)]' : 'text-foreground/70',
        )}>
          {ngay.getDate()}
        </span>
        {quaTai && (
          <span className="font-mono text-[8.5px] font-bold uppercase tracking-wider text-[var(--rr-khong)]">
            quá tải
          </span>
        )}
      </span>

      {/* CHỒNG THẺ. Xếp chồng lệch vài pixel chứ không liệt kê đầy đủ: một ngày
          bốn việc mà vẽ bốn thẻ thì ô đó cao gấp bốn ô khác và cả lưới méo. */}
      <div className="relative mt-1 min-h-0 flex-1">
        {xep.slice(0, 4).map((c, i) => (
          <TheViec
              ngay={ngay}
            key={c.id}
            ck={c}
            viTri={i}
            xoe={xoe}
            onBam={(e) => onBamThe({ ck: c, x: e.clientX, y: e.clientY })}
          />
        ))}
        {xep.length > 4 && !xoe && (
          <span className="absolute bottom-0 right-0.5 font-mono text-[9px] text-muted-foreground">
            +{xep.length - 4}
          </span>
        )}
      </div>
    </div>
  )
}

function TheViec({
  ck, viTri, xoe, onBam, ngay,
}: {
  ck: CamKet
  viTri: number
  xoe: boolean
  onBam: (e: React.MouseEvent) => void
  /** Ngày của ô đang vẽ — quyết định thẻ này là đầu đợt hay chỉ là đoạn nối. */
  ngay: Date
}) {
  const doan = viTriTrongDot(ck, ngay)
  // Nghỉ: chồng lệch 3px mỗi thẻ. Xoè: xếp thành hàng thật.
  const y = xoe ? viTri * 26 : viTri * 3
  return (
    <button
      onClick={onBam}
      style={{ transform: `translateY(${y}px)`, zIndex: 10 - viTri }}
      className={cn(
        'absolute inset-x-0 top-0 flex flex-col gap-0.5 px-1.5 py-1 text-left',
        'transition-[transform,box-shadow] duration-200 ease-soft',
        ck.mucRuiRo === 3 ? 'rui-ro-3' : ck.mucRuiRo === 2 ? 'rui-ro-2' : 'rui-ro-1',
        'bg-[var(--elevated)]/90 backdrop-blur-sm hover:z-30 hover:-translate-y-px hover:scale-[1.02]',
        // GÓC CẮT CHỈ Ở HAI ĐẦU ĐỢT. Ngày giữa để vuông cả hai phía, nên khi các ô
        // nằm cạnh nhau thì các đoạn nối liền thành MỘT thanh dài thay vì ba viên
        // rời rạc — đó mới đọc ra là "một việc kéo dài ba ngày".
        doan === 'don' && 'goc-cat-nho goc-cat',
        doan === 'dau' && 'goc-cat-nho [clip-path:polygon(8px_0,100%_0,100%_100%,0_100%,0_8px)]',
        doan === 'cuoi' && '[clip-path:polygon(0_0,100%_0,100%_calc(100%-8px),calc(100%-8px)_100%,0_100%)]',
      )}
    >
      {/* Chỉ NGÀY ĐẦU mang chữ. Ngày giữa/cuối chỉ là thanh nối — lặp lại tiêu đề
          ở mọi ngày thì mắt đọc ra ba việc, không phải một việc kéo dài. */}
      {doan === 'don' || doan === 'dau' ? (
        <>
          <span className="truncate text-[10.5px] font-medium leading-tight text-foreground">
            {ck.noiDung}
          </span>
          {/* Người gửi luôn hiện: không có nguồn thì người dùng không kiểm được,
              và không kiểm được thì không tin. */}
          <span className="truncate text-[9px] leading-tight text-muted-foreground">
            {ck.nguoiCho}
          </span>
        </>
      ) : (
        <span className="h-[18px]" aria-hidden />
      )}
    </button>
  )
}

/* ── Danh sách việc (khi chat mở, lịch nhường chỗ) ───────────────────────── */
function DanhSachViec({
  camKet, homNay, onBamThe,
}: {
  camKet: CamKet[]
  homNay: Date
  onBamThe: (v: { ck: CamKet; x: number; y: number }) => void
}) {
  const con = camKet.filter((c) => c.trangThai !== 'xong')
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto scrollbar-thin p-3">
      {con.map((c) => (
        <button
          key={c.id}
          onClick={(e) => onBamThe({ ck: c, x: e.clientX, y: e.clientY })}
          className={cn(
            'goc-cat flex items-start gap-3 p-3 text-left transition-transform hover:-translate-y-px',
            c.mucRuiRo === 3 ? 'rui-ro-3' : c.mucRuiRo === 2 ? 'rui-ro-2' : 'rui-ro-1',
          )}
        >
          <span className={cn('cham-rr mt-1.5', `c${c.mucRuiRo}`)} aria-hidden />
          <span className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className="truncate text-[13.5px] font-medium">{c.noiDung}</span>
            <span className="flex flex-wrap items-center gap-x-2 text-[11.5px] text-muted-foreground">
              <span className="inline-flex items-center gap-1"><Mail className="size-3" />{c.nguoiCho}</span>
              {c.uocLuongPhut > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Clock className="size-3" />
                  {c.uocLuongPhut >= 60 ? `${c.uocLuongPhut / 60} giờ` : `${c.uocLuongPhut} phút`}
                </span>
              )}
            </span>
          </span>
          <span className="shrink-0 font-mono text-[10.5px] tabular-nums text-muted-foreground">
            {c.han ? nhanNgay(c.han, homNay) : '—'}
          </span>
        </button>
      ))}
    </div>
  )
}

/* ── Khung hỏi: xem thư hay hỏi AI ───────────────────────────────────────── */
function KhungHoi({
  ck, x, y, onDong, onXemThu, onHoiAI,
}: {
  ck: CamKet
  x: number
  y: number
  onDong: () => void
  onXemThu: () => void
  onHoiAI: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onDong()
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onDong()
    }
    window.addEventListener('keydown', onKey)
    // `setTimeout` 0: nếu gắn ngay thì chính cú bấm mở khung này lại đóng nó.
    const t = setTimeout(() => window.addEventListener('mousedown', onClick), 0)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('mousedown', onClick)
      clearTimeout(t)
    }
  }, [onDong])

  // Kẹp vào trong màn hình: bấm một thẻ sát mép phải/đáy thì khung không được
  // tràn ra ngoài rồi mất một nửa.
  const W = 246
  const left = Math.min(Math.max(8, x - W / 2), window.innerWidth - W - 8)
  const top = Math.min(y + 12, window.innerHeight - 168)

  return (
    <div
      ref={ref}
      role="dialog"
      aria-label="Chọn hành động"
      style={{ left, top, width: W }}
      className="nhay-bat den-vien-chon goc-cat fixed z-50 flex flex-col gap-2 bg-[var(--elevated)]/95 p-3 backdrop-blur-md"
    >
      <div className="flex items-start gap-2">
        <span className="min-w-0 flex-1 text-[12px] font-medium leading-snug text-foreground">
          {ck.noiDung}
        </span>
        <button onClick={onDong} className="o-icon size-6 shrink-0" aria-label="Đóng">
          <X className="size-3" />
        </button>
      </div>

      <button onClick={onXemThu} className="nut-ky-thuat flex items-center gap-2 px-3 py-2 text-[12.5px] font-medium text-foreground">
        <Mail className="size-3.5" />
        Xem thư gốc
      </button>
      <button onClick={onHoiAI} className="nut-ky-thuat flex items-center gap-2 px-3 py-2 text-[12.5px] font-medium text-foreground"
        style={{ ['--tint' as string]: 'var(--spark)' }}>
        <MessageSquare className="size-3.5" />
        Hỏi trợ lý về việc này
      </button>
    </div>
  )
}

const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
function nhanNgay(d: Date, homNay: Date): string {
  const a = new Date(homNay); a.setHours(0, 0, 0, 0)
  const b = new Date(d); b.setHours(0, 0, 0, 0)
  const cach = Math.round((b.getTime() - a.getTime()) / 86400000)
  if (cach === 0) return `Nay ${gioPhut(d)}`
  if (cach === 1) return `Mai ${gioPhut(d)}`
  if (cach < 0) return `Trễ ${-cach} ngày`
  if (cach < 7) return `${THU[d.getDay()]} ${gioPhut(d)}`
  return `${d.getDate()}/${d.getMonth() + 1}`
}
function gioPhut(d: Date): string {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
