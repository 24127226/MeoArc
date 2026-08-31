import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, ArrowLeft, AlertTriangle, ChevronDown } from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { cn } from '@/lib/utils'
import { LogoMark } from '@/components/logo'
import { MeoMascot } from '@/components/meo-mascot'

/* ══════════════════════════════════════════════════════════════════════════════
   TRANG ĐĂNG NHẬP (UC001) — hero tối toàn màn.

   Nền là video chạy vòng với nhịp MỜ DẦN do JS điều khiển: 0.5s hiện ở đầu, 0.5s
   tắt ở cuối, hết thì đưa về 0 rồi phát lại — chuyển vòng êm, không giật khung
   như thuộc tính loop mặc định.

   Phía sau nội dung có một khối mờ lớn (blur 82px) làm nền cho chữ, nên không cần
   phủ gradient lên video. Dải thương hiệu chạy ngang ở đáy.

   Logic OAuth giữ nguyên: Google (mặc định) và Outlook (đa nhà cung cấp).
   ══════════════════════════════════════════════════════════════════════════════ */

const HERO_VIDEO =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_065045_c44942da-53c6-4804-b734-f9e07fc22e08.mp4'
const FALLBACK_VIDEO = '/landing/flower-arc.mp4'

const BRANDS = ['Gmail', 'Outlook', 'Gemini', 'LangGraph', 'FastAPI', 'MCP']

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.4-1.7 4.1-5.5 4.1-3.3 0-6-2.7-6-6.1S8.7 5.9 12 5.9c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.3 14.6 2.3 12 2.3 6.9 2.3 2.8 6.4 2.8 11.5S6.9 20.7 12 20.7c5.3 0 8.8-3.7 8.8-8.9 0-.6-.07-1.1-.16-1.6H12z" />
    </svg>
  )
}

function MicrosoftIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <rect x="3" y="3" width="8" height="8" fill="#F25022" />
      <rect x="13" y="3" width="8" height="8" fill="#7FBA00" />
      <rect x="3" y="13" width="8" height="8" fill="#00A4EF" />
      <rect x="13" y="13" width="8" height="8" fill="#FFB900" />
    </svg>
  )
}

/** Video nền với nhịp mờ dần do JS điều khiển (không dùng thuộc tính loop). */
function FadingVideo() {
  const ref = useRef<HTMLVideoElement>(null)
  const [src, setSrc] = useState(HERO_VIDEO)

  useEffect(() => {
    const v = ref.current
    if (!v) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      v.style.opacity = '0.55'
      return
    }
    const FADE = 0.5
    let raf = 0
    // Phân vai rõ ràng: HIỆN DẦN do CSS transition lo (bền, không cần khung hình),
    // rAF chỉ lo TẮT DẦN ở cuối để chuyển vòng cho êm. Nếu vòng lặp khung hình có
    // dừng thì opacity vẫn nằm ở 1 — video hiện bình thường thay vì biến mất.
    const tick = () => {
      if (v.duration && Number.isFinite(v.duration)) {
        const left = v.duration - v.currentTime
        v.style.opacity = left < FADE ? String(Math.max(0, left / FADE)) : '1'
      }
      raf = requestAnimationFrame(tick)
    }
    // Lưới an toàn: nếu vòng lặp khung hình không chạy (tab nền, chế độ tiết kiệm
    // pin), video sẽ kẹt ở opacity 0 và nền thành đen trơn. Nên vừa sẵn sàng phát
    // là cho hiện luôn bằng transition CSS; rAF chỉ lo phần chuyển vòng cho mượt.
    const reveal = () => { v.style.transition = 'opacity 0.5s linear'; v.style.opacity = '1' }
    if (v.readyState >= 2) reveal()
    v.addEventListener('canplay', reveal, { once: true })
    const onEnded = () => {
      v.style.opacity = '0'
      window.setTimeout(() => {
        v.currentTime = 0
        void v.play().catch(() => {})
        v.style.opacity = '1' // tự bật lại, không trông chờ vòng lặp khung hình
      }, 100)
    }
    v.addEventListener('ended', onEnded)
    void v.play().catch(() => {})
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      v.removeEventListener('ended', onEnded)
      v.removeEventListener('canplay', reveal)
    }
  }, [src])

  return (
    <video
      ref={ref}
      key={src}
      src={src}
      autoPlay
      muted
      playsInline
      preload="auto"
      onError={() => setSrc((s) => (s === HERO_VIDEO ? FALLBACK_VIDEO : s))}
      className="absolute inset-0 size-full object-cover opacity-0"
    />
  )
}

export function LoginPage() {
  const { isAuthenticated, isLoading, loginWithGoogle, loginWithOutlook } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const loginError = params.get('loi')
  const errorDetail = params.get('chi_tiet')
  const ERROR_LABEL: Record<string, string> = {
    doi_token: 'Không đổi được mã uỷ quyền lấy token',
    lay_ho_so: 'Không lấy được hồ sơ tài khoản Microsoft',
    'microsoft-tu-choi': 'Microsoft từ chối yêu cầu đăng nhập',
    'thieu-code': 'Microsoft không gửi mã uỷ quyền',
    'khong-xac-dinh': 'Lỗi không lường trước',
  }

  useEffect(() => {
    if (isAuthenticated) navigate('/app', { replace: true })
  }, [isAuthenticated, navigate])

  const handleLogin = async () => {
    await loginWithGoogle()
    navigate('/app', { replace: true })
  }
  const handleOutlookLogin = async () => {
    await loginWithOutlook()
    navigate('/app', { replace: true })
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#06060B] text-white">
      <style>{`
        @keyframes lg-marquee { from { transform: translateX(0%) } to { transform: translateX(-50%) } }
        .lg-marquee { animation: lg-marquee 20s linear infinite; }
        @media (prefers-reduced-motion: reduce) { .lg-marquee { animation: none } }
      `}</style>

      <FadingVideo />

      {/* Khối mờ lớn phía sau nội dung — thay cho việc phủ gradient lên video */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 h-[527px] w-[984px] max-w-[130vw] -translate-x-1/2 -translate-y-1/2 bg-gray-950 opacity-90 blur-[82px]"
      />

      <section className="relative z-10 flex min-h-screen flex-col">
        {/* ── Thanh trên ── */}
        <nav className="flex items-center justify-between px-6 py-5 sm:px-8">
          <button onClick={() => navigate('/')} className="flex items-center gap-2">
            <LogoMark className="size-8 text-white" />
            <span className="font-serif text-lg font-semibold tracking-wide">MeoArc</span>
          </button>

          <div className="hidden items-center gap-7 md:flex">
            {[
              { label: 'Tính năng', chev: true },
              { label: 'Cách vận hành', chev: false },
              { label: 'Gói dịch vụ', chev: false },
              { label: 'Giải đáp', chev: true },
            ].map((n) => (
              <button
                key={n.label}
                onClick={() => navigate('/')}
                className="flex items-center gap-1 text-sm text-white/90 transition-colors hover:text-white"
              >
                {n.label}
                {n.chev && <ChevronDown className="size-3.5 opacity-70" />}
              </button>
            ))}
          </div>

          <button
            onClick={() => navigate('/')}
            className="liquid-glass rounded-full px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/[0.06]"
          >
            <span className="flex items-center gap-1.5">
              <ArrowLeft className="size-3.5" />
              Trang giới thiệu
            </span>
          </button>
        </nav>
        <div className="mt-[3px] h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* ── Nội dung giữa ── */}
        <div className="flex flex-1 items-center justify-center px-6 py-10">
          <div className="grid w-full max-w-6xl items-center gap-10 lg:grid-cols-2">
            {/* Trái: lời chào */}
            <div className="text-center lg:text-left">
              <h1
                className="font-serif font-normal leading-[1.02] tracking-[-0.024em]"
                style={{ fontSize: 'clamp(3rem, 9vw, 7rem)' }}
              >
                <span className="text-white">Mèo </span>
                <span
                  className="bg-clip-text text-transparent"
                  style={{ backgroundImage: 'linear-gradient(to left, #6366f1, #a855f7, #fcd34d)' }}
                >
                  AI
                </span>
              </h1>
              <p className="mx-auto mt-[9px] max-w-md text-lg leading-8 text-white/80 lg:mx-0">
                Trợ lý thư mạnh nhất từng được giao cho
                <br />
                một chú mèo — đang chờ bạn ở bên trong.
              </p>

              <div className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12.5px] text-white/55 lg:justify-start">
                {['Không tự ý gửi thư', 'Thu hồi quyền bất cứ lúc nào', 'Gmail & Outlook'].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <span className="size-1 rounded-full bg-white/50" />
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Phải: thẻ đăng nhập */}
            <div className="mx-auto w-full max-w-md">
              <div className="liquid-glass rounded-3xl p-7">
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-4">
                    <span aria-hidden className="absolute inset-0 rounded-full bg-[#a855f7]/35 blur-2xl" />
                    <div className="relative flex size-[72px] items-center justify-center rounded-full border border-white/15 bg-white/[0.06]">
                      <MeoMascot mood="happy" className="size-11" />
                    </div>
                  </div>
                  <h2 className="font-serif text-2xl font-semibold">Đăng nhập MeoArc</h2>
                  <p className="mt-1.5 text-[13.5px] text-white/60">
                    Kết nối hộp thư để chú mèo bắt đầu dọn giúp bạn.
                  </p>
                </div>

                {loginError && (
                  <div className="mt-5 rounded-2xl border border-[#FF6FB5]/35 bg-[#FF6FB5]/10 p-3.5 text-left">
                    <p className="flex items-center gap-2 text-[13px] font-semibold text-[#FF9ECF]">
                      <AlertTriangle className="size-4 shrink-0" />
                      {ERROR_LABEL[loginError] ?? 'Đăng nhập không thành công'}
                    </p>
                    {errorDetail && (
                      <p className="mt-1.5 break-words text-[12px] leading-relaxed text-white/65">{errorDetail}</p>
                    )}
                    <p className="mt-2 text-[11px] text-white/40">Thử lại, hoặc dùng tài khoản Google.</p>
                  </div>
                )}

                <button
                  onClick={handleLogin}
                  disabled={isLoading}
                  className={cn(
                    'btn-cut mt-6 flex w-full items-center justify-center gap-3 bg-white px-4 py-3.5 text-[15px] font-semibold text-black',
                    'transition-all duration-200 hover:bg-white/90 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-70',
                  )}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="size-5 animate-spin" />
                      Đang kết nối…
                    </>
                  ) : (
                    <>
                      <GoogleIcon className="size-5" />
                      Đăng nhập với Google
                    </>
                  )}
                </button>

                <button
                  onClick={handleOutlookLogin}
                  disabled={isLoading}
                  className="btn-cut-border mt-3 flex w-full items-center justify-center gap-3 px-4 py-3.5 text-[15px] font-semibold text-white transition-colors hover:bg-white/10 disabled:pointer-events-none disabled:opacity-70"
                >
                  <span className="flex items-center gap-3">
                    <MicrosoftIcon className="size-5" />
                    Đăng nhập với Outlook
                  </span>
                </button>

                <p className="mt-5 text-center text-[11px] leading-relaxed text-white/45">
                  MeoArc sẽ xin quyền <span className="text-white/70">đọc &amp; quản lý thư</span> (gắn nhãn,
                  lưu trữ, soạn/gửi). Bạn có thể thu hồi bất cứ lúc nào trong phần Cài đặt.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Dải nền tảng chạy ngang ở đáy ── */}
        <div className="pb-10">
          <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 px-6 md:flex-row md:gap-12">
            <p className="shrink-0 text-center text-sm text-white/50 md:text-left">
              Dựng trên nền tảng
              <br />
              được tin dùng toàn cầu
            </p>
            <div className="relative w-full overflow-hidden"
              style={{
                maskImage: 'linear-gradient(90deg, transparent, black 8%, black 92%, transparent)',
                WebkitMaskImage: 'linear-gradient(90deg, transparent, black 8%, black 92%, transparent)',
              }}>
              <div className="lg-marquee flex w-max items-center gap-16">
                {[...BRANDS, ...BRANDS].map((b, i) => (
                  <span key={`${b}-${i}`} className="flex shrink-0 items-center gap-3">
                    <span className="liquid-glass flex size-6 items-center justify-center rounded-lg text-[11px] font-bold text-white">
                      {b[0]}
                    </span>
                    <span className="text-base font-semibold text-white">{b}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
