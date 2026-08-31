import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Check, Loader2, X, Sparkles, Zap, Crown } from 'lucide-react'
import { api } from '@/lib/api'
import type { Plan, SubscriptionStatus } from '@/lib/api'
import { cn } from '@/lib/utils'
import { useToast } from '@/components/ui/toast'
import { TOKENS_PER_TURN } from '@/lib/subscription'

/* ══════════════════════════════════════════════════════════════════════════════
   TRANG NÂNG CẤP — chiếm TRỌN khung hình, KHÔNG cuộn.

   Ba điểm kỹ thuật quan trọng:
   1. Render qua PORTAL thẳng vào <body>. Nếu đặt trong cây DOM của ChatPanel thì
      z-index bị nhốt trong stacking context của panel → thanh điều hướng và danh
      sách thư vẫn đè lên trên.
   2. Bố cục vừa khít một màn: khung h-screen + overflow-hidden, phần thẻ giá co
      giãn theo chiều cao còn lại (flex-1 min-h-0) nên không bao giờ phải kéo.
   3. Khoá cuộn nền khi mở.

   Ngôn ngữ thị giác "khoa học viễn tưởng": nền đen tuyệt đối, video phát sáng phủ
   nửa dưới, wordmark MEOARC khổng lồ ghim đáy, chữ hiện dần từ mặt nạ mờ, con trỏ
   tuỳ biến (vòng bám tức thì + thẻ kính trễ nhịp). Màu nhấn CYAN của MeoArc.
   ══════════════════════════════════════════════════════════════════════════════ */

const NEON = '#87F5F5'
const TIER_ICON: Record<string, React.ElementType> = { free: Sparkles, pro: Zap, max: Crown }

/** Nền màn nâng cấp gói — đoạn phim của bản mẫu Asme, ĐÃ TỰ HOST.
 *
 *  Bản gốc là một luồng HLS trên Mux (`.m3u8`). Dùng nguyên nó thì phải kéo thêm
 *  thư viện `hls.js` (~400 KB) vì ngoài Safari ra không trình duyệt nào phát
 *  được HLS trực tiếp — tức là bốn trăm kilobyte cho một cái nền trang trí.
 *
 *  ffmpeg đọc thẳng được `.m3u8`, nên lấy về rồi chuyển thành mp4 thường: bỏ
 *  được cả phụ thuộc lẫn rủi ro CDN, và nhẹ hơn (840 KB cho 12 giây).
 *
 *  Vẫn giữ đường lùi: nền hỏng thì màn này chỉ mất phần trang trí, chứ các gói
 *  và nút chọn vẫn dùng được bình thường. */
const HERO_VIDEO = '/landing/asme-hero.mp4'
const FALLBACK_VIDEO = '/landing/flower-field.mp4'

function shortNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1).replace('.', ',')}Tr`
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`
  return String(n)
}
const formatVnd = (n: number) => (n === 0 ? 'Miễn phí' : `${n.toLocaleString('vi-VN')}₫`)

/** Chữ hiện từng TỪ, trượt lên khỏi mặt nạ + tan mờ dần. */
function WordReveal({ text, delayStep = 0.1 }: { text: string; delayStep?: number }) {
  const words = text.split(' ')
  return (
    <>
      {words.map((w, i) => (
        <span key={`${w}-${i}`} className="ps-word-wrap">
          <span className="ps-word-inner" style={{ animationDelay: `${i * delayStep}s` }}>{w}</span>
          {i < words.length - 1 ? ' ' : ''}
        </span>
      ))}
    </>
  )
}

/** Wordmark khổng lồ: hiện từng CHỮ CÁI, trượt vào từ bên trái. */
function LetterReveal({ text }: { text: string }) {
  return (
    <>
      {[...text].map((ch, i) => (
        <span key={i} className="ps-letter-wrap">
          <span className="ps-letter-inner" style={{ animationDelay: `${i * 0.09}s` }}>
            {ch === ' ' ? ' ' : ch}
          </span>
        </span>
      ))}
    </>
  )
}

/** Con trỏ tuỳ biến: vòng bám tức thì + thẻ kính trễ nhịp (nội suy tuyến tính). */
function SciFiCursor({ label }: { label: string }) {
  const ring = useRef<HTMLDivElement>(null)
  const card = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    let mx = innerWidth / 2, my = innerHeight / 2
    let cx = mx, cy = my
    let scale = 0, target = 0
    let first = true
    let raf = 0

    const onMove = (e: PointerEvent) => {
      mx = e.clientX; my = e.clientY
      if (first) { cx = mx; cy = my; first = false }
      const overBtn = (e.target as HTMLElement)?.closest?.('button, a')
      target = overBtn ? 0 : 1
      ring.current?.classList.toggle('ps-ring-big', !!overBtn)
    }
    const onLeave = () => { target = 0 }

    const loop = () => {
      cx += (mx - cx) * 0.08          // thẻ kính bám trễ
      cy += (my - cy) * 0.08
      scale += (target - scale) * 0.15
      const ringScale = ring.current?.classList.contains('ps-ring-big') ? 1.6 : 1
      if (ring.current) {
        ring.current.style.transform =
          `translate3d(${mx}px, ${my}px, 0) translate(-50%, -50%) scale(${ringScale})`
        ring.current.style.opacity = first ? '0' : '1'
      }
      if (card.current) {
        card.current.style.transform =
          `translate3d(${cx}px, ${cy}px, 0) translate(-50%, -50%) scale(${scale})`
        card.current.style.opacity = String(scale)
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    window.addEventListener('pointermove', onMove)
    document.addEventListener('mouseleave', onLeave)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('pointermove', onMove)
      document.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  return (
    <>
      <div ref={ring} aria-hidden className="ps-ring" />
      <div ref={card} aria-hidden className="ps-cursor-card">
        <span className="ps-cursor-text">{label}</span>
      </div>
    </>
  )
}

export function PricingScreen({ open, onClose, status, onChanged }: {
  open: boolean
  onClose: () => void
  status: SubscriptionStatus | null
  onChanged: (s: SubscriptionStatus) => void
}) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [videoSrc, setVideoSrc] = useState(HERO_VIDEO)
  const toast = useToast()

  useEffect(() => {
    if (!open) return
    let alive = true
    api.plans().then((p) => alive && setPlans(p)).catch(() => {})
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      alive = false
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, onClose])

  if (!open) return null

  const choose = async (tier: string) => {
    if (tier === status?.tier) return
    setBusy(tier)
    try {
      const next = await api.setTier(tier)
      onChanged(next)
      toast(`Đã chuyển sang gói ${next.tierLabel}`, 'success')
    } catch {
      toast('Không đổi được gói, thử lại sau', 'destructive')
    } finally {
      setBusy(null)
    }
  }

  // PORTAL: thoát khỏi mọi stacking context của panel cha → không bị nav/danh sách thư đè.
  return createPortal(
    <div className="ps-root fixed inset-0 z-[2147483000] flex h-screen w-screen flex-col overflow-hidden bg-black text-white">
      <style>{`
        .ps-root { cursor: none; }
        .ps-root button, .ps-root a { cursor: none; }

        .ps-video { position:absolute; bottom:0; left:0; width:100%; height:84%; overflow:hidden; z-index:0; }
        .ps-video video, .ps-video img { width:100%; height:112%; object-fit:cover; display:block; }
        .ps-fade-top { position:absolute; inset:0 0 auto 0; height:66%; z-index:1; pointer-events:none;
          background: linear-gradient(180deg,#000 0%,rgba(0,0,0,0.93) 32%,rgba(0,0,0,0.55) 70%,transparent 100%); }
        .ps-fade-bottom { position:absolute; inset:auto 0 0 0; height:40%; z-index:1; pointer-events:none;
          background: linear-gradient(0deg,#000 8%,rgba(0,0,0,0.72) 46%,transparent 100%); }

        .ps-wordmark { position:absolute; bottom:-1.2vh; left:0; right:0; z-index:2; pointer-events:none;
          text-align:center; white-space:nowrap; line-height:0.78; opacity:0.13;
          font-size:17vw; font-weight:700; letter-spacing:-0.035em; }
        .ps-letter-wrap { display:inline-block; overflow:hidden; vertical-align:bottom; line-height:0.78; }
        .ps-letter-inner { display:inline-block; opacity:0; transform:translateX(-105%); filter:blur(20px);
          animation: ps-letter 1.2s cubic-bezier(0.05,0.9,0.1,1) forwards; }
        @keyframes ps-letter { 0%{opacity:0;transform:translateX(-105%);filter:blur(20px)}
          25%{opacity:1} 100%{opacity:1;transform:translateX(0);filter:blur(0)} }

        .ps-word-wrap { display:inline-block; overflow:hidden; vertical-align:bottom;
          padding-bottom:0.16em; margin-bottom:-0.16em; }
        .ps-word-inner { display:inline-block; opacity:0; transform:translateY(105%); filter:blur(20px);
          animation: ps-word 1.3s cubic-bezier(0.05,0.9,0.1,1) forwards; }
        @keyframes ps-word { 0%{opacity:0;transform:translateY(105%);filter:blur(20px)}
          30%{opacity:1} 100%{opacity:1;transform:translateY(0);filter:blur(0)} }

        /* Thẻ giá dùng hoạt ảnh RIÊNG: chỉ nhích 22px chứ không phải 105%.
           Chữ có mặt nạ che nên trượt cả dòng thì an toàn; thẻ thì KHÔNG có mặt nạ —
           nếu hoạt ảnh không chạy (tab nền, tiết kiệm pin) thẻ sẽ kẹt ngoài màn và
           nút bấm biến mất. Dịch nhẹ + mờ dần vừa an toàn vừa đủ mượt. */
        .ps-card { opacity:0; transform:translateY(22px); filter:blur(10px);
          animation: ps-card-in 0.8s cubic-bezier(0.05,0.9,0.1,1) forwards; }
        @keyframes ps-card-in { to{ opacity:1; transform:translateY(0); filter:blur(0) } }

        .ps-ring { position:fixed; top:0; left:0; width:46px; height:46px; border-radius:50%;
          border:1.5px solid rgba(255,255,255,0.45); z-index:2147483001; pointer-events:none; opacity:0;
          transition: border-color .35s ease, opacity .35s ease; will-change:transform; }
        .ps-ring.ps-ring-big { border-color:${NEON}; box-shadow:0 0 22px -4px ${NEON}; }
        .ps-cursor-card { position:fixed; top:0; left:0; z-index:2147483002; pointer-events:none; opacity:0;
          padding:0.55rem 1.1rem; border-radius:9999px; white-space:nowrap;
          background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.18);
          backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
          box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.15); will-change:transform; }
        .ps-cursor-text { font-size:0.72rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase;
          color:${NEON}; text-shadow:0 0 10px ${NEON}66; }

        .ps-dot { width:7px; height:7px; border-radius:50%; background:${NEON}; position:relative;
          display:inline-block; animation: ps-pulse 2s infinite ease-in-out; }
        .ps-dot::after { content:''; position:absolute; inset:-5px; border-radius:50%;
          background:${NEON}55; animation: ps-wave 2s infinite ease-in-out; }
        @keyframes ps-pulse { 0%,100%{opacity:.55;transform:scale(.85);box-shadow:0 0 4px ${NEON}55}
          50%{opacity:1;transform:scale(1.1);box-shadow:0 0 14px ${NEON}} }
        @keyframes ps-wave { 0%{transform:scale(.6);opacity:.85} 100%{transform:scale(2.3);opacity:0} }

        .ps-grid { position:absolute; inset:0; z-index:1; pointer-events:none; opacity:0.3;
          background-image: linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px);
          background-size: 64px 64px;
          mask-image: radial-gradient(ellipse at 50% 26%, black 8%, transparent 70%);
          -webkit-mask-image: radial-gradient(ellipse at 50% 26%, black 8%, transparent 70%); }

        @media (prefers-reduced-motion: reduce) {
          .ps-word-inner, .ps-letter-inner, .ps-card { animation:none; opacity:1; transform:none; filter:none; }
          .ps-dot, .ps-dot::after { animation:none; }
          .ps-root, .ps-root button, .ps-root a { cursor:auto; }
          .ps-ring, .ps-cursor-card { display:none; }
        }
      `}</style>

      {/* nền */}
      <div className="ps-video" aria-hidden>
        <video
          key={videoSrc}
          src={videoSrc}
          poster="/landing/flower-field-poster.jpg"
          autoPlay muted loop playsInline preload="auto"
          onError={() => setVideoSrc((s) => (s === HERO_VIDEO ? FALLBACK_VIDEO : s))}
        />
      </div>
      <div className="ps-grid" aria-hidden />
      <div className="ps-fade-top" aria-hidden />
      <div className="ps-fade-bottom" aria-hidden />
      <div className="ps-wordmark" aria-hidden><LetterReveal text="MEOARC" /></div>

      <SciFiCursor label="Chọn gói" />

      <button
        onClick={onClose}
        aria-label="Đóng trang nâng cấp"
        className="absolute right-5 top-5 z-30 flex size-10 items-center justify-center rounded-full border border-white/15 bg-white/[0.06] text-white/70 backdrop-blur-md transition-all hover:border-white/40 hover:text-white active:scale-95"
      >
        <X className="size-4.5" />
      </button>

      {/* NỘI DUNG — vừa khít một màn, không cuộn */}
      {/* Desktop: khoá trong một màn, không kéo. Màn hẹp (điện thoại): 3 thẻ xếp dọc
          không thể nhét vừa, nên cho cuộn — thà kéo còn hơn mất nút bấm. */}
      <div className="relative z-20 flex min-h-0 flex-1 flex-col items-center overflow-y-auto px-6 pb-[9vh] pt-[3vh] md:overflow-hidden">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.05] px-3 py-1 text-[10.5px] font-medium backdrop-blur-md">
          <span className="ps-dot" />
          Hạn mức token · cập nhật theo thời gian thực
        </div>

        <h1 className="mt-3 text-center font-serif text-[1.9rem] font-bold leading-[1.08] sm:text-[2.6rem]">
          <WordReveal text="Chọn tốc độ" />
          <br />
          <span style={{ color: NEON }}><WordReveal text="cho chú mèo của bạn" delayStep={0.09} /></span>
        </h1>

        {status && (
          <p className="mt-2 text-center text-[12.5px] text-white/60">
            Đang dùng <span className="font-semibold text-white">{status.tierLabel}</span> · còn{' '}
            <span className="font-mono font-semibold" style={{ color: NEON }}>
              {shortNum(status.daily.remaining)}
            </span>{' '}
            token hôm nay
            <span className="text-white/40"> (~{Math.floor(status.daily.remaining / TOKENS_PER_TURN)} lượt)</span>
          </p>
        )}

        {/* Ba gói — PHẢI co theo chiều cao còn lại.
            grid-auto-rows:minmax(0,1fr) là mấu chốt: thiếu nó, hàng của lưới giãn
            theo nội dung và nút "Nâng cấp" bị đẩy ra ngoài màn (không bấm được). */}
        <div className="mt-3 grid w-full max-w-5xl shrink-0 gap-3 md:min-h-0 md:flex-1 md:shrink md:grid-cols-3 md:[grid-auto-rows:minmax(0,1fr)]">
          {plans.map((p, idx) => {
            const Icon = TIER_ICON[p.id] ?? Sparkles
            const current = status?.tier === p.id
            const featured = p.id === 'pro'
            return (
              <div
                key={p.id}
                style={{ animationDelay: `${0.45 + idx * 0.12}s` }}
                className={cn(
                  // `liquid-glass` thay cho viền tô đều: viền của nó là một dải
                  // sáng gắt ở mép trên/dưới và tắt ở giữa — đúng cách ánh sáng đập
                  // vào một tấm kính có bề dày. Viền một màu không ra được cảm giác đó.
                  'ps-card liquid-glass flex min-h-0 flex-col rounded-2xl p-4',
                  current ? 'bg-white/[0.10]' : featured ? 'bg-white/[0.07]' : 'bg-white/[0.035]',
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="flex size-8 items-center justify-center rounded-xl border border-white/15 bg-white/[0.06]"
                    style={{ color: NEON }}>
                    <Icon className="size-4" />
                  </span>
                  {featured && !current && (
                    <span className="rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-black"
                      style={{ background: NEON }}>Được chọn nhiều</span>
                  )}
                  {current && (
                    <span className="rounded-full border border-white/30 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider">
                      Đang dùng
                    </span>
                  )}
                </div>

                <h2 className="mt-2.5 font-serif text-xl font-bold">{p.label}</h2>
                <p className="text-[11.5px] leading-snug text-white/45">{p.tagline}</p>

                <p className="mt-2.5 font-serif text-2xl font-bold">
                  {formatVnd(p.priceVnd)}
                  {p.priceVnd > 0 && <span className="ml-1 text-[12px] font-normal text-white/45">/tháng</span>}
                </p>

                {/* hạn mức — điểm chính để demo */}
                <div className="mt-2.5 rounded-xl border border-white/10 bg-black/45 p-2.5 font-mono text-[10.5px] tabular-nums">
                  <div className="flex items-baseline justify-between">
                    <span className="text-white/40">NGÀY</span>
                    <span className="font-semibold" style={{ color: NEON }}>{shortNum(p.dailyTokens)}</span>
                  </div>
                  <div className="mt-1 flex items-baseline justify-between">
                    <span className="text-white/40">THÁNG</span>
                    <span className="font-semibold text-white/85">{shortNum(p.monthlyTokens)}</span>
                  </div>
                  <div className="mt-1.5 border-t border-white/10 pt-1.5 text-center text-[11px]">
                    <span className="font-bold" style={{ color: NEON }}>
                      {Math.floor(p.dailyTokens / TOKENS_PER_TURN)}
                    </span>
                    <span className="text-white/40"> lượt hỏi / ngày</span>
                  </div>
                </div>

                <ul className="mt-2.5 min-h-0 flex-1 space-y-1 overflow-hidden">
                  {p.features.slice(0, 3).map((f) => (
                    <li key={f} className="flex items-start gap-1.5 text-[11.5px] leading-snug text-white/60">
                      <Check className="mt-0.5 size-3 shrink-0" style={{ color: NEON }} />
                      <span className="line-clamp-2">{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => choose(p.id)}
                  disabled={current || busy !== null}
                  className={cn(
                    'mt-3 flex shrink-0 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-[13px] font-semibold transition-all active:scale-[0.98] disabled:pointer-events-none',
                    current ? 'border border-white/15 bg-white/[0.06] text-white/50'
                      : featured ? 'text-black hover:-translate-y-0.5'
                        : 'border border-white/20 bg-white/[0.08] text-white hover:-translate-y-0.5 hover:bg-white/[0.14]',
                  )}
                  style={featured && !current ? { background: NEON, boxShadow: `0 10px 40px -12px ${NEON}` } : undefined}
                >
                  {busy === p.id && <Loader2 className="size-3.5 animate-spin" />}
                  {current ? 'Gói hiện tại' : p.priceVnd === 0 ? 'Về Miễn phí' : `Nâng cấp ${p.label}`}
                </button>
              </div>
            )
          })}
        </div>

        <p className="mt-2.5 shrink-0 text-center text-[10.5px] leading-snug text-white/30">
          Bản đồ án chưa nối cổng thanh toán — chọn gói là đổi hạn mức ngay để thấy rõ ràng buộc token khi trò chuyện.
        </p>
      </div>
    </div>,
    document.body,
  )
}
