import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, ShieldCheck, Mail, Sparkles, ArrowLeft } from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { LogoMark } from '@/components/logo'
import { MeoMascot } from '@/components/meo-mascot'
import { Aurora, PlayfulLetter, SpotCard, VideoBackdrop } from '@/components/landing/ui'

/* ══════════════════════════════════════════════════════════════════════════════
   TRANG ĐĂNG NHẬP (UC001)

   Cùng ngôn ngữ thị giác với landing: nền #06060B, aurora violet/cyan, chất liệu
   kính, nút chính màu amber. Đặc biệt dùng LẠI cảnh biển của khối CTA cuối trang
   giới thiệu — bấm "Bắt đầu" ở đó rồi sang đây là thấy tiếp đúng cảnh ấy, không bị
   cảm giác nhảy sang một website khác.

   Logic OAuth giữ nguyên: Google (mặc định) và Outlook (đa nhà cung cấp).
   ══════════════════════════════════════════════════════════════════════════════ */

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

export function LoginPage() {
  const { isAuthenticated, isLoading, loginWithGoogle, loginWithOutlook } = useAuth()
  const navigate = useNavigate()

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

  // Nghiêng 3D nhẹ theo con trỏ — cập nhật qua rAF, không re-render
  const cardRef = useRef<HTMLDivElement>(null)
  const raf = useRef<number | null>(null)
  const reduced =
    typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const onPointerMove = (e: React.PointerEvent) => {
    if (reduced) return
    const x = e.clientX
    const y = e.clientY
    if (raf.current) return
    raf.current = window.requestAnimationFrame(() => {
      raf.current = null
      const card = cardRef.current
      if (!card) return
      const rx = (y / window.innerHeight - 0.5) * -6
      const ry = (x / window.innerWidth - 0.5) * 8
      card.style.transform = `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)`
    })
  }
  const resetTilt = () => {
    const card = cardRef.current
    if (card) card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)'
  }

  // overflow-x-clip chứ KHÔNG overflow-hidden: màn thấp phải cuộn được, nếu không thẻ bị cắt.
  return (
    <div
      onPointerMove={onPointerMove}
      onPointerLeave={resetTilt}
      className="relative flex min-h-screen items-center justify-center overflow-x-clip bg-[#06060B] px-4 py-10 text-white lg:justify-start lg:px-[8vw]"
    >
      <style>{`
        @property --beam { syntax: '<angle>'; inherits: false; initial-value: 0deg; }
        .ld-beam::after{ content:''; position:absolute; inset:-1px; border-radius:inherit; padding:1.5px;
          background: conic-gradient(from var(--beam), transparent 0deg, #8B7BF0 60deg, #4FD1C5 95deg, transparent 155deg, transparent 360deg);
          -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          -webkit-mask-composite: xor; mask-composite: exclude; opacity:.5; pointer-events:none;
          animation: ld-beam 7s linear infinite; }
        @keyframes ld-beam{ to{ --beam:360deg } }
        @keyframes ld-drift1{ 0%,100%{ transform:translate(0,0) scale(1) } 50%{ transform:translate(7vw,5vh) scale(1.18) } }
        @keyframes ld-drift2{ 0%,100%{ transform:translate(0,0) scale(1.12) } 50%{ transform:translate(-6vw,-4vh) scale(1) } }
        @keyframes ld-breathe{ 0%,100%{ opacity:.35; transform:scale(1) } 50%{ opacity:.8; transform:scale(1.12) } }
        @keyframes lg-float{ 0%,100%{ transform:translateY(0) rotate(-4deg) } 50%{ transform:translateY(-10px) rotate(4deg) } }
        @media (prefers-reduced-motion: reduce){ .ld-beam::after{ animation:none } }
      `}</style>

      {/* Nền: CỔNG VÒM HOA — đúng nghĩa cánh cửa bước vào MeoArc.
          Vòm nằm bên phải khung hình, nên thẻ đăng nhập đặt lệch trái để không che. */}
      <VideoBackdrop src="/landing/flower-arc.mp4" poster="/landing/flower-arc.jpg" tint="violet" dim="soft" />
      <div aria-hidden className="absolute inset-0 z-0 bg-gradient-to-t from-[#06060B] via-[#06060B]/70 to-transparent lg:bg-gradient-to-r lg:via-[#06060B]/80" />
      <Aurora className="opacity-60" />

      {/* Về trang giới thiệu */}
      <button
        onClick={() => navigate('/')}
        className="absolute left-5 top-5 z-20 flex items-center gap-1.5 rounded-full border border-white/12 bg-white/[0.05] px-3.5 py-2 text-[13px] font-medium text-white/70 backdrop-blur-md transition-all hover:-translate-x-0.5 hover:text-white"
      >
        <ArrowLeft className="size-4" />
        Trang giới thiệu
      </button>

      {/* Lá thư mèo trước cổng hoa — rê chuột vào là nó né đi chỗ khác */}
      <div className="absolute bottom-28 right-[16vw] z-20 hidden lg:block">
        <PlayfulLetter tone="#F0A848" size="w-14" />
      </div>

      {/* Thẻ đăng nhập */}
      <div
        ref={cardRef}
        style={{ transition: 'transform 0.25s cubic-bezier(0.22,1,0.36,1)' }}
        className="relative z-20 w-full max-w-md"
      >
        <SpotCard className="p-8">
          <div className="flex flex-col items-center text-center">
            <div className="relative mb-4">
              <span aria-hidden className="absolute inset-0 rounded-full bg-[#F0A848]/40 blur-2xl"
                style={{ animation: reduced ? undefined : 'ld-breathe 3.4s ease-in-out infinite' }} />
              <div className="relative flex size-[76px] items-center justify-center rounded-full border border-[#F0A848]/25 bg-[#F0A848]/10 backdrop-blur-md">
                <MeoMascot mood="happy" className="size-11" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <LogoMark className="size-6 text-white/80" />
              <h1 className="font-serif text-3xl font-semibold">MeoArc</h1>
            </div>
            <p className="mt-2 text-sm text-white/60">
              Đăng nhập để chú mèo AI bắt đầu dọn hộp thư giúp bạn.
            </p>
          </div>

          <div className="mt-7 space-y-2.5">
            <Feature icon={Sparkles} text="Trợ lý AI tóm tắt, phân loại, soạn thư giúp bạn" />
            <Feature icon={ShieldCheck} text="Mọi hành động quan trọng đều cần bạn xác nhận" />
            <Feature icon={Mail} text="Kết nối an toàn qua Google hoặc Outlook" />
          </div>

          {/* Nút chính — cùng màu amber với CTA ở trang giới thiệu */}
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="mt-7 flex w-full items-center justify-center gap-3 rounded-2xl bg-[#F0A848] px-4 py-3.5 text-[15px] font-semibold text-[#1a1206] shadow-[0_10px_40px_-10px_rgba(240,168,72,0.6)] transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-70"
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
            className="mt-3 flex w-full items-center justify-center gap-3 rounded-2xl border border-white/15 bg-white/[0.06] px-4 py-3.5 text-[15px] font-semibold text-white backdrop-blur-md transition-all duration-200 hover:-translate-y-0.5 hover:bg-white/[0.1] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-70"
          >
            <MicrosoftIcon className="size-5" />
            Đăng nhập với Outlook
          </button>

          <p className="mt-5 text-center text-[11px] leading-relaxed text-white/45">
            MeoArc sẽ xin quyền <span className="text-white/70">đọc &amp; quản lý thư</span> (gắn nhãn,
            lưu trữ, soạn/gửi). Bạn có thể thu hồi bất cứ lúc nào trong phần Cài đặt.
          </p>
        </SpotCard>
      </div>

      <p className="absolute bottom-5 z-20 text-center text-[11px] text-white/35">
        MeoArc · Đồ án Nhập môn CNPM — HCMUS, Nhóm 7
      </p>
    </div>
  )
}

function Feature({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl text-[13.5px] text-white/75">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#8B7BF0]/18 text-[#8B7BF0]">
        <Icon className="size-4" />
      </span>
      {text}
    </div>
  )
}
