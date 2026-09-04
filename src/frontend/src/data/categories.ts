import type { Category } from '@/data/emails'

/** Bảng màu category của inbox — NGUỒN DUY NHẤT, rút từ palette "Nebula" của
 *  trang giới thiệu (violet · cyan · amber) và giãn ra đủ 7 sắc phân biệt được.
 *  bar = sọc/điểm nhấn (dùng trên nền tối); soft = nền nhuốm nhẹ;
 *  ink = chữ đậm hơn để đọc tốt trên nền nhuốm ở theme sáng. */
export const CATEGORY: Record<Category, { bar: string; soft: string; ink: string }> = {
  moss: { bar: '#977DFF', soft: 'rgba(151, 125, 255, 0.16)', ink: '#4A2CC0' },  // Học tập — tím điện
  sea: { bar: '#87F5F5', soft: 'rgba(135, 245, 245, 0.16)', ink: '#0A5F58' },   // Công việc — cyan (vệt sáng)
  sun: { bar: '#AEB6C2', soft: 'rgba(174, 182, 194, 0.18)', ink: '#4A5364' },   // Hệ thống — Titanium Fog
  cherry: { bar: '#FF2FA3', soft: 'rgba(255, 47, 163, 0.14)', ink: '#B00A63' }, // Cá nhân — Synth Magenta
  sky: { bar: '#3D5AFE', soft: 'rgba(61, 90, 254, 0.14)', ink: '#1C31C0' },     // Mạng xã hội — Electric Cobalt
  terra: { bar: '#FF8A1E', soft: 'rgba(255, 138, 30, 0.16)', ink: '#A85405' },  // Mua sắm — Toxic Amber
  wine: { bar: '#FFCCF2', soft: 'rgba(255, 204, 242, 0.20)', ink: '#8E2C6B' },  // Tài chính — hồng chân trời
  // Đi lại — ngọc bích. Bảy sắc kia đã chiếm tím/cyan/xám/magenta/lam/hổ phách/hồng;
  // XANH LỤC là mảng còn trống duy nhất đủ xa mọi màu đang có. Cyan #87F5F5 (Công việc)
  // là màu gần nhất, nhưng lệch ~25° sắc độ và đậm hơn hẳn nên phân biệt được cả khi
  // hai chip nằm cạnh nhau.
  jade: { bar: '#3EE9A0', soft: 'rgba(62, 233, 160, 0.16)', ink: '#046B4A' },    // Đi lại — ngọc bích
}

/** 8 nhãn phân loại email (UC006/UC009) — ĐỒNG BỘ 1-1 với labeling engine
 *  backend (app/core/labeling.py) và tài liệu Design. Đổi ở đây là đổi mọi nơi. */
export const CATEGORY_OPTIONS: { key: Category; label: string }[] = [
  { key: 'moss', label: 'Học tập' },
  { key: 'sea', label: 'Công việc' },
  { key: 'sun', label: 'Cập nhật & Hệ thống' },
  { key: 'cherry', label: 'Cá nhân' },
  { key: 'sky', label: 'Mạng xã hội' },
  { key: 'terra', label: 'Mua sắm & Ưu đãi' },
  { key: 'wine', label: 'Tài chính' },
  { key: 'jade', label: 'Đi lại' },
]
