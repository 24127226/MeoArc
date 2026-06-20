import { cn } from '@/lib/utils'

/**
 * MeoPet — thú cưng AI dựng bằng SVG + CSS (không phụ thuộc thư viện, không lỗi render).
 * Cử động theo trạng thái: idle thì trôi nhẹ + chớp mắt; `thinking` thì lắc lư nhanh + hiện "...".
 * Tông cam giống pet của Claude, hợp nền đỏ vang của app.
 */
export function MeoMascot({
  thinking = false,
  mood = 'idle',
  className,
}: {
  thinking?: boolean
  mood?: 'idle' | 'happy' | 'thinking' | 'worry'
  className?: string
}) {
  const happy = mood === 'happy'
  const worry = mood === 'worry'
  return (
    <svg
      viewBox="0 0 64 64"
      className={cn('meo-pet', thinking && 'is-thinking', className)}
      role="img"
      aria-label="Trợ lý MeoArc"
    >
      <g className="pet">
        {/* Đuôi */}
        <path
          d="M50 42c7 0 10-6 8-11"
          fill="none"
          stroke="#C2613A"
          strokeWidth="4"
          strokeLinecap="round"
        />
        {/* Tai */}
        <path d="M19 20 14 8l11 6z" fill="#E0875A" stroke="#C2613A" strokeWidth="1.5" strokeLinejoin="round" />
        <path d="M45 20 50 8 39 14z" fill="#E0875A" stroke="#C2613A" strokeWidth="1.5" strokeLinejoin="round" />
        <path d="M19.5 16.5 17 10l5 3z" fill="#F6C9A6" />
        <path d="M44.5 16.5 47 10l-5 3z" fill="#F6C9A6" />

        {/* Thân */}
        <ellipse cx="32" cy="38" rx="21" ry="19" fill="#E0875A" stroke="#C2613A" strokeWidth="1.5" />
        {/* Bụng sáng */}
        <ellipse cx="32" cy="42" rx="13" ry="12" fill="#F6D7BE" />
        {/* Vệt sáng specular — "căng mọng dưới ánh sáng" */}
        <ellipse cx="23" cy="28" rx="6.5" ry="3.4" fill="#fff" opacity="0.45" transform="rotate(-20 23 28)" />
        <circle cx="40" cy="27" r="1.6" fill="#fff" opacity="0.35" />

        {/* Má hồng */}
        <circle cx="19" cy="42" r="3.4" fill="#FDABA5" opacity="0.8" />
        <circle cx="45" cy="42" r="3.4" fill="#FDABA5" opacity="0.8" />

        {/* Lông mày lo lắng + giọt mồ hôi (khi worry) */}
        {worry && (
          <g>
            <path d="M22.4 31.6q2.6 -1.5 4.9 -.2" fill="none" stroke="#2E1410" strokeWidth="1.4" strokeLinecap="round" />
            <path d="M36.7 31.4q2.3 -1.3 4.9 .2" fill="none" stroke="#2E1410" strokeWidth="1.4" strokeLinecap="round" />
            <path d="M45.5 28.4q1.7 2.3 0 3.6q-1.7 -1.3 0 -3.6z" fill="#7FC7CC" opacity="0.85" />
          </g>
        )}

        {/* Mắt — vui thì nhắm cong (^^), bình thường/lo thì tròn (có nhóm chớp) */}
        {happy ? (
          <g fill="none" stroke="#2E1410" strokeWidth="2" strokeLinecap="round">
            <path d="M23 37q2.5 -3.2 5 0" />
            <path d="M36 37q2.5 -3.2 5 0" />
          </g>
        ) : (
          <g className="pet-eyes" fill="#2E1410">
            <ellipse cx="25.5" cy="36" rx="2.6" ry="3.6" />
            <ellipse cx="38.5" cy="36" rx="2.6" ry="3.6" />
            <circle cx="26.4" cy="34.7" r="0.9" fill="#fff" />
            <circle cx="39.4" cy="34.7" r="0.9" fill="#fff" />
          </g>
        )}

        {/* Mũi */}
        <path d="M30.5 40.5h3l-1.5 1.8z" fill="#C2613A" />
        {/* Miệng — vui: cười rộng · lo: miệng nhíu (∩) · thường: nét nhỏ */}
        {happy ? (
          <path d="M28 42.6q4 4 8 0" fill="none" stroke="#C2613A" strokeWidth="1.3" strokeLinecap="round" />
        ) : worry ? (
          <path d="M30 43.8q2 -1.9 4 0" fill="none" stroke="#C2613A" strokeWidth="1.2" strokeLinecap="round" />
        ) : (
          <path d="M32 42.3v1.4M32 43.7c-1.4 0-2.2-.9-2.2-.9M32 43.7c1.4 0 2.2-.9 2.2-.9"
            fill="none" stroke="#C2613A" strokeWidth="1.1" strokeLinecap="round" />
        )}
      </g>

      {/* "..." khi đang nghĩ */}
      <g fill="var(--active)">
        <circle className="pet-think" cx="50" cy="14" r="2" style={{ animationDelay: '0s' }} />
        <circle className="pet-think" cx="56" cy="11" r="2.3" style={{ animationDelay: '0.15s' }} />
      </g>
    </svg>
  )
}
