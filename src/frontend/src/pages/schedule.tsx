import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ChevronLeft, ChevronRight, Clock, Mail } from 'lucide-react'
import { emails as seedEmails, type Email } from '@/data/emails'
import { api, apiBaseUrlDaCauHinh } from '@/lib/api'
import {
  trichCamKet, gomTheoNgay, luoiThang, khoaNgay, TRAN_MOI_NGAY, type CamKet,
} from '@/lib/cam-ket'
import { ChatPanel } from '@/components/layout/chat-panel'
import type { EmailActions } from '@/lib/email-actions'
import { LogoMark } from '@/components/logo'
import { cn } from '@/lib/utils'
import { AlertOverlay } from '@/components/layout/alert-overlay'
import { useEffect } from 'react'

/**
 * SchedulePage — TRANG RIÊNG cho lịch trình, không phải một tab trong hộp thư.
 *
 * ── VÌ SAO TÁCH HẲN RA MỘT TRANG ──
 * Hộp thư trong MeoArc cố ý chiếm một cột hẹp, và đó là một quyết định sản phẩm
 * chứ không phải hạn chế bố cục: người ta không vào MeoArc để đọc thư và thao tác
 * từng lá như Gmail — nếu chỉ cần thế thì họ đã ở lại Gmail rồi.
 *
 * Lịch trình thì ngược lại. Đó chính là thứ MeoArc làm mà Gmail không làm: đọc
 * thư ra nghĩa vụ, rồi giữ lịch hộ. Nhét nó vào một cột giữa ba cột là tự hạ nó
 * xuống ngang hàng với "Thùng rác".
 *
 * Nên nó có trang riêng, và trên trang đó KHÔNG có danh sách thư nào cả. Người
 * dùng ở đây đang nghĩ về thời gian của họ, không nghĩ về từng lá thư. Muốn xem
 * thư nào sinh ra một việc thì bấm vào việc đó — thư là NGUỒN, không phải giao diện.
 */
export function SchedulePage() {
  const [emails, setEmails] = useState<Email[]>(apiBaseUrlDaCauHinh ? [] : seedEmails)
  const homNay = useMemo(() => new Date(), [])
  const [thang, setThang] = useState(() => new Date(homNay.getFullYear(), homNay.getMonth(), 1))
  const [ngayChon, setNgayChon] = useState<string>(khoaNgay(homNay))
  const [lenh, setLenh] = useState<string | null>(null)

  useEffect(() => {
    if (!apiBaseUrlDaCauHinh) return
    api.listEmails({ folder: 'inbox' }).then((r) => setEmails(r.items)).catch(() => {})
  }, [])

  const camKet = useMemo(() => trichCamKet(emails), [emails])
  const theoNgay = useMemo(() => gomTheoNgay(camKet), [camKet])
  const o = useMemo(() => luoiThang(thang.getFullYear(), thang.getMonth()), [thang])
  const viecNgayChon = theoNgay.get(ngayChon) ?? []
  const khongHan = camKet.filter((c) => !c.han && c.trangThai !== 'xong')

  return (
    <div className="giao-dien-app relative flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* Báo hiệu nổi trên cùng — thư cần xử lý và hạn sắp tới. */}
      <AlertOverlay emails={emails} />
      {/* ── Cột chính: LỊCH ── */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="den-noi-duoi flex shrink-0 items-center gap-4 px-6 py-4">
          <Link
            to="/app"
            className="o-icon size-9 shrink-0"
            aria-label="Về hộp thư"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-2.5">
              <h1 className="text-[19px] font-semibold leading-none tracking-tight">Lịch trình</h1>
              <span className="font-mono text-[12px] tabular-nums text-[var(--spark)]">
                {String(camKet.filter((c) => c.trangThai !== 'xong').length).padStart(2, '0')}
              </span>
            </div>
            <p className="mt-2 flex items-center gap-1.5 text-[9.5px] uppercase tracking-[0.2em] text-muted-foreground/60">
              <span className="pulse-dot" aria-hidden />
              Trích từ hộp thư · chưa ghi vào lịch Google
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-1.5">
            <button
              onClick={() => setThang((t) => new Date(t.getFullYear(), t.getMonth() - 1, 1))}
              className="o-icon size-8" aria-label="Tháng trước"
            >
              <ChevronLeft className="size-4" />
            </button>
            <span className="w-[104px] text-center font-mono text-[12px] tabular-nums">
              Tháng {thang.getMonth() + 1}/{thang.getFullYear()}
            </span>
            <button
              onClick={() => setThang((t) => new Date(t.getFullYear(), t.getMonth() + 1, 1))}
              className="o-icon size-8" aria-label="Tháng sau"
            >
              <ChevronRight className="size-4" />
            </button>
          </div>
          <LogoMark className="ml-2 size-6 shrink-0 text-foreground/40" />
        </header>

        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto scrollbar-thin p-5">
          {/* Lưới lịch */}
          <div className="grid shrink-0 grid-cols-7 gap-1.5">
            {['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((t) => (
              <div key={t} className="pb-1 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/60">
                {t}
              </div>
            ))}
            {o.map((d) => (
              <ONgay
                key={d.toISOString()}
                ngay={d}
                trongThang={d.getMonth() === thang.getMonth()}
                laHomNay={khoaNgay(d) === khoaNgay(homNay)}
                daChon={khoaNgay(d) === ngayChon}
                viec={theoNgay.get(khoaNgay(d)) ?? []}
                onChon={() => setNgayChon(khoaNgay(d))}
              />
            ))}
          </div>

          {/* Chi tiết ngày đang chọn */}
          {/* `shrink-0` chứ KHÔNG `min-h-0`: khối này nằm trong một khung cuộn dạng
              flex-column, và `min-h-0` cho phép flex bóp nó nhỏ hơn nội dung — kết
              quả là danh sách việc bị nuốt mất, chỉ còn trơ dòng tiêu đề. */}
          <div className="den-vien goc-cat flex shrink-0 flex-col gap-1 p-4">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
              {ngayChon === khoaNgay(homNay) ? 'Hôm nay' : doiNgay(ngayChon)}
              {viecNgayChon.length > 0 && ` · ${tongGio(viecNgayChon)}`}
            </p>
            {viecNgayChon.length === 0 ? (
              <p className="py-3 text-[13px] text-muted-foreground">Ngày này chưa có việc nào.</p>
            ) : (
              viecNgayChon.map((c) => <DongViec key={c.id} ck={c} onHoi={setLenh} />)
            )}
          </div>

          {/* Việc không có thời điểm — một cuốn lịch không chứa nổi loại này, mà nó
              lại đúng là loại hay bị quên nhất. */}
          {khongHan.length > 0 && (
            <div className="den-vien goc-cat flex shrink-0 flex-col gap-1 p-4">
              <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
                Không có thời điểm · {khongHan.length}
              </p>
              {khongHan.map((c) => <DongViec key={c.id} ck={c} onHoi={setLenh} />)}
            </div>
          )}
        </div>
      </div>

      {/* ── Cột phải: TRAO ĐỔI VỚI MEOARC để sắp lại lộ trình ──
          Dùng lại đúng ChatPanel của hộp thư, không dựng bản riêng: cùng một trợ
          lý, cùng một lịch sử hội thoại. Người dùng đổi trang chứ không đổi người
          nói chuyện. */}
      <div className="den-noi-trai flex w-[420px] shrink-0 flex-col">
        <ChatPanel
          emails={emails}
          actions={KHONG_LAM_GI}
          injectedCommand={lenh}
          onInjectConsumed={() => setLenh(null)}
        />
      </div>
    </div>
  )
}

/** Trang lịch KHÔNG thao tác trên thư — không gắn nhãn, không xoá, không lưu trữ.
 *  Người dùng ở đây đang nghĩ về thời gian, không nghĩ về từng lá thư. Truyền một
 *  bộ hành động rỗng là cách nói rõ điều đó ở mức mã nguồn. */
const KHONG_LAM_GI: EmailActions = {
  markRead: () => {},
  setImportant: () => {},
  applyLabel: () => {},
  removeEmails: () => {},
}

function ONgay({
  ngay, trongThang, laHomNay, daChon, viec, onChon,
}: {
  ngay: Date
  trongThang: boolean
  laHomNay: boolean
  daChon: boolean
  viec: CamKet[]
  onChon: () => void
}) {
  const phut = viec.reduce((s, c) => s + c.uocLuongPhut, 0)
  const tyLe = Math.min(1, phut / TRAN_MOI_NGAY)
  const quaTai = phut > TRAN_MOI_NGAY

  return (
    <button
      onClick={onChon}
      className={cn(
        'goc-cat-nho goc-cat flex min-h-[74px] flex-col gap-1.5 p-2 text-left transition-colors',
        daChon ? 'den-vien-chon' : 'den-vien hover:bg-foreground/[0.04]',
        !trongThang && 'opacity-35',
      )}
    >
      <span className="flex items-center justify-between">
        <span className={cn(
          'font-mono text-[12px] tabular-nums',
          laHomNay ? 'font-bold text-[var(--spark)]' : 'text-foreground/80',
        )}>
          {ngay.getDate()}
        </span>
        {viec.length > 0 && (
          <span className="font-mono text-[9px] tabular-nums text-muted-foreground">
            {viec.length}
          </span>
        )}
      </span>

      {/* KHỐI LƯỢNG hiện bằng một vạch, không bằng con số.
          Cả tháng có 42 ô — bắt người dùng đọc 42 con số rồi tự so là bắt họ làm
          việc của biểu đồ. Một vạch dài ngắn thì so được bằng liếc mắt. */}
      {phut > 0 && (
        <span className="mt-auto block h-[4px] w-full overflow-hidden bg-foreground/10">
          <i
            className="block h-full"
            style={{
              width: `${Math.max(tyLe * 100, 8)}%`,
              background: quaTai
                ? 'linear-gradient(90deg, var(--rr-can), var(--rr-khong))'
                : 'var(--rr-hoan)',
            }}
          />
        </span>
      )}
    </button>
  )
}

function DongViec({ ck, onHoi }: { ck: CamKet; onHoi: (l: string) => void }) {
  return (
    <div className="flex items-start gap-3 border-t border-foreground/[0.07] py-2.5 first:border-t-0">
      <span className={cn('cham-rr mt-1.5', `c${ck.mucRuiRo}`)} aria-hidden />
      <span className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="text-[13.5px] font-medium text-foreground">{ck.noiDung}</span>
        <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11.5px] text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Mail className="size-3" />
            {ck.nguoiCho}
          </span>
          {ck.uocLuongPhut > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3" />
                {ck.uocLuongPhut >= 60 ? `${ck.uocLuongPhut / 60} giờ` : `${ck.uocLuongPhut} phút`}
              </span>
            </>
          )}
          {ck.hanSuyRa && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="text-[var(--rr-can)]">hạn tự tính</span>
            </>
          )}
        </span>
      </span>
      <button
        onClick={() => onHoi(`Sắp xếp giúp mình việc: ${ck.noiDung}`)}
        className="nut-ky-thuat shrink-0 px-2.5 py-1.5 text-[11px] font-medium text-foreground"
      >
        Xếp giúp
      </button>
    </div>
  )
}

function tongGio(ds: CamKet[]): string {
  const p = ds.reduce((s, c) => s + c.uocLuongPhut, 0)
  if (!p) return ''
  return p >= 60 ? `${(p / 60).toFixed(1).replace('.0', '')} giờ` : `${p} phút`
}

function doiNgay(k: string): string {
  const [n, t, d] = k.split('-')
  return `Ngày ${Number(d)}/${Number(t)}/${n}`
}
