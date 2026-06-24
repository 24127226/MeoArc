import { useEffect, useRef } from 'react'

/**
 * ChatAmbience — NỀN SINH ĐỘNG + TƯƠNG TÁC cho panel AI (đặt sau nội dung).
 *
 * Mục tiêu: panel chat "có hồn", trẻ trung, và dark mode bớt creepy.
 * 4 lớp:
 *   1) Aurora ấm trôi chậm (trong lớp parallax → dịch nhẹ NGƯỢC con trỏ = chiều sâu 3D).
 *   2) Quầng "nến" toả từ đỉnh (warm, chống creepy).
 *   3) Vầng sáng ĐI THEO CON TRỎ (đèn pin ấm dưới kính mờ) — chất tương tác thời thượng.
 *   4) Tàn lửa bay lên + hạt nhiễu.
 *
 * Kỹ thuật: chỉ transform/opacity (mượt); `-z-10` nằm sau chữ; `pointer-events-none`
 * để không chắn click (nghe chuột ở panel cha qua ref); reduced-motion tắt phần động.
 */

const EMBERS = [
  { left: '12%', size: 6, dur: 17, delay: 0, drift: '16px', tone: 'var(--spark)' },
  { left: '30%', size: 4, dur: 22, delay: 5, drift: '-12px', tone: 'var(--active)' },
  { left: '50%', size: 7, dur: 19, delay: 9, drift: '10px', tone: 'var(--spark)' },
  { left: '68%', size: 4, dur: 24, delay: 3, drift: '-16px', tone: 'var(--active)' },
  { left: '86%', size: 5, dur: 20, delay: 7, drift: '12px', tone: 'var(--accent)' },
] as const

export function ChatAmbience() {
  const rootRef = useRef<HTMLDivElement>(null)

  // Nghe di chuyển con trỏ trên PANEL CHA (vì lớp này pointer-events-none) →
  // cập nhật biến CSS: --gx/--gy (tâm vầng sáng) + --px/--py (độ dịch parallax).
  useEffect(() => {
    const root = rootRef.current
    const panel = root?.parentElement
    if (!root || !panel) return
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return

    // Đặt vị trí ban đầu của vầng sáng = giữa-trên panel (trước khi rê chuột).
    const r0 = panel.getBoundingClientRect()
    root.style.setProperty('--gx', `${r0.width / 2}px`)
    root.style.setProperty('--gy', `${r0.height * 0.18}px`)

    let raf = 0
    const onMove = (e: PointerEvent) => {
      cancelAnimationFrame(raf) // gộp nhiều sự kiện vào 1 khung hình → êm, không phí
      raf = requestAnimationFrame(() => {
        const r = panel.getBoundingClientRect()
        const x = e.clientX - r.left
        const y = e.clientY - r.top
        root.style.setProperty('--gx', `${x}px`)
        root.style.setProperty('--gy', `${y}px`)
        // Parallax dịch tối đa ~18px, NGƯỢC hướng con trỏ (trừ) cho cảm giác chiều sâu.
        root.style.setProperty('--px', `${-(x / r.width - 0.5) * 18}px`)
        root.style.setProperty('--py', `${-(y / r.height - 0.5) * 18}px`)
      })
    }
    panel.addEventListener('pointermove', onMove)
    return () => {
      panel.removeEventListener('pointermove', onMove)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <div ref={rootRef} aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* (1) Aurora ấm trong lớp parallax — 3 vầng trôi lệch pha, dồn ra mép */}
      <div className="chat-parallax">
        <div
          className="aurora-blob chat-aurora left-[-18%] top-[-12%] size-[42vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--spark) 52%, transparent), transparent 70%)',
            animation: 'aurora-a 30s ease-in-out infinite',
          }}
        />
        <div
          className="aurora-blob chat-aurora right-[-16%] bottom-[-14%] size-[40vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--active) 48%, transparent), transparent 70%)',
            animation: 'aurora-b 36s ease-in-out infinite',
          }}
        />
        <div
          className="aurora-blob chat-aurora left-[14%] bottom-[-20%] size-[32vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--accent) 42%, transparent), transparent 70%)',
            animation: 'aurora-c 42s ease-in-out infinite reverse',
          }}
        />
      </div>

      {/* (2) Quầng ấm "nến" toả từ đỉnh — chống creepy ở dark */}
      <div className="chat-hearth" />

      {/* (3) Vầng sáng đi theo con trỏ — tương tác, thời thượng */}
      <div className="chat-cursor-glow" />

      {/* (4) Hạt nhiễu mịn — chất giấy in cao cấp */}
      <div className="grain-overlay" />

      {/* (4) Tàn lửa bay lên rất chậm */}
      {EMBERS.map((e, i) => (
        <span
          key={i}
          className="cherry-particle bottom-0"
          style={{
            left: e.left,
            width: e.size,
            height: e.size,
            background: e.tone,
            opacity: 0.65,
            ['--drift' as string]: e.drift,
            animation: `cherry-float ${e.dur}s linear ${e.delay}s infinite`,
          }}
        />
      ))}
    </div>
  )
}
