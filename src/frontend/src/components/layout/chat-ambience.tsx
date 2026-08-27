import { useEffect, useRef } from 'react'

/**
 * ChatAmbience — nền cho panel trợ lý.
 *
 * ── Lịch sử hai lần sai, để không lặp lại ──
 * Bản 1: ba quầng tròn nhoè + hạt nhiễu. Mọi lớp đều khuếch tán, không lớp nào
 *        có cạnh → chồng lên nhau chỉ ra một mảng xám, đọc là "mặt phẳng trơn".
 * Bản 2: chùm vạch sáng chéo. Sửa được chuyện thiếu cấu trúc, nhưng sai kiểu
 *        khác: vạch phủ kín khung, cắt ngang mọi thứ người dùng đang đọc, và vì
 *        trải đều nên không bao giờ thành một VẬT — vẫn chỉ là hoa văn, chỉ là
 *        hoa văn chói hơn.
 *
 * ── Bản này ──
 * Một BONG BÓNG. Đúng một vật thể: có tâm, có mép, có chỗ để nhìn vào, và chừa
 * sạch phần còn lại của khung cho chữ.
 *
 * Chọn bong bóng không phải vì nó đẹp. Màu ngũ sắc trên bong bóng xà phòng không
 * phải màu của xà phòng — nước xà phòng trong suốt. Màu sinh ra do giao thoa
 * màng mỏng: tia phản xạ ở mặt ngoài và mặt trong của màng lệch pha nhau, một số
 * bước sóng triệt tiêu, số còn lại nổi lên. Tức là LẠI LÀ tán sắc — đúng hiện
 * tượng đã chọn làm chữ ký cho bản sáng, lần này bọc quanh một khối cầu. Nhờ vậy
 * một khối duy nhất chạy được cả hai theme mà không phải làm hai bản.
 *
 * Bốn lớp, xếp từ trong ra ngoài — thiếu lớp nào cũng tụt xuống thành hình tròn
 * tô màu: thân (trong ở tâm, đậm ra rìa) · vân giao thoa (băng ngang vì màng
 * mỏng dần từ đỉnh xuống do trọng lực) · mép (màng nhìn nghiêng nên dày nhất) ·
 * hai điểm loé (nguồn sáng + ánh phản xạ từ môi trường).
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
    <div ref={rootRef} aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
      /* Tắt dần về đáy: bong bóng không được lấn vào vùng chip gợi ý và ô nhập —
         đó là chỗ người dùng đọc và bấm, nền ở đó phải sạch. */
      style={{
        maskImage: 'linear-gradient(to bottom, #000 0%, #000 62%, rgba(0,0,0,0.4) 82%, transparent 94%)',
        WebkitMaskImage: 'linear-gradient(to bottom, #000 0%, #000 62%, rgba(0,0,0,0.4) 82%, transparent 94%)',
      }}>
      {/* Bong bóng lớn — đặt lệch phải và hơi thấp, để phần trên trái (nơi bong
          bóng chat của trợ lý rơi vào) còn thoáng. Nằm trong lớp parallax nên
          dịch nhẹ ngược con trỏ, đủ để cảm được nó ở phía sau chứ không dán lên
          mặt kính. */}
      <div className="chat-parallax absolute inset-0">
        <div className="bb-khoi left-[30%] top-[16%] size-[clamp(230px,32vw,430px)]">
          <div className="bb-than" />
          <div className="bb-van" />
          <div className="bb-mep" />
          <div className="bb-loe" />
        </div>

        {/* Bong bóng phụ, nhỏ và mờ — một mình một khối thì khung hình chết cứng;
            có bạn đồng hành thì thành một khoảng không có chiều sâu. */}
        <div className="bb-khoi right-[8%] top-[8%] size-[clamp(90px,13vw,168px)] opacity-55"
          style={{ animationDelay: '-9s', animationDuration: '28s' }}>
          <div className="bb-than" />
          <div className="bb-van" />
          <div className="bb-mep" />
          <div className="bb-loe" />
        </div>
      </div>

      {/* Vầng sáng đi theo con trỏ — thứ tương tác, không phải thứ trang trí */}
      <div className="chat-cursor-glow" />
    </div>
  )
}
