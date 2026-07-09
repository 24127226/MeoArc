import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, ShieldCheck, Mail, Sparkles } from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { LogoMark } from '@/components/logo'
import { ThemeToggle } from '@/components/theme-toggle'
import { useTheme } from '@/components/theme-provider'

// Ảnh nền theo chế độ: Dark dùng ảnh tối, Light dùng ảnh sáng (đổi tức thì khi bật ThemeToggle).
import bgLight from '@/assets/login-light.jpg' // Ảnh cho Light Mode
import bgDark from '@/assets/login-dark.jpg'   // Ảnh cho Dark Mode

/** Logo Google nhiều màu cho nút đăng nhập. */
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 10.2v3.9h5.5c-.24 1.4-1.7 4.1-5.5 4.1-3.3 0-6-2.7-6-6.1S8.7 5.9 12 5.9c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.3 14.6 2.3 12 2.3 6.9 2.3 2.8 6.4 2.8 11.5S6.9 20.7 12 20.7c5.3 0 8.8-3.7 8.8-8.9 0-.6-.07-1.1-.16-1.6H12z"
      />
    </svg>
  )
}

export function LoginPage() {
  const { isAuthenticated, isLoading, loginWithGoogle } = useAuth()
  const { theme } = useTheme()
  const bg = theme === 'dark' ? bgDark : bgLight // nền login khớp theme (UC013)
  const navigate = useNavigate()

  // Đã đăng nhập thì vào thẳng app.
  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  const handleLogin = async () => {
    await loginWithGoogle()
    navigate('/', { replace: true })
  }

  // Nghiêng 3D nhẹ cho card theo con trỏ — cập nhật qua rAF, không re-render
  const cardRef = useRef<HTMLDivElement>(null)
  const raf = useRef<number | null>(null)
  const reduced =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const onPointerMove = (e: React.PointerEvent) => {
    if (reduced) return
    const x = e.clientX
    const y = e.clientY
    if (raf.current) return
    raf.current = window.requestAnimationFrame(() => {
      raf.current = null
      const card = cardRef.current
      if (!card) return
      const rx = (y / window.innerHeight - 0.5) * -8
      const ry = (x / window.innerWidth - 0.5) * 10
      card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg)`
    })
  }
  const resetTilt = () => {
    const card = cardRef.current
    if (card) card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg)'
  }

  // Vài hạt cherry bay
  const particles = [
    { left: '14%', size: 7, dur: 15, delay: 0, drift: '18px' },
    { left: '28%', size: 5, dur: 19, delay: 4, drift: '-14px' },
    { left: '47%', size: 8, dur: 17, delay: 8, drift: '10px' },
    { left: '63%', size: 5, dur: 21, delay: 2, drift: '-20px' },
    { left: '78%', size: 7, dur: 16, delay: 6, drift: '14px' },
    { left: '90%', size: 4, dur: 23, delay: 10, drift: '-10px' },
  ]

  return (
    <div
      onPointerMove={onPointerMove}
      onPointerLeave={resetTilt}
      className="fixed inset-0 flex items-center justify-center overflow-hidden bg-black px-4 w-screen h-screen"
    >
      {/* LAYER 0: HỆ THỐNG NỀN ĐÃ KHỬ QUẦNG SÁNG VÀ DIỆT MÉP TRẮNG */}
      <div aria-hidden className="pointer-events-none absolute inset-0 select-none z-0 overflow-hidden w-full h-full">
        {/* Ảnh nền phủ tràn tuyệt đối */}
        <div
          className="absolute inset-0 bg-cover bg-center scale-105 w-full h-full transition-[background-image] duration-500"
          style={{ backgroundImage: `url(${bg})` }}
        />
        
        {/* LỚP MASK ĐẦM MÀU: Xóa bỏ màu kem sáng gây quầng đục, thay bằng đỏ mận tối để ảnh sâu và nét chữ nổi bật hẳn lên */}
        <div className="absolute inset-0 mix-blend-multiply bg-[#1a0505]/45 w-full h-full" />
        
        {/* LỚP PHỦ LÀM MỜ: Đẩy scale lên 125% để phần mờ tràn hẳn ra ngoài viewport, dứt điểm mép xám trắng */}
        <div className="absolute inset-0 backdrop-blur-[6px] scale-125 w-full h-full" />
        
        {/* Hạt nhiễu mịn phủ trên cùng nền */}
        <div className="grain-overlay absolute inset-0 w-full h-full" />
      </div>

      {/* LAYER 1: CHỈ GIỮ LẠI HẠT CHERRY BAY TỪ DƯỚI LÊN */}
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden z-10 w-full h-full">
        {particles.map((p, i) => (
          <span
            key={i}
            className="cherry-particle cherry-dot bottom-0"
            style={{
              left: p.left,
              width: p.size,
              height: p.size,
              ['--drift' as string]: p.drift,
              animation: `cherry-float ${p.dur}s linear ${p.delay}s infinite`,
            }}
          />
        ))}
      </div>

      {/* LAYER 2: INTERFACE ĐĂNG NHẬP CHÍNH (z-20) */}
      <div className="absolute right-5 top-5 z-20">
        <ThemeToggle />
      </div>

      {/* Thẻ kính đăng nhập — nghiêng 3D nhẹ theo con trỏ */}
      <div
        ref={cardRef}
        style={{ transition: 'transform 0.25s var(--ease-soft)' }}
        className="glass relative z-20 w-full max-w-md rounded-2xl p-8 shadow-float edge-light"
      >
        {/* Logo orb phát sáng */}
        <div className="flex flex-col items-center text-center">
          <div className="ai-orb flex size-[72px] items-center justify-center shadow-float">
            <span className="ripe flex size-[58px] items-center justify-center rounded-full bg-active text-active-foreground">
              <LogoMark className="size-9 text-active-foreground" />
            </span>
          </div>
          <h1 className="mt-4 font-serif text-3xl font-semibold text-foreground">MeoArc</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Email Intelligence — quản lý Gmail bằng ngôn ngữ tự nhiên
          </p>
        </div>

        {/* Điểm nhấn tính năng */}
        <div className="mt-7 space-y-2.5">
          <Feature icon={Sparkles} text="Trợ lý AI tóm tắt, phân loại, soạn thư giúp bạn" />
          <Feature icon={ShieldCheck} text="Mọi hành động quan trọng đều cần bạn xác nhận" />
          <Feature icon={Mail} text="Kết nối an toàn qua tài khoản Google của bạn" />
        </div>

        {/* Nút đăng nhập Google */}
        <button
          onClick={handleLogin}
          disabled={isLoading}
          className="mt-7 flex w-full items-center justify-center gap-3 rounded-2xl bg-popover px-4 py-3 text-sm font-semibold text-popover-foreground shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:shadow-float disabled:pointer-events-none disabled:opacity-70"
        >
          {isLoading ? (
            <>
              <Loader2 className="size-5 animate-spin" />
              Đang kết nối Google…
            </>
          ) : (
            <>
              <GoogleIcon className="size-5" />
              Đăng nhập với Google
            </>
          )}
        </button>

        {/* Quyền sẽ xin */}
        <p className="mt-4 text-center text-[11px] leading-relaxed text-muted-foreground">
          MeoArc sẽ xin quyền <span className="text-foreground">đọc &amp; quản lý thư</span> (gắn nhãn,
          lưu trữ, soạn/gửi) trên Gmail của bạn. Bạn có thể thu hồi bất cứ lúc nào trong phần Cài đặt.
        </p>
      </div>

      {/* Chân trang */}
      <p className="absolute bottom-5 text-center text-[11px] text-muted-foreground z-20">
        MeoArc · Đồ án Nhập môn CNPM — HCMUS, Nhóm 7
      </p>
    </div>
  )
}

function Feature({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl px-1 text-sm text-foreground">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent-foreground">
        <Icon className="size-4" />
      </span>
      {text}
    </div>
  )
}