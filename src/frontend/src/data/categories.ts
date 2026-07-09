import type { Category } from '@/data/emails'

/** Bảng màu category của inbox — NGUỒN DUY NHẤT, rút từ palette "Provence Meadow".
 *  bar = sọc/điểm nhấn; soft = nền nhuốm nhẹ; ink = chữ đọc tốt trên nền nhuốm. */
export const CATEGORY: Record<Category, { bar: string; soft: string; ink: string }> = {
  moss: { bar: '#4B5B34', soft: 'rgba(75, 91, 52, 0.16)', ink: '#3c4a2a' },
  sea: { bar: '#092F33', soft: 'rgba(9, 47, 51, 0.12)', ink: '#092f33' },
  sun: { bar: '#EA8913', soft: 'rgba(234, 137, 19, 0.16)', ink: '#b46708' },
  cherry: { bar: '#FDABA5', soft: 'rgba(253, 171, 165, 0.26)', ink: '#bb5a52' },
  sky: { bar: '#7FC7CC', soft: 'rgba(127, 199, 204, 0.22)', ink: '#2f6f74' },
  terra: { bar: '#AF5031', soft: 'rgba(175, 80, 49, 0.15)', ink: '#8f3f25' },
  wine: { bar: '#980204', soft: 'rgba(152, 2, 4, 0.12)', ink: '#980204' },
}

/** 7 nhãn phân loại email (UC006/UC009) — ĐỒNG BỘ 1-1 với labeling engine
 *  backend (app/core/labeling.py) và tài liệu Design. Đổi ở đây là đổi mọi nơi. */
export const CATEGORY_OPTIONS: { key: Category; label: string }[] = [
  { key: 'moss', label: 'Học tập' },
  { key: 'sea', label: 'Công việc' },
  { key: 'sun', label: 'Cập nhật & Hệ thống' },
  { key: 'cherry', label: 'Cá nhân' },
  { key: 'sky', label: 'Mạng xã hội' },
  { key: 'terra', label: 'Mua sắm & Ưu đãi' },
  { key: 'wine', label: 'Tài chính' },
]
