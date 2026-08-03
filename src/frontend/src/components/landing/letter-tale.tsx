import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useSpring, useTransform, useReducedMotion, type MotionValue } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

/* ══════════════════════════════════════════════════════════════════════════════
   HÀNH TRÌNH LÁ THƯ — khung điện ảnh cắt góc bát giác.

   Điểm cốt lõi về trải nghiệm: video KHÔNG tự chạy một mạch. Nó được TUA theo
   đúng vị trí cuộn (video scrubbing) — người dùng kéo tới đâu, hình chạy tới đó,
   dừng tay thì hình đứng lại. Nhờ vậy đoạn phim và bốn chặng của lá thư luôn khớp
   nhau, và người đọc chậm không bị phim "chạy mất".

   Kỹ thuật: gán video.currentTime = tiến-độ-cuộn × thời-lượng, làm mượt bằng lò xo
   rồi ghi trong vòng lặp rAF (đặt currentTime trực tiếp mỗi lần cuộn sẽ giật).
   ══════════════════════════════════════════════════════════════════════════════ */

const JOURNEY_VIDEO =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260717_120352_eb988725-1351-43b3-8095-16e4a1005e3d.mp4'
const FALLBACK_VIDEO = '/landing/purple-desert.mp4'

const STAGES = [
  {
    no: '01',
    tag: 'Soạn thảo',
    heading: ['Bạn nói một câu', 'Mèo cầm bút lên', 'Thư thành hình'],
    side: 'Một câu tiếng Việt là đủ.\nMèo hiểu ngữ cảnh\nvà viết thay bạn.',
    body: 'MeoArc đọc lại cuộc trò chuyện, chọn giọng văn hợp với người nhận rồi dựng sẵn nội dung.',
    cta: 'Chặng kế: bạn duyệt',
  },
  {
    no: '02',
    tag: 'Niêm phong',
    heading: ['Thư nằm im', 'Chờ bạn gật đầu', 'Rồi mới đóng dấu'],
    side: 'Dấu sáp không tự\nđóng xuống. Quyền\nquyết định là của bạn.',
    body: 'Đây là chỗ MeoArc khác các trợ lý khác: mọi việc không hoàn tác được đều dừng lại xin phép.',
    cta: 'Chặng kế: lên đường',
  },
  {
    no: '03',
    tag: 'Truyền đi',
    heading: ['Thư rời bàn', 'Băng qua đêm', 'Tới máy chủ thư'],
    side: 'Gmail API hay\nMicrosoft Graph —\nbạn không phải bận tâm.',
    body: 'Cùng một thao tác cho cả hai nhà cung cấp. Thư đi bằng đường nào là việc của MeoArc.',
    cta: 'Chặng cuối: đến nơi',
  },
  {
    no: '04',
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
  const videoRef = useRef<HTMLVideoElement>(null)
  const [src, setSrc] = useState(JOURNEY_VIDEO)
  const [stage, setStage] = useState(0)

  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const p = useSpring(scrollYProgress, { stiffness: 80, damping: 26, restDelta: 0.0005 })

  // ── TUA VIDEO THEO CUỘN ──
  // Ghi currentTime trong vòng lặp rAF thay vì ngay trong sự kiện cuộn: trình duyệt
  // chỉ tua được vài lần mỗi giây, gọi dồn dập sẽ khựng hình.
  useEffect(() => {
    if (reduced) return
    let raf = 0
    let last = -1
    const loop = () => {
      const v = videoRef.current
      if (v && v.readyState >= 2 && Number.isFinite(v.duration)) {
        const t = Math.min(v.duration - 0.05, Math.max(0, p.get() * v.duration))
        if (Math.abs(t - last) > 0.03) {
          v.currentTime = t
          last = t
        }
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [p, reduced])

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
          <video
            ref={videoRef}
            key={src}
            src={src}
            muted
            playsInline
            preload="auto"
            onError={() => setSrc((s) => (s === JOURNEY_VIDEO ? FALLBACK_VIDEO : s))}
            className="anim-fade absolute inset-0 size-full object-cover"
            style={{ animationDelay: '0.2s' }}
          />
          {/* Làm trầm hình để chữ trắng luôn đọc được */}
          <div aria-hidden className="absolute inset-0 bg-black/45" />
          <div aria-hidden className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_25%,rgba(0,0,0,0.75)_100%)]" />

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
