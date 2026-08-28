import { useRef, type ReactNode } from 'react'
import { motion, useScroll, useSpring, useTransform, useReducedMotion } from 'framer-motion'

/* ══════════════════════════════════════════════════════════════════════════════
   CHUYỂN CẢNH GIỮA CÁC KHỐI TRANG GIỚI THIỆU

   Vấn đề của bản trước: mọi khối vào bằng cùng một cách — trôi lên, mờ dần hiện.
   Từng khối một thì ổn; xếp năm khối liên tiếp thì não đoán trước được khối kế
   tiếp trông sẽ ra sao, và khi não đoán trước được thì nó thôi nhìn. Đó chính
   xác là cảm giác "một tờ giấy phẳng kéo xuống".

   Cách chữa KHÔNG phải làm hiệu ứng mạnh hơn — mà làm chúng KHÁC NHAU. Mỗi khối
   một cách vào, nên không khối nào đoán trước được từ khối trước.

   Ba kiểu ở đây, mỗi kiểu mô phỏng một cách "một tấm bảng điều khiển được bật":
     QuetCheo    — khối lộ ra qua một nhát cắt chéo đang mở rộng
     DayChieuSau — khối tiến từ xa lại gần, không phải trượt lên
     KeoNgang    — khối bị ghim, nội dung chạy NGANG trong lúc cuộn dọc

   Cả ba đều thoái lui về "hiện ngay, không hiệu ứng" khi người dùng bật giảm
   chuyển động — đây là loại hiệu ứng gây chóng mặt thật sự, không phải trang trí.
   ══════════════════════════════════════════════════════════════════════════════ */

/**
 * QuetCheo — khối lộ ra qua một NHÁT CẮT CHÉO đang mở rộng.
 *
 * Cùng ngôn ngữ hình học với khung góc cắt: đường mở là một đường chéo 45°, nên
 * chuyển cảnh và khung nói cùng một thứ tiếng. Dùng `clip-path` với một điểm
 * chạy từ 0% tới 140% — vượt quá 100% để nhát cắt ra hẳn khỏi khung chứ không
 * dừng lửng ở mép.
 */
export function QuetCheo({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 0.85', 'start 0.25'] })
  const p = useSpring(scrollYProgress, { stiffness: 90, damping: 28, restDelta: 0.001 })
  const mo = useTransform(p, [0, 1], [0, 140])
  const clip = useTransform(mo, (v) => `polygon(0 0, ${v}% 0, ${v - 40}% 100%, 0 100%)`)

  if (reduced) return <div className={className}>{children}</div>
  return (
    <motion.div ref={ref} className={className} style={{ clipPath: clip, WebkitClipPath: clip }}>
      {children}
    </motion.div>
  )
}

/**
 * DayChieuSau — khối TIẾN TỪ XA LẠI, không trượt lên.
 *
 * Trượt lên là chuyển động trong mặt phẳng: khối ở đâu đó phía dưới rồi đi lên.
 * Tiến từ xa là chuyển động theo TRỤC SÂU: khối ở phía sau màn hình rồi đi ra.
 * Hai thứ này khác nhau về chất, và đặt cạnh nhau thì mắt đọc ra ngay là hai
 * cảnh khác nhau — đó là toàn bộ mục đích.
 *
 * `perspective` đặt ở phần tử cha, `rotateX` nhỏ (6°) để khối hơi ngửa ra lúc ở
 * xa rồi phẳng lại khi tới nơi. Nhiều hơn 6° thì thành hiệu ứng trình chiếu.
 */
export function DayChieuSau({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 0.95', 'start 0.35'] })
  const p = useSpring(scrollYProgress, { stiffness: 80, damping: 26, restDelta: 0.001 })
  const scale = useTransform(p, [0, 1], [0.86, 1])
  const rotateX = useTransform(p, [0, 1], [6, 0])
  const opacity = useTransform(p, [0, 0.4, 1], [0, 0.85, 1])

  if (reduced) return <div className={className}>{children}</div>
  return (
    <div ref={ref} style={{ perspective: 1400 }} className={className}>
      <motion.div style={{ scale, rotateX, opacity, transformOrigin: 'center 30%' }}>
        {children}
      </motion.div>
    </div>
  )
}

/**
 * KeoNgang — khối bị GHIM lại, nội dung chạy NGANG trong lúc người dùng cuộn dọc.
 *
 * Đây là kiểu phá vỡ mạnh nhất trong ba kiểu, và cũng là thứ khiến một trang thôi
 * đọc ra như "tờ giấy": trên tờ giấy thì mọi thứ chỉ đi một chiều.
 *
 * Cách dựng: một khối ngoài rất cao (chiều cao quyết định phải cuộn bao lâu),
 * bên trong là một khung dính cao đúng một màn hình. Tiến độ cuộn của khối ngoài
 * được ánh xạ thành độ dịch ngang của hàng nội dung.
 *
 * `soManHinh` = số màn hình cuộn dọc dành cho đoạn ngang này. Đặt quá lớn thì
 * người dùng cảm thấy bị kẹt; 2–3 là khoảng dùng được.
 */
export function KeoNgang({
  children,
  soManHinh = 2.4,
  className,
}: {
  children: ReactNode
  soManHinh?: number
  className?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  const hangRef = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const p = useSpring(scrollYProgress, { stiffness: 70, damping: 26, restDelta: 0.0005 })

  // Dịch đúng bằng phần nội dung TRÀN ra ngoài khung, không phải một con số cố
  // định: nội dung rộng bao nhiêu thì dịch bấy nhiêu, nên không bao giờ dừng
  // sớm (còn thừa nội dung) hay dịch quá (hở một mảng trống ở cuối).
  const x = useTransform(p, (v) => {
    const el = hangRef.current
    if (!el) return 0
    const tran = el.scrollWidth - el.parentElement!.clientWidth
    return -v * Math.max(0, tran)
  })

  if (reduced) {
    return (
      <div className={className}>
        <div className="flex gap-5 overflow-x-auto px-6 pb-4">{children}</div>
      </div>
    )
  }
  return (
    <div ref={ref} className={className} style={{ height: `${soManHinh * 100}vh` }}>
      <div className="sticky top-0 flex h-screen items-center overflow-hidden">
        <motion.div ref={hangRef} style={{ x }} className="flex gap-5 px-[6vw] will-change-transform">
          {children}
        </motion.div>
      </div>
    </div>
  )
}
