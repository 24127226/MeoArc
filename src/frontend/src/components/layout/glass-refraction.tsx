import { useEffect, useRef, type ReactNode, type RefObject } from 'react'

/* ══════════════════════════════════════════════════════════════════════════════
   KÍNH KHÚC XẠ THẬT — bộ lọc SVG + canvas đồng bộ từng khung hình

   Đây KHÔNG phải gradient giả lập. Khối kính là một CỬA SỔ nhìn xuống một bản
   sao của chính đoạn phim phía sau nó, và bản sao đó bị bẻ cong thật bằng bộ lọc
   SVG. Thông số giữ nguyên từ bản gốc — chúng đã được tinh chỉnh, đổi là hỏng.

   ── Bộ lọc làm gì, theo thứ tự ──
   1. feTurbulence dựng một trường nhiễu fractal tĩnh: đây là bản đồ pháp tuyến
      khúc xạ (refraction normal map).
   2. SourceAlpha bị đẩy lên đục hoàn toàn (hàng alpha `0 0 0 100 0`), làm nhoè
      45, rồi ĐẢO NGƯỢC bằng feFuncA slope=-1.3 intercept=1. Kết quả là một MẶT
      NẠ MÉP: gần 0 ở lòng khối, tăng dần ra phía viền.
   3. Nhiễu nhân với mặt nạ đó (feComposite arithmetic, k1=1) → độ bẻ mạnh ở rìa
      và gần như bằng không ở giữa. Chính điều này đọc ra là một vành kính dày.
   4. SourceGraphic bị bẻ BA LẦN ở ba cường độ khác nhau — 65 / 56 / 47 — mỗi lần
      lọc xuống đúng một kênh màu (R, G, B) rồi ghép lại bằng hai phép screen.
      Khoảng lệch giữa ba kênh chính là sai sắc màu / viền cầu vồng.
   5. Vùng lọc -30% / 160% cho phần nhoè và phần bẻ chỗ tràn ra ngoài khối.
   ══════════════════════════════════════════════════════════════════════════════ */

/** Bộ lọc phải TỈ LỆ VỚI KÍCH THƯỚC KHỐI KÍNH — đây là điều bản gốc không nói ra
 *  vì nó chỉ có đúng một khối kính, cỡ 340×460.
 *
 *  Mặt nạ mép được dựng bằng cách làm nhoè alpha đi `stdDeviation`. Với tấm
 *  340×460 thì 45px là một VÀNH mỏng quanh mép, đúng ý đồ. Với một viên cao 54px
 *  thì 45px PHỦ TRỌN phần tử — mọi điểm ảnh đều nằm trong "vùng mép", nhận độ bẻ
 *  tối đa, và ba kênh màu tách hẳn ra thành mấy dải cứng. Đã thử và đúng là vậy.
 *
 *  Nên có hai bản. Bản `-lon` giữ nguyên thông số gốc (45 / 65-56-47) cho khối
 *  lớn. Bản `-nho` thu theo cùng tỉ lệ (12 / 17-15-12) cho khối cỡ thanh/viên.
 *  Tỉ lệ giữa ba scale được giữ nguyên vì chính nó quyết định độ tán sắc. */
function MotBoLoc({ id, nhoe, s1, s2, s3 }: { id: string; nhoe: number; s1: number; s2: number; s3: number }) {
  return (
        <filter
          id={id}
          x="-30%" y="-30%" width="160%" height="160%"
          colorInterpolationFilters="sRGB"
        >
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.015" numOctaves={3} result="noise" />

          <feColorMatrix
            in="SourceAlpha" type="matrix" result="boosted_alpha"
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 100 0"
          />

          <feGaussianBlur in="boosted_alpha" stdDeviation={nhoe} result="blurred_alpha" />

          <feComponentTransfer in="blurred_alpha" result="edge_mask">
            <feFuncA type="linear" slope="-1.3" intercept="1" />
          </feComponentTransfer>

          <feComposite in="noise" in2="edge_mask" operator="arithmetic" k1={1} k2={0} k3={0} k4={0} result="masked_noise" />

          {/* Tán sắc: mỗi kênh màu một lần bẻ, cường độ khác nhau */}
          <feDisplacementMap in="SourceGraphic" in2="masked_noise" scale={s1} xChannelSelector="R" yChannelSelector="G" result="red_displaced" />
          <feColorMatrix
            in="red_displaced" type="matrix" result="red"
            values="1 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 1 0"
          />

          <feDisplacementMap in="SourceGraphic" in2="masked_noise" scale={s2} xChannelSelector="R" yChannelSelector="G" result="green_displaced" />
          <feColorMatrix
            in="green_displaced" type="matrix" result="green"
            values="0 0 0 0 0
                    0 1 0 0 0
                    0 0 0 0 0
                    0 0 0 1 0"
          />

          <feDisplacementMap in="SourceGraphic" in2="masked_noise" scale={s3} xChannelSelector="R" yChannelSelector="G" result="blue_displaced" />
          <feColorMatrix
            in="blue_displaced" type="matrix" result="blue"
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 1 0 0
                    0 0 0 1 0"
          />

          <feBlend in="red" in2="green" mode="screen" result="rg" />
          <feBlend in="rg" in2="blue" mode="screen" result="chromatic_dispersion" />
        </filter>
  )
}

/** Gắn MỘT LẦN ở gốc cây; các khối kính chỉ trỏ tới bằng id. */
export function KinhKhucXaDefs() {
  return (
    <svg className="glass-defs" width="0" height="0" aria-hidden focusable="false">
      <defs>
        <MotBoLoc id="kkx-lon" nhoe={45} s1={65} s2={56} s3={47} />
        <MotBoLoc id="kkx-nho" nhoe={12} s1={17} s2={15} s3={12} />
      </defs>
    </svg>
  )
}

/** Bản sao chỉ vẽ ở 1× kể cả trên màn hình retina: chi phí của bộ lọc SVG tỉ lệ
 *  với SỐ ĐIỂM ẢNH, mà thứ hiện ra chỉ là một lớp khúc xạ mềm — trả gấp 4 lần
 *  công cho bộ lọc không mua thêm được gì. */
const DUP_PIXEL_RATIO = 1

/**
 * KinhKhucXa — một khối kính khúc xạ thứ nằm sau nó.
 *
 * Bên trong khối có một canvas được đặt và vẽ lại MỖI KHUNG HÌNH sao cho điểm
 * ảnh của nó trùng khít 1:1 với đoạn phim thật phía sau. `overflow: hidden` +
 * bo góc của khối lo toàn bộ phần cắt. Nhìn từ ngoài, khối trông đúng như một
 * mảnh kính dày đặt lên trên đoạn phim.
 *
 * MỘT QUYẾT ĐỊNH KHÔNG HIỂN NHIÊN: bản sao được vẽ theo kích thước của ĐOẠN PHIM,
 * không phải theo kích thước khối kính. Bộ lọc dịch mỗi kênh màu một khoảng khác
 * nhau, nên chính các mép của phần tử được lọc sẽ lộ ra những dải tách kênh gắt.
 * Vẽ ở cỡ đoạn phim thì các dải đó rơi ra NGOÀI khối kính, và bên trong chỉ còn
 * lại phần khúc xạ sạch.
 */
export function KinhKhucXa({
  videoRef,
  co = 'lon',
  className,
  style,
  children,
}: {
  /** Cỡ khối kính. `lon` cho tấm vài trăm pixel; `nho` cho thanh/viên. Chọn sai
   *  thì hoặc không thấy khúc xạ (lọc quá nhẹ), hoặc lộ dải tách kênh (quá nặng). */
  co?: 'lon' | 'nho'
  /** Đoạn phim (hoặc ảnh) nằm phía sau — nguồn để khúc xạ. */
  videoRef: RefObject<HTMLVideoElement | null>
  className?: string
  style?: React.CSSProperties
  children?: ReactNode
}) {
  const kinhRef = useRef<HTMLDivElement>(null)
  const khungRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const kinh = kinhRef.current
    const khung = khungRef.current
    const canvas = canvasRef.current
    if (!kinh || !khung || !canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // ── DỪNG KHI KHÔNG AI NHÌN ──
    // Vòng lặp này vẽ lại một canvas cỡ vài trăm nghìn điểm ảnh rồi cho bộ lọc
    // SVG bẻ nó BA LẦN, sáu mươi lần mỗi giây. Đó là cái giá phải trả để có khúc
    // xạ thật, và trả trong lúc người dùng đang nhìn thì xứng đáng. Trả trong
    // lúc họ đã chuyển sang tab khác, hoặc đã đóng khung trợ lý, thì chỉ là đốt
    // pin. Bản gốc không cần lo chuyện này vì nó là một trang tĩnh chỉ có đúng
    // khối kính đó; ở đây khung trợ lý đóng/mở được và nằm trong một ứng dụng
    // chạy cả ngày.
    let hienHuu = true
    const quanSat = new IntersectionObserver(([e]) => { hienHuu = e.isIntersecting }, { threshold: 0 })
    quanSat.observe(kinh)
    const onVisibility = () => { if (!document.hidden) raf = raf || requestAnimationFrame(vong) }
    document.addEventListener('visibilitychange', onVisibility)

    let raf = 0
    const vong = () => {
      if (document.hidden) { raf = 0; return } // tab ẩn: dừng hẳn, visibilitychange sẽ bật lại
      raf = requestAnimationFrame(vong)
      if (!hienHuu) return
      const video = videoRef.current
      if (!video || !video.videoWidth || !video.videoHeight) return

      const rKinh = kinh.getBoundingClientRect()
      if (!rKinh.width || !rKinh.height) return
      const rVideo = video.getBoundingClientRect()
      if (!rVideo.width || !rVideo.height) return

      // Đặt khung bản sao chồng khít lên hộp của đoạn phim. Vì khung nằm
      // absolute BÊN TRONG khối kính, độ lệch âm này đưa nó về đúng gốc toạ độ
      // của đoạn phim — pixel khớp 1:1 với đoạn phim thật phía sau.
      khung.style.left = `${rVideo.left - rKinh.left}px`
      khung.style.top = `${rVideo.top - rKinh.top}px`
      khung.style.width = `${rVideo.width}px`
      khung.style.height = `${rVideo.height}px`

      const w = Math.max(1, Math.round(rVideo.width * DUP_PIXEL_RATIO))
      const h = Math.max(1, Math.round(rVideo.height * DUP_PIXEL_RATIO))
      if (canvas.width !== w) canvas.width = w
      if (canvas.height !== h) canvas.height = h

      // Vẽ lại khung hình hiện tại, tái tạo đúng cách `object-fit: cover` cắt ảnh
      const cover = Math.max(rVideo.width / video.videoWidth, rVideo.height / video.videoHeight)
      const sw = rVideo.width / cover
      const sh = rVideo.height / cover
      const sx = (video.videoWidth - sw) / 2
      const sy = (video.videoHeight - sh) / 2
      try {
        ctx.drawImage(video, sx, sy, sw, sh, 0, 0, w, h)
      } catch {
        // Một khung hình có thể chưa giải mã xong — bỏ qua, khung sau sẽ vẽ được.
      }
    }

    raf = requestAnimationFrame(vong)
    return () => {
      cancelAnimationFrame(raf)
      quanSat.disconnect()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [videoRef])

  return (
    <div ref={kinhRef} className={className} style={style}>
      <div ref={khungRef} className="kkx-khung" aria-hidden>
        <canvas ref={canvasRef} className="kkx-anh" style={{ filter: `url(#kkx-${co})` }} />
      </div>
      <div className="kkx-suong" aria-hidden />
      {children}
    </div>
  )
}
