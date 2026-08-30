import { useEffect, useState } from 'react'
import { Plane, Hotel, X, Loader2, ShieldCheck, FlaskConical, Code2, ExternalLink, MapPin } from 'lucide-react'
import { duongDanApi, apiBaseUrlDaCauHinh } from '@/lib/api'
import { cn } from '@/lib/utils'

/**
 * TraCuuPanel — tra cứu chuyến bay & phòng, gọi THẲNG backend.
 *
 * ── KHUNG NÀY TỒN TẠI ĐỂ CHỨNG MINH, KHÔNG CHỈ ĐỂ DÙNG ──
 * Câu hỏi khó nhất khi trình bày là "cái này có thật không, hay các em bịa số".
 * Trả lời bằng lời thì không ai tin được; phải trả lời bằng thứ người xem tự kiểm
 * được. Nên khung này làm ba việc mà một khung tra cứu thường không làm:
 *
 *   1. DÁN NHÃN NGUỒN ngay trên đầu — "AMADEUS · dữ liệu thật" hay "MÔ PHỎNG".
 *      Nhãn đổi theo cấu hình máy chủ, không phải theo chữ ai gõ vào.
 *   2. HIỆN DẤU THỜI GIAN của lần truy vấn, để đối chiếu tại chỗ.
 *   3. CHO XEM PHẢN HỒI GỐC. Người hoài nghi bấm một nút là thấy JSON thô từ nhà
 *      cung cấp. Không còn chỗ nào để nghi ngờ, và cũng không còn chỗ nào để giấu.
 *
 * ── VÌ SAO KHÔNG ĐI QUA TRỢ LÝ ──
 * Hạn mức Gemini free là 20 lượt/ngày mỗi model. Phần quan trọng nhất của buổi bảo
 * vệ không được phép chết vì hết lượt. Đường này không gọi mô hình lần nào.
 * Nó cũng tách bạch điều đang chứng minh: dữ liệu đi thẳng từ nhà cung cấp về màn
 * hình, không qua chỗ nào cho mô hình diễn đạt lại.
 *
 * KHÔNG CÓ NÚT ĐẶT. Đặt chỗ phải đi qua cổng xác nhận riêng — xem thẻ dự định.
 */

// `la_that` và `co_gia` TÁCH RỜI: AeroDataBox là nguồn thật nhưng không bán vé nên
// không có giá. Gộp làm một cờ thì hoặc phải dán nhãn giả cho dữ liệu thật, hoặc phải
// hứa có giá trong khi không có.
type Nguon = {
  nguon: string; la_that: boolean; nhan: string
  co_gia?: boolean; huong_dan?: string | null
}
type KetQua = Nguon & { thoi_diem: string; so_ket_qua: number; ket_qua: Record<string, unknown>[] }

const HOM_NAY_CONG = (n: number) => {
  const d = new Date()
  d.setDate(d.getDate() + n)
  const p = (x: number) => String(x).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}

export function TraCuuPanel({ onDong }: { onDong: () => void }) {
  const [loai, setLoai] = useState<'bay' | 'phong'>('bay')
  const [tu, setTu] = useState('SGN')
  const [den, setDen] = useState('DAD')
  const [thanhPho, setThanhPho] = useState('Đà Nẵng')
  const [ngay, setNgay] = useState(HOM_NAY_CONG(14))
  const [tra, setTra] = useState(HOM_NAY_CONG(16))
  const [dangChay, setDangChay] = useState(false)
  const [ketQua, setKetQua] = useState<KetQua | null>(null)
  const [loi, setLoi] = useState<string | null>(null)
  const [hienTho, setHienTho] = useState(false)
  const [nguon, setNguon] = useState<Nguon | null>(null)

  // Hỏi máy chủ đang dùng nhà cung cấp nào NGAY KHI MỞ, để nhãn có mặt trước cả
  // lần tra cứu đầu tiên — người xem biết mình sắp thấy gì.
  useEffect(() => {
    if (!apiBaseUrlDaCauHinh) return
    fetch(duongDanApi('/tra-cuu/trang-thai'))
      .then((r) => r.json())
      .then(setNguon)
      .catch(() => {})
  }, [])

  const chay = async () => {
    setDangChay(true)
    setLoi(null)
    setKetQua(null)
    try {
      const d =
        loai === 'bay'
          ? `/tra-cuu/chuyen-bay?tu=${tu}&den=${den}&ngay=${encodeURIComponent(ngay)}&so_ket_qua=5`
          : `/tra-cuu/khach-san?thanh_pho=${encodeURIComponent(thanhPho)}`
            + `&nhan_phong=${encodeURIComponent(ngay)}&tra_phong=${encodeURIComponent(tra)}&so_ket_qua=5`
      const r = await fetch(duongDanApi(d))
      const j = await r.json()
      if (!r.ok) {
        // Hiện ĐÚNG thông điệp máy chủ trả về. "Có lỗi xảy ra" thì lúc trình bày mà
        // hỏng, không ai sửa được trong ba mươi giây.
        setLoi(j?.error?.message ?? j?.detail ?? `Máy chủ trả về ${r.status}`)
        return
      }
      setKetQua(j)
      setNguon(j)
    } catch (e) {
      setLoi(`Không gọi được máy chủ: ${String(e).slice(0, 120)}`)
    } finally {
      setDangChay(false)
    }
  }

  const that = nguon?.la_that === true

  return (
    // z CAO HƠN lớp thông báo nổi (z-9999). Thông báo là thứ tự nó xen vào; hộp
    // thoại là thứ người dùng CHỦ ĐỘNG mở — cái sau phải thắng. Đã chụp được cảnh
    // thông báo che đúng cái nhãn nguồn, tức che mất phần đáng tin nhất của khung.
    <div className="fixed inset-0 z-[10000] flex items-start justify-center bg-black/55 p-4 backdrop-blur-sm"
         onClick={onDong}>
      <div
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Tra cứu chuyến bay và phòng"
        className="goc-cat den-vien-chon mt-10 flex max-h-[calc(100dvh-6rem)] w-[min(680px,96vw)]
                   flex-col overflow-hidden bg-[var(--elevated)]/97 backdrop-blur-md"
      >
        {/* ── Đầu khung: NHÃN NGUỒN là thứ đầu tiên đập vào mắt ── */}
        <div className="flex shrink-0 items-center gap-3 border-b border-border/20 px-4 py-3">
          <span className="o-icon size-9 shrink-0">
            {loai === 'bay' ? <Plane className="size-4" /> : <Hotel className="size-4" />}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[14px] font-semibold leading-tight">Tra cứu chỗ đi lại</p>
            <p className="truncate text-[11px] text-muted-foreground">
              Chỉ tra cứu — không đặt, không thanh toán
            </p>
          </div>
          <span
            className={cn(
              'flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1',
              'font-mono text-[10px] font-semibold uppercase tracking-[0.08em]',
              that
                ? 'bg-[var(--rr-hoan,#0E8F63)]/15 text-[var(--rr-hoan,#0E8F63)]'
                : 'bg-[var(--ut-gap,#B45309)]/15 text-[var(--ut-gap,#B45309)]',
            )}
            title={nguon?.huong_dan ?? undefined}
          >
            {that ? <ShieldCheck className="size-3" /> : <FlaskConical className="size-3" />}
            {nguon?.nhan ?? 'đang hỏi máy chủ…'}
          </span>
          <button onClick={onDong} className="o-icon size-8 shrink-0" aria-label="Đóng">
            <X className="size-3.5" />
          </button>
        </div>

        {/* ── Ô nhập: để NGƯỜI XEM tự gõ. Nhập tại chỗ là bằng chứng mạnh hơn hẳn
              một kịch bản dựng sẵn — số liệu diễn tập được, phản ứng thì không. ── */}
        <div className="flex shrink-0 flex-wrap items-end gap-2 border-b border-border/15 px-4 py-3">
          <div className="flex overflow-hidden rounded-lg border border-border/40">
            {(['bay', 'phong'] as const).map((l) => (
              <button
                key={l}
                onClick={() => { setLoai(l); setKetQua(null); setLoi(null) }}
                className={cn('px-3 py-1.5 text-[12px] font-medium transition-colors',
                  loai === l ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:bg-secondary/40')}
              >
                {l === 'bay' ? 'Chuyến bay' : 'Khách sạn'}
              </button>
            ))}
          </div>

          {loai === 'bay' ? (
            <>
              <O nhan="Từ" giaTri={tu} datGiaTri={(v) => setTu(v.toUpperCase().slice(0, 3))} rong="w-[68px]" />
              <O nhan="Đến" giaTri={den} datGiaTri={(v) => setDen(v.toUpperCase().slice(0, 3))} rong="w-[68px]" />
              <O nhan="Ngày bay" giaTri={ngay} datGiaTri={setNgay} rong="w-[112px]" />
            </>
          ) : (
            <>
              <O nhan="Thành phố" giaTri={thanhPho} datGiaTri={setThanhPho} rong="w-[130px]" />
              <O nhan="Nhận phòng" giaTri={ngay} datGiaTri={setNgay} rong="w-[112px]" />
              <O nhan="Trả phòng" giaTri={tra} datGiaTri={setTra} rong="w-[112px]" />
            </>
          )}

          <button
            onClick={chay}
            disabled={dangChay}
            className="nut-ky-thuat ml-auto flex items-center gap-1.5 px-4 py-2 text-[12.5px] font-medium disabled:opacity-50"
          >
            {dangChay && <Loader2 className="size-3.5 animate-spin" />}
            {dangChay ? 'Đang hỏi…' : 'Tra cứu'}
          </button>
        </div>

        {/* ── Kết quả ── */}
        <div className="fade-y min-h-0 flex-1 overflow-y-auto scrollbar-thin px-4 py-3">
          {loi && (
            <p className="rui-ro-3 goc-cat-nho goc-cat px-3 py-2 text-[12.5px]">{loi}</p>
          )}

          {!loi && !ketQua && (
            <p className="py-6 text-center text-[12.5px] text-muted-foreground">
              Nhập chặng và ngày rồi bấm “Tra cứu”.
            </p>
          )}

          {ketQua && (
            <>
              <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground/60">
                {ketQua.so_ket_qua} kết quả · truy vấn lúc {ketQua.thoi_diem}
              </p>

              <div className="flex flex-col gap-1.5">
                {ketQua.ket_qua.map((k, i) => (
                  <div key={i} className="goc-cat-nho goc-cat den-vien flex items-center gap-3 px-3 py-2">
                    {loai === 'bay' ? <DongBay k={k} /> : <DongPhong k={k} />}
                  </div>
                ))}
              </div>

              {/* XEM PHẢN HỒI GỐC — dành cho người hoài nghi. Đây là chỗ chuyển từ
                  "tin lời người trình bày" sang "tự nhìn thấy". */}
              <button
                onClick={() => setHienTho((v) => !v)}
                className="mt-3 flex items-center gap-1.5 text-[11.5px] text-muted-foreground hover:text-foreground"
              >
                <Code2 className="size-3.5" />
                {hienTho ? 'Ẩn phản hồi gốc' : 'Xem phản hồi gốc từ máy chủ'}
              </button>
              {hienTho && (
                <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-background/60 p-3
                                font-mono text-[10.5px] leading-relaxed text-muted-foreground">
                  {JSON.stringify(ketQua, null, 2)}
                </pre>
              )}
            </>
          )}
        </div>

        <div className="shrink-0 border-t border-border/15 px-4 py-2 text-[11px] text-muted-foreground">
          <p>
            Khung này <strong className="text-foreground">không đặt chỗ</strong>. Muốn đặt thì phải qua
            thẻ dự định có nút duyệt — và khâu chuyển tiền hiện là mô phỏng.
          </p>
          {/* KHI ĐANG MÔ PHỎNG, NÓI RÕ CHỖ NÀO VẪN LÀ THẬT.
              Nhãn "MÔ PHỎNG" ở trên là lời thú nhận cần thiết, nhưng nếu dừng ở đó
              thì người xem kết luận "cả khung này đều giả" — mà không đúng: đường
              dẫn mở ra đúng chặng, đúng ngày, trên một trang tra cứu thật. Chỉ ra
              chỗ kiểm được biến điểm yếu thành một phép thử. */}
          {!that && ketQua && (
            <p className="mt-1 text-foreground/70">
              Giá trên là số mô phỏng, nhưng nút{' '}
              <strong className="text-[var(--spark)]">Xem chuyến bay</strong> mở ra
              chuyến bay <strong className="text-foreground">thật</strong> của đúng chặng và
              ngày này — bấm để đối chiếu.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function O({ nhan, giaTri, datGiaTri, rong }: {
  nhan: string; giaTri: string; datGiaTri: (v: string) => void; rong: string
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground/60">
        {nhan}
      </span>
      <input
        value={giaTri}
        onChange={(e) => datGiaTri(e.target.value)}
        className={cn('rounded-lg border border-border/40 bg-background/50 px-2.5 py-1.5',
          'text-[12.5px] outline-none focus:border-[var(--spark)]', rong)}
      />
    </label>
  )
}

function DongBay({ k }: { k: Record<string, unknown> }) {
  const gia = Number(k.gia_vnd ?? 0)
  const phut = Number(k.phut_bay ?? 0)
  const gioBay = phut ? `${Math.floor(phut / 60)}h${String(phut % 60).padStart(2, '0')}` : null
  // Nguồn BÁN VÉ mới có giá. Nguồn dữ liệu bay (AeroDataBox) thì không — và nó cũng
  // không biết chính sách hoàn vé, nên hai thứ đó cùng ẩn/hiện theo một cờ.
  const coGia = k.co_gia !== false
  const chiTiet = typeof k.lien_ket_chi_tiet === 'string' ? k.lien_ket_chi_tiet : null
  // Chỉ nguồn thật mới có mấy thứ này; rỗng nghĩa là KHÔNG BIẾT, không phải "không có".
  const them = [k.may_bay, k.nha_ga ? `nhà ga ${k.nha_ga}` : '', k.trang_thai]
    .filter((x) => typeof x === 'string' && x).join(' · ')

  return (
    <>
      {/* SỐ HIỆU LÀ NÚT khi chuyến bay có thật: bấm ra đúng thẻ chi tiết của chuyến đó
          trên Google (giờ, nhà ga, cửa ra, loại máy bay, đang bay hay chưa). Bản dựng
          theo CHẶNG ở cột phải chỉ mở ra một bảng nhiều chuyến, người dùng vẫn phải tự
          dò lại dòng mình vừa xem. Nguồn mô phỏng KHÔNG có link này — số hiệu do hàm
          băm sinh ra, dẫn tới trang trống thì người dùng kết luận công cụ hỏng. */}
      {chiTiet ? (
        <a
          href={chiTiet}
          target="_blank"
          rel="noreferrer noopener"
          title="Xem chi tiết chuyến bay này trên Google"
          className="group flex shrink-0 items-center gap-0.5 font-mono text-[12px] font-semibold text-[var(--spark)] hover:underline"
        >
          {String(k.ma)}
          <ExternalLink className="size-2.5 opacity-0 transition-opacity group-hover:opacity-100" />
        </a>
      ) : (
        <span className="font-mono text-[12px] font-semibold text-[var(--spark)]">{String(k.ma)}</span>
      )}

      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12.5px] font-medium">{String(k.hang)}</span>
        <span className="block truncate text-[11px] text-muted-foreground">
          {String(k.khoi_hanh)} → {String(k.ha_canh)}
          {gioBay ? ` · ${gioBay}` : ''}
          {' · '}{Number(k.so_diem_dung) === 0 ? 'bay thẳng' : `${k.so_diem_dung} điểm dừng`}
          {/* KHÔNG hiện "không hoàn" cho nguồn không bán vé: đó là một KHẲNG ĐỊNH về
              điều kiện vé mà nguồn đó không hề biết. Im lặng mới đúng. */}
          {coGia ? ` · ${k.hoan_duoc ? 'hoàn được' : 'không hoàn'}` : ''}
        </span>
        {them && (
          <span className="block truncate text-[10.5px] text-muted-foreground/80">{them}</span>
        )}
      </span>

      <span className="shrink-0 text-right">
        {coGia ? (
          <span className="block font-mono text-[12.5px] font-semibold tabular-nums">
            {gia.toLocaleString('vi-VN')} ₫
          </span>
        ) : (
          // "—" chứ KHÔNG phải "0 ₫". Số 0 là một mức giá, và là mức giá hấp dẫn nhất
          // có thể — người dùng tin ngay. "—" là thú nhận không biết. Cùng lý do với
          // "—" ở cột số sao khách sạn.
          <span
            title="Nguồn này cung cấp lịch bay, không bán vé nên không có giá"
            className="block cursor-help font-mono text-[12.5px] font-semibold text-muted-foreground"
          >
            —
          </span>
        )}
        {/* BẤM RA TRANG THẬT. Một bảng giá không bấm được thì người dùng vẫn phải mở
            tab khác gõ lại từ đầu — công cụ chưa tiết kiệm được gì. Đây cũng là cách
            người xem TỰ KIỂM số liệu: khớp hay không khớp, thấy ngay trong ba giây. */}
        {typeof k.lien_ket === 'string' && (
          <a
            href={k.lien_ket}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-0.5 flex items-center justify-end gap-1 text-[10.5px] text-[var(--spark)] hover:underline"
          >
            {coGia ? 'Xem chuyến bay' : 'Xem giá'} <ExternalLink className="size-2.5" />
          </a>
        )}
      </span>
    </>
  )
}

function DongPhong({ k }: { k: Record<string, unknown> }) {
  const tong = Number(k.tong_vnd ?? 0)
  return (
    <>
      {/* 0 = Amadeus KHÔNG trả số sao ở endpoint này. Hiện "—" chứ không hiện "0★":
          "0 sao" là một khẳng định về chất lượng, còn "—" là thú nhận không biết. */}
      <span className="w-9 shrink-0 text-center font-mono text-[12px] font-semibold text-[var(--spark)]">
        {Number(k.so_sao) > 0 ? `${k.so_sao}★` : '—'}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12.5px] font-medium">{String(k.ten)}</span>
        <span className="block truncate text-[11px] text-muted-foreground">
          {String(k.so_dem)} đêm · cách trung tâm {String(k.cach_trung_tam_km)} km
          {' · '}{k.huy_mien_phi ? 'huỷ miễn phí' : 'không huỷ được'}
        </span>
      </span>
      <span className="shrink-0 text-right">
        <span className="block font-mono text-[12.5px] font-semibold tabular-nums">
          {tong.toLocaleString('vi-VN')} ₫
        </span>
        {typeof k.lien_ket === 'string' && (
          <a
            href={k.lien_ket}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-0.5 flex items-center justify-end gap-1 text-[10.5px] text-[var(--spark)] hover:underline"
          >
            Xem trên bản đồ <MapPin className="size-2.5" />
          </a>
        )}
      </span>
    </>
  )
}
