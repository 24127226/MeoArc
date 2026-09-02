import { useEffect, useMemo, useState } from 'react'
import { Plane, Hotel, X, Loader2, ShieldCheck, FlaskConical, Code2, ExternalLink } from 'lucide-react'
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
/** Một giá trị lọc CÓ THẬT trong kết quả, kèm số chuyến. Máy chủ sinh từ chính dữ
 *  liệu trả về nên mọi ô lọc đều đảm bảo ra ít nhất một chuyến. */
type OLoc = { gia_tri: string; ten?: string; so_chuyen: number }
type BoLoc = {
  hang: OLoc[]; may_bay: OLoc[]; nha_ga: OLoc[]; trang_thai: OLoc[]; khung_gio: OLoc[]
}
type KetQua = Nguon & {
  thoi_diem: string; so_ket_qua: number; ket_qua: Record<string, unknown>[]
  bo_loc?: BoLoc
}

/** Các nhóm lọc, theo ĐÚNG những gì nguồn dữ liệu trả về — không hơn.
 *  AeroDataBox cho: hãng, giờ khởi hành, loại máy bay, nhà ga, trạng thái. KHÔNG có
 *  giá, nên không có ô lọc giá — thêm một ô lọc không có dữ liệu đằng sau là hứa suông. */
const NHOM_LOC = [
  { khoa: 'khung_gio' as const, ten: 'Giờ bay', truong: null },
  { khoa: 'hang' as const, ten: 'Hãng', truong: 'hang' },
  { khoa: 'may_bay' as const, ten: 'Máy bay', truong: 'may_bay' },
  { khoa: 'nha_ga' as const, ten: 'Nhà ga', truong: 'nha_ga' },
  { khoa: 'trang_thai' as const, ten: 'Trạng thái', truong: 'trang_thai' },
]

function _khungCua(khoiHanh: unknown): string {
  // "dd/mm/yyyy HH:MM" → giờ nằm ở vị trí 11–13. Cùng cách cắt với máy chủ, nên hai
  // bên không thể xếp một chuyến vào hai khung khác nhau.
  const g = Number(String(khoiHanh ?? '').slice(11, 13))
  if (Number.isNaN(g)) return ''
  return g < 6 ? 'dem_khuya' : g < 12 ? 'sang' : g < 18 ? 'chieu' : 'toi'
}

const HOM_NAY_CONG = (n: number) => {
  const d = new Date()
  d.setDate(d.getDate() + n)
  const p = (x: number) => String(x).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}

export function TraCuuPanel({ onDong }: { onDong: () => void }) {
  const [loai, setLoai] = useState<'bay' | 'phong'>('bay')
  // Mở ra đã có sẵn một chặng CHẠY ĐƯỢC: người xem bấm "Tra cứu" là thấy kết quả ngay,
  // không phải nghĩ xem gõ gì trước. Điền tên thành phố chứ không phải mã, để lần đầu
  // nhìn vào là biết ô này nhận tên — không ai đọc placeholder trước khi gõ.
  const [tu, setTu] = useState('TP HCM')
  const [den, setDen] = useState('Đà Nẵng')
  const [thanhPho, setThanhPho] = useState('Đà Nẵng')
  const [ngay, setNgay] = useState(HOM_NAY_CONG(14))
  const [tra, setTra] = useState(HOM_NAY_CONG(16))
  const [dangChay, setDangChay] = useState(false)
  const [ketQua, setKetQua] = useState<KetQua | null>(null)
  const [loi, setLoi] = useState<string | null>(null)
  const [hienTho, setHienTho] = useState(false)
  const [nguon, setNguon] = useState<Nguon | null>(null)
  // Bộ lọc đang chọn: nhóm → tập giá trị. Lọc chạy TẠI CHỖ, không gọi lại máy chủ —
  // cả ngày bay đã tải về rồi, và gọi lại còn tốn hạn mức nhà cung cấp.
  const [dangLoc, setDangLoc] = useState<Record<string, Set<string>>>({})

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
    // Bỏ bộ lọc cũ: các giá trị lọc sinh từ KẾT QUẢ, nên giữ lại lựa chọn của chặng
    // trước là lọc theo một hãng có thể không bay chặng mới — bảng rỗng mà không rõ
    // vì sao, và người dùng sẽ tưởng chặng đó không có chuyến nào.
    setDangLoc({})
    try {
      const d =
        loai === 'bay'
          // Lấy nhiều chuyến để bộ lọc có ý nghĩa. Không tốn thêm lượt gọi nhà cung
          // cấp: máy chủ vẫn quét cả ngày như cũ, chỉ là không cắt bớt trước khi trả.
          ? `/tra-cuu/chuyen-bay?tu=${encodeURIComponent(tu)}&den=${encodeURIComponent(den)}`
            + `&ngay=${encodeURIComponent(ngay)}&so_ket_qua=60`
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

  // Lọc TẠI CHỖ. Mỗi nhóm là "hoặc" trong nhóm, "và" giữa các nhóm — đúng cách mọi
  // trang đặt vé hoạt động, nên không phải giải thích cho người dùng.
  const daLoc = useMemo(() => {
    const ds = ketQua?.ket_qua ?? []
    const nhomDangChon = Object.entries(dangLoc).filter(([, v]) => v.size > 0)
    if (!nhomDangChon.length) return ds
    return ds.filter((k) =>
      nhomDangChon.every(([khoa, chon]) =>
        chon.has(khoa === 'khung_gio'
          ? _khungCua(k.khoi_hanh)
          : String(k[NHOM_LOC.find((n) => n.khoa === khoa)?.truong ?? ''] ?? '').trim()),
      ),
    )
  }, [ketQua, dangLoc])

  const doiLoc = (nhom: string, gt: string) =>
    setDangLoc((truoc) => {
      const chon = new Set(truoc[nhom] ?? [])
      chon.has(gt) ? chon.delete(gt) : chon.add(gt)
      return { ...truoc, [nhom]: chon }
    })

  const soDangChon = Object.values(dangLoc).reduce((s, v) => s + v.size, 0)

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
        // RỘNG HƠN vì giờ có cột bộ lọc bên trái. Khung 680px cũ vừa đủ cho một bảng
        // trơn; nhét thêm bộ lọc vào đó thì cả hai phần đều chật và bảng bị cắt chữ.
        className="goc-cat den-vien-chon mt-8 flex max-h-[calc(100dvh-4.5rem)] w-[min(1040px,97vw)]
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
              <GoiYSanBay />
              <O nhan="Từ" giaTri={tu} datGiaTri={setTu} rong="w-[132px]"
                 goiY="meoarc-san-bay" chuThich="TP HCM" />
              <O nhan="Đến" giaTri={den} datGiaTri={setDen} rong="w-[132px]"
                 goiY="meoarc-san-bay" chuThich="Đà Nẵng" />
              <O nhan="Ngày bay" giaTri={ngay} datGiaTri={setNgay} rong="w-[112px]" />
            </>
          ) : (
            <>
              <GoiYThanhPho />
              <O nhan="Thành phố" giaTri={thanhPho} datGiaTri={setThanhPho} rong="w-[168px]"
                 goiY="meoarc-thanh-pho" chuThich="Đà Nẵng" />
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
                {soDangChon > 0
                  ? `${daLoc.length}/${ketQua.so_ket_qua} chuyến · đang lọc`
                  : `${ketQua.so_ket_qua} kết quả`}
                {' · truy vấn lúc '}{ketQua.thoi_diem}
              </p>

              {/* HAI CỘT: bộ lọc trái, kết quả phải. Bộ lọc nằm CẠNH bảng chứ không
                  nằm trên: đặt trên thì mỗi lần đổi lọc mắt phải chạy xuống tìm lại
                  chỗ cũ, còn cạnh nhau thì thấy bảng đổi ngay lúc bấm. */}
              <div className="flex gap-4">
                {loai === 'bay' && ketQua.bo_loc && (
                  <CotBoLoc boLoc={ketQua.bo_loc} dangLoc={dangLoc} doiLoc={doiLoc}
                            soDangChon={soDangChon} xoaHet={() => setDangLoc({})} />
                )}

                <div className="min-w-0 flex-1">
                  <div className="flex flex-col gap-1.5">
                    {daLoc.map((k, i) => (
                      <div key={i} className="goc-cat-nho goc-cat den-vien flex items-center gap-3 px-3 py-2">
                        {loai === 'bay' ? <DongBay k={k} /> : <DongPhong k={k} />}
                      </div>
                    ))}
                  </div>
                  {daLoc.length === 0 && (
                    // Nói RÕ là do bộ lọc, không phải do chặng không có chuyến — hai
                    // chuyện đó khác hẳn nhau mà bảng rỗng thì nhìn giống hệt.
                    <p className="py-8 text-center text-[12.5px] text-muted-foreground">
                      Không chuyến nào khớp bộ lọc.{' '}
                      <button onClick={() => setDangLoc({})}
                              className="text-[var(--spark)] underline">Bỏ lọc</button>
                    </p>
                  )}
                </div>
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

/** Cột bộ lọc — dựng TỪ dữ liệu máy chủ trả về, không gõ cứng.
 *
 *  Mỗi ô kèm SỐ CHUYẾN. Con số đó làm hai việc cùng lúc: cho biết trước bấm vào sẽ
 *  còn lại bao nhiêu, và chứng minh ô lọc này có thật — không ô nào bấm vào ra rỗng.
 *
 *  Chỉ có 5 nhóm vì nguồn chỉ cho 5 loại dữ liệu lọc được. Không có ô lọc GIÁ, vì
 *  AeroDataBox không bán vé nên không có giá — thêm một ô lọc không có dữ liệu đằng
 *  sau là hứa suông với người dùng. */
function CotBoLoc({ boLoc, dangLoc, doiLoc, soDangChon, xoaHet }: {
  boLoc: BoLoc
  dangLoc: Record<string, Set<string>>
  doiLoc: (nhom: string, gt: string) => void
  soDangChon: number
  xoaHet: () => void
}) {
  const coGiDeLoc = NHOM_LOC.some((n) => (boLoc[n.khoa]?.length ?? 0) > 1)
  if (!coGiDeLoc) return null   // một hãng, một nhà ga → cột lọc chỉ tổ chiếm chỗ

  return (
    // DÍNH THEO CUỘN. Danh sách bên phải có thể dài vài chục chuyến; cuộn xuống mà bộ
    // lọc trôi mất thì muốn đổi một ô lọc lại phải cuộn ngược lên đầu — và sau khi bấm
    // thì mất luôn chỗ đang xem. `self-start` là bắt buộc: mặc định của flex là kéo
    // con giãn hết chiều cao, mà một phần tử cao bằng cả cha thì `sticky` không có gì
    // để trượt bên trong, nên nó đứng im một cách vô hại và rất khó nhận ra là hỏng.
    <aside className="sticky top-0 z-10 max-h-[62vh] w-[196px] shrink-0 self-start
                      overflow-y-auto scrollbar-thin pr-3">
      {/* Nền kính + viền cắt góc — cùng chất liệu với phần còn lại của app, thay cho
          một cột trắng trơn có mỗi đường kẻ dọc. */}
      <div className="goc-cat-nho goc-cat den-vien glass p-2.5"
           style={{ position: 'relative' }}>
      <div className="mb-2.5 flex items-baseline justify-between gap-2">
        <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground/70">
          Bộ lọc
        </span>
        {soDangChon > 0 && (
          <button
            onClick={xoaHet}
            className="rounded-full bg-[var(--spark)]/15 px-2 py-0.5 font-mono text-[9.5px] font-semibold uppercase tracking-[0.08em] text-[var(--spark)] transition-colors hover:bg-[var(--spark)]/25"
          >
            Xoá {soDangChon}
          </button>
        )}
      </div>

      <div className="flex flex-col gap-3">
        {NHOM_LOC.map((nhom) => {
          const muc = boLoc[nhom.khoa] ?? []
          // Nhóm chỉ có MỘT giá trị thì lọc theo nó là vô nghĩa — bấm vào không bớt
          // được chuyến nào. Ẩn đi để cột lọc chỉ chứa thứ dùng được.
          if (muc.length < 2) return null
          const chon = dangLoc[nhom.khoa] ?? new Set<string>()
          return (
            <div key={nhom.khoa}>
              <p className="mb-1 font-mono text-[9px] uppercase tracking-[0.14em] text-muted-foreground/60">
                {nhom.ten}
              </p>
              <div className="flex flex-col gap-0.5">
                {muc.map((m) => {
                  const dangBat = chon.has(m.gia_tri)
                  return (
                    <button
                      key={m.gia_tri}
                      onClick={() => doiLoc(nhom.khoa, m.gia_tri)}
                      aria-pressed={dangBat}
                      className={cn(
                        'group flex items-center gap-2 rounded-lg px-2 py-1.5 text-left',
                        'text-[11.5px] transition-all duration-150 ease-spring',
                        dangBat
                          ? 'bg-[var(--spark)]/15 font-medium text-foreground shadow-subtle'
                          : 'text-foreground/80 hover:bg-foreground/[0.06]',
                      )}
                    >
                      {/* Chấm trạng thái: bật/tắt phải nhận ra được bằng HÌNH, không chỉ
                          bằng sắc nền — nền nhạt trên kính mờ rất khó thấy ở màn sáng. */}
                      <span className={cn(
                        'size-1.5 shrink-0 rounded-full transition-all',
                        dangBat ? 'bg-[var(--spark)] shadow-[0_0_6px_var(--spark)]'
                                : 'bg-foreground/20 group-hover:bg-foreground/40',
                      )} />
                      <span className="min-w-0 flex-1 truncate">{m.ten ?? m.gia_tri}</span>
                      <span className={cn(
                        'shrink-0 rounded px-1 font-mono text-[9.5px] tabular-nums',
                        dangBat ? 'bg-[var(--spark)]/20 text-[var(--spark)]'
                                : 'text-muted-foreground/70',
                      )}>
                        {m.so_chuyen}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
      </div>
    </aside>
  )
}

/** Danh sách sân bay để gợi ý. Nhúng thẳng vào giao diện thay vì gọi máy chủ:
 *  ô gợi ý phải hiện NGAY lúc người dùng gõ chữ đầu tiên, mà chờ một vòng mạng thì
 *  danh sách bật lên sau khi họ đã gõ xong — tức là vô dụng. Bảng đầy đủ vẫn nằm ở
 *  máy chủ (`/tra-cuu/san-bay`) và nó mới là nơi quyết định mã cuối cùng. */
const SAN_BAY_GOI_Y = [
  ['SGN', 'TP HCM'], ['HAN', 'Hà Nội'], ['DAD', 'Đà Nẵng'], ['CXR', 'Nha Trang'],
  ['PQC', 'Phú Quốc'], ['HPH', 'Hải Phòng'], ['HUI', 'Huế'], ['DLI', 'Đà Lạt'],
  ['VCA', 'Cần Thơ'], ['UIH', 'Quy Nhơn'], ['VII', 'Vinh'], ['VDO', 'Vân Đồn'],
  ['BMV', 'Buôn Ma Thuột'], ['THD', 'Thanh Hoá'], ['VDH', 'Đồng Hới'],
  ['BKK', 'Bangkok'], ['SIN', 'Singapore'], ['ICN', 'Seoul'], ['NRT', 'Tokyo'],
] as const

function O({ nhan, giaTri, datGiaTri, rong, goiY, chuThich }: {
  nhan: string; giaTri: string; datGiaTri: (v: string) => void; rong: string
  goiY?: string; chuThich?: string
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted-foreground/60">
        {nhan}
      </span>
      <input
        value={giaTri}
        onChange={(e) => datGiaTri(e.target.value)}
        list={goiY}
        placeholder={chuThich}
        className={cn('rounded-lg border border-border/40 bg-background/50 px-2.5 py-1.5',
          'text-[12.5px] outline-none focus:border-[var(--spark)]', rong)}
      />
    </label>
  )
}

/** Gợi ý sân bay dùng chung cho ô "Từ" và "Đến".
 *
 *  Người dùng gõ TÊN THÀNH PHỐ, máy chủ đổi sang mã. Bản trước ép ô nhập thành 3 ký
 *  tự viết hoa, tức là bắt họ tự biết "Nội Bài là HAN" — phải mở Google tra mã rồi
 *  quay lại gõ, nên công cụ chưa tiết kiệm được gì cho họ. */
function GoiYSanBay() {
  return (
    <datalist id="meoarc-san-bay">
      {SAN_BAY_GOI_Y.map(([ma, ten]) => (
        <option key={ma} value={ten}>{`${ten} · ${ma}`}</option>
      ))}
    </datalist>
  )
}

/** Thành phố gợi ý cho ô tìm chỗ ở. Nhóm CÓ KHÁCH SẠN THẬT lên trước — người dùng
 *  chọn từ trên xuống, nên thứ tự này quyết định thứ họ nhìn thấy đầu tiên.
 *  Bắt gõ đủ tên thành phố mới tra được là bắt họ làm việc của máy, cùng lỗi đã sửa
 *  ở ô sân bay. */
const TP_CO_KS_THAT = [
  'Đà Nẵng', 'TP HCM', 'Hà Nội', 'Nha Trang', 'Phú Quốc', 'Đà Lạt', 'Hội An',
  'Huế', 'Hạ Long', 'Vũng Tàu', 'Sa Pa', 'Quy Nhơn', 'Mũi Né', 'Cần Thơ', 'Hải Phòng',
]
const TP_KHAC = [
  'Buôn Ma Thuột', 'Pleiku', 'Vinh', 'Thanh Hoá', 'Ninh Bình', 'Phan Thiết',
  'Biên Hoà', 'Mỹ Tho', 'Rạch Giá', 'Cà Mau', 'Côn Đảo', 'Cát Bà',
]

function GoiYThanhPho() {
  return (
    <datalist id="meoarc-thanh-pho">
      {TP_CO_KS_THAT.map((t) => (
        <option key={t} value={t}>{`${t} · có khách sạn thật`}</option>
      ))}
      {TP_KHAC.map((t) => <option key={t} value={t} />)}
    </datalist>
  )
}

export function DongBay({ k }: { k: Record<string, unknown> }) {
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

export function DongPhong({ k }: { k: Record<string, unknown> }) {
  const tong = Number(k.tong_vnd ?? 0)

  return (
    <div className="w-full">
      <div className="flex items-center gap-3">
        {/* 0 = Amadeus KHÔNG trả số sao ở endpoint này. Hiện "—" chứ không hiện "0★":
            "0 sao" là một khẳng định về chất lượng, còn "—" là thú nhận không biết. */}
        <span className="w-9 shrink-0 text-center font-mono text-[12px] font-semibold text-[var(--spark)]">
          {Number(k.so_sao) > 0 ? `${k.so_sao}★` : '—'}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5">
            <span className="min-w-0 truncate text-[12.5px] font-medium">{String(k.ten)}</span>
            {/* Cơ sở CÓ THẬT: tên, hạng sao, vị trí đều kiểm chứng được. Giá thì vẫn mô
                phỏng, nên nhãn phải nói ĐÚNG phần nào thật — gộp thành "dữ liệu thật"
                là nói quá về chính con số người dùng ra quyết định dựa vào. */}
            {k.ten_that === true && (
              <span
                title="Tên, hạng sao và vị trí là thật — giá phòng là số mô phỏng"
                className="shrink-0 cursor-help rounded-full bg-[var(--rr-hoan,#0E8F63)]/15 px-1.5 py-px font-mono text-[9px] font-semibold uppercase tracking-[0.06em] text-[var(--rr-hoan,#0E8F63)]"
              >
                thật
              </span>
            )}
          </span>
          <span className="block truncate text-[11px] text-muted-foreground">
            {String(k.so_dem)} đêm · cách trung tâm {String(k.cach_trung_tam_km)} km
            {' · '}{k.huy_mien_phi ? 'huỷ miễn phí' : 'không huỷ được'}
          </span>
        </span>
        <span className="shrink-0 text-right">
          <span className="block font-mono text-[12.5px] font-semibold tabular-nums">
            {tong.toLocaleString('vi-VN')} ₫
          </span>
          {/* MỘT đường dẫn duy nhất. Trước đây có thêm nút bung bản đồ ngay trong thẻ,
              nhưng nó chiếm gần 200px chiều cao cho mỗi khách sạn — so năm chỗ với nhau
              thì phải cuộn nhiều hơn hẳn, mà thứ cần so (sao, giá, khoảng cách) lại bị
              đẩy ra khỏi màn hình. Bấm "Chi tiết" mở Google kèm ĐÚNG ngày nhận/trả
              phòng: có bản đồ, có ảnh, có giá thật — nhiều hơn hẳn một khung nhúng. */}
          {typeof k.lien_ket === 'string' && (
            <a
              href={k.lien_ket}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-0.5 flex items-center justify-end gap-1 text-[10.5px] text-[var(--spark)] hover:underline"
            >
              Chi tiết <ExternalLink className="size-2.5" />
            </a>
          )}
        </span>
      </div>

    </div>
  )
}
