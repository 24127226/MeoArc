import { useEffect, useRef, useState } from 'react'
import { X, Send, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { MeoMascot } from '@/components/meo-mascot'

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Voice Mode (mở rộng UC007) — nhập lệnh bằng giọng nói.
 * STT qua Web Speech API (trình duyệt, không cần backend); orb phản ứng theo
 * biên độ giọng nói thật qua Web Audio. Nói → speech-to-text → đẩy vào pipeline
 * NL controller như khi gõ phím. Thoái lui an toàn nếu trình duyệt không hỗ trợ.
 */
export function VoiceMode({
  open,
  onClose,
  onResult,
}: {
  open: boolean
  onClose: () => void
  onResult: (text: string) => void
}) {
  const [transcript, setTranscript] = useState('')
  const [level, setLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const recRef = useRef<any>(null)
  const finalRef = useRef('')
  const audioRef = useRef<{ ctx: AudioContext; stream: MediaStream; raf: number } | null>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    finalRef.current = ''
    setTranscript('')
    setError(null)
    setLevel(0)

    // 1) Sóng âm thật → biên độ điều khiển orb
    ;(async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        const Ctx = window.AudioContext || (window as any).webkitAudioContext
        const ctx: AudioContext = new Ctx()
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        ctx.createMediaStreamSource(stream).connect(analyser)
        const data = new Uint8Array(analyser.frequencyBinCount)
        const tick = () => {
          analyser.getByteTimeDomainData(data)
          let sum = 0
          for (let i = 0; i < data.length; i++) {
            const v = (data[i] - 128) / 128
            sum += v * v
          }
          const rms = Math.sqrt(sum / data.length)
          setLevel(Math.min(1, rms * 3.2))
          const raf = requestAnimationFrame(tick)
          if (audioRef.current) audioRef.current.raf = raf
        }
        const raf = requestAnimationFrame(tick)
        audioRef.current = { ctx, stream, raf }
      } catch {
        if (!cancelled) setError('Không truy cập được micro — hãy cấp quyền micro cho trang.')
      }
    })()

    // 2) Speech-to-text (vi-VN)
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SR) {
      const rec = new SR()
      rec.lang = 'vi-VN'
      rec.interimResults = true
      rec.continuous = true
      rec.onresult = (e: any) => {
        let interim = ''
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i]
          if (r.isFinal) finalRef.current += r[0].transcript
          else interim += r[0].transcript
        }
        setTranscript(`${finalRef.current} ${interim}`.trim())
      }
      rec.onerror = (e: any) => {
        if (e.error === 'not-allowed' || e.error === 'service-not-allowed')
          setError('Micro bị từ chối — hãy cấp quyền micro cho trang.')
      }
      try {
        rec.start()
      } catch {
        /* đã start */
      }
      recRef.current = rec
    } else {
      setError('Trình duyệt chưa hỗ trợ nhận diện giọng nói (hãy dùng Chrome hoặc Edge).')
    }

    return () => {
      cancelled = true
      try {
        recRef.current?.stop()
      } catch {
        /* noop */
      }
      recRef.current = null
      if (audioRef.current) {
        cancelAnimationFrame(audioRef.current.raf)
        audioRef.current.stream.getTracks().forEach((t) => t.stop())
        audioRef.current.ctx.close()
        audioRef.current = null
      }
    }
  }, [open])

  if (!open) return null

  const submit = () => {
    const t = transcript.trim()
    onClose()
    if (t) onResult(t)
  }

  const scale = 1 + level * 0.34 // mèo "bóp to/nhỏ" theo giọng
  const auraScale = 1 + level * 0.6
  const auraOpacity = 0.4 + level * 0.5

  return (
    <div className="absolute inset-0 z-40 flex flex-col items-center justify-center gap-8 bg-popover/85 p-6 backdrop-blur-md duration-200 animate-in fade-in">
      <button
        onClick={onClose}
        title="Đóng"
        aria-label="Đóng voice mode"
        className="absolute right-4 top-4 flex size-9 items-center justify-center rounded-xl text-popover-foreground/60 transition-colors hover:bg-popover-foreground/10 hover:text-popover-foreground active:scale-95"
      >
        <X className="size-4" />
      </button>

      {error ? (
        <div className="flex max-w-xs flex-col items-center gap-3 text-center">
          <span className="flex size-14 items-center justify-center rounded-2xl bg-destructive/15 text-destructive">
            <AlertTriangle className="size-6" />
          </span>
          <p className="text-sm font-medium text-popover-foreground">{error}</p>
          <button
            onClick={onClose}
            className="rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground"
          >
            Quay lại gõ phím
          </button>
        </div>
      ) : (
        <>
          {/* Mèo MeoArc làm linh hồn AI — bóp to/nhỏ + quầng sáng theo giọng */}
          <div className="relative flex size-52 items-center justify-center">
            {/* vòng sóng lan toả */}
            {[0, 0.8, 1.6].map((d) => (
              <span
                key={d}
                className="voice-ring absolute size-28 rounded-full"
                style={{
                  background: 'radial-gradient(circle, var(--spark), transparent 70%)',
                  animationDelay: `${d}s`,
                }}
              />
            ))}
            {/* quầng sáng AI sau mèo — sáng & phình theo biên độ giọng */}
            <span
              aria-hidden
              className="absolute size-36 rounded-full"
              style={{
                background:
                  'radial-gradient(circle, color-mix(in srgb, var(--spark) 60%, transparent), transparent 70%)',
                filter: 'blur(10px)',
                transform: `scale(${auraScale})`,
                opacity: auraOpacity,
                transition: 'transform 0.08s linear, opacity 0.12s linear',
              }}
            />
            {/* con mèo — co giãn theo giọng nói */}
            <div
              className="relative"
              style={{ transform: `scale(${scale})`, transition: 'transform 0.08s linear' }}
            >
              <MeoMascot thinking className="size-32 drop-shadow-xl" />
            </div>
          </div>

          {/* Transcript trực tiếp */}
          <div className="flex min-h-[4.5rem] max-w-sm flex-col items-center text-center">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              {transcript ? 'Đang nghe…' : 'Hãy nói yêu cầu của bạn'}
            </p>
            <p className="mt-2 text-lg font-medium leading-relaxed text-foreground">
              {transcript || (
                <span className="text-muted-foreground">vd: “tóm tắt thư chưa đọc”</span>
              )}
            </p>
          </div>

          {/* Hành động */}
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="rounded-full px-4 py-2 text-sm font-medium text-popover-foreground/70 transition-colors hover:bg-popover-foreground/10"
            >
              Huỷ
            </button>
            <button
              onClick={submit}
              disabled={!transcript.trim()}
              className={cn(
                'gloss flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground shadow-soft transition-all ease-spring hover:-translate-y-0.5 hover:shadow-float active:scale-95',
                'disabled:pointer-events-none disabled:opacity-50',
              )}
            >
              <Send className="size-4" />
              Gửi cho trợ lý
            </button>
          </div>
        </>
      )}
    </div>
  )
}
