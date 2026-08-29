import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, ChevronLeft, ChevronRight, Clock, Mail,
  MessageSquare, Sparkles,
} from 'lucide-react'
import { emails as seedEmails, type Email } from '@/data/emails'
import { api, apiBaseUrlDaCauHinh } from '@/lib/api'
import {
  trichCamKet, gomTheoNgay, luoiThang, khoaNgay, TRAN_MOI_NGAY,
  xepDoanTheoTuan, thangNenMo, phutMoiNgay, type CamKet, type DoanThe,
} from '@/lib/cam-ket'
import { ChatPanel } from '@/components/layout/chat-panel'
import { EmailDetail } from '@/components/layout/email-detail'
import type { EmailActions } from '@/lib/email-actions'
import { AlertOverlay } from '@/components/layout/alert-overlay'
import { LogoMark } from '@/components/logo'
import { cn } from '@/lib/utils'
import { chuyenCanh } from '@/lib/chuyen-canh'

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
  const dieuHuong = useNavigate()
  const [emails, setEmails] = useState<Email[]>(apiBaseUrlDaCauHinh ? [] : seedEmails)
  const homNay = useMemo(() => new Date(), [])
  const [thang, setThang] = useState(() => new Date(homNay.getFullYear(), homNay.getMonth(), 1))
  const [lenh, setLenh] = useState<string | null>(null)
  const [chatMo, setChatMo] = useState(false)
  /** Thẻ vừa bấm → hiện khung hỏi "xem thư hay hỏi AI". */
  /** Thẻ đang rê chuột → thanh hành động xổ ra ngay dưới nó.
   *  Giữ HÌNH CHỮ NHẬT của thẻ chứ không giữ toạ độ chuột: thanh phải bám vào
   *  MÉP DƯỚI của thẻ, không phải chỗ con trỏ tình cờ dừng lại. */
  const [dangHoi, setDangHoi] = useState<{ ck: CamKet; hcn: DOMRect } | null>(null)
  /** Thư đang mở toàn màn — bấm quay lại là về đúng lịch, không mất chỗ. */
  const [thuMo, setThuMo] = useState<string | null>(null)

  useEffect(() => {
    if (!apiBaseUrlDaCauHinh) return
    api.listEmails({ folder: 'inbox' }).then((r) => setEmails(r.items)).catch(() => {})
  }, [])

  const camKet = useMemo(() => trichCamKet(emails), [emails])
  const theoNgay = useMemo(() => gomTheoNgay(camKet), [camKet])

  // MỞ RA Ở CHỖ CÓ VIỆC. Đo thật ngày 29/08: mọi cam kết rơi vào tháng 9, nên lịch
  // mở ra là một tháng 8 trống trơn, còn nội dung thật thì nằm ở hàng "ngoài tháng"
  // và bị làm mờ — vừa trống vừa giấu mất thứ đáng xem.
  //
  // Chỉ nhảy MỘT LẦN, lúc dữ liệu về. Chạy lại mỗi lần `camKet` đổi thì người dùng
  // bấm sang tháng khác sẽ bị kéo ngược về, và đó là kiểu bực nhất: giao diện tự ý
  // huỷ thao tác của mình mà không nói gì.
  const daNhay = useRef(false)
  useEffect(() => {
    if (daNhay.current || camKet.length === 0) return
    daNhay.current = true
    setThang(thangNenMo(camKet, homNay))
  }, [camKet, homNay])
  const o = useMemo(() => luoiThang(thang.getFullYear(), thang.getMonth()), [thang])
  const sapToi = useMemo(
    () => camKet.filter((c) => c.trangThai !== 'xong').slice(0, 6),
    [camKet],
  )
  const emailDangMo = thuMo ? emails.find((e) => e.id === thuMo) : null

  const hoiAI = (ck: CamKet) => {
    chuyenCanh(() => {
      setDangHoi(null)
      setChatMo(true)
    })
    setLenh(`Về việc "${ck.noiDung}" (${ck.nguoiCho} đang chờ) — giúp mình sắp xếp thời gian làm.`)
  }

  // Thư mở toàn màn: che hẳn lịch. Quay lại là về đúng chỗ cũ vì lịch không
  // bị unmount — state tháng, thẻ, chat đều còn nguyên.
  if (emailDangMo) {
    return (
      <div className="giao-dien-app flex h-screen w-full overflow-hidden bg-background text-foreground">
        <EmailDetail
          email={emailDangMo}
          onClose={() => chuyenCanh(() => setThuMo(null))}
          actions={KHONG_LAM_GI}
          onAgentAction={(c) => { chuyenCanh(() => { setThuMo(null); setChatMo(true) }); setLenh(c) }}
        />
      </div>
    )
  }

  return (
    <div className="giao-dien-app relative flex h-screen w-full overflow-hidden bg-background text-foreground">
      <AlertOverlay emails={emails} />

      {/* ══ CỘT TRÁI — lịch nhỏ + sắp tới. Đây là phần "tóm tắt" ══ */}
      {/* Mở chat → cột này GIÃN RA và cột giữa BIẾN MẤT. Trước đó cả hai cùng
          liệt kê lịch trình, tức là hai chỗ nói cùng một thứ trên một màn hình —
          thừa, và làm loãng chính thứ đang muốn nhấn. Mở chat thì màn hình chỉ
          còn đúng hai khối: lịch và cuộc trò chuyện. */}
      <aside className={cn(
        'den-noi-phai flex shrink-0 flex-col overflow-hidden',
        chatMo ? 'flex-1' : 'w-[268px]',
      )}>
        <div className="flex items-center gap-3 px-4 py-4">
          {/* Chặn điều hướng mặc định của Link để bọc được chuyển cảnh. Vẫn giữ
              thẻ <a> (có href thật) nên mở tab mới / bàn phím vẫn chạy đúng. */}
          <Link
            to="/app"
            onClick={(e) => {
              if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return
              e.preventDefault()
              chuyenCanh(() => dieuHuong('/app'))
            }}
            className="o-icon size-8 shrink-0"
            aria-label="Về hộp thư"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <span className="text-[15px] font-semibold tracking-tight">Lịch trình</span>
          <LogoMark className="ml-auto size-5 text-foreground/35" />
        </div>

        <LichNho thang={thang} homNay={homNay} theoNgay={theoNgay} onDoiThang={setThang} />

        {/* Chat mở → cột này là khối chính, nên hiện DANH SÁCH ĐẦY ĐỦ.
            Chat đóng → nó chỉ là phần tóm tắt bên cạnh lưới thẻ, nên rút gọn còn
            6 mục sắp tới. Cùng một chỗ, hai vai khác nhau tuỳ ngữ cảnh. */}
        {chatMo ? (
          <div className="mt-1 min-h-0 flex-1 overflow-hidden">
            <DanhSachViec camKet={camKet} homNay={homNay} onBamThe={setDangHoi} />
          </div>
        ) : (
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
                onClick={(e) => setDangHoi({ ck: c, hcn: e.currentTarget.getBoundingClientRect() })}
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
        )}
      </aside>

      {/* ══ KHUNG LỚN — lịch thẻ. ẨN HẲN khi chat mở. ══ */}
      {!chatMo && (
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
        <LuoiThe o={o} thang={thang} homNay={homNay} theoNgay={theoNgay} camKet={camKet} onBamThe={setDangHoi} />
      </main>
      )}

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
        <ThanhViec
          ck={dangHoi.ck} hcn={dangHoi.hcn}
          onDong={() => setDangHoi(null)}
          onXemThu={() => chuyenCanh(() => { setThuMo(dangHoi.ck.emailId); setDangHoi(null) })}
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
  o, thang, homNay, theoNgay, camKet, onBamThe,
}: {
  o: Date[]
  thang: Date
  homNay: Date
  theoNgay: Map<string, CamKet[]>
  camKet: CamKet[]
  onBamThe: (v: { ck: CamKet; hcn: DOMRect }) => void
}) {
  const tuan = useMemo(() => xepDoanTheoTuan(camKet, o), [camKet, o])

  // CẮT HÀNG TUẦN RỖNG Ở ĐÁY. Lưới tháng luôn là 6 hàng, nhưng phần lớn tháng chỉ
  // cần 5 — hàng thừa nằm hoàn toàn ngoài tháng và trống trơn. Giữ nó lại là ăn
  // mất 1/6 chiều cao để không nói gì, mà chiều cao đó chính là thứ các hàng còn
  // lại đang thiếu (thẻ bị cắt chữ vì ô quá thấp).
  const soTuan = useMemo(() => {
    for (let w = 5; w >= 0; w--) {
      const trongThang = o.slice(w * 7, w * 7 + 7).some((d) => d.getMonth() === thang.getMonth())
      if (trongThang || tuan[w].doan.length > 0) return w + 1
    }
    return 6
  }, [o, thang, tuan])

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-1 p-3">
      <div className="grid shrink-0 grid-cols-7 gap-1">
        {['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((t) => (
          <div key={t} className="pb-0.5 text-center font-mono text-[9.5px] uppercase tracking-[0.16em] text-muted-foreground/55">
            {t}
          </div>
        ))}
      </div>
      {tuan.slice(0, soTuan).map((tt, w) => (
        <HangTuan
          key={o[w * 7].toISOString()}
          ngay={o.slice(w * 7, w * 7 + 7)}
          thang={thang}
          homNay={homNay}
          theoNgay={theoNgay}
          doan={tt.doan}
          du={tt.du}
          onBamThe={onBamThe}
        />
      ))}
    </div>
  )
}

/* ── MỘT HÀNG TUẦN = ô ngày ở dưới + LỚP THANH phủ lên trên ──────────────────
   Bản trước để mỗi ô ngày tự vẽ phần thẻ của mình rồi trông chờ các mảnh cạnh
   nhau trông như một thanh liền. Chúng không liền — giữa hai ô có khe lưới, có
   viền, có padding — nên một việc ba ngày hiện ra ba viên rời rạc và mắt đọc ra
   ba việc. Mà cả lý do tồn tại của màn này là cho thấy việc DÀI tới đâu.

   Nay thanh là MỘT phần tử trải ngang qua nhiều cột. Lớp thanh dùng lại đúng
   `grid-cols-7 gap-1` của lớp ô bên dưới, nên nó tự khớp cột — không phải tính
   phần trăm bằng tay, và không lệch khi đổi khoảng cách lưới.

   Mỗi làn là MỘT HÀNG của lưới con (`grid-rows-[repeat(3,17px)]`), nên hai việc
   trùng ngày nằm đúng hai làn mà không cần cộng trừ vị trí. */
function HangTuan({
  ngay, thang, homNay, theoNgay, doan, du, onBamThe,
}: {
  ngay: Date[]
  thang: Date
  homNay: Date
  theoNgay: Map<string, CamKet[]>
  doan: DoanThe[]
  du: Map<string, number>
  onBamThe: (v: { ck: CamKet; hcn: DOMRect }) => void
}) {
  return (
    <div className="relative min-h-0 flex-1">
      <div className="grid h-full grid-cols-7 gap-1">
        {ngay.map((d) => (
          <ONgay
            key={d.toISOString()}
            ngay={d}
            trongThang={d.getMonth() === thang.getMonth()}
            laHomNay={khoaNgay(d) === khoaNgay(homNay)}
            viec={theoNgay.get(khoaNgay(d)) ?? []}
            con={du.get(khoaNgay(d)) ?? 0}
          />
        ))}
      </div>

      {/* `top-[26px]` chừa chỗ cho số ngày; `pointer-events-none` để khoảng trống
          giữa các thanh không nuốt cú rê chuột vào ô ngày bên dưới. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-1 top-[26px] grid grid-cols-7 grid-rows-[repeat(3,17px)] content-start gap-x-1 gap-y-[3px] px-1">
        {doan.map((dt) => (
          <ThanhCamKet
            key={dt.ck.id + '-' + dt.cot}
            doan={dt}
            mo={dt.ck.han ? dt.ck.han.getMonth() !== thang.getMonth() : false}
            onBam={(e) => onBamThe({ ck: dt.ck, hcn: e.currentTarget.getBoundingClientRect() })}
          />
        ))}
      </div>
    </div>
  )
}

/** Ô một ngày — giờ chỉ còn NỀN: số ngày, vạch tải, và "+N" khi hết làn.
 *  Việc vẽ thẻ đã chuyển hẳn lên lớp thanh của `HangTuan`. */
function ONgay({
  ngay, trongThang, laHomNay, viec, con,
}: {
  ngay: Date
  trongThang: boolean
  laHomNay: boolean
  viec: CamKet[]
  con: number
}) {
  // Chia đều phút theo số ngày việc trải qua. Cộng thẳng `uocLuongPhut` cho mọi
  // ngày như bản trước thì một việc 6 tiếng trải 3 ngày bị tính thành 18 tiếng,
  // và ngày nào cũng "quá tải" — cảnh báo lúc nào cũng bật thì hết là cảnh báo.
  const phut = viec.reduce((s, c) => s + phutMoiNgay(c), 0)
  const ty = Math.min(1, phut / TRAN_MOI_NGAY)
  const quaTai = phut > TRAN_MOI_NGAY

  return (
    <div
      className={cn(
        'goc-cat-nho goc-cat relative flex min-h-0 flex-col p-1.5',
        laHomNay ? 'den-vien-chon' : 'den-vien',
        // 30% là quá mờ — nội dung thật rơi vào hàng ngoài tháng thì gần như biến
        // mất. 55% vẫn đọc được mà vẫn lùi ra sau tháng đang xem.
        !trongThang && 'opacity-55',
      )}
    >
      <span className="flex shrink-0 items-center justify-between">
        <span className={cn(
          'font-mono text-[11px] tabular-nums',
          laHomNay ? 'font-bold text-[var(--spark)]' : 'text-foreground/70',
        )}>
          {ngay.getDate()}
        </span>
        {con > 0 && (
          <span className="font-mono text-[9px] font-semibold text-muted-foreground">+{con}</span>
        )}
      </span>

      {/* VẠCH TẢI ở đáy ô — trả lời câu hỏi thật của người dùng: không phải "ngày
          này có việc không" mà "ngày này nặng tới đâu". Nhờ nó mà một ô không có
          thẻ nào vẫn khác một ô kín việc, và cả tháng đọc ra được bằng một cái
          liếc thay vì phải đếm từng thanh. */}
      {phut > 0 && (
        <span
          className="absolute inset-x-1.5 bottom-1 h-[2px] overflow-hidden rounded-full bg-foreground/8"
          title={`${Math.round(phut / 6) / 10} giờ`}
        >
          <span
            className={cn(
              'block h-full rounded-full transition-[width] duration-300 ease-soft',
              quaTai ? 'bg-[var(--rr-khong)]' : 'bg-[var(--spark)]/70',
            )}
            style={{ width: `${Math.max(8, ty * 100)}%` }}
          />
        </span>
      )}
    </div>
  )
}

/** Một THANH cam kết trải ngang qua các cột của hàng tuần.
 *
 *  Ba mức ưu tiên phải đọc được mà KHÔNG cần so sánh cạnh nhau, nên mỗi mức khác
 *  nhau ở ba thứ cùng lúc: hình (▲ ● ▪), độ dày vạch trái, và cường độ quầng
 *  sáng. Chỉ đổi màu là không đủ — người mù màu không thấy gì, và ngay cả mắt
 *  thường cũng khó xếp hạng ba màu nếu chúng không đứng cạnh nhau. */
function ThanhCamKet({
  doan, mo, onBam,
}: {
  doan: DoanThe
  /** Hạn nằm ngoài tháng đang xem → lùi lại một bậc cho khỏi tranh chỗ. */
  mo: boolean
  onBam: (e: { currentTarget: HTMLElement }) => void
}) {
  const { ck, cot, rong, lan, moDau, ketThuc } = doan
  const ut = ck.mucUuTien
  // Ba mức phải đọc được KHÔNG CẦN so sánh cạnh nhau, nên mỗi mức khác ở BỐN thứ
  // cùng lúc: hình, độ dày vạch, cường độ quầng, và độ đậm chữ. Chỉ đổi màu thì
  // người mù màu không thấy gì, mà mắt thường cũng khó xếp hạng ba màu khi chúng
  // nằm rải rác trên lưới chứ không đứng cạnh nhau.
  const dau = ut === 3 ? '▲' : ut === 2 ? '◆' : '▪'
  return (
    <button
      // RÊ CHUỘT là đủ để xổ bảng chi tiết — không tốn một cú bấm chỉ để biết có
      // gì. Giữ onClick cho bàn phím/cảm ứng, nơi không có "rê chuột".
      onMouseEnter={onBam}
      onFocus={onBam}
      onClick={onBam}
      style={{ gridColumn: `${cot + 1} / span ${rong}`, gridRow: lan + 1 }}
      title={ck.noiDung}
      className={cn(
        'nhay-bat pointer-events-auto relative flex h-[17px] items-center gap-1 overflow-hidden pr-1 text-left',
        'transition-[box-shadow,transform] duration-150 ease-soft hover:z-30 hover:scale-[1.012]',
        ut === 3 ? 'uu-tien-3' : ut === 2 ? 'uu-tien-2' : 'uu-tien-1',
        'bg-[var(--elevated)]/90 backdrop-blur-sm',
        ut === 3
          // Nhịp thở nhẹ chỉ dành cho việc SÁT HẠN — thứ duy nhất đáng kéo mắt
          // người dùng về khi họ đang nhìn chỗ khác trên lưới.
          ? 'tho-gap'
          : ut === 2
            ? 'shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--ut)_60%,transparent),0_0_10px_-5px_var(--ut)]'
            : 'shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--ut)_26%,transparent)]',
        'hover:shadow-[inset_0_0_0_1px_var(--ut),0_0_20px_-2px_var(--ut)]',
        // Bo góc CHỈ ở hai đầu THẬT của đợt. Đoạn bị tuần cắt để vuông, nên nhìn
        // sang hàng dưới vẫn đọc ra là "còn tiếp".
        moDau && 'rounded-l-[4px]',
        ketThuc && 'rounded-r-[4px]',
        mo && 'opacity-70',
      )}
    >
      {/* Vạch ưu tiên bên trái: cấp 3 dày 4px, cấp 2 dày 3px, cấp 1 mảnh 2px. */}
      {moDau ? (
        <span
          className="h-full shrink-0 bg-[var(--ut)]"
          style={{ width: ut === 3 ? 4 : ut === 2 ? 3 : 2 }}
          aria-hidden
        />
      ) : (
        // Đoạn nối tiếp từ tuần trước — mũi nhọn thay cho vạch, để không đọc nhầm
        // thành một việc mới bắt đầu.
        <span className="shrink-0 pl-1 font-mono text-[9px] leading-none text-[var(--ut)]" aria-hidden>‹</span>
      )}

      {moDau && (
        <span className="shrink-0 text-[8px] leading-none text-[var(--ut)]" aria-hidden>{dau}</span>
      )}

      <span className={cn(
        'truncate text-[10px] leading-none',
        ut === 3 ? 'font-semibold text-foreground' : ut === 2 ? 'font-medium text-foreground/90' : 'text-foreground/75',
      )}>
        {ck.noiDung}
      </span>

      {/* Dấu hạn chỉ đặt ở ĐÚNG ngày hạn, và chỉ khi thanh đủ rộng để không đè chữ. */}
      {ketThuc && rong >= 2 && ck.han && (
        <span className="ml-auto shrink-0 font-mono text-[8.5px] tabular-nums text-muted-foreground">
          {gioPhut(ck.han)}
        </span>
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
  onBamThe: (v: { ck: CamKet; hcn: DOMRect }) => void
}) {
  const con = camKet.filter((c) => c.trangThai !== 'xong')
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto scrollbar-thin p-3">
      {con.map((c) => (
        <button
          key={c.id}
          onClick={(e) => onBamThe({ ck: c, hcn: e.currentTarget.getBoundingClientRect() })}
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
/**
 * ThanhViec — thanh hành động xổ ra NGAY DƯỚI thẻ khi rê chuột.
 *
 * ── VÌ SAO KHÔNG DÙNG HỘP THOẠI NHƯ BẢN TRƯỚC ──
 * Bản trước bấm vào thẻ mới mở một hộp có hai dòng chữ. Hai vấn đề: nó tốn một
 * cú bấm chỉ để BIẾT có những lựa chọn gì, và nó là một hộp chữ đặt đè lên lịch
 * — nặng nề so với việc nó chỉ đang hỏi "xem thư hay hỏi trợ lý".
 *
 * Xổ ra khi rê chuột thì lựa chọn tự lộ, không tốn cú bấm nào; và hai icon thì
 * nhận ra nhanh hơn hai dòng chữ.
 *
 * ── VÌ SAO ĐỊNH VỊ `fixed` CHỨ KHÔNG ĐẶT TRONG THẺ ──
 * Ô ngày mang `clip-path` (góc cắt), mà clip-path CẮT CẢ CON. Đặt thanh này bên
 * trong thẻ thì nó bị xén mất ngay khi tràn khỏi ô. Nên tính toạ độ từ hình chữ
 * nhật của thẻ rồi vẽ ở tầng trên cùng.
 */
function ThanhViec({
  ck, hcn, onDong, onXemThu, onHoiAI,
}: {
  ck: CamKet
  hcn: DOMRect
  onDong: () => void
  onXemThu: () => void
  onHoiAI: () => void
}) {
  // Rộng hơn hẳn bản trước (188 → 300). Thanh trong lưới chỉ cao 17px và rộng
  // bằng một ô ngày, nên tiêu đề LUÔN bị cắt — đó là giới hạn của lưới tháng,
  // không phải lỗi sửa được bằng cách chỉnh cỡ chữ. Chỗ đọc đủ phải là ĐÂY.
  //
  // Chia vai rõ: lưới là BẢN ĐỒ (ở đâu, dài bao lâu, gấp cỡ nào), bảng này là
  // CHI TIẾT (việc gì, ai chờ, hạn lúc nào, tốn bao lâu).
  const W = 300
  const left = Math.min(Math.max(8, hcn.left + hcn.width / 2 - W / 2), window.innerWidth - W - 8)
  // Bảng cao hơn nên phải tự lật LÊN TRÊN khi thẻ nằm sát đáy màn hình — không
  // thì nó tràn ra ngoài và người dùng không đọc được gì.
  const CAO = 150
  const duoi = hcn.bottom + 6
  const lat = duoi + CAO > window.innerHeight - 8
  const top = lat ? Math.max(8, hcn.top - CAO - 6) : duoi

  const ut = ck.mucUuTien
  const nhanUuTien = ut === 3 ? 'Gấp' : ut === 2 ? 'Quan trọng' : 'Thường'
  const gio = Math.round(ck.uocLuongPhut / 6) / 10

  return (
    <div
      // Giữ mở khi con trỏ đi từ thẻ xuống thanh — không có cái này thì thanh
      // biến mất ngay lúc người dùng với tay tới nó.
      onMouseEnter={() => {}}
      onMouseLeave={onDong}
      // `position` PHẢI ghi nội tuyến. `.goc-cat` đặt `position: relative`, và vì
      // nó là CSS tự viết nằm ngoài @layer nên nó THẮNG tiện ích `fixed` của
      // Tailwind. Dùng class thì thanh này thành `relative`, rơi vào dòng chảy
      // bình thường ở cuối DOM và văng ra ngoài màn hình — đã đo được: left 2260,
      // top 1017 trên khung 1440×900.
      //
      // Đúng cái bẫy đã ghi chú cho nút trợ lý ở trên, và tôi vẫn giẫm lại. Ghi
      // ở CẢ HAI chỗ để lần sau ai đọc file này cũng vấp thấy.
      style={{ position: 'fixed', left, top, width: W }}
      className={cn(
        'nhay-bat goc-cat-nho goc-cat z-50 flex flex-col gap-2 p-2.5 backdrop-blur-md',
        ut === 3 ? 'uu-tien-3' : ut === 2 ? 'uu-tien-2' : 'uu-tien-1',
        'border border-[color-mix(in_srgb,var(--ut)_60%,transparent)]',
        'bg-[var(--nen-2,var(--elevated))]/97',
        'shadow-[0_10px_30px_-8px_rgba(0,0,0,0.6)]',
      )}
    >
      {/* Hàng nhãn: mức ưu tiên + hạn. Hai thứ quyết định "có làm ngay không". */}
      <div className="flex items-center gap-2">
        <span className={cn(
          'shrink-0 px-1.5 py-0.5 font-mono text-[8.5px] uppercase tracking-[0.14em]',
          'border border-[color-mix(in_srgb,var(--ut)_55%,transparent)] text-[var(--ut)]',
        )}>
          {nhanUuTien}
        </span>
        {ck.han && (
          <span className="truncate font-mono text-[9.5px] tabular-nums text-muted-foreground">
            {ck.han.getDate()}/{ck.han.getMonth() + 1} · {gioPhut(ck.han)}
          </span>
        )}
        {/* Hạn SUY RA phải nói rõ là suy ra. Trình bày một phỏng đoán như một sự
            thật là cách nhanh nhất làm người dùng mất tin vào cả tính năng. */}
        {ck.hanSuyRa && (
          <span className="ml-auto shrink-0 font-mono text-[8.5px] uppercase tracking-wider text-muted-foreground/60">
            ước tính
          </span>
        )}
      </div>

      {/* TIÊU ĐỀ ĐẦY ĐỦ — không cắt. Đây là lý do bảng này tồn tại. */}
      <p className="text-[12.5px] font-medium leading-snug text-foreground">
        {ck.noiDung}
      </p>

      <p className="flex items-center gap-1.5 text-[10.5px] text-muted-foreground">
        <Clock className="size-3 shrink-0" />
        {ck.nguoiCho} đang chờ · ~{gio} giờ
      </p>

      <div className="flex items-center gap-1 border-t border-border/15 pt-2">
        <button
          onClick={onXemThu}
          title="Xem thư gốc"
          className="nut-ky-thuat flex flex-1 items-center justify-center gap-1.5 px-2 py-1.5
                     text-[11px] font-medium text-foreground"
        >
          <Mail className="size-3.5" />
          Thư gốc
        </button>
        <button
          onClick={onHoiAI}
          title={`Hỏi trợ lý về: ${ck.noiDung}`}
          className="nut-ky-thuat flex flex-1 items-center justify-center gap-1.5 px-2 py-1.5
                     text-[11px] font-medium text-foreground"
          style={{ ['--tint' as string]: 'var(--spark)' }}
        >
          <MessageSquare className="size-3.5" />
          Hỏi trợ lý
        </button>
      </div>
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
