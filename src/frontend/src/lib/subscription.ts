import { useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { SubscriptionStatus } from '@/lib/api'

/** Ước lượng token cho MỘT lượt hỏi trợ lý (prompt + suy luận + trả lời).
 *  Dùng để quy hạn mức ra "còn khoảng bao nhiêu lượt" — dễ hiểu hơn con số token trần trụi. */
export const TOKENS_PER_TURN = 5_000

/** Số lượt hỏi còn lại (lấy mức chặt hơn giữa hạn ngày và hạn tháng). */
export function turnsLeft(s: SubscriptionStatus | null): number {
  if (!s) return 0
  return Math.floor(Math.min(s.daily.remaining, s.monthly.remaining) / TOKENS_PER_TURN)
}

/** Đã chạm trần ngày hoặc tháng → backend sẽ từ chối lượt chat tiếp theo. */
export function isOutOfTokens(s: SubscriptionStatus | null): boolean {
  if (!s) return false
  return s.daily.remaining <= 0 || s.monthly.remaining <= 0
}

/** Tỉ lệ đã dùng của hạn mức ngày (0..1). */
export function dailyRatio(s: SubscriptionStatus | null): number {
  if (!s || s.daily.limit <= 0) return 0
  return Math.min(1, s.daily.used / s.daily.limit)
}

/** Nạp gói + mức tiêu thụ token. `refresh()` gọi lại sau mỗi lượt chat (token vừa bị trừ). */
export function useSubscription() {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null)

  const refresh = useCallback(async () => {
    try {
      setStatus(await api.subscription())
    } catch {
      /* chưa đăng nhập hoặc backend tắt → để null, giao diện tự ẩn */
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { status, refresh, setStatus }
}
