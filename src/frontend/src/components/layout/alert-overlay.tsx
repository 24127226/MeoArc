import { useEffect, useMemo, useState } from 'react'
import { X, Mail, AlarmClock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Email } from '@/data/emails'
import { trichCamKet } from '@/lib/cam-ket'
import { cn } from '@/lib/utils'

/**
 * AlertOverlay — báo hiệu nổi trên cùng màn hình.
 *
 * Hai loại tin, và chúng KHÁC NHAU về bản chất chứ không chỉ khác nội dung:
 *   • THƯ MỚI      — một sự kiện vừa xảy ra. Đọc xong là hết.
 *   • HẠN SẮP TỚI  — một trạng thái đang xấu đi. Không đọc thì nó vẫn ở đó.
 * Nên hạn dùng mức rủi ro cao hơn và ở lại lâu hơn.
 *
 * ── BA QUY TẮC CHỐNG LÀM PHIỀN ──
 * Một trợ lý nhắc quá nhiều sẽ bị tắt thông báo, và lúc đó nó vô dụng hoàn toàn.
 * Nên có trần cứng, và cả ba quy tắc dưới đây đều là để bảo vệ chính tính năng này:
 *
 *   1. MỘT LẦN cho mỗi thứ. Đã báo rồi thì thôi, kể cả khi tải lại trang — nhớ
 *      qua sessionStorage. Không có bước này thì mỗi lần F5 lại dội lại từ đầu.
 *   2. TỐI ĐA HAI tin cùng lúc. Nhiều hơn thì nó thành một danh sách, mà danh
 *      sách thì đã có ở "Lịch trình" rồi — chỗ này chỉ để CHẶN sự chú ý.
 *   3. CHỈ BÁO KHI CÒN KỊP LÀM GÌ ĐÓ. Hạn đã trôi qua thì báo cũng vô ích, chỉ
 *      thêm khó chịu. Ngưỡng: còn dưới 24 giờ và chưa quá hạn.
 *
 * Tự tắt sau 9 giây với thư mới; HẠN thì KHÔNG tự tắt — người dùng phải chủ động
 * đóng, vì đó là thứ họ cần thấy.
 */

type Tin = {
  id: string
  loai: 'thu' | 'han'
  tieu_de: string
  phu: string
  mucRuiRo: 1 | 2 | 3
}

const KHOA_DA_BAO = 'meoarc:daBao'

/* ── VÌ SAO CÁC BIẾN NÀY Ở CẤP MÔ-ĐUN, KHÔNG PHẢI useRef ──
   `AlertOverlay` được gắn ở HAI nơi: hộp thư (app-shell) và trang lịch. Nếu mỗi
   bản giữ một tập riêng trong bộ nhớ thì đổi trang là mất trí nhớ, và cùng một
   hạn được báo lại — đúng triệu chứng "thông báo lặp lại nhiều quá".

   Đặt ở cấp mô-đun thì mọi bản dùng CHUNG một tập, và sessionStorage lo phần
   sống sót qua F5. */
let _daBao: Set<string> | null = null
let _daThay: Set<string> | null = null

function docDaBao(): Set<string> {
  try {
    return new Set(JSON.parse(sessionStorage.getItem(KHOA_DA_BAO) ?? '[]') as string[])
  } catch {
    return new Set()
  }
}
function ghiDaBao(s: Set<string>) {
  try {
    sessionStorage.setItem(KHOA_DA_BAO, JSON.stringify([...s]))
  } catch {
    // Cửa sổ riêng tư / bộ nhớ bị chặn → chấp nhận báo lại sau khi tải lại trang.
    // Thà lặp một lần còn hơn vỡ cả giao diện vì một chỗ lưu tuỳ chọn.
  }
}

export function AlertOverlay({ emails }: { emails: Email[] }) {
  const navigate = useNavigate()
  const [hien, setHien] = useState<Tin[]>([])
  if (_daBao === null) _daBao = docDaBao()

  /* ── THƯ NÀO LÀ "MỚI" ──────────────────────────────────────────────────
     Bản trước lọc theo `priority === 'High'`, và đó là một lỗi mô hình chứ
     không phải lỗi ngưỡng: thư vừa từ Gmail về CHƯA qua triage của AI nên
     `priority` là null — tức là đúng những lá thư vừa đến thì không bao giờ
     được báo. Bấm làm mới xong không thấy gì, y như báo cáo.

     Cái đáng báo là thư MỚI ĐẾN, không phải thư ưu tiên cao. Nên phải nhớ
     danh sách id đã thấy, rồi so ra thư nào chưa từng thấy.

     Lần đầu gắn thì ghi nhận TOÀN BỘ id mà KHÔNG báo gì — nếu không thì mở
     app lên là dội một loạt thông báo cho những lá thư đã nằm đó từ hôm qua,
     và người dùng sẽ tắt tính năng này trong ngày đầu tiên. */

  // Danh sách tin ĐÁNG báo, tính lại mỗi khi hộp thư đổi.
  const ungVien = useMemo<Tin[]>(() => {
    const ra: Tin[] = []
    const gio = Date.now()

    for (const c of trichCamKet(emails)) {
      if (!c.han || c.trangThai === 'xong') continue
      const conLai = c.han.getTime() - gio
      // Quy tắc 3: quá hạn rồi thì báo cũng vô ích.
      if (conLai <= 0 || conLai > 24 * 3600 * 1000) continue
      const soGio = Math.max(1, Math.round(conLai / 3600000))
      ra.push({
        id: `han-${c.id}`,
        loai: 'han',
        tieu_de: c.noiDung,
        phu: `Còn ${soGio} giờ · ${c.nguoiCho} đang chờ`,
        mucRuiRo: 2,
      })
    }

    // Lần đầu: chỉ ghi nhận, không báo.
    if (_daThay === null) {
      _daThay = new Set(emails.map((e) => e.id))
    } else {
      for (const e of emails) {
        if (_daThay.has(e.id)) continue
        _daThay.add(e.id)
        if (!e.unread) continue // thư mình vừa gửi cũng là "mới" nhưng không cần báo
        ra.push({
          id: `thu-${e.id}`,
          loai: 'thu',
          tieu_de: e.subject,
          // Thư mới chưa qua triage nên chưa biết mức ưu tiên. Nói đúng thứ
          // BIẾT CHẮC (ai gửi) còn hơn đoán một mức ưu tiên chưa có.
          phu: `${e.sender} · thư mới`,
          mucRuiRo: e.priority === 'High' ? 2 : 1,
        })
      }
    }

    // Hạn lên trước thư: một trạng thái đang xấu đi quan trọng hơn một sự kiện
    // vừa xảy ra.
    return ra.sort((a, b) => (a.loai === b.loai ? 0 : a.loai === 'han' ? -1 : 1))
  }, [emails])

  useEffect(() => {
    const chuaBao = ungVien.filter((t) => !_daBao!.has(t.id))
    if (!chuaBao.length) return

    // ĐÁNH DẤU TẤT CẢ, kể cả những tin không được hiện.
    //
    // Đây là lỗi lặp thật sự: bản trước `slice(0, 2)` TRƯỚC rồi mới đánh dấu, nên
    // tin thứ ba trở đi bị bỏ mà KHÔNG được ghi nhận — và cứ mỗi lần hộp thư đổi
    // (đánh dấu đã đọc, gắn nhãn, làm mới) là chúng lại lọt vào danh sách ứng viên
    // và bắn lại. Mãi mãi.
    //
    // Trần "2 tin cùng lúc" là trần HIỂN THỊ, không phải trần ghi nhận. Tin thứ ba
    // đã có chỗ của nó ở trang Lịch trình rồi; chỗ này chỉ để chặn sự chú ý.
    for (const t of chuaBao) _daBao!.add(t.id)
    ghiDaBao(_daBao!)

    setHien((cu) => [...chuaBao.slice(0, 2), ...cu].slice(0, 2))
    const moi = chuaBao.slice(0, 2)

    // Thư mới tự tắt; HẠN thì ở lại cho tới khi người dùng đóng.
    const hens = moi
      .filter((t) => t.loai === 'thu')
      .map((t) => window.setTimeout(() => setHien((cu) => cu.filter((x) => x.id !== t.id)), 9000))
    return () => hens.forEach(clearTimeout)
  }, [ungVien])

  if (!hien.length) return null

  return (
    // `pointer-events-none` ở lớp bao + bật lại trên từng thẻ: overlay phủ ngang
    // màn hình nhưng KHÔNG được chặn thao tác vào thứ nằm dưới nó.
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 top-0 z-[9999] flex flex-col items-center gap-2 p-3"
    >
      {hien.map((t) => (
        <div
          key={t.id}
          className={cn(
            'nhay-bat goc-cat pointer-events-auto flex w-[min(560px,94vw)] items-center gap-3',
            'bg-[var(--elevated)]/94 px-4 py-3 backdrop-blur-md',
            t.mucRuiRo === 2 ? 'rui-ro-2' : 'rui-ro-1',
          )}
        >
          <span className="o-icon size-9 shrink-0" style={{ ['--tint' as string]: 'var(--rr)' }}>
            {t.loai === 'han' ? <AlarmClock className="size-4" /> : <Mail className="size-4" />}
          </span>

          <span className="flex min-w-0 flex-1 flex-col">
            <span className="truncate text-[13.5px] font-semibold text-foreground">{t.tieu_de}</span>
            <span className="truncate text-[11.5px] text-muted-foreground">{t.phu}</span>
          </span>

          {t.loai === 'han' && (
            <button
              onClick={() => {
                setHien((cu) => cu.filter((x) => x.id !== t.id))
                navigate('/lich')
              }}
              className="nut-ky-thuat shrink-0 px-3 py-1.5 text-[11.5px] font-medium text-foreground"
              style={{ ['--tint' as string]: 'var(--rr)' }}
            >
              Xem lịch
            </button>
          )}

          <button
            onClick={() => setHien((cu) => cu.filter((x) => x.id !== t.id))}
            className="o-icon size-7 shrink-0"
            aria-label="Đóng thông báo"
          >
            <X className="size-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
