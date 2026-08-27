import { useEffect, useRef } from 'react'

/**
 * ChatAmbience — nền cho panel trợ lý.
 *
 * ── Bản trước sai ở đâu ──
 * Nền cũ gồm ba quầng tròn nhoè + một quầng "nến" + hạt nhiễu. Mọi lớp đều
 * khuếch tán: không lớp nào có cạnh, không lớp nào có lõi sáng. Chồng bao nhiêu
 * lớp mờ lên nhau cũng chỉ ra một mảng xám — mắt không bắt được gì để nhìn, nên
 * đọc ra là một mặt phẳng trơn. Đúng như nhận xét nhận được.
 *
 * ── Bản này ──
 * Ánh sáng chỉ đọc ra là ánh sáng khi nó có HÌNH. Nên nền giờ là một TRƯỜNG SÁNG
 * có cấu trúc, xếp từ xa tới gần:
 *
 *   1. Sàn lưới tụ xa      — chiều sâu, cho biết đây là một không gian
 *   2. Chùm sợi sáng       — lõi 1px gần trắng, đây là thứ mắt bám vào
 *   3. Quầng của chính nó  — cùng dải sợi, nhoè dày, đặt sau → thành "sợi phát sáng"
 *   4. Hai kênh tán sắc    — bản sao lệch vài pixel theo trục đỏ/lam
 *   5. Vầng sáng theo con trỏ — giữ lại từ bản cũ, thứ duy nhất còn dùng được
 *
 * Lớp 4 là chỗ hai theme rẽ đôi, và nó nằm trong CSS chứ không nằm ở đây:
 * nền tối thì tán sắc CỘNG sáng (screen) và rất nhẹ, vì phần việc chính đã do
 * quầng neon lo; nền sáng thì tán sắc NHÂN tối (multiply) và đậm hơn, vì trên
 * nền sáng không có gì để phát ra — thứ đọc được là phổ màu tách ra, không phải
 * ánh sáng loé lên.
 *
 * Kỹ thuật: chỉ transform/opacity/filter; `-z-10` nằm sau chữ; `pointer-events-none`
 * để không chắn click (nghe chuột ở panel cha qua ref); reduced-motion tắt phần động.
 */
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
    <div ref={rootRef} aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* 1 — sàn lưới tụ về xa: nói "đây là một không gian", không phải một mảng màu */}
      <div className="san-tu" />

      {/* 2+3+4 — chùm sợi sáng. Bốn bản của CÙNG một dải:
          quầng nhoè phía sau, hai kênh tán sắc lệch, rồi lõi nét trên cùng.
          Thứ tự này quan trọng: lõi nét phải nằm trên, nếu không sợi mất cạnh. */}
      <div className="chat-parallax absolute inset-0">
        <div className="tia-sang quang-xa" />
        <div className="tia-sang quang" />
        <div className="tia-sang tan-sac kenh-do" />
        <div className="tia-sang tan-sac kenh-lam" />
        <div className="tia-sang" style={{ opacity: 0.7 }} />
      </div>

      {/* 5 — vầng sáng đi theo con trỏ: lớp duy nhất của bản cũ còn giữ lại,
          vì nó là thứ tương tác, không phải thứ trang trí */}
      <div className="chat-cursor-glow" />
    </div>
  )
}
