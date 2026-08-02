import { useEffect, useRef, useState, type ReactNode } from 'react'
import {
  AnimatePresence, motion, useInView, useMotionValue, useMotionTemplate, useSpring, useTransform,
  useScroll, useReducedMotion,
} from 'framer-motion'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

/* ══════════════════════════════════════════════════════════════════════════════
   Bộ chất liệu cho Landing — phong cách Aceternity UI, viết lại bằng CSS/Framer
   cho stack Vite (Aceternity phát hành dạng copy-paste cho Next.js).

   Tham khảo: Spotlight · Aurora Background · Card Spotlight · Moving Border ·
   Container Scroll Animation · Meteors · Text Generate Effect.

   PALETTE (bám theo 3 video/ảnh của dự án — đều là nền tối + nguồn sáng phát quang):
     nền     #06060B  (đen xanh)
     violet  #8B7BF0  ← cánh đồng hoa phát sáng
     cyan    #4FD1C5  ← vệt sáng lam, tượng kim loại
     amber   #F0A848  ← cột sáng trên biển (dùng cho CTA để nổi trên nền lạnh)
   ══════════════════════════════════════════════════════════════════════════════ */

/** Biểu tượng THƯ MÈO — phong thư origami có tai + mặt mèo. */
export function CatLetter({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg viewBox="0 0 64 58" className={className} style={style} fill="none" stroke="currentColor" strokeWidth="1.25"
      strokeLinejoin="round" strokeLinecap="round" aria-hidden>
      <path d="M15 15 10 4 22 11" />
      <path d="M49 15 54 4 42 11" />
      <rect x="6" y="13" width="52" height="40" rx="7" />
      <path d="M6 17 32 37 58 17" />
      <circle cx="24" cy="23" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="40" cy="23" r="1.1" fill="currentColor" stroke="none" />
      <path d="M30.6 26h2.8l-1.4 1.8z" fill="currentColor" stroke="none" />
      <g opacity="0.55"><path d="M13 25h7M13 28h6" /><path d="M51 25h-7M51 28h-6" /></g>
    </svg>
  )
}

/** Hiện dần khi cuộn tới (thay cho AOS). */
export function Reveal({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-15%' })
  const reduced = useReducedMotion()
  return (
    <motion.div
      ref={ref}
      initial={reduced ? false : { opacity: 0, y: 28, filter: 'blur(6px)' }}
      animate={inView ? { opacity: 1, y: 0, filter: 'blur(0px)' } : undefined}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/** Aurora — dải sáng cực quang trôi rất chậm (Aceternity: Aurora Background). */
export function Aurora({ className }: { className?: string }) {
  const reduced = useReducedMotion()
  return (
    <div aria-hidden className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      <div className="absolute -left-[20%] top-[-25%] size-[75vh] rounded-full bg-[#8B7BF0]/25 blur-[140px]"
        style={{ animation: reduced ? undefined : 'ld-drift1 19s ease-in-out infinite' }} />
      <div className="absolute right-[-18%] top-[15%] size-[65vh] rounded-full bg-[#4FD1C5]/18 blur-[140px]"
        style={{ animation: reduced ? undefined : 'ld-drift2 23s ease-in-out infinite' }} />
      <div className="absolute bottom-[-25%] left-[25%] size-[60vh] rounded-full bg-[#F0A848]/12 blur-[150px]"
        style={{ animation: reduced ? undefined : 'ld-drift1 27s ease-in-out infinite' }} />
    </div>
  )
}

/** Spotlight — quầng sáng hình nón phía trên hero (Aceternity: Spotlight). */
export function Spotlight({ className }: { className?: string }) {
  return (
    <svg aria-hidden className={cn('pointer-events-none absolute z-0 opacity-45', className)}
      viewBox="0 0 800 800" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g filter="url(#sp-blur)">
        <ellipse cx="400" cy="180" rx="180" ry="420" transform="rotate(-14 400 180)" fill="#8B7BF0" fillOpacity="0.28" />
      </g>
      <defs><filter id="sp-blur" x="0" y="-260" width="800" height="1100" filterUnits="userSpaceOnUse">
        <feGaussianBlur stdDeviation="110" /></filter></defs>
    </svg>
  )
}

/** Lưới chấm mờ — nền kỹ thuật (Aceternity: Grid and Dot Backgrounds). */
export function DotGrid({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn('pointer-events-none absolute inset-0', className)}
      style={{
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.12) 1px, transparent 1px)',
        backgroundSize: '26px 26px',
        maskImage: 'radial-gradient(ellipse at center, black 20%, transparent 72%)',
        WebkitMaskImage: 'radial-gradient(ellipse at center, black 20%, transparent 72%)',
      }} />
  )
}

/** Card kính: viền sáng chạy + quầng sáng bám con trỏ (Card Spotlight + Border Beam). */
export function SpotCard({ children, className, beam = true }: { children: ReactNode; className?: string; beam?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  const mx = useMotionValue(-500)
  const my = useMotionValue(-500)
  const glow = useMotionTemplate`radial-gradient(340px circle at ${mx}px ${my}px, rgba(139,123,240,0.16), transparent 72%)`
  return (
    <div
      ref={ref}
      onPointerMove={(e) => {
        const r = ref.current?.getBoundingClientRect()
        if (!r) return
        mx.set(e.clientX - r.left)
        my.set(e.clientY - r.top)
      }}
      onPointerLeave={() => { mx.set(-500); my.set(-500) }}
      className={cn(
        'group relative overflow-hidden rounded-3xl border border-white/[0.09] bg-white/[0.03] backdrop-blur-xl',
        beam && 'ld-beam',
        className,
      )}
    >
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -inset-px opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: glow }}
      />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent" />
      {children}
    </div>
  )
}

/** Nút CTA có viền sáng chạy quanh (Aceternity: Moving Border). */
export function MovingBorderButton({
  children, onClick, tone = 'amber', className,
}: { children: ReactNode; onClick?: () => void; tone?: 'amber' | 'ghost'; className?: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'ld-mb relative inline-flex items-center gap-2.5 overflow-hidden rounded-2xl px-7 py-4 text-[15px] font-semibold',
        'transition-transform duration-200 hover:-translate-y-0.5 active:scale-[0.97]',
        tone === 'amber'
          ? 'bg-[#F0A848] text-[#1a1206] shadow-[0_10px_40px_-8px_rgba(240,168,72,0.55)]'
          : 'border border-white/15 bg-white/[0.06] text-white backdrop-blur-md hover:bg-white/[0.1]',
        className,
      )}
    >
      {children}
    </button>
  )
}

/** Số liệu đếm tăng dần khi cuộn tới (không đứng im, đơn điệu). */
export function CountUp({
  to, suffix = '', prefix = '', decimals = 0, duration = 1.6, className,
}: { to: number; suffix?: string; prefix?: string; decimals?: number; duration?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-20%' })
  const reduced = useReducedMotion()
  const [val, setVal] = useState(0)

  useEffect(() => {
    if (!inView) return
    if (reduced) { setVal(to); return }
    let raf = 0
    const t0 = performance.now()
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / (duration * 1000))
      // easeOutExpo — chạy nhanh rồi ghì lại ở cuối, cảm giác "chốt số"
      const e = p === 1 ? 1 : 1 - Math.pow(2, -10 * p)
      setVal(to * e)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [inView, to, duration, reduced])

  return (
    <span ref={ref} className={className}>
      {prefix}
      {val.toLocaleString('vi-VN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  )
}

/** Khung ảnh/mockup nghiêng 3D rồi dựng thẳng khi cuộn (Container Scroll Animation). */
export function ContainerScroll({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'center center'] })
  const rotate = useSpring(useTransform(scrollYProgress, [0, 1], [22, 0]), { stiffness: 120, damping: 26 })
  const scale = useSpring(useTransform(scrollYProgress, [0, 1], [0.88, 1]), { stiffness: 120, damping: 26 })
  return (
    <div ref={ref} className={cn('[perspective:1100px]', className)}>
      <motion.div
        style={reduced ? undefined : { rotateX: rotate, scale }}
        className="origin-top will-change-transform"
      >
        {children}
      </motion.div>
    </div>
  )
}

/** Ảnh có khung kính + quầng sáng — dùng cho bố cục zig-zag. */
export function FramedImage({ src, alt, className, glow = 'violet' }: {
  src: string; alt: string; className?: string; glow?: 'violet' | 'cyan' | 'amber'
}) {
  const [loaded, setLoaded] = useState(false)
  const tint = glow === 'amber' ? 'bg-[#F0A848]/25' : glow === 'cyan' ? 'bg-[#4FD1C5]/25' : 'bg-[#8B7BF0]/25'
  return (
    <div className={cn('relative', className)}>
      <div aria-hidden className={cn('absolute -inset-6 rounded-[2rem] blur-3xl', tint)} />
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03]">
        <div className={cn('absolute inset-0 animate-pulse bg-white/[0.04] transition-opacity duration-700',
          loaded ? 'opacity-0' : 'opacity-100')} />
        <img
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          onLoad={() => setLoaded(true)}
          className={cn('block w-full object-cover transition-all duration-1000',
            loaded ? 'scale-100 opacity-100 blur-0' : 'scale-105 opacity-0 blur-md')}
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#06060B] via-transparent to-transparent opacity-70" />
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
      </div>
    </div>
  )
}

/** Nền video phủ kín + scrim nhiều lớp; có poster hiện ngay để không bị màn đen.
 *  `parallax` = video trôi chậm hơn trang một nhịp → tạo chiều sâu khi cuộn qua. */
export function VideoBackdrop({
  src, poster, className, tint = 'violet', dim = 'strong', parallax = false, play = 'always',
}: {
  src: string; poster: string; className?: string
  tint?: 'violet' | 'amber' | 'cyan' | 'none'; dim?: 'strong' | 'soft' | 'none'
  parallax?: boolean; play?: 'always' | 'inview'
}) {
  const [failed, setFailed] = useState(false)
  const [ready, setReady] = useState(false)
  const ref = useRef<HTMLVideoElement>(null)
  const wrap = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const inView = useInView(wrap, { margin: '10%' })

  useEffect(() => { if (ref.current && ref.current.readyState >= 3) setReady(true) }, [])
  // Chỉ phát khi thấy được → đỡ tốn pin, tránh nhiều video cùng chạy
  useEffect(() => {
    const v = ref.current
    if (!v || play !== 'inview') return
    if (inView) v.play().catch(() => {})
    else v.pause()
  }, [inView, play])

  const { scrollYProgress } = useScroll({ target: wrap, offset: ['start end', 'end start'] })
  const y = useTransform(scrollYProgress, [0, 1], ['-12%', '12%'])

  return (
    <div ref={wrap} aria-hidden className={cn('absolute inset-0 z-0 overflow-hidden', className)}>
      <motion.div className="absolute inset-[-14%]" style={parallax && !reduced ? { y } : undefined}>
        <img src={poster} alt="" className="absolute inset-0 size-full object-cover" />
        {!failed && (
          <video
            ref={ref}
            className={cn('absolute inset-0 size-full object-cover transition-opacity duration-1000',
              ready ? 'opacity-100' : 'opacity-0')}
            src={src} muted loop playsInline preload="auto"
            autoPlay={play === 'always'}
            onCanPlay={() => setReady(true)} onError={() => setFailed(true)}
          />
        )}
      </motion.div>
      {dim !== 'none' && (
        <div className={cn('absolute inset-0 bg-gradient-to-b',
          dim === 'strong' ? 'from-[#06060B]/75 via-[#06060B]/45 to-[#06060B]' : 'from-[#06060B]/45 via-transparent to-[#06060B]')} />
      )}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_25%,rgba(6,6,11,0.75)_100%)]" />
      {tint !== 'none' && (
        <div className={cn('absolute inset-0 mix-blend-soft-light',
          tint === 'amber' ? 'bg-[#F0A848]/25' : tint === 'cyan' ? 'bg-[#4FD1C5]/20' : 'bg-[#8B7BF0]/25')} />
      )}
      <div className="grain-overlay absolute inset-0 opacity-40" />
    </div>
  )
}

/** Mảng chuyển cảnh: một khối trượt lên ĐÈ khối trước, bám đúng tốc độ cuộn.
 *  Dùng lại cho mọi chỗ cần "lật màn" thay vì viết tay từng nơi. */
export function StackReveal({
  base, cover, className, height = '210vh',
}: { base: ReactNode; cover: ReactNode; className?: string; height?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const y = useTransform(scrollYProgress, [0.06, 0.94], ['100%', '0%'])
  const baseScale = useTransform(scrollYProgress, [0.06, 0.94], [1, 0.93])
  const baseFade = useTransform(scrollYProgress, [0.35, 0.95], [1, 0.3])
  const baseBlur = useTransform(scrollYProgress, [0.35, 0.95], ['blur(0px)', 'blur(5px)'])

  if (reduced) {
    return <div className={className}>{base}{cover}</div>
  }
  return (
    <div ref={ref} className={cn('relative', className)} style={{ height }}>
      <div className="sticky top-0 h-screen overflow-hidden">
        <motion.div style={{ scale: baseScale, opacity: baseFade, filter: baseBlur }}
          className="absolute inset-0 z-10 will-change-transform">
          {base}
        </motion.div>
        <motion.div style={{ y }} className="absolute inset-0 z-20 will-change-transform">
          {cover}
        </motion.div>
      </div>
    </div>
  )
}

/** Đường sáng ngang ngăn giữa hai khối — nét chuyển cảnh nhỏ nhưng làm trang "liền". */
export function GlowDivider({ tone = 'violet' }: { tone?: 'violet' | 'cyan' | 'amber' }) {
  const c = tone === 'amber' ? '#F0A848' : tone === 'cyan' ? '#4FD1C5' : '#8B7BF0'
  return (
    <div aria-hidden className="relative h-px w-full">
      <motion.div
        initial={{ scaleX: 0, opacity: 0 }}
        whileInView={{ scaleX: 1, opacity: 1 }}
        viewport={{ once: true, margin: '-10%' }}
        transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        className="h-px w-full origin-center"
        style={{ background: `linear-gradient(90deg, transparent, ${c}66 35%, ${c} 50%, ${c}66 65%, transparent)` }}
      />
    </div>
  )
}

/** Quầng sáng bám con trỏ ở tầng nền — cảm giác "hệ thống đang phản hồi bạn".
 *  Tự tắt trên thiết bị cảm ứng và khi người dùng chọn giảm chuyển động. */
export function CursorGlow() {
  const mx = useMotionValue(-1000)
  const my = useMotionValue(-1000)
  const sx = useSpring(mx, { stiffness: 60, damping: 20 })
  const sy = useSpring(my, { stiffness: 60, damping: 20 })
  const bg = useMotionTemplate`radial-gradient(420px circle at ${sx}px ${sy}px, rgba(139,123,240,0.10), transparent 70%)`
  const reduced = useReducedMotion()
  const [fine, setFine] = useState(false)

  useEffect(() => {
    if (reduced || !window.matchMedia('(pointer: fine)').matches) return
    setFine(true)
    const on = (e: PointerEvent) => { mx.set(e.clientX); my.set(e.clientY) }
    window.addEventListener('pointermove', on)
    return () => window.removeEventListener('pointermove', on)
  }, [mx, my, reduced])

  if (!fine) return null
  return <motion.div aria-hidden className="pointer-events-none fixed inset-0 z-30" style={{ background: bg }} />
}

/** Thanh tiến độ cuộn — người đọc biết mình đang ở đâu trong trang dài. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  const w = useSpring(scrollYProgress, { stiffness: 140, damping: 30, restDelta: 0.001 })
  return (
    <motion.div aria-hidden style={{ scaleX: w }}
      className="fixed inset-x-0 top-0 z-[60] h-0.5 origin-left bg-gradient-to-r from-[#8B7BF0] via-[#4FD1C5] to-[#F0A848]" />
  )
}

/** Chấm điều hướng theo khối — nhảy nhanh trong trang dài (Aceternity: Floating Dock). */
export function SectionDots({ sections }: { sections: { id: string; label: string }[] }) {
  const [active, setActive] = useState(sections[0]?.id)
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-45% 0px -45% 0px' },
    )
    sections.forEach((s) => { const el = document.getElementById(s.id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [sections])
  return (
    <nav aria-label="Điều hướng nhanh"
      className="fixed right-5 top-1/2 z-40 hidden -translate-y-1/2 flex-col items-end gap-3 lg:flex">
      {sections.map((s) => (
        <button key={s.id} onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth' })}
          className="group flex items-center gap-2.5" aria-current={active === s.id}>
          <span className={cn('text-[11px] font-medium transition-all duration-300',
            active === s.id ? 'text-white/80' : 'text-white/0 group-hover:text-white/50')}>
            {s.label}
          </span>
          <span className={cn('rounded-full transition-all duration-300',
            active === s.id ? 'h-6 w-[3px] bg-[#8B7BF0]' : 'size-[6px] bg-white/25 group-hover:bg-white/60')} />
        </button>
      ))}
    </nav>
  )
}

/** Dải chạy vô tận (Aceternity: Infinite Moving Cards) — dùng cho nền tảng công nghệ. */
export function Marquee({ items, speed = 32 }: { items: string[]; speed?: number }) {
  const reduced = useReducedMotion()
  const row = [...items, ...items]
  if (reduced) {
    return (
      <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-[15px] font-medium text-white/45">
        {items.map((t) => <span key={t}>{t}</span>)}
      </div>
    )
  }
  return (
    <div className="relative overflow-hidden"
      style={{ maskImage: 'linear-gradient(90deg, transparent, black 12%, black 88%, transparent)',
               WebkitMaskImage: 'linear-gradient(90deg, transparent, black 12%, black 88%, transparent)' }}>
      <div className="flex w-max gap-10" style={{ animation: `ld-marquee ${speed}s linear infinite` }}>
        {row.map((t, i) => (
          <span key={`${t}-${i}`}
            className="flex shrink-0 items-center gap-2 whitespace-nowrap text-[15px] font-medium text-white/45">
            <span className="size-1 rounded-full bg-[#4FD1C5]/60" />
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}

/** Bản trình diễn agent tự chạy: gõ lệnh → lập kế hoạch → chạy từng bước → chờ duyệt.
 *  Đây là cách chứng minh "agent-native" tốt hơn mọi câu chữ mô tả. */
const DEMO_STEPS = [
  { t: 'Quét 128 thư chưa đọc trong tuần', ms: 1200 },
  { t: 'Gắn nhãn theo 7 nhóm · 96 thư', ms: 1400 },
  { t: 'Gộp 18 thư quảng cáo vào một chỗ', ms: 1200 },
]
export function AgentDemo() {
  const CMD = 'Dọn hộp thư tuần này giúp mình'
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { margin: '-20%' })
  const reduced = useReducedMotion()
  const [typed, setTyped] = useState('')
  const [phase, setPhase] = useState<'idle' | 'think' | 'run' | 'confirm'>('idle')
  const [done, setDone] = useState(0)

  useEffect(() => {
    if (!inView) return
    if (reduced) { setTyped(CMD); setPhase('confirm'); setDone(DEMO_STEPS.length); return }
    let cancelled = false
    const timers: number[] = []
    const sleep = (ms: number) => new Promise<void>((r) => { timers.push(window.setTimeout(r, ms)) })

    const run = async () => {
      while (!cancelled) {
        setTyped(''); setPhase('idle'); setDone(0)
        await sleep(600)
        for (let i = 1; i <= CMD.length; i++) {
          if (cancelled) return
          setTyped(CMD.slice(0, i))
          await sleep(38)
        }
        await sleep(450); setPhase('think')
        await sleep(900); setPhase('run')
        for (let i = 0; i < DEMO_STEPS.length; i++) {
          await sleep(DEMO_STEPS[i].ms)
          if (cancelled) return
          setDone(i + 1)
        }
        await sleep(500); setPhase('confirm')
        await sleep(4200)
      }
    }
    run()
    return () => { cancelled = true; timers.forEach(clearTimeout) }
  }, [inView, reduced])

  return (
    <div ref={ref} className="overflow-hidden rounded-2xl border border-white/10 bg-[#0b0b12]/90 backdrop-blur-xl">
      <div className="flex items-center gap-2 border-b border-white/[0.07] px-4 py-2.5">
        <span className="size-2 rounded-full bg-[#F0A848]/70" />
        <span className="size-2 rounded-full bg-white/15" />
        <span className="size-2 rounded-full bg-white/15" />
        <span className="ml-1.5 text-[10px] text-white/40">Trợ lý MeoArc · phiên trực tiếp</span>
        <span className="ml-auto flex items-center gap-1.5 text-[10px] text-[#4FD1C5]">
          <span className="size-1.5 rounded-full bg-[#4FD1C5]" />MCP
        </span>
      </div>

      <div className="space-y-3 p-4">
        {/* Lệnh người dùng gõ */}
        <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-tr-sm bg-[#8B7BF0] px-3.5 py-2 text-[13px] text-white">
          {typed || ' '}
          {phase === 'idle' && !reduced && <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-white align-middle" />}
        </div>

        {/* Agent suy nghĩ */}
        {phase !== 'idle' && (
          <div className="flex items-center gap-2 text-[12px] text-white/50">
            <span className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span key={i} className="size-1.5 rounded-full bg-[#4FD1C5]"
                  style={{ animation: reduced ? undefined : `ld-bounce 1s ${i * 0.15}s infinite` }} />
              ))}
            </span>
            {phase === 'think' ? 'Đang lập kế hoạch…' : 'Kế hoạch 3 bước'}
          </div>
        )}

        {/* Các bước chạy */}
        {(phase === 'run' || phase === 'confirm') && (
          <div className="space-y-1.5 rounded-2xl border border-white/[0.07] bg-white/[0.03] p-3">
            {DEMO_STEPS.map((s, i) => {
              const state = i < done ? 'done' : i === done ? 'running' : 'wait'
              return (
                <div key={s.t} className="flex items-center gap-2.5 text-[12.5px]">
                  <span className={cn('flex size-4 shrink-0 items-center justify-center rounded-full border',
                    state === 'done' ? 'border-[#4FD1C5] bg-[#4FD1C5]/20 text-[#4FD1C5]'
                      : state === 'running' ? 'border-[#8B7BF0] text-[#8B7BF0]' : 'border-white/15 text-white/25')}>
                    {state === 'done' ? <Check className="size-2.5" strokeWidth={3} />
                      : state === 'running' ? <span className="size-1.5 rounded-full bg-current"
                          style={{ animation: reduced ? undefined : 'ld-bounce 0.9s infinite' }} />
                      : <span className="size-1 rounded-full bg-current" />}
                  </span>
                  <span className={state === 'wait' ? 'text-white/35' : 'text-white/80'}>{s.t}</span>
                </div>
              )
            })}
          </div>
        )}

        {/* Dừng lại xin phép — điểm khác biệt của MeoArc */}
        {phase === 'confirm' && (
          <motion.div initial={reduced ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-[#F0A848]/30 bg-[#F0A848]/10 p-3">
            <p className="text-[12.5px] font-medium text-[#F0A848]">Cần bạn duyệt trước khi xoá</p>
            <p className="mt-0.5 text-[11.5px] text-white/60">12 thư quảng cáo đã hết hạn · thao tác không hoàn tác được</p>
            <div className="mt-2.5 flex gap-2">
              <span className="rounded-lg bg-[#F0A848] px-3 py-1.5 text-[11px] font-semibold text-[#1a1206]">Duyệt</span>
              <span className="rounded-lg bg-white/[0.07] px-3 py-1.5 text-[11px] text-white/60">Từ chối</span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

/** Nút "có từ tính": nhích về phía con trỏ khi rê tới gần (Aceternity: Magnetic Button).
 *  Cảm giác nút đang chủ động đón tay người dùng. */
export function Magnetic({ children, strength = 0.35, className }: {
  children: ReactNode; strength?: number; className?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const x = useSpring(mx, { stiffness: 200, damping: 15, mass: 0.4 })
  const y = useSpring(my, { stiffness: 200, damping: 15, mass: 0.4 })

  const onMove = (e: React.PointerEvent) => {
    if (reduced) return
    const r = ref.current?.getBoundingClientRect()
    if (!r) return
    mx.set((e.clientX - (r.left + r.width / 2)) * strength)
    my.set((e.clientY - (r.top + r.height / 2)) * strength)
  }
  const reset = () => { mx.set(0); my.set(0) }

  return (
    <motion.div ref={ref} onPointerMove={onMove} onPointerLeave={reset}
      style={reduced ? undefined : { x, y }} className={cn('w-fit', className)}>
      {children}
    </motion.div>
  )
}

/* ── Lá thư mèo tinh nghịch ────────────────────────────────────────────────────
   Rê chuột lại gần thì nó NÉ đi chỗ khác, mỗi lần né một câu càu nhàu khác nhau.
   Né đủ số lần thì "thở dốc" đứng yên cho bắt; bấm vào là bung hạt giấy + lời cảm ơn.
   Người dùng có thứ để nghịch trong lúc đọc trang — vui mà không cản đường. */
const DODGE_LINES = ['Ơ kìa!', 'Không bắt được đâu~', 'Hụt rồi nhé', 'Nhanh nữa lên!', 'Suýt nữa thì…']
const CAUGHT_LINES = ['Thôi… bắt được rồi 🐾', 'Cho bạn thắng đó!', 'Thư này gửi bạn nè ♡']

export function PlayfulLetter({
  className, size = 'w-14', tone = '#F0A848', dodgesToCatch = 5,
}: { className?: string; size?: string; tone?: string; dodgesToCatch?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const [rot, setRot] = useState(0)
  const [dodges, setDodges] = useState(0)
  const [caught, setCaught] = useState(false)
  const [line, setLine] = useState<string | null>(null)
  const [burst, setBurst] = useState(0)
  const cooling = useRef(false)

  useEffect(() => {
    if (reduced || caught) return
    const onMove = (e: PointerEvent) => {
      const el = ref.current
      if (!el || cooling.current) return
      const r = el.getBoundingClientRect()
      const dx = e.clientX - (r.left + r.width / 2)
      const dy = e.clientY - (r.top + r.height / 2)
      if (Math.hypot(dx, dy) > 96) return

      // Nhảy NGƯỢC hướng con trỏ, kèm chút ngẫu nhiên để không đoán trước được
      cooling.current = true
      const ang = Math.atan2(dy, dx) + Math.PI + (Math.random() - 0.5) * 1.1
      const dist = 120 + Math.random() * 70
      setPos((p) => ({
        x: Math.max(-170, Math.min(170, p.x + Math.cos(ang) * dist)),
        y: Math.max(-110, Math.min(70, p.y + Math.sin(ang) * dist)),
      }))
      setRot((Math.random() - 0.5) * 60)
      setLine(DODGE_LINES[Math.floor(Math.random() * DODGE_LINES.length)])
      setDodges((d) => d + 1) // updater phải thuần — StrictMode gọi nó hai lần
      window.setTimeout(() => { cooling.current = false }, 320)
      window.setTimeout(() => setLine(null), 1100)
    }
    window.addEventListener('pointermove', onMove)
    return () => window.removeEventListener('pointermove', onMove)
  }, [reduced, caught, dodgesToCatch])

  // Né đủ số lần thì thôi, đứng yên cho bắt
  useEffect(() => {
    if (caught || dodges < dodgesToCatch) return
    setCaught(true)
    setLine(null)
    setPos({ x: 0, y: 0 })
    setRot(0)
  }, [dodges, dodgesToCatch, caught])

  const onCatch = () => {
    if (!caught) return
    setBurst((b) => b + 1)
    setLine(CAUGHT_LINES[Math.floor(Math.random() * CAUGHT_LINES.length)])
    window.setTimeout(() => setLine(null), 1800)
  }

  return (
    <div className={cn('pointer-events-none relative', className)}>
      <motion.div
        ref={ref}
        animate={{ x: pos.x, y: pos.y, rotate: rot }}
        transition={{ type: 'spring', stiffness: 240, damping: 14, mass: 0.5 }}
        className={cn('relative', caught && 'pointer-events-auto cursor-pointer')}
        onClick={onCatch}
      >
        {/* lời càu nhàu khi né / cảm ơn khi bị bắt */}
        <AnimatePresence>
          {line && (
            <motion.span
              key={line}
              initial={{ opacity: 0, y: 6, scale: 0.9 }}
              animate={{ opacity: 1, y: -6, scale: 1 }}
              exit={{ opacity: 0, y: -14 }}
              className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border border-white/15 bg-[#0b0b12]/90 px-2.5 py-1 text-[11px] font-medium text-white/90 backdrop-blur-md"
            >
              {line}
            </motion.span>
          )}
        </AnimatePresence>

        {/* hạt giấy bung ra khi bắt được */}
        {burst > 0 && (
          <span key={burst} aria-hidden className="absolute inset-0">
            {Array.from({ length: 10 }).map((_, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 1, x: 0, y: 0, scale: 1 }}
                animate={{
                  opacity: 0,
                  x: Math.cos((i / 10) * Math.PI * 2) * 60,
                  y: Math.sin((i / 10) * Math.PI * 2) * 60,
                  scale: 0.3,
                }}
                transition={{ duration: 0.85, ease: 'easeOut' }}
                className="absolute left-1/2 top-1/2 size-1.5 rounded-full"
                style={{ background: tone }}
              />
            ))}
          </span>
        )}

        <div style={{ animation: reduced ? undefined : 'ld-flutter 3.6s ease-in-out infinite' }}>
          <div className="absolute inset-0 -z-10 rounded-full blur-xl" style={{ background: `${tone}55` }} />
          <CatLetter className={cn(size, 'drop-shadow-[0_10px_20px_rgba(0,0,0,0.35)]')} style={{ color: tone }} />
        </div>
      </motion.div>

      {/* gợi ý nhỏ, chỉ hiện trước khi người dùng nghịch */}
      {!reduced && dodges === 0 && !caught && (
        <span className="absolute left-1/2 top-full mt-2 -translate-x-1/2 whitespace-nowrap text-[10px] text-white/35">
          thử rê chuột vào lá thư
        </span>
      )}
    </div>
  )
}

/** Tiêu đề hiện theo từng chữ (Aceternity: Text Generate Effect). */
export function TextGenerate({ text, className }: { text: string; className?: string }) {
  const reduced = useReducedMotion()
  const words = text.split(' ')
  if (reduced) return <span className={className}>{text}</span>
  return (
    <span className={className}>
      {words.map((w, i) => (
        <motion.span
          key={`${w}-${i}`}
          initial={{ opacity: 0, filter: 'blur(8px)', y: 8 }}
          whileInView={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
          viewport={{ once: true, margin: '-12%' }}
          transition={{ duration: 0.5, delay: i * 0.055, ease: [0.22, 1, 0.36, 1] }}
          className="inline-block"
        >
          {w}&nbsp;
        </motion.span>
      ))}
    </span>
  )
}
