import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { MeoMascot } from '@/components/meo-mascot'

const CAT = 46 // cạnh hộp mèo (px) — khớp size-11 + chút hở chân

type Perch = { y: number; left: number; right: number }

/** Gom các "gờ" mèo đậu được: mọi phần tử gắn data-cat-perch="top|bottom"
 *  (header Hộp thư, header Trợ lý, mái khu nhập liệu…). Đo lại MỖI chuyến bằng
 *  getBoundingClientRect nên panel co giãn/đổi cỡ xong mèo vẫn đậu đúng mép. */
function collectPerches(): Perch[] {
  return [...document.querySelectorAll<HTMLElement>('[data-cat-perch]')]
    .map((el) => {
      const r = el.getBoundingClientRect()
      const surface = el.dataset.catPerch === 'bottom' ? r.bottom : r.top
      return { y: surface - CAT + 4, left: r.left + 12, right: r.right - 12 }
    })
    .filter((p) => p.y > 40 && p.y < window.innerHeight - CAT && p.right - p.left > 140)
}

/** WanderingCat — mèo MeoArc QUẬY: không chỉ đi ngang sàn mà còn PHÓNG LÊN các
 *  khung trong giao diện (header Hộp thư, header Trợ lý, mái ô nhập chat…),
 *  dạo dọc gờ, ngồi nghỉ vài giây rồi phóng xuống chạy tiếp. "Cảm giác thật"
 *  đến từ chuyển động: nhún nhịp chân khi đi (.cat-bob), khuỵu lấy đà → vươn
 *  dài trên không → tiếp đất nhún (.cat-stretch), quay mặt theo hướng chạy,
 *  bóng đổ dưới chân. Trang trí thuần: pointer-events-none, z-40 (dưới dialog),
 *  ẩn hẳn với prefers-reduced-motion. Mỗi chuyến cách nhau ~20–60s. */
export function WanderingCat() {
  const [visible, setVisible] = useState(false)
  const [sitting, setSitting] = useState(false)
  const [leaping, setLeaping] = useState(false)
  const [pos, setPos] = useState({ x: -90, y: 0 })
  const [dir, setDir] = useState(1)
  const [ms, setMs] = useState(0) // thời lượng transition chặng hiện tại (0 = đặt tức thì)
  const [easing, setEasing] = useState('linear')
  const posRef = useRef(pos)
  const alive = useRef(true)

  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
    alive.current = true
    const sleep = (t: number) => new Promise<void>((r) => window.setTimeout(r, t))
    const floorY = () => window.innerHeight - CAT - 2

    /** Dịch tới (x,y) trong dur ms; tự quay mặt theo hướng đi. */
    const move = async (x: number, y: number, dur: number, ease = 'linear') => {
      if (!alive.current) return
      if (Math.abs(x - posRef.current.x) > 4) setDir(x >= posRef.current.x ? 1 : -1)
      posRef.current = { x, y }
      setEasing(ease)
      setMs(dur)
      setPos({ x, y })
      await sleep(dur + 40)
    }
    /** Chạy trên mặt phẳng — tốc độ ~0.12px/ms cho dáng chạy tự nhiên. */
    const runTo = (x: number, y: number) =>
      move(x, y, Math.max(700, Math.abs(x - posRef.current.x) / 0.12))
    /** Cú phóng: bật stretch trong lúc bay (đường bay do transition lo). */
    const leapTo = async (x: number, y: number) => {
      setLeaping(true)
      await move(x, y, 640, 'cubic-bezier(0.35, 0, 0.3, 1)')
      setLeaping(false)
    }
    const rest = async (t: number) => {
      setSitting(true)
      await sleep(t)
      setSitting(false)
    }
    const teleport = (x: number, y: number) => {
      posRef.current = { x, y }
      setMs(0)
      setPos({ x, y })
    }

    /** Một chuyến: 70% leo gờ (nếu có gờ hợp lệ), còn lại chạy sàn nghịch. */
    async function tour() {
      if (!alive.current) return
      const w = window.innerWidth
      const fromLeft = Math.random() < 0.5
      const startX = fromLeft ? -90 : w + 90
      const endX = fromLeft ? w + 90 : -90
      const perches = collectPerches()
      const perch = perches.length ? perches[(Math.random() * perches.length) | 0] : null

      teleport(startX, floorY())
      setVisible(true)
      await sleep(40) // cho browser áp vị trí xuất phát trước khi bật transition

      if (perch && Math.random() < 0.7) {
        // LEO GỜ: chạy sàn tới chân gờ → phóng lên → dạo dọc gờ → (ngồi nghỉ)
        // → phóng xuống sàn → chạy khỏi màn hình
        const upX = fromLeft ? perch.left + 34 : perch.right - 34
        await runTo(upX + (fromLeft ? -70 : 70), floorY())
        await leapTo(upX, perch.y)
        const acrossX = fromLeft ? perch.right - 26 : perch.left + 26
        await move(acrossX, perch.y, 2800 + Math.random() * 1600)
        if (Math.random() < 0.7) await rest(2600 + Math.random() * 2600)
        await leapTo(acrossX + (fromLeft ? 90 : -90), floorY())
        await runTo(endX, floorY())
      } else {
        // SÀN: chạy tới giữa, hoặc ngồi thở hoặc nhảy chơi một cú, rồi chạy tiếp
        const midX = w * (0.3 + Math.random() * 0.4)
        await runTo(fromLeft ? midX : w - midX, floorY())
        if (Math.random() < 0.4) await rest(2200 + Math.random() * 2400)
        else await leapTo(posRef.current.x + (fromLeft ? 90 : -90), floorY())
        await runTo(endX, floorY())
      }

      setVisible(false)
      if (!alive.current) return
      await sleep(20000 + Math.random() * 40000)
      void tour()
    }

    const kickoff = window.setTimeout(() => void tour(), 4500 + Math.random() * 6000)
    return () => {
      alive.current = false
      clearTimeout(kickoff)
    }
  }, [])

  if (!visible) return null
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed left-0 top-0 z-40 select-none"
      style={{
        transform: `translate(${pos.x}px, ${pos.y}px)`,
        transition: ms ? `transform ${ms}ms ${easing}` : 'none',
      }}
    >
      {/* 3 lớp transform tách bạch: vươn người khi phóng → lật hướng → nhún chân */}
      <div className={cn(leaping && 'cat-stretch')}>
        <div style={{ transform: `scaleX(${dir})` }}>
          <div className={cn(!sitting && !leaping && 'cat-bob')}>
            <MeoMascot className="size-11" mood={sitting || leaping ? 'happy' : 'idle'} />
          </div>
        </div>
      </div>
      <span className="cat-shadow" />
    </div>
  )
}
