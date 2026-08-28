import { useEffect, useMemo, useRef, useState } from 'react'
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
  const daBao = useRef<Set<string>>(docDaBao())

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

    for (const e of emails) {
      if (!e.unread || e.priority !== 'High') continue
      ra.push({
        id: `thu-${e.id}`,
        loai: 'thu',
        tieu_de: e.subject,
        phu: `${e.sender} · cần bạn xử lý`,
        mucRuiRo: 1,
      })
    }

    // Hạn lên trước thư: một trạng thái đang xấu đi quan trọng hơn một sự kiện
    // vừa xảy ra.
    return ra.sort((a, b) => (a.loai === b.loai ? 0 : a.loai === 'han' ? -1 : 1))
  }, [emails])

  useEffect(() => {
    const moi = ungVien.filter((t) => !daBao.current.has(t.id)).slice(0, 2)
    if (!moi.length) return
    for (const t of moi) daBao.current.add(t.id)
    ghiDaBao(daBao.current)
    setHien((cu) => [...moi, ...cu].slice(0, 2))

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
