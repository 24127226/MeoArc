import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css' // BẮT BUỘC: thiếu file này Lenis khoá cứng scroll
import {
  Sparkles, ShieldCheck, Mails, Tags, Mic, ArrowRight, ArrowDown, Check, MessageSquare,
  Plus, Minus, Lock, Zap, ArrowDownToLine,
} from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { cn } from '@/lib/utils'
import { LogoMark } from '@/components/logo'
import { MeoMascot } from '@/components/meo-mascot'
import {
  Reveal, Aurora, Spotlight, DotGrid, SpotCard, MovingBorderButton, CountUp,
  ContainerScroll, VideoBackdrop, StackReveal, GlowDivider, TextGenerate,
  CursorGlow, ScrollProgress, SectionDots, Marquee, AgentDemo, PlayfulLetter, Magnetic,
  GridFloor, BeamSweep, ContourLines, ParticleField,
} from '@/components/landing/ui'
import { LetterTale, JOURNEY_VIDEO } from '@/components/landing/letter-tale'

const NAV_SECTIONS = [
  { id: 'hero', label: 'Mở đầu' },
  { id: 'agent', label: 'Agent' },
  { id: 'features', label: 'Tính năng' },
  { id: 'auto', label: 'Tự động hoá' },
  { id: 'how', label: 'Cách chạy' },
  { id: 'faq', label: 'Giải đáp' },
  { id: 'start', label: 'Bắt đầu' },
]

const TECHS = [
  'Gmail API', 'Microsoft Graph', 'Google Gemini', 'Model Context Protocol',
  'LangGraph', 'FastAPI', 'React 19', 'PostgreSQL', 'OAuth 2.0',
]

/* ══════════════════════════════════════════════════════════════════════════════
   LANDING PAGE — MeoArc

   Chuyển cảnh (đã nâng cấp):
   · Lenis: cuộn có quán tính → mọi hiệu ứng bám scroll đều mượt hơn hẳn.
   · StackReveal: khối sau trượt lên ĐÈ khối trước, tốc độ bám đúng tay người dùng;
     khối bị đè thì lùi + mờ + nhoè nhẹ để mắt biết nó đang ra sau.
   · Video nền có parallax (trôi chậm hơn trang) → chiều sâu khi cuộn ngang qua.
   · GlowDivider + TextGenerate: nối và mở từng khối, tránh cảm giác "hết đoạn này
     sang đoạn khác" đột ngột.

   Quy tắc ảnh: mỗi hình phải CHỨNG MINH đúng tiêu đề bên cạnh nó — không dùng ảnh
   nền chung chung cho mục nói về tính năng cụ thể.
   ══════════════════════════════════════════════════════════════════════════════ */

const CATS = [
  { n: 'Học tập', c: '#8B7BF0' }, { n: 'Công việc', c: '#4FD1C5' }, { n: 'Tài chính', c: '#F0A848' },
  { n: 'Mạng xã hội', c: '#F06AA8' }, { n: 'Mua sắm', c: '#7BC4F0' }, { n: 'Hệ thống', c: '#9AA4B2' },
  { n: 'Cá nhân', c: '#A8E06A' },
]

const SKILLS = [
  { icon: Tags, t: 'Tự phân loại', d: 'Gắn nhãn thư mới theo 7 nhóm' },
  { icon: Zap, t: 'Triage hộp thư', d: 'Xếp thư chưa đọc theo mức ưu tiên' },
  { icon: MessageSquare, t: 'Brief cuộc họp', d: 'Rút việc cần làm & hạn chót từ luồng thư' },
  { icon: Mic, t: 'Giọng nói & ⌘K', d: 'Ra lệnh bằng mic hoặc command palette' },
]

const FAQS = [
  { q: 'MeoArc xin những quyền gì trên hộp thư của tôi?',
    a: 'Quyền đọc và quản lý thư (gắn nhãn, lưu trữ, soạn và gửi) trên tài khoản bạn kết nối. Bạn có thể thu hồi bất cứ lúc nào trong phần Cài đặt hoặc ngay trong trang bảo mật của Google / Microsoft.' },
  { q: 'AI có tự ý gửi thư thay tôi không?',
    a: 'Không. Mọi hành động không hoàn tác được đều phải qua bước xác nhận: MeoArc hiện bản nháp hoặc danh sách việc sắp làm, bạn bấm Duyệt thì nó mới chạy.' },
  { q: 'Thư của tôi có bị dùng để huấn luyện mô hình không?',
    a: 'Không. Nội dung thư chỉ được gửi tới mô hình để xử lý đúng yêu cầu bạn đưa ra tại thời điểm đó, và lưu trong cơ sở dữ liệu của chính bạn để hiển thị nhanh hơn.' },
  { q: 'Tôi dùng Outlook thay vì Gmail được không?',
    a: 'Được. MeoArc nói chuyện với Gmail qua Gmail API và với Outlook qua Microsoft Graph, cùng một giao diện và cùng bộ lệnh.' },
  { q: 'Ứng dụng ngoài có gọi được MeoArc không?',
    a: 'Có. MeoArc mở sẵn một máy chủ MCP, nên các trợ lý khác (Claude Desktop, Codex…) có thể gọi trực tiếp các công cụ tìm thư, tóm tắt, soạn, gửi trong đúng phạm vi quyền bạn cấp.' },
]

/* ── Logo nhà cung cấp (dùng trong mockup hợp nhất hộp thư) ── */
function GoogleGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.4-1.7 4.1-5.5 4.1-3.3 0-6-2.7-6-6.1S8.7 5.9 12 5.9c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.3 14.6 2.3 12 2.3 6.9 2.3 2.8 6.4 2.8 11.5S6.9 20.7 12 20.7c5.3 0 8.8-3.7 8.8-8.9 0-.6-.07-1.1-.16-1.6H12z" />
    </svg>
  )
}
function MsGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <rect x="3" y="3" width="8" height="8" fill="#F25022" />
      <rect x="13" y="3" width="8" height="8" fill="#7FBA00" />
      <rect x="3" y="13" width="8" height="8" fill="#00A4EF" />
      <rect x="13" y="13" width="8" height="8" fill="#FFB900" />
    </svg>
  )
}

/** Hình chứng minh cho "Gmail và Outlook trong một chỗ":
 *  hai nguồn ở trên, đường dẫn hội tụ xuống MỘT hộp thư chung ở dưới. */
function UnifiedInboxMock() {
  const reduced = useReducedMotion()
  const rows = [
    { n: 'Giáo vụ HCMUS', s: 'gmail', tag: 'Học tập', c: '#8B7BF0' },
    { n: 'Microsoft Teams', s: 'ms', tag: 'Công việc', c: '#4FD1C5' },
    { n: 'GitHub', s: 'gmail', tag: 'Công việc', c: '#4FD1C5' },
    { n: 'Outlook Calendar', s: 'ms', tag: 'Hệ thống', c: '#9AA4B2' },
  ] as const
  return (
    <div className="relative">
      <div aria-hidden className="absolute -inset-6 rounded-[2rem] bg-[#4FD1C5]/15 blur-3xl" />
      <div className="relative">
        {/* Hai nguồn */}
        <div className="flex items-center justify-center gap-4 sm:gap-10">
          {[
            { Glyph: GoogleGlyph, t: 'Gmail', d: 'Gmail API' },
            { Glyph: MsGlyph, t: 'Outlook', d: 'Microsoft Graph' },
          ].map(({ Glyph, t, d }) => (
            <div key={t} className="flex items-center gap-2.5 lit-edge rounded-2xl bg-white/[0.05] px-4 py-2.5 backdrop-blur-md [--lit:#4FE9FF]">
              <Glyph className="size-5" />
              <div className="leading-tight">
                <p className="text-[13px] font-semibold">{t}</p>
                <p className="text-[10px] text-white/45">{d}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Đường hội tụ */}
        <svg viewBox="0 0 320 64" className="mx-auto -my-1 h-16 w-full max-w-[320px]" fill="none" aria-hidden>
          <path d="M78 0 V22 Q78 42 160 42 V64" stroke="url(#g1)" strokeWidth="1.5" />
          <path d="M242 0 V22 Q242 42 160 42 V64" stroke="url(#g2)" strokeWidth="1.5" />
          {!reduced && (
            <>
              <circle r="2.5" fill="#8B7BF0">
                <animateMotion dur="2.6s" repeatCount="indefinite" path="M78 0 V22 Q78 42 160 42 V64" />
              </circle>
              <circle r="2.5" fill="#4FD1C5">
                <animateMotion dur="2.6s" begin="1.3s" repeatCount="indefinite" path="M242 0 V22 Q242 42 160 42 V64" />
              </circle>
            </>
          )}
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="0" y2="64" gradientUnits="userSpaceOnUse">
              <stop stopColor="#8B7BF0" stopOpacity="0.1" /><stop offset="1" stopColor="#8B7BF0" stopOpacity="0.7" />
            </linearGradient>
            <linearGradient id="g2" x1="0" y1="0" x2="0" y2="64" gradientUnits="userSpaceOnUse">
              <stop stopColor="#4FD1C5" stopOpacity="0.1" /><stop offset="1" stopColor="#4FD1C5" stopOpacity="0.7" />
            </linearGradient>
          </defs>
        </svg>

        {/* Một hộp thư chung */}
        <div className="lit-edge overflow-hidden rounded-2xl bg-[#0b0b12]/90 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-2.5">
            <span className="flex items-center gap-2 text-[12px] font-semibold">
              <MeoMascot mood="idle" className="size-4" />
              Hộp thư MeoArc
            </span>
            <span className="rounded-full bg-white/[0.07] px-2 py-0.5 text-[10px] text-white/50">2 tài khoản</span>
          </div>
          <div className="divide-y divide-white/[0.05]">
            {rows.map((r) => (
              <div key={r.n} className="flex items-center gap-3 px-4 py-2.5">
                <span className="relative flex size-7 shrink-0 items-center justify-center rounded-full bg-white/[0.07] text-[10px] font-bold">
                  {r.n[0]}
                  <span className="absolute -bottom-0.5 -right-0.5 flex size-3.5 items-center justify-center rounded-full bg-[#0b0b12]">
                    {r.s === 'gmail' ? <GoogleGlyph className="size-2.5" /> : <MsGlyph className="size-2.5" />}
                  </span>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-medium">{r.n}</p>
                  <p className="truncate text-[10px] text-white/40">Thư mới · đã tự gắn nhãn</p>
                </div>
                <span className="shrink-0 rounded px-1.5 py-0.5 text-[9px]" style={{ background: `${r.c}22`, color: r.c }}>
                  {r.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/** Mockup giao diện 3 cột — dùng cho hero và mục "bạn bấm nút cuối". */
function AppMock({ compact = false }: { compact?: boolean }) {
  return (
    <div className="lit-edge overflow-hidden rounded-2xl bg-[#0b0b12]/90 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center gap-1.5 border-b border-white/[0.07] px-3 py-2">
        <span className="size-2 rounded-full bg-[#F0A848]/70" />
        <span className="size-2 rounded-full bg-white/20" />
        <span className="size-2 rounded-full bg-white/20" />
        <span className="ml-2 text-[10px] text-white/40">MeoArc — Hộp thư</span>
      </div>
      <div className="grid grid-cols-12 gap-2 p-2.5">
        <div className={cn('col-span-3 flex-col gap-1.5', compact ? 'hidden' : 'hidden sm:flex')}>
          <div className="flex items-center gap-1.5 px-1 py-1">
            <MeoMascot mood="idle" className="size-5" />
            <span className="text-[11px] font-semibold">MeoArc</span>
          </div>
          {['Hộp thư', 'AI Agent', 'Đã gửi', 'Nháp'].map((s, i) => (
            <div key={s} className={cn('rounded-lg px-2 py-1.5 text-[10px]',
              i === 1 ? 'bg-[#8B7BF0]/25 text-white' : 'text-white/50')}>{s}</div>
          ))}
        </div>
        <div className={cn('flex flex-col gap-1.5', compact ? 'col-span-12 sm:col-span-6' : 'col-span-12 sm:col-span-5')}>
          {[['Giáo vụ HCMUS', 'Học tập', '#8B7BF0'], ['GitHub', 'Công việc', '#4FD1C5'], ['Sacombank', 'Tài chính', '#F0A848']].map(([n, tag, c]) => (
            <div key={n} className="flex items-center gap-2 rounded-xl bg-white/[0.05] p-2">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full text-[9px] font-bold"
                style={{ background: `${c}33`, color: c }}>{n[0]}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[10px] font-medium">{n}</p>
                <p className="truncate text-[9px] text-white/40">Thư mới · nhấn để xem…</p>
              </div>
              <span className="rounded px-1.5 py-0.5 text-[8px]" style={{ background: `${c}22`, color: c }}>{tag}</span>
            </div>
          ))}
        </div>
        <div className={cn('flex flex-col gap-1.5 rounded-xl bg-gradient-to-b from-[#8B7BF0]/10 to-transparent p-2',
          compact ? 'col-span-12 sm:col-span-6' : 'col-span-12 sm:col-span-4')}>
          <div className="flex items-center gap-1.5">
            <MeoMascot mood="thinking" thinking className="size-4" />
            <span className="text-[10px] font-semibold">Trợ lý MeoArc</span>
          </div>
          <div className="ml-auto max-w-[92%] rounded-xl rounded-tr-sm bg-[#8B7BF0] px-2.5 py-1.5 text-[10px] text-white">
            Gửi thư xin nghỉ cho thầy Sơn
          </div>
          <div className="max-w-[94%] rounded-xl rounded-tl-sm bg-white/[0.08] px-2.5 py-1.5 text-[10px]">
            <p className="font-medium">Bản nháp đã sẵn sàng</p>
            <p className="mt-0.5 text-white/50">Cần bạn duyệt trước khi gửi</p>
          </div>
          <div className="mt-auto flex gap-1.5 pt-1">
            <span className="flex-1 rounded-lg bg-[#F0A848] px-2 py-1 text-center text-[9px] font-semibold text-[#1a1206]">✓ Duyệt & gửi</span>
            <span className="rounded-lg bg-white/[0.07] px-2 py-1 text-center text-[9px] text-white/50">Sửa</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-white/[0.08]">
      <button onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 py-5 text-left transition-colors hover:text-white">
        <span className="text-[15px] font-medium sm:text-base">{q}</span>
        <span className="flex size-7 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/[0.05]">
          {open ? <Minus className="size-3.5" /> : <Plus className="size-3.5" />}
        </span>
      </button>
      <motion.div initial={false} animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }} className="overflow-hidden">
        <p className="pb-5 pr-10 text-[14px] leading-relaxed text-white/60">{a}</p>
      </motion.div>
    </div>
  )
}

/* ── Hai màn đầu (tách ra để StackReveal dùng lại) ── */
function HeroPanel({ onCta, ctaPrimary, onSeeMore }: { onCta: () => void; ctaPrimary: string; onSeeMore: () => void }) {
  return (
    <section id="hero" className="relative flex h-full items-center justify-center">
      <VideoBackdrop src="/landing/flower-field.mp4" poster="/landing/flower-field-poster.jpg" tint="violet" />
      <Spotlight className="-top-40 left-1/2 h-[160vh] w-[110vw] -translate-x-1/2" />
      <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-10 px-6 lg:grid-cols-12">
        <div className="text-center lg:col-span-6 lg:text-left">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-3 py-1.5 text-[11px] font-medium backdrop-blur-md">
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-[#4FD1C5] opacity-75" />
              <span className="relative inline-flex size-1.5 rounded-full bg-[#4FD1C5]" />
            </span>
            Trợ lý email agent-native · HCMUS Nhóm 7
          </div>
          <h1 className="font-serif text-4xl font-bold leading-[1.06] drop-shadow-[0_2px_24px_rgba(0,0,0,0.65)] sm:text-6xl">
            Hộp thư của bạn,
            <br />
            giờ <span className="bg-gradient-to-r from-[#8B7BF0] via-[#4FD1C5] to-[#F0A848] bg-clip-text text-transparent">biết nghe lời</span>.
          </h1>
          <p className="mx-auto mt-5 max-w-lg text-base leading-relaxed text-white/75 sm:text-lg lg:mx-0">
            Dành cho sinh viên và người đi làm đang chết chìm trong hộp thư: nói một câu tiếng Việt,
            MeoArc tóm tắt, phân loại, soạn và dọn thư giúp bạn — nhưng luôn hỏi trước khi làm việc lớn.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 lg:justify-start">
            <Magnetic>
              <MovingBorderButton onClick={onCta}>
                <Sparkles className="size-4.5" />
                {ctaPrimary}
              </MovingBorderButton>
            </Magnetic>
            <Magnetic strength={0.25}>
              <MovingBorderButton tone="ghost" onClick={onSeeMore}>Xem cách hoạt động</MovingBorderButton>
            </Magnetic>
          </div>
          <div className="mt-7 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] text-white/55 lg:justify-start">
            {['Miễn phí cho tài khoản cá nhân', 'Không tự ý gửi thư', 'Thu hồi quyền bất cứ lúc nào'].map((t) => (
              <span key={t} className="flex items-center gap-1.5">
                <Check className="size-3.5 text-[#4FD1C5]" />{t}
              </span>
            ))}
          </div>
        </div>
        {/* Bên phải là phiên agent chạy thật, không phải ảnh chụp tĩnh */}
        <div className="hidden lg:col-span-6 lg:block">
          <ContainerScroll><AgentDemo /></ContainerScroll>
        </div>
      </div>
      <div className="absolute bottom-6 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-1 text-[11px] text-white/55">
        <ArrowDown className="size-4 animate-bounce" />
        Cuộn để xem tiếp
      </div>
    </section>
  )
}

function BenefitsPanel() {
  return (
    <section className="relative flex h-full items-center overflow-hidden bg-[#06060B]">
      <Aurora />
      <DotGrid />
      <div className="relative z-10 mx-auto w-full max-w-6xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="ld-chip mx-auto">Vì sao cần MeoArc</p>
          <h2 className="mt-4 text-[1.9rem] leading-[1.05] sm:text-[3rem]">
            Bạn không thiếu app email.
            <br />
            Bạn thiếu <span className="text-[#F0A848]">thời gian</span>.
          </h2>
        </div>
        {/* Ba khối ICON LỚN — mỗi khối chỉ vài từ, không đoạn văn */}
        <div className="mt-8 grid gap-3 sm:mt-12 sm:grid-cols-3 sm:gap-4">
          {[
            { icon: Sparkles, c: '#8B7BF0', t: 'Nói,\nkhông bấm', n: '01' },
            { icon: Tags, c: '#4FD1C5', t: 'Hộp thư\ntự gọn', n: '02' },
            { icon: ShieldCheck, c: '#F0A848', t: 'AI hỏi\ntrước khi làm', n: '03' },
          ].map((b, i) => (
            <Reveal key={b.n} delay={i * 0.08}>
              <SpotCard className="group relative h-full overflow-hidden p-6">
                <b.icon aria-hidden
                  className="pointer-events-none absolute -bottom-6 -right-5 size-36 opacity-[0.07] transition-transform duration-700 group-hover:scale-110"
                  style={{ color: b.c }} />
                <div className="relative flex items-center justify-between">
                  <span className="flex size-12 items-center justify-center rounded-2xl"
                    style={{ background: `${b.c}20`, color: b.c }}>
                    <b.icon className="size-6" />
                  </span>
                  <span className="ld-num" style={{ color: b.c }}>{b.n}</span>
                </div>
                <h3 className="ld-title relative mt-6 whitespace-pre-line text-[1.6rem] leading-[1.08]">
                  {b.t}
                </h3>
              </SpotCard>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

export function LandingPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const reduced = useReducedMotion()
  const goCta = () => navigate(isAuthenticated ? '/app' : '/login')
  const ctaLabel = isAuthenticated ? 'Vào MeoArc' : 'Đăng nhập'

  // Cuộn có quán tính — nền tảng để mọi hiệu ứng bám scroll thấy mượt
  useEffect(() => {
    if (reduced) return
    const lenis = new Lenis({ duration: 1.15, smoothWheel: true })
    let raf = 0
    const loop = (t: number) => { lenis.raf(t); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); lenis.destroy() }
  }, [reduced])

  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > window.innerHeight * 0.75)
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Khối "agent thật sự": chữ trôi ngược chiều video → cảm giác lớp
  const agentRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress: agentP } = useScroll({ target: agentRef, offset: ['start end', 'end start'] })
  const agentTextY = useTransform(agentP, [0, 1], ['14%', '-14%'])

  const [email, setEmail] = useState('')
  const seeMore = () => document.getElementById('agent')?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="ld-tech relative min-h-screen bg-[#06060B] text-white">
      <style>{`
        @property --beam { syntax: '<angle>'; inherits: false; initial-value: 0deg; }
        .ld-beam::after{ content:''; position:absolute; inset:-1px; border-radius:inherit; padding:1.5px;
          background: conic-gradient(from var(--beam), transparent 0deg, #8B7BF0 60deg, #4FD1C5 95deg, transparent 155deg, transparent 360deg);
          -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          -webkit-mask-composite: xor; mask-composite: exclude; opacity:0; transition:opacity .45s ease; pointer-events:none; }
        .ld-beam:hover::after{ opacity:1; animation: ld-beam 4s linear infinite; }
        @keyframes ld-beam{ to{ --beam:360deg } }
        .ld-mb::before{ content:''; position:absolute; inset:0; background:linear-gradient(110deg,transparent 25%,rgba(255,255,255,.45) 50%,transparent 75%);
          transform:translateX(-100%); animation: ld-sweep 4.5s ease-in-out infinite; }
        @keyframes ld-sweep{ 0%,55%{ transform:translateX(-100%) } 85%,100%{ transform:translateX(100%) } }
        @keyframes ld-drift1{ 0%,100%{ transform:translate(0,0) scale(1) } 50%{ transform:translate(7vw,5vh) scale(1.18) } }
        @keyframes ld-drift2{ 0%,100%{ transform:translate(0,0) scale(1.12) } 50%{ transform:translate(-6vw,-4vh) scale(1) } }
        @keyframes ld-breathe{ 0%,100%{ opacity:.35; transform:scale(1) } 50%{ opacity:.85; transform:scale(1.14) } }
        @keyframes ld-flutter{ 0%,100%{ transform:translateY(0) rotate(-4deg) } 50%{ transform:translateY(-12px) rotate(4deg) } }
        @keyframes ld-marquee{ from{ transform:translateX(0) } to{ transform:translateX(-50%) } }
        @keyframes ld-bounce{ 0%,100%{ transform:translateY(0); opacity:.55 } 50%{ transform:translateY(-3px); opacity:1 } }

        /* Lớp nền thay cho mảng đen trơn — dựng bằng CSS, không tải thêm gì */
        @keyframes ld-grid-run{ to{ background-position: 0 54px } }
        @keyframes ld-beam-sweep{
          0%,100%{ transform: translateX(-40%) rotate(18deg); opacity:0 }
          40%{ opacity:1 }
          60%{ opacity:1 }
          100%{ transform: translateX(140%) rotate(18deg); opacity:0 } }
        @keyframes ld-float-up{
          0%{ transform: translateY(0); opacity:0 }
          10%{ opacity:1 }
          90%{ opacity:1 }
          100%{ transform: translateY(-115vh); opacity:0 } }

        /* ── BỘ CHỮ CÔNG NGHỆ (chỉ trong trang giới thiệu, không đụng app) ──
           Tiêu đề dùng Space Grotesk: hình học, sắc nét, nén chữ lại cho "đặc".
           Mọi số liệu/nhãn kỹ thuật dùng JetBrains Mono — chữ số đều li nên
           bảng số trông như bảng điều khiển chứ không như văn bản. */
        .ld-tech h1, .ld-tech h2, .ld-tech h3, .ld-tech .ld-title {
          font-family: var(--font-tech); font-weight: 700; letter-spacing: -0.035em; }
        .ld-tech .ld-num, .ld-tech .font-mono, .ld-tech .tabular-nums {
          font-family: var(--font-tech-mono); }
        /* Nhãn nhỏ kiểu mã hiệu: mono, giãn chữ, viết hoa */
        .ld-tech .ld-chip {
          display:inline-flex; align-items:center; gap:.4rem;
          font-family: var(--font-tech-mono); font-size:10px; font-weight:500;
          letter-spacing:.16em; text-transform:uppercase; color:rgba(255,255,255,.62);
          border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.05);
          border-radius:9999px; padding:.28rem .7rem; }
        .ld-tech .ld-num {
          font-size:11px; font-weight:700; letter-spacing:.1em; opacity:.85; }

        @media (prefers-reduced-motion: reduce){ .ld-beam:hover::after,.ld-mb::before{ animation:none } }
      `}</style>

      <ScrollProgress />
      <CursorGlow />
      <SectionDots sections={NAV_SECTIONS} />

      {/* ══ HEADER thích ứng ══ */}
      <header className={cn('fixed inset-x-0 top-0 z-50 transition-all duration-500',
        scrolled ? 'border-b border-white/[0.08] bg-[#06060B]/80 py-2.5 backdrop-blur-xl' : 'py-4')}>
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 sm:px-8">
          <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-2">
            <LogoMark className="size-8 text-white" />
            <span className="font-serif text-lg font-semibold tracking-wide">MeoArc</span>
          </button>
          <button onClick={goCta}
            className={cn('flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-all duration-300 active:scale-95',
              scrolled
                ? 'bg-[#F0A848] text-[#1a1206] shadow-[0_8px_30px_-8px_rgba(240,168,72,0.6)] hover:-translate-y-0.5'
                : 'border border-white/15 bg-white/[0.07] text-white backdrop-blur-md hover:bg-white/[0.12]')}>
            {scrolled && !isAuthenticated ? 'Dùng thử miễn phí' : ctaLabel}
            <ArrowRight className="size-4" />
          </button>
        </div>
      </header>

      {/* ══ MÀN 1 → MÀN 2: đè lên nhau theo tốc độ cuộn ══ */}
      <StackReveal
        base={<HeroPanel onCta={goCta} onSeeMore={seeMore}
          ctaPrimary={isAuthenticated ? 'Vào MeoArc ngay' : 'Bắt đầu miễn phí'} />}
        cover={<BenefitsPanel />}
      />

      <GlowDivider />

      {/* ══ SỐ LIỆU — nền lưới phối cảnh chạy về chân trời ══ */}
      <section className="relative overflow-hidden bg-white/[0.02] py-16">
        <GridFloor tone="#8B7BF0" className="opacity-70" />
        <div aria-hidden className="absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-[#06060B] to-transparent" />
        <div aria-hidden className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#06060B] to-transparent" />
        <div className="relative z-10 mx-auto grid max-w-5xl grid-cols-2 gap-8 px-6 sm:grid-cols-4">
          {[
            { v: 16, s: '', l: 'Use case đã dựng' },
            { v: 7, s: '', l: 'Nhóm phân loại tự động' },
            { v: 2, s: '', l: 'Nhà cung cấp thư' },
            { v: 100, s: '%', l: 'Việc rủi ro cần bạn duyệt' },
          ].map((k) => (
            <div key={k.l} className="text-center">
              <p className="font-serif text-4xl font-bold sm:text-5xl">
                <CountUp to={k.v} suffix={k.s} className="bg-gradient-to-b from-white to-white/50 bg-clip-text text-transparent" />
              </p>
              <p className="mt-2 text-[12px] leading-snug text-white/50">{k.l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ══ AGENT THẬT SỰ — video metal human phủ TOÀN MÀN ══ */}
      <section ref={agentRef} id="agent"
        className="relative flex min-h-screen items-end overflow-hidden py-20 sm:items-center sm:py-24">
        {/* Desktop: đẩy tượng sang phải, chữ bên trái. Điện thoại: tượng ở giữa, chữ dồn xuống dưới. */}
        <VideoBackdrop
          src="/landing/metal-human.mp4" poster="/landing/metal-human.jpg"
          tint="cyan" dim="none" parallax play="inview"
          className="[&_img]:object-center [&_video]:object-center sm:[&_img]:object-[72%_center] sm:[&_video]:object-[72%_center]"
        />
        {/* Điện thoại tối từ DƯỚI lên (giữ mặt tượng lộ ra); desktop tối từ TRÁI sang */}
        <div aria-hidden className="absolute inset-0 z-0 bg-gradient-to-t from-[#06060B] via-[#06060B]/75 to-transparent sm:bg-gradient-to-r sm:via-[#06060B]/85" />
        <div aria-hidden className="absolute inset-x-0 top-0 z-0 h-32 bg-gradient-to-b from-[#06060B] to-transparent" />
        <div aria-hidden className="absolute inset-x-0 bottom-0 z-0 h-32 bg-gradient-to-t from-[#06060B] to-transparent" />

        <motion.div style={reduced ? undefined : { y: agentTextY }}
          className="relative z-10 mx-auto w-full max-w-6xl px-6">
          <div className="max-w-xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#4FD1C5]/25 bg-[#4FD1C5]/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#4FD1C5]">
              <Sparkles className="size-3.5" />Agent-native
            </span>
            <h2 className="mt-5 font-serif text-3xl font-bold leading-[1.12] sm:text-[3rem]">
              <TextGenerate text="Không phải chatbot." />
              <br />
              <span className="text-[#4FD1C5]"><TextGenerate text="Là một agent thật sự." /></span>
            </h2>
            <p className="mt-5 text-[15px] leading-relaxed text-white/70 sm:text-base">
              Chatbot chỉ trả lời. MeoArc nhận yêu cầu tiếng Việt, tự vạch kế hoạch nhiều bước,
              gọi đúng công cụ qua giao thức MCP, chạy tuần tự rồi báo lại kết quả — và dừng xin phép
              mỗi khi chạm tới việc không hoàn tác được.
            </p>
            <ul className="mt-7 space-y-3">
              {[
                'Hiểu tiếng Việt tự nhiên, hỏi lại khi yêu cầu mơ hồ',
                'Tự chia việc thành nhiều bước và hiện kế hoạch trước khi chạy',
                'Trợ lý ngoài (Claude Desktop, Codex…) gọi được qua MCP',
              ].map((t, i) => (
                <Reveal key={t} delay={i * 0.1}>
                  <li className="flex items-start gap-3 text-[14.5px] text-white/80">
                    <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-[#4FD1C5]/20">
                      <Check className="size-3 text-[#4FD1C5]" />
                    </span>
                    {t}
                  </li>
                </Reveal>
              ))}
            </ul>
          </div>
        </motion.div>
      </section>

      <GlowDivider tone="cyan" />

      {/* ══ TÍNH NĂNG — zig-zag, mỗi hình chứng minh đúng tiêu đề ══ */}
      <section id="features" className="relative py-24 sm:py-28">
        <Aurora className="opacity-60" />
        <div className="relative z-10 mx-auto max-w-6xl px-6">
          <Reveal className="mx-auto max-w-2xl text-center">
            <p className="ld-chip mx-auto">Tính năng</p>
            <h2 className="mt-3 font-serif text-3xl font-bold sm:text-[2.6rem]">MeoArc giải quyết việc gì</h2>
          </Reveal>

          {/* BENTO ưu tiên HÌNH: mỗi ô chỉ một nhãn ngắn + một hình chứng minh.
              Bỏ hẳn các đoạn văn dài — người xem lướt bằng mắt, không đọc. */}
          <div className="mt-12 grid gap-3 sm:grid-cols-12">
            {/* Ô lớn — màn duyệt bản nháp */}
            <Reveal className="sm:col-span-7">
              <SpotCard className="group relative h-full overflow-hidden p-5">
                <div aria-hidden className="absolute -right-16 -top-16 size-52 rounded-full bg-[#F0A848]/15 blur-3xl" />
                <div className="relative flex items-center justify-between">
                  <span className="ld-chip">
                    <ShieldCheck className="size-3.5" />Human-in-the-loop
                  </span>
                  <span className="ld-num text-[#F0A848]">01</span>
                </div>
                <h3 className="ld-title relative mt-3 text-2xl sm:text-[1.75rem]">
                  Bạn bấm nút cuối
                </h3>
                <div className="relative mt-4"><AppMock compact /></div>
              </SpotCard>
            </Reveal>

            {/* Ô — hai nguồn hội tụ */}
            <Reveal delay={0.06} className="sm:col-span-5">
              <SpotCard className="relative h-full overflow-hidden p-5">
                <div aria-hidden className="absolute -left-12 -top-12 size-44 rounded-full bg-[#4FD1C5]/15 blur-3xl" />
                <div className="relative flex items-center justify-between">
                  <span className="ld-chip"><Mails className="size-3.5" />Đa nền tảng</span>
                  <span className="ld-num text-[#4FD1C5]">02</span>
                </div>
                <h3 className="ld-title relative mt-3 text-2xl sm:text-[1.75rem]">Hai hộp thư, một nơi</h3>
                <div className="relative mt-4"><UnifiedInboxMock /></div>
              </SpotCard>
            </Reveal>

            {/* Ba ô nhỏ — ICON KHỔNG LỒ, chỉ vài chữ */}
            {[
              { icon: Tags, n: '03', c: '#8B7BF0', t: '7 nhóm', s: 'tự gắn nhãn' },
              { icon: Mic, n: '04', c: '#F06AA8', t: 'Giọng nói', s: 'và ⌘K' },
              { icon: Zap, n: '05', c: '#4FD1C5', t: 'MCP', s: 'cho trợ lý ngoài' },
            ].map((b, i) => (
              <Reveal key={b.n} delay={0.12 + i * 0.06} className="sm:col-span-4">
                <SpotCard className="group relative h-full overflow-hidden p-5">
                  {/* icon lớn mờ làm hoạ tiết nền */}
                  <b.icon
                    aria-hidden
                    className="pointer-events-none absolute -bottom-5 -right-4 size-32 opacity-[0.07] transition-transform duration-700 group-hover:scale-110"
                    style={{ color: b.c }}
                  />
                  <div className="relative flex items-center justify-between">
                    <span className="flex size-11 items-center justify-center rounded-2xl"
                      style={{ background: `${b.c}20`, color: b.c }}>
                      <b.icon className="size-5.5" />
                    </span>
                    <span className="ld-num" style={{ color: b.c }}>{b.n}</span>
                  </div>
                  <h3 className="ld-title relative mt-5 text-2xl">{b.t}</h3>
                  <p className="relative mt-0.5 text-[13px] text-white/45">{b.s}</p>
                </SpotCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ══ BENTO — nền hạt sáng trôi + chùm quét chéo ══ */}
      <section id="auto" className="relative overflow-hidden py-20 sm:py-24">
        <ParticleField tone="#87F5F5" count={22} />
        <BeamSweep tone="#8B7BF0" />
        <div className="relative z-10 mx-auto max-w-6xl px-6">
          <Reveal className="mx-auto max-w-2xl text-center">
            <p className="ld-chip mx-auto">Tự động hoá</p>
            <h2 className="mt-3 font-serif text-3xl font-bold sm:text-[2.6rem]">Hộp thư tự xếp gọn mỗi ngày</h2>
          </Reveal>
          <div className="mt-12 grid gap-4 sm:grid-cols-12">
            <Reveal className="sm:col-span-7">
              <SpotCard className="h-full p-7">
                <h3 className="font-serif text-2xl font-bold">7 nhóm, gắn nhãn ngay khi thư vừa đến</h3>
                <p className="mt-2 text-[14px] leading-relaxed text-white/60">
                  Không cần bạn tạo bộ lọc thủ công. MeoArc đọc nội dung và tự chọn nhóm phù hợp.
                </p>
                <div className="mt-6 flex flex-wrap gap-2">
                  {CATS.map((c, i) => (
                    <motion.span key={c.n}
                      initial={reduced ? false : { opacity: 0, scale: 0.85 }}
                      whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
                      transition={{ delay: i * 0.06, duration: 0.4 }}
                      className="rounded-xl border px-3 py-1.5 text-[13px] font-medium"
                      style={{ borderColor: `${c.c}44`, background: `${c.c}1a`, color: c.c }}>
                      {c.n}
                    </motion.span>
                  ))}
                </div>
              </SpotCard>
            </Reveal>
            {SKILLS.map((s, i) => (
              <Reveal key={s.t} delay={0.05 * i} className={cn(i === 0 ? 'sm:col-span-5' : 'sm:col-span-4')}>
                <SpotCard className="h-full p-6">
                  <span className="flex size-10 items-center justify-center rounded-xl bg-[#4FD1C5]/15 text-[#4FD1C5]">
                    <s.icon className="size-5" />
                  </span>
                  <h3 className="mt-4 text-base font-semibold">{s.t}</h3>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-white/55">{s.d}</p>
                </SpotCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ══ CÁCH VẬN HÀNH ══ */}
      <section id="how" className="relative border-y border-white/[0.07]">
        <div className="mx-auto max-w-6xl px-6 pt-24">
          <Reveal className="mx-auto max-w-2xl text-center">
            <p className="ld-chip mx-auto">Chuyện một lá thư</p>
            <h2 className="mt-3 font-serif text-3xl font-bold sm:text-[2.6rem]">Từ lúc bạn nói đến khi thư tới tay</h2>
            <p className="mt-3 text-[14px] text-white/50">Cuộn chậm để nghe hết bốn trang chuyện.</p>
          </Reveal>
        </div>
        {/* Khung truyện: dải cảnh đêm trượt ngang nhiều lớp, nằm trọn trong một khung */}
        <LetterTale />
      </section>

      {/* ══ NỀN TẢNG — vệt sáng quét ngang phía sau dải thương hiệu ══ */}
      <section className="relative overflow-hidden py-16 sm:py-20">
        <BeamSweep tone="#4FD1C5" className="opacity-70" />
        <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-white/40">Xây dựng trên</p>
        </div>
        <div className="mt-7"><Marquee items={TECHS} /></div>
        <p className="mt-8 px-6 text-center text-[13px] text-white/35">
          Đồ án Nhập môn Công nghệ Phần mềm — Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM · Nhóm 7
        </p>
      </section>

      {/* ══ FAQ — nền đường đồng mức, tĩnh và mảnh nên không cướp sự chú ý khi đọc ══ */}
      <section id="faq" className="relative overflow-hidden py-16 sm:py-20">
        <ContourLines tone="#8B7BF0" className="opacity-60" />
        <div className="relative z-10 mx-auto max-w-3xl px-6">
          <Reveal className="text-center">
            <p className="ld-chip mx-auto">Giải đáp</p>
            <h2 className="mt-3 font-serif text-3xl font-bold sm:text-[2.4rem]">Câu hỏi thường gặp</h2>
          </Reveal>
          <div className="mt-10">{FAQS.map((f) => <FaqItem key={f.q} q={f.q} a={f.a} />)}</div>
        </div>
      </section>

      {/* ══ CTA CUỐI — video thuyền giữa biển, có parallax ══ */}
      <section id="start" className="relative flex min-h-[94vh] items-center justify-center overflow-hidden py-24">
        {/* Video HÀNH TRÌNH LÁ THƯ thay cho cảnh sa mạc.
            Sa mạc là ẩn dụ đẹp nhưng nói về sự trống trải — sai thông điệp ở đúng chỗ
            người xem sắp bấm nút. Đoạn hành trình thì cho thấy sản phẩm đang làm việc,
            và nó khép lại vòng đã mở ở mục "Chuyện một lá thư" phía trên. */}
        <VideoBackdrop src={JOURNEY_VIDEO} poster="/landing/flower-arc.jpg"
          tint="violet" dim="soft" parallax play="inview" />
        <div className="relative z-10 mx-auto max-w-2xl px-6 text-center">
          <Reveal>
            <div className="relative mx-auto mb-6 w-fit">
              <span aria-hidden className="absolute inset-0 rounded-full bg-[#8B7BF0]/50 blur-2xl"
                style={{ animation: reduced ? undefined : 'ld-breathe 3.2s ease-in-out infinite' }} />
              <div className="relative flex size-[92px] items-center justify-center rounded-full border border-[#8B7BF0]/30 bg-[#8B7BF0]/10 backdrop-blur-md">
                <MeoMascot mood="happy" className="size-14" />
              </div>
            </div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#8B7BF0]">Chặng cuối · bắt đầu thôi</p>
            <h2 className="mt-4 font-serif text-4xl font-bold leading-tight drop-shadow-[0_2px_24px_rgba(0,0,0,0.7)] sm:text-5xl">
              Hộp thư rộng như sa mạc.
              <br />
              Để mèo <span className="text-[#F0A848]">dẫn đường</span>.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-[15px] text-white/75">
              Kết nối trong 30 giây bằng chính tài khoản Google hoặc Outlook của bạn.
            </p>
            <form onSubmit={(e) => { e.preventDefault(); goCta() }}
              className="mx-auto mt-8 flex w-full max-w-md flex-col gap-2.5 sm:flex-row">
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="email@cua-ban.com" aria-label="Địa chỉ email"
                className="min-w-0 flex-1 lit-edge rounded-2xl bg-white/[0.07] px-4 py-3.5 text-[15px] text-white outline-none backdrop-blur-md placeholder:text-white/35 [--lit:#FFB03A]" />
              <MovingBorderButton className="justify-center">
                {isAuthenticated ? 'Vào MeoArc' : 'Bắt đầu'}
                <ArrowRight className="size-4.5" />
              </MovingBorderButton>
            </form>
            <p className="mt-3 flex items-center justify-center gap-1.5 text-[12px] text-white/50">
              <Lock className="size-3.5" />
              Bạn sẽ đăng nhập bằng chính tài khoản của email này — MeoArc không lưu mật khẩu.
            </p>
          </Reveal>
        </div>
        {/* Lá thư nghịch ngợm: rê chuột lại gần là nó né, né đủ 5 lần mới cho bắt */}
        <div className="absolute bottom-20 left-1/2 z-20 -translate-x-1/2">
          <PlayfulLetter tone="#F0A848" size="w-14" />
        </div>
      </section>

      {/* ══ FOOTER ══ */}
      <footer className="border-t border-white/[0.07] py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <LogoMark className="size-6 text-white/70" />
            <span className="font-serif text-base font-semibold text-white/70">MeoArc</span>
          </div>
          <p className="text-center text-[12px] text-white/35">© 2026 MeoArc · Đồ án Nhập môn CNPM — HCMUS, Nhóm 7</p>
          <button onClick={goCta} className="text-[13px] font-medium text-white/60 transition-colors hover:text-white">
            {ctaLabel} →
          </button>
        </div>
      </footer>

      {/* ══ CTA đáy cho điện thoại ══ */}
      <div className={cn('fixed inset-x-0 bottom-0 z-50 lit-edge bg-[#06060B]/90 p-3 backdrop-blur-xl transition-transform duration-500 sm:hidden',
        scrolled ? 'translate-y-0' : 'translate-y-full')}>
        <button onClick={goCta}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#F0A848] py-3.5 text-[15px] font-semibold text-[#1a1206] active:scale-[0.98]">
          {isAuthenticated ? 'Vào MeoArc' : 'Bắt đầu miễn phí'}
          <ArrowDownToLine className="size-4.5 rotate-[-90deg]" />
        </button>
      </div>
    </div>
  )
}
