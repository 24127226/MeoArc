import { useEffect, useRef, useState, type ReactElement } from 'react'
import { motion, useScroll, useSpring, useTransform, useReducedMotion, type MotionValue } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

/* ══════════════════════════════════════════════════════════════════════════════
   HÀNH TRÌNH LÁ THƯ — khung điện ảnh cắt góc bát giác.

   ĐÃ BỎ VIDEO Ở KHỐI NÀY. Trước đây nền là một đoạn phim được tua theo vị trí
   cuộn. Nó ngốn băng thông, phải phủ hai lớp đen lên trên mới đọc được chữ, và
   chính hai lớp đen đó kéo cả trang xuống tối. Đoạn phim ấy giờ chỉ còn ở nút
   bấm cuối trang, nơi nó đứng một mình và được nhìn tử tế.

   Thay vào đó là một SÂN KHẤU NEON dựng bằng CSS: sàn lưới chạy xa dần, hai vệt
   đèn quét, và một vầng sáng chân trời ĐỔI MÀU THEO CHẶNG — chặng 01 tím, 02 hổ
   phách, 03 lam, 04 hồng. Nhờ vậy màu nền tự kể chuyện lá thư đi tới đâu, mà
   không cần một byte video nào, và sáng hơn hẳn vì không còn lớp phủ tối.
   ══════════════════════════════════════════════════════════════════════════════ */

/** Đoạn phim hành trình — GIỜ CHỈ DÙNG cho khối kêu gọi cuối trang (landing.tsx). */
export const JOURNEY_VIDEO =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260717_120352_eb988725-1351-43b3-8095-16e4a1005e3d.mp4'

const STAGES = [
  { no: '01', glow: '#9D7BFF', tag: 'Soạn thảo', line: 'Bạn nói một câu.',      cta: 'Bạn duyệt' },
  { no: '02', glow: '#FFB03A', tag: 'Niêm phong', line: 'Mèo chờ bạn gật đầu.', cta: 'Lên đường' },
  { no: '03', glow: '#4FE9FF', tag: 'Truyền đi', line: 'Thư băng qua đêm.',     cta: 'Đến nơi' },
  { no: '04', glow: '#FF6FB5', tag: 'Đã giao',   line: 'Thư đến tay người nhận.', cta: 'Xem MeoArc làm được gì' },
]

const BOUNDS: [number, number][] = [[0, 0.26], [0.26, 0.52], [0.52, 0.78], [0.78, 1.01]]

/** Logo Thư Mèo dạng khối — bốn góc phần tư xoay quanh tâm, gợi phong thư gấp. */
function VortexMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 256 256" className={className} fill="currentColor" aria-hidden>
      <path d="M120 8h16v104h-16z" />
      <path d="M120 144h16v104h-16z" />
      <path d="M8 120h104v16H8z" />
      <path d="M144 120h104v16h-104z" />
      <path d="M128 40a88 88 0 0 1 88 88h-24a64 64 0 0 0-64-64z" opacity="0.55" />
      <path d="M128 216a88 88 0 0 1-88-88h24a64 64 0 0 0 64 64z" opacity="0.55" />
    </svg>
  )
}


/* ══ HÌNH TƯỢNG TRƯNG CHO TỪNG CHẶNG ══════════════════════════════════════════
   Bốn hình vẽ nét, cùng khung 120×120, cùng độ dày nét. Vẽ tay chứ không dùng bộ
   icon có sẵn vì bộ icon nào cũng chỉ có "phong bì" chung chung — ở đây cần bốn
   TRẠNG THÁI khác nhau của cùng một lá thư, và người xem phải nhận ra ngay đó là
   cùng một lá thư đang đi qua bốn chặng.

   Nét dùng currentColor nên tự ăn theo màu đèn của chặng; lớp glow là chính hình
   đó vẽ lại lần nữa, nhoè và dày hơn, đặt phía sau.                             */
const GLYPH: Record<string, ReactElement> = {
  // 01 — Ngòi bút đang viết: thư mới thành hình, mấy dòng chữ hiện dần
  '01': (
    <g>
      <rect x="26" y="18" width="58" height="76" rx="4" />
      <path d="M38 40h30M38 52h34M38 64h22" opacity="0.55" />
      <path d="M74 84l18-18a5 5 0 0 0-7-7L67 77l-3 10z" />
    </g>
  ),
  // 02 — Phong bì niêm phong + dấu tick: chỗ MeoArc dừng lại xin phép
  '02': (
    <g>
      <rect x="16" y="30" width="88" height="60" rx="5" />
      <path d="M16 34l44 32 44-32" opacity="0.55" />
      <circle cx="60" cy="62" r="15" />
      <path d="M53 62l5 5 10-11" />
    </g>
  ),
  // 03 — Thư bay theo cung, có các nút mạng: đang truyền qua Gmail / Graph
  '03': (
    <g>
      <path d="M12 84C30 40 74 22 108 30" strokeDasharray="6 7" opacity="0.6" />
      <path d="M52 40l30 12-30 12 6-12z" />
      <circle cx="12" cy="84" r="5" />
      <circle cx="108" cy="30" r="5" />
    </g>
  ),
  // 04 — Phong bì đã mở, thư trồi lên, có tick: hành trình khép lại
  '04': (
    <g>
      <path d="M18 54l42-28 42 28v40a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z" />
      <rect x="38" y="14" width="44" height="44" rx="4" />
      <path d="M50 32l7 7 14-15" />
      <path d="M18 54l42 30 42-30" opacity="0.55" />
    </g>
  ),
}

/** Hình chặng — vẽ hai lần: một lớp nhoè làm quầng đèn, một lớp nét sắc phía trên. */
function StageGlyph({ no, color }: { no: string; color: string }) {
  const g = GLYPH[no]
  const common = {
    viewBox: '0 0 120 120', fill: 'none', stroke: 'currentColor',
    strokeWidth: 2.2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
  }
  return (
    <div key={no} className="anim-fade relative size-[132px] sm:size-[168px] md:size-[196px]"
      style={{ color }}>
      {/* Quầng đèn: chính hình đó, nét dày gấp ba và nhoè mạnh */}
      <svg {...common} aria-hidden
        className="absolute inset-0 size-full opacity-90"
        style={{ filter: 'blur(11px)', strokeWidth: 6 }}>{g}</svg>
      {/* Nét sắc — trắng ngả về màu đèn, để hình luôn đọc được rõ */}
      <svg {...common} aria-hidden className="absolute inset-0 size-full"
        style={{ color: 'color-mix(in srgb, ' + color + ' 35%, #ffffff)' }}>{g}</svg>
    </div>
  )
}

export function LetterTale() {
  const reduced = useReducedMotion()
  const ref = useRef<HTMLDivElement>(null)
  const [stage, setStage] = useState(0)

  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const p = useSpring(scrollYProgress, { stiffness: 80, damping: 26, restDelta: 0.0005 })

  // Chặng hiện tại theo tiến độ cuộn
  useEffect(() => {
    const un = p.on('change', (v) => {
      const idx = BOUNDS.findIndex(([a, b]) => v >= a && v < b)
      setStage(idx < 0 ? BOUNDS.length - 1 : idx)
    })
    return () => un()
  }, [p])

  const cur = STAGES[stage]

  if (reduced) {
    return (
      <div className="mt-12 grid gap-4 px-6 sm:grid-cols-2 lg:grid-cols-4">
        {STAGES.map((s) => (
          // Nhanh khong-chuyen-dong: van la HINH dan dat, khong quay ve tuong chu
          <div key={s.no} className="lit-edge flex flex-col items-center rounded-2xl bg-white/[0.03] p-6 text-center"
            style={{ ['--lit' as string]: s.glow }}>
            <StageGlyph no={s.no} color={s.glow} />
            <span className="mt-4 font-mono text-xs" style={{ color: s.glow }}>{s.no}</span>
            <span className="mt-1 text-[11px] font-medium uppercase tracking-[0.28em] text-white/75">{s.tag}</span>
            <p className="mt-3 text-[15px] leading-relaxed text-white/90">{s.line}</p>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div ref={ref} className="relative h-[340vh]">
      <div className="sticky top-0 h-screen w-full bg-black p-3 md:p-4">
        {/* Khung điện ảnh bo góc — video nằm sau, nội dung nổi trên */}
        <div className="relative flex h-full w-full flex-col overflow-hidden rounded-2xl bg-black">
          {/* ══ SÂN KHẤU NEON — thay chỗ đoạn phim cũ ══
              Bốn tầng, xếp từ xa tới gần. Tất cả đều ăn theo màu `cur.glow` nên khi
              sang chặng mới cả sân khấu đổi màu trong 1.2s, đủ chậm để thấy là một
              chuyển cảnh chứ không phải một cú nháy. */}
          <div aria-hidden className="absolute inset-0 overflow-hidden bg-[#04030A]"
            style={{ ['--g' as string]: cur.glow, transition: 'none' }}>

            {/* 1 — VẦNG SÁNG CHÂN TRỜI. Nguồn sáng chính. Đặt thấp và rộng để ánh
                 sáng hắt NGƯỢC LÊN chữ, kiểu đèn sân khấu rọi từ dưới. */}
            <div className="lt-fade absolute inset-x-0 bottom-0 h-[62%]"
              style={{
                background:
                  'radial-gradient(120% 100% at 50% 100%, color-mix(in srgb, var(--g) 85%, transparent) 0%, ' +
                  'color-mix(in srgb, var(--g) 34%, transparent) 32%, transparent 68%)',
              }} />

            {/* 2 — SÀN LƯỚI CHẠY XA DẦN. Kẻ ngang giãn dần + kẻ dọc toả ra tạo phối
                 cảnh một mặt sàn. Đây là thứ làm khung hình "ra chất công nghệ". */}
            <div className="lt-floor absolute inset-x-0 bottom-0 h-[46%]"
              style={{
                backgroundImage:
                  'repeating-linear-gradient(to bottom, color-mix(in srgb, var(--g) 95%, transparent) 0 1.5px, transparent 1.5px 54px),' +
                  'repeating-linear-gradient(to right, color-mix(in srgb, var(--g) 72%, transparent) 0 1.5px, transparent 1.5px 76px)',
                // rotateX 74deg + perspective 320px ep san thanh mot soi ~2px: nhin
                // ra man hinh la khong thay gi. Ha goc xuong 58deg va noi rong
                // perspective de con do sau ma van con be mat de nhin.
                maskImage: 'linear-gradient(to top, #000 0%, rgba(0,0,0,0.55) 45%, transparent 88%)',
                WebkitMaskImage: 'linear-gradient(to top, #000 0%, rgba(0,0,0,0.55) 45%, transparent 88%)',
                transform: 'perspective(520px) rotateX(58deg) scale(1.45)',
                transformOrigin: 'bottom center',
              }} />

            {/* 3 — HAI VỆT ĐÈN QUÉT chéo qua khung, lệch pha nhau để không đập nhịp. */}
            <div className="lt-beam absolute -left-1/3 top-[-30%] h-[170%] w-[46%] rotate-[18deg]"
              style={{ background: 'linear-gradient(90deg, transparent, color-mix(in srgb, var(--g) 30%, transparent), transparent)' }} />
            <div className="lt-beam absolute -right-1/4 top-[-30%] h-[170%] w-[34%] -rotate-[14deg]"
              style={{ animationDelay: '-5s', background: 'linear-gradient(90deg, transparent, color-mix(in srgb, #ffffff 22%, transparent), transparent)' }} />

            {/* 4 — VIỀN HẮT SÁNG quanh mép khung. Chính chi tiết này khiến mắt đọc ra
                 "đèn neon" chứ không phải "nền tối màu": ánh sáng phải chạm được vào
                 một CẠNH thì mới có gì để phản chiếu. */}
            <div className="absolute inset-0 rounded-2xl"
              style={{
                boxShadow:
                  'inset 0 0 1px 1px color-mix(in srgb, var(--g) 70%, transparent),' +
                  'inset 0 0 60px -12px color-mix(in srgb, var(--g) 55%, transparent),' +
                  'inset 0 -90px 120px -70px color-mix(in srgb, var(--g) 80%, transparent)',
              }} />
          </div>

          {/* Lớp làm trầm: CHỈ 18% và chỉ ở giữa, vừa đủ cho chữ trắng đạt tương phản.
              Bản cũ phủ 45% toàn khung + một lớp radial 75% nữa — hai lớp đó là lý do
              chính khiến trang bị chê tối. Bỏ video thì cũng không cần phủ dày như thế. */}
          <div aria-hidden className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,0,0,0.42)_0%,transparent_72%)]" />

          {/* ── Thanh trên: nhãn thương hiệu + hai nút cắt góc ── */}
          <nav className="relative z-10 flex items-start justify-between px-6 pt-6 md:px-10 md:pt-8">
            <div className="anim-stagger" style={{ animationDelay: '0.1s' }}>
              <VortexMark className="size-12 text-white md:size-14" />
              <span className="mt-1 block text-[10px] font-light tracking-[0.4em] text-white md:text-xs">
                M E O A R C
              </span>
            </div>
            <div className="anim-stagger flex items-center gap-3" style={{ animationDelay: '0.2s' }}>
              <button className="btn-cut-border hidden px-5 py-2.5 text-sm text-white transition-colors hover:bg-white/10 md:block">
                <span>Hành trình lá thư</span>
              </button>
              <button
                onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })}
                className="btn-cut hidden bg-white px-5 py-2.5 text-sm text-black transition-colors hover:bg-white/90 md:block"
              >
                Bắt đầu dùng
              </button>
            </div>
          </nav>

          {/* ── Nội dung chính ──
              Bản cũ có BỐN khối chữ cùng lúc: ghi chú cột trái, tiêu đề ba dòng cỡ
              lớn, tên chặng, và đoạn mô tả dưới. Mắt không biết đọc đâu trước nên
              rốt cuộc không đọc gì, và khối này thành ra một bức tường chữ.

              Bản này để HÌNH nói: một hình vẽ nét lớn phát sáng ở giữa cho biết lá
              thư đang ở trạng thái nào, và đúng MỘT dòng chữ ngắn bên dưới. Người
              xem nắm được chặng chỉ bằng liếc mắt, không phải bằng đọc. */}
          <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 pb-8 md:px-10 md:pb-10">

            {/* Hình tượng trưng — nhân vật chính của khung hình */}
            <StageGlyph no={cur.no} color={cur.glow} />

            {/* Tên chặng: số + một chữ, cỡ nhỏ, để không tranh với hình */}
            <div className="anim-fade mt-7 flex items-center gap-3">
              <span className="font-mono text-xs tabular-nums" style={{ color: cur.glow }}>{cur.no}</span>
              <span className="h-3 w-px bg-white/25" />
              <span className="text-[11px] font-medium uppercase tracking-[0.32em] text-white/80">
                {cur.tag}
              </span>
            </div>

            {/* Dòng chữ DUY NHẤT của chặng */}
            <StageLine p={p} />

            {/* Chỉ báo chặng — bốn vạch, vạch đang chạy sáng lên và dài ra */}
            <div className="anim-fade mt-10 flex items-center gap-2">
              {STAGES.map((st, i) => (
                <span key={st.no}
                  className={cn('h-[3px] rounded-full transition-all duration-700',
                    i === stage ? 'w-10' : 'w-5 bg-white/20')}
                  style={i === stage
                    ? { background: st.glow, boxShadow: `0 0 12px 1px ${st.glow}` }
                    : undefined} />
              ))}
            </div>

            {/* Một nút duy nhất, chỉ hiện ở chặng cuối — trước đó nút chỉ làm nhiễu */}
            {stage === STAGES.length - 1 && (
              <button
                onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })}
                className="anim-fade btn-cut group mt-8 flex items-center justify-center gap-2 bg-white px-7 py-3.5 text-black transition-colors hover:bg-white/90"
              >
                <span className="text-sm font-medium">{cur.cta}</span>
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
              </button>
            )}
          </div>

          {/* Thanh tiến độ của riêng khối này */}
          <motion.div aria-hidden style={{ scaleX: p }}
            className="absolute inset-x-0 bottom-0 z-20 h-[2px] origin-left bg-white/70" />
        </div>
      </div>
    </div>
  )
}

/** Một dòng chữ duy nhất mỗi chặng, mờ vào/mờ ra theo tiến độ cuộn. */
function StageLine({ p }: { p: MotionValue<number> }) {
  return (
    <div className="relative mx-auto h-[4.5rem] w-full max-w-3xl sm:h-[5.5rem]">
      {STAGES.map((s, i) => (
        <LineLayer key={s.no} p={p} index={i} text={s.line} />
      ))}
    </div>
  )
}

function LineLayer({ p, index, text }: { p: MotionValue<number>; index: number; text: string }) {
  const [a, b] = BOUNDS[index]
  const f = 0.05
  const opacity = useTransform(p, [a - f, a + f, b - f, b + f], [0, 1, 1, 0], { clamp: true })
  const y = useTransform(p, [a - f, a + f, b - f, b + f], [22, 0, 0, -22], { clamp: true })
  return (
    <motion.h2
      style={{ opacity, y, textShadow: '0 2px 16px rgba(0,0,0,0.55)' }}
      className="absolute inset-0 flex items-center justify-center text-center text-2xl font-normal leading-tight tracking-[-0.03em] text-white sm:text-3xl md:text-4xl"
    >
      {text}
    </motion.h2>
  )
}
