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
  { left: '12%', size: 5, dur: 18, delay: 0, drift: '20px', tone: 'var(--spark)' },
  { left: '28%', size: 3, dur: 24, delay: 4, drift: '-14px', tone: 'var(--active)' },
  { left: '52%', size: 6, dur: 21, delay: 8, drift: '12px', tone: 'var(--spark)' },
  { left: '70%', size: 4, dur: 26, delay: 2, drift: '-18px', tone: 'var(--active)' },
  { left: '88%', size: 5, dur: 22, delay: 6, drift: '15px', tone: 'var(--accent)' },
] as const

export function ChatAmbience() {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const root = rootRef.current
    const panel = root?.parentElement
    if (!root || !panel) return
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return

    const r0 = panel.getBoundingClientRect()
    root.style.setProperty('--gx', `${r0.width / 2}px`)
    root.style.setProperty('--gy', `${r0.height * 0.18}px`)

    let raf = 0
    const onMove = (e: PointerEvent) => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => {
        const r = panel.getBoundingClientRect()
        const x = e.clientX - r.left
        const y = e.clientY - r.top
        root.style.setProperty('--gx', `${x}px`)
        root.style.setProperty('--gy', `${y}px`)
        root.style.setProperty('--px', `${-(x / r.width - 0.5) * 14}px`)
        root.style.setProperty('--py', `${-(y / r.height - 0.5) * 14}px`)
      })
    }
    panel.addEventListener('pointermove', onMove)
    return () => {
      panel.removeEventListener('pointermove', onMove)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    // [OLD MONEY] Kích hoạt thêm .stars-faint phủ đốm sao tĩnh mờ như bụi than trong phòng đọc hoàng gia
    <div ref={rootRef} aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden stars-faint">
      <div className="chat-parallax">
        <div
          className="aurora-blob chat-aurora left-[-18%] top-[-12%] size-[42vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--spark) 45%, transparent), transparent 70%)',
            animation: 'aurora-a 30s ease-in-out infinite',
          }}
        />
        <div
          className="aurora-blob chat-aurora right-[-16%] bottom-[-14%] size-[40vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--active) 42%, transparent), transparent 70%)',
            animation: 'aurora-b 36s ease-in-out infinite',
          }}
        />
        <div
          className="aurora-blob chat-aurora left-[14%] bottom-[-20%] size-[32vw]"
          style={{
            background:
              'radial-gradient(circle, color-mix(in srgb, var(--accent) 38%, transparent), transparent 70%)',
            animation: 'aurora-c 42s ease-in-out infinite reverse',
          }}
        />
      </div>

      <div className="chat-hearth" />
      <div className="chat-cursor-glow" />
      <div className="grain-overlay" />

      {EMBERS.map((e, i) => (
        <span
          key={i}
          className="cherry-particle bottom-0"
          style={{
            left: e.left,
            width: e.size,
            height: e.size,
            background: e.tone,
            opacity: 0.45, // Làm dịu tàn lửa xuống một chút cho tinh tế, không bị rực quá
            ['--drift' as string]: e.drift,
            animation: `cherry-float ${e.dur}s linear ${e.delay}s infinite`,
          }}
        />
      ))}
    </div>
  )
}