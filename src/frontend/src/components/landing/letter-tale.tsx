import { useEffect, useRef, useState } from 'react'
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
  {
    no: '01',
    glow: '#9D7BFF',
    tag: 'Soạn thảo',
    heading: ['Bạn nói một câu', 'Mèo cầm bút lên', 'Thư thành hình'],
    side: 'Một câu tiếng Việt là đủ.\nMèo hiểu ngữ cảnh\nvà viết thay bạn.',
    body: 'MeoArc đọc lại cuộc trò chuyện, chọn giọng văn hợp với người nhận rồi dựng sẵn nội dung.',
    cta: 'Chặng kế: bạn duyệt',
  },
  {
    no: '02',
    glow: '#FFB03A',
    tag: 'Niêm phong',
    heading: ['Thư nằm im', 'Chờ bạn gật đầu', 'Rồi mới đóng dấu'],
    side: 'Dấu sáp không tự\nđóng xuống. Quyền\nquyết định là của bạn.',
    body: 'Đây là chỗ MeoArc khác các trợ lý khác: mọi việc không hoàn tác được đều dừng lại xin phép.',
    cta: 'Chặng kế: lên đường',
  },
  {
    no: '03',
    glow: '#4FE9FF',
    tag: 'Truyền đi',
    heading: ['Thư rời bàn', 'Băng qua đêm', 'Tới máy chủ thư'],
    side: 'Gmail API hay\nMicrosoft Graph —\nbạn không phải bận tâm.',
    body: 'Cùng một thao tác cho cả hai nhà cung cấp. Thư đi bằng đường nào là việc của MeoArc.',
    cta: 'Chặng cuối: đến nơi',
  },
  {
    no: '04',
    glow: '#FF6FB5',
    tag: 'Đã giao',
    heading: ['Thư đến tay', 'Người nhận mở ra', 'Hành trình khép lại'],
    side: 'Một bản lưu trong\nmục Đã gửi. Một dòng\ntrong nhật ký.',
    body: 'Bạn luôn tra lại được: gửi cho ai, lúc nào, do bạn duyệt hay do bạn tự bấm.',
    cta: 'Xem MeoArc làm được gì',
  },
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
          <div key={s.no} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <span className="font-mono text-4xl font-bold text-white/15">{s.no}</span>
            <h3 className="mt-3 font-serif text-lg font-bold">{s.heading.join(' · ')}</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-white/55">{s.body}</p>
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

          {/* ── Nội dung chính ── */}
          <div className="relative z-10 flex flex-1 flex-col justify-between px-6 pb-8 md:px-10 md:pb-10">
            <div className="relative flex flex-1 items-center">
              {/* Cột trái — chú thích chặng */}
              <div className="anim-stagger absolute left-0 top-[18%] hidden flex-col gap-6 lg:flex"
                style={{ animationDelay: '0.4s' }}>
                <p className="max-w-[220px] whitespace-pre-line text-base leading-relaxed text-white/80">
                  {cur.side}
                </p>
                <div className="mt-4 flex flex-col gap-2">
                  <div className="flex items-center gap-1">
                    {STAGES.map((s, i) => (
                      <span key={s.no}
                        className={cn('size-4 rounded-full border transition-colors duration-500',
                          i === stage ? 'border-white bg-white/80' : 'border-white/40')} />
                    ))}
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="whitespace-pre-line text-xs text-white/70">{cur.tag}</span>
                    <span className="font-mono text-xs text-white/50">{cur.no}</span>
                  </div>
                </div>
              </div>

              {/* Tiêu đề giữa — ba dòng, đổi theo chặng */}
              <div className="anim-stagger w-full text-center" style={{ animationDelay: '0.5s' }}>
                <StageHeading p={p} />
              </div>
            </div>

            {/* ── Hàng dưới: mô tả · nút · chỉ báo ── */}
            <div className="mt-8 grid grid-cols-1 items-center gap-6 md:grid-cols-3">
              <div className="anim-stagger flex items-center justify-center md:justify-end"
                style={{ animationDelay: '0.7s' }}>
                <p className="max-w-[260px] text-center text-sm leading-relaxed text-white md:ml-auto md:text-left">
                  {cur.body}
                </p>
              </div>

              <div className="anim-stagger flex flex-col items-center gap-8 md:gap-24"
                style={{ animationDelay: '0.85s' }}>
                <span className="text-2xl font-medium text-white md:text-3xl">{cur.tag}</span>
                <button
                  onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })}
                  className="btn-cut group flex w-full max-w-[280px] items-center justify-center gap-2 bg-white py-3.5 text-black transition-colors hover:bg-white/90"
                >
                  <span className="text-sm font-medium">{cur.cta}</span>
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </button>
              </div>

              <div className="anim-stagger flex items-center justify-center gap-3 md:justify-end"
                style={{ animationDelay: '1s' }}>
                {STAGES.map((s, i) => (
                  <span key={s.no}
                    className={cn(
                      'btn-cut-sm flex size-10 items-center justify-center font-mono text-xs transition-colors duration-500',
                      i === stage ? 'bg-white text-black' : 'bg-white/25 text-white/70',
                    )}>
                    {s.no}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Thanh tiến độ của riêng khối này */}
          <motion.div aria-hidden style={{ scaleX: p }}
            className="absolute inset-x-0 bottom-0 z-20 h-[2px] origin-left bg-white/70" />
        </div>
      </div>
    </div>
  )
}

/** Ba dòng tiêu đề, mỗi chặng mờ vào/mờ ra theo tiến độ cuộn. */
function StageHeading({ p }: { p: MotionValue<number> }) {
  return (
    <div className="relative mx-auto h-[13rem] max-w-4xl sm:h-[15rem] md:h-[17rem] lg:h-[19rem]">
      {STAGES.map((s, i) => (
        <HeadingLayer key={s.no} p={p} index={i} lines={s.heading} />
      ))}
    </div>
  )
}

function HeadingLayer({ p, index, lines }: { p: MotionValue<number>; index: number; lines: string[] }) {
  const [a, b] = BOUNDS[index]
  const f = 0.05
  const opacity = useTransform(p, [a - f, a + f, b - f, b + f], [0, 1, 1, 0], { clamp: true })
  const y = useTransform(p, [a - f, a + f, b - f, b + f], [26, 0, 0, -26], { clamp: true })
  return (
    <motion.h2
      style={{ opacity, y, textShadow: '0 2px 12px rgba(0,0,0,0.45)' }}
      className="absolute inset-0 flex flex-col justify-center text-3xl font-normal leading-[1.1] tracking-[-0.04em] text-white sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl"
    >
      {lines.map((l) => <span key={l}>{l}</span>)}
    </motion.h2>
  )
}
