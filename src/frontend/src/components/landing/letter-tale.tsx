import { useRef } from 'react'
import { motion, useScroll, useSpring, useTransform, useReducedMotion, type MotionValue } from 'framer-motion'
import { MeoMascot } from '@/components/meo-mascot'
import { CatLetter } from '@/components/landing/ui'
import { cn } from '@/lib/utils'

/* ══════════════════════════════════════════════════════════════════════════════
   CHUYỆN MỘT LÁ THƯ — kể trong ĐÚNG MỘT khung, như lật trang sách tranh.

   Cách dựng: một dải phong cảnh đêm dài gấp 4 lần màn hình, trượt ngang theo
   scroll. Nhiều lớp chạy với tốc độ khác nhau (sao chậm nhất → đồi gần nhanh
   nhất) nên có chiều sâu thật, giống cảnh nền phim hoạt hình.

   Bốn trang truyện:
     1. Mèo ngồi viết thư bên cửa sổ sáng đèn
     2. Gấp thư, đóng dấu sáp — nhưng phải có bạn gật đầu
     3. Thư băng qua đồi, qua trăng
     4. Sáng ra, thư nằm trên bậc cửa của mèo bên kia

   Bật "giảm chuyển động" → thành 4 trang tĩnh xếp dọc, vẫn đọc trọn câu chuyện.
   ══════════════════════════════════════════════════════════════════════════════ */

const PAGES = [
  { n: '01', title: 'Đêm ấy, mèo ngồi viết thư',
    line: 'Bạn chỉ cần nói một câu. Mèo bắc ghế lên bàn, chấm bút, và viết thay bạn — đúng giọng bạn muốn gửi tới người ấy.' },
  { n: '02', title: 'Thư gấp lại, chờ bạn gật đầu',
    line: 'Dấu sáp không tự đóng xuống. Thư nằm im trên bàn cho tới khi bạn đọc lại và nói “ừ, gửi đi”.' },
  { n: '03', title: 'Rồi thư băng qua đêm',
    line: 'Qua đồi, qua vầng trăng, thư đi bằng đường của Gmail hay Outlook — bạn không phải bận tâm nó đi lối nào.' },
  { n: '04', title: 'Sáng ra, thư đã nằm trước cửa',
    line: 'Thư tới tay người nhận, một bản lưu trong mục Đã gửi của bạn, và một dòng trong nhật ký để bạn luôn tra lại được.' },
]

/** Bầu trời sao — mỗi ngôi sao nhấp nháy lệch nhịp nhau. */
function Stars({ count = 46 }: { count?: number }) {
  const reduced = useReducedMotion()
  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const top = (i * 37) % 62
        const left = (i * 53) % 100
        const size = i % 7 === 0 ? 3 : i % 3 === 0 ? 2 : 1.5
        return (
          <span key={i} className="absolute rounded-full bg-white"
            style={{
              top: `${top}%`, left: `${left}%`, width: size, height: size,
              opacity: 0.25 + ((i * 13) % 60) / 100,
              animation: reduced ? undefined : `tale-twinkle ${2.6 + (i % 5) * 0.7}s ${(i % 9) * 0.4}s ease-in-out infinite`,
            }} />
        )
      })}
    </>
  )
}

/** Ngôi nhà nhỏ có cửa sổ sáng đèn. */
function Cottage({ lit = true, className, flip = false }: { lit?: boolean; className?: string; flip?: boolean }) {
  return (
    <svg viewBox="0 0 120 110" className={cn(className, flip && 'scale-x-[-1]')} aria-hidden>
      <path d="M12 52 60 16 108 52 108 104 12 104Z" fill="#0d0d1c" stroke="rgba(255,255,255,0.14)" strokeWidth="1.2" strokeLinejoin="round" />
      <path d="M6 54 60 12 114 54" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="30" y="64" width="24" height="22" rx="3" fill={lit ? '#F0A848' : '#161628'} opacity={lit ? 0.92 : 1} />
      {lit && <rect x="30" y="64" width="24" height="22" rx="3" fill="#F0A848" opacity="0.5" style={{ filter: 'blur(7px)' }} />}
      <path d="M42 64v22M30 75h24" stroke="#0d0d1c" strokeWidth="1.6" />
      <rect x="70" y="70" width="18" height="34" rx="3" fill="#161628" stroke="rgba(255,255,255,0.12)" />
      <rect x="80" y="24" width="10" height="18" rx="2" fill="#0d0d1c" stroke="rgba(255,255,255,0.14)" />
    </svg>
  )
}

/** Đường viền đồi — dùng cho các lớp xa/gần. */
function Hills({ tone, className }: { tone: string; className?: string }) {
  return (
    <svg viewBox="0 0 1200 200" preserveAspectRatio="none" className={className} aria-hidden>
      <path d="M0 200 V120 Q90 66 180 108 T400 96 Q520 52 640 104 T880 88 Q1000 44 1120 96 T1200 110 V200Z" fill={tone} />
    </svg>
  )
}

export function LetterTale() {
  const reduced = useReducedMotion()
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const p = useSpring(scrollYProgress, { stiffness: 80, damping: 26, restDelta: 0.0005 })

  // Các lớp trượt ngang với tốc độ khác nhau → chiều sâu
  const xStars = useTransform(p, [0, 1], ['0%', '-12%'])
  const xMoon = useTransform(p, [0, 1], ['0%', '-26%'])
  const xFar = useTransform(p, [0, 1], ['0%', '-45%'])
  const xMid = useTransform(p, [0, 1], ['0%', '-62%'])
  // Lớp gần rộng 260%, nên chỉ được trượt tối đa −60% (=156% bề ngang khung).
  // Trượt sâu hơn là nhà của mèo nhận bị đẩy ra ngoài màn đúng lúc cần thấy nó.
  const xNear = useTransform(p, [0, 1], ['0%', '-60%'])

  // Lá thư: nằm trên bàn → được gấp → bay lên → đáp xuống bậc cửa
  const letterX = useTransform(p, [0, 0.28, 0.52, 0.78, 1], ['30%', '42%', '56%', '68%', '74%'])
  const letterY = useTransform(p, [0, 0.28, 0.45, 0.62, 0.82, 1], ['64%', '58%', '30%', '24%', '52%', '62%'])
  const letterScale = useTransform(p, [0, 0.25, 0.5, 0.8, 1], [0.75, 1.25, 0.85, 0.7, 0.62])
  const letterRot = useTransform(p, [0, 0.3, 0.55, 0.8, 1], [-6, 4, -10, 8, 0])
  const sealScale = useTransform(p, [0.3, 0.42, 0.48], [2.6, 0.92, 1])
  const sealOpacity = useTransform(p, [0.3, 0.44], [0, 1])
  const trailOpacity = useTransform(p, [0.5, 0.6, 0.78], [0, 0.9, 0])

  if (reduced) {
    return (
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PAGES.map((pg) => (
          <div key={pg.n} className="rounded-3xl border border-white/[0.09] bg-white/[0.03] p-6">
            <span className="font-serif text-4xl font-bold text-white/12">{pg.n}</span>
            <h3 className="mt-3 font-serif text-lg font-bold">{pg.title}</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-white/55">{pg.line}</p>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div ref={ref} className="relative h-[340vh]">
      <style>{`
        @keyframes tale-twinkle{ 0%,100%{ opacity:.2; transform:scale(.85) } 50%{ opacity:1; transform:scale(1.15) } }
        @keyframes tale-firefly{ 0%,100%{ transform:translate(0,0) } 33%{ transform:translate(14px,-16px) } 66%{ transform:translate(-10px,-8px) } }
        @keyframes tale-flutter{ 0%,100%{ transform:translateY(0) } 50%{ transform:translateY(-7px) } }
      `}</style>

      <div className="sticky top-0 h-screen overflow-hidden">
        {/* Bầu trời đêm */}
        <div className="absolute inset-0 bg-[linear-gradient(180deg,#070a1e_0%,#131038_45%,#241a4a_78%,#2e1f4f_100%)]" />

        {/* Lớp sao — chạy chậm nhất */}
        <motion.div style={{ x: xStars }} className="absolute inset-0 w-[125%]">
          <Stars />
        </motion.div>

        {/* Trăng */}
        <motion.div style={{ x: xMoon }} className="absolute inset-0 w-[135%]">
          <div className="absolute left-[58%] top-[12%]">
            <div className="relative size-24 rounded-full bg-[#FFF3D6]">
              <div className="absolute inset-0 rounded-full bg-[#FFF3D6] blur-2xl opacity-70" />
              <div className="absolute left-5 top-6 size-3 rounded-full bg-black/[0.06]" />
              <div className="absolute left-12 top-12 size-4 rounded-full bg-black/[0.05]" />
              <div className="absolute left-6 top-14 size-2 rounded-full bg-black/[0.05]" />
            </div>
          </div>
        </motion.div>

        {/* Đồi xa */}
        <motion.div style={{ x: xFar }} className="absolute inset-x-0 bottom-0 h-[46%] w-[160%]">
          <Hills tone="#161231" className="absolute inset-0 size-full" />
        </motion.div>

        {/* Đồi giữa + hàng cây */}
        <motion.div style={{ x: xMid }} className="absolute inset-x-0 bottom-0 h-[34%] w-[200%]">
          <Hills tone="#0f0c24" className="absolute inset-0 size-full" />
          {[12, 26, 41, 58, 73, 88].map((l, i) => (
            <svg key={l} viewBox="0 0 40 70" className="absolute bottom-[38%] w-6 opacity-80" style={{ left: `${l}%` }} aria-hidden>
              <path d="M20 4 34 34H26L20 66 14 34H6Z" fill={i % 2 ? '#0a081c' : '#0c0a20'} />
            </svg>
          ))}
        </motion.div>

        {/* Lớp gần: hai ngôi nhà + hai chú mèo + đom đóm */}
        <motion.div style={{ x: xNear }} className="absolute inset-x-0 bottom-0 h-[30%] w-[260%]">
          <div className="absolute inset-x-0 bottom-0 h-[62%] bg-[#08060f]" />

          {/* Nhà mèo viết thư — đầu truyện nằm ở ~13% bề ngang khung */}
          <div className="absolute bottom-[52%] left-[5%] flex items-end gap-3">
            <Cottage className="w-24 drop-shadow-[0_0_30px_rgba(240,168,72,0.25)]" />
            <div className="mb-1" style={{ animation: 'tale-flutter 4s ease-in-out infinite' }}>
              <MeoMascot mood="thinking" thinking className="size-11" />
            </div>
          </div>

          {/* Nhà mèo nhận thư — cuối truyện dừng ở ~72% bề ngang khung, ngay chỗ thư đáp xuống */}
          <div className="absolute bottom-[52%] left-[88%] flex items-end gap-3">
            <div className="mb-1" style={{ animation: 'tale-flutter 4.6s ease-in-out infinite' }}>
              <MeoMascot mood="happy" className="size-11" />
            </div>
            <Cottage flip className="w-24 drop-shadow-[0_0_30px_rgba(240,168,72,0.25)]" />
          </div>

          {/* Đom đóm */}
          {[16, 24, 33, 47, 63, 71, 82, 90].map((l, i) => (
            <span key={l} className="absolute rounded-full bg-[#F0A848]"
              style={{
                left: `${l}%`, bottom: `${48 + (i % 4) * 9}%`, width: 4, height: 4,
                boxShadow: '0 0 10px 3px rgba(240,168,72,0.55)',
                animation: `tale-firefly ${5 + (i % 4)}s ${i * 0.6}s ease-in-out infinite`,
              }} />
          ))}
        </motion.div>

        {/* ── Lá thư: nhân vật chính, luôn nằm trong khung ── */}
        <motion.div className="absolute z-20" style={{ left: letterX, top: letterY, translateX: '-50%', translateY: '-50%' }}>
          <motion.div style={{ scale: letterScale, rotate: letterRot }} className="relative">
            {/* vệt sáng khi thư đang bay */}
            <motion.span style={{ opacity: trailOpacity }}
              className="absolute right-full top-1/2 h-[2px] w-28 -translate-y-1/2 rounded-full bg-gradient-to-l from-[#F0A848] to-transparent blur-[1px]" />
            <span className="absolute inset-0 -z-10 rounded-full bg-[#F0A848]/35 blur-2xl" />
            <div style={{ animation: 'tale-flutter 3.4s ease-in-out infinite' }}>
              <CatLetter className="w-16 drop-shadow-[0_10px_24px_rgba(0,0,0,0.5)]" style={{ color: '#FFF3D6' }} />
              {/* dấu sáp đóng xuống khi bạn duyệt */}
              <motion.span style={{ scale: sealScale, opacity: sealOpacity }}
                className="absolute left-1/2 top-[58%] flex size-5 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-[#F0A848]">
                <span className="text-[9px] leading-none text-white">♥</span>
              </motion.span>
            </div>
          </motion.div>
        </motion.div>

        {/* Mép trên/dưới mờ dần để khung hoà vào trang */}
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-[#06060B] to-transparent" />
        <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-[#06060B] to-transparent" />

        {/* ── Lời kể ── */}
        <div className="absolute inset-x-0 bottom-10 z-30 px-6">
          <div className="relative mx-auto h-[132px] max-w-xl">
            {PAGES.map((pg, i) => (
              <TaleLine key={pg.n} p={p} index={i} page={pg} />
            ))}
          </div>
          <div className="mt-3 flex justify-center gap-2">
            {PAGES.map((pg, i) => <TaleDot key={pg.n} p={p} index={i} />)}
          </div>
        </div>
      </div>
    </div>
  )
}

const BOUNDS = [[0, 0.26], [0.26, 0.52], [0.52, 0.78], [0.78, 1.01]]

function TaleLine({ p, index, page }: { p: MotionValue<number>; index: number; page: (typeof PAGES)[number] }) {
  const [a, b] = BOUNDS[index]
  const f = 0.05
  const opacity = useTransform(p, [a - f, a + f, b - f, b + f], [0, 1, 1, 0], { clamp: true })
  const y = useTransform(p, [a - f, a + f, b - f, b + f], [16, 0, 0, -16], { clamp: true })
  return (
    <motion.div style={{ opacity, y }} className="absolute inset-0 text-center">
      <p className="font-mono text-[11px] tracking-[0.3em] text-[#F0A848]/80">{page.n}</p>
      <h3 className="mt-2 font-serif text-2xl font-bold leading-tight sm:text-[1.9rem]">{page.title}</h3>
      <p className="mx-auto mt-2.5 max-w-lg text-[14px] leading-relaxed text-white/65">{page.line}</p>
    </motion.div>
  )
}

function TaleDot({ p, index }: { p: MotionValue<number>; index: number }) {
  const [a, b] = BOUNDS[index]
  const active = useTransform(p, [a - 0.02, a + 0.02, b - 0.02, b + 0.02], [0.25, 1, 1, 0.25], { clamp: true })
  const w = useTransform(active, [0.25, 1], [6, 22])
  return <motion.span style={{ opacity: active, width: w }} className="h-1.5 rounded-full bg-[#F0A848]" />
}
