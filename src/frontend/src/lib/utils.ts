import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Gộp className có điều kiện + xử lý xung đột Tailwind. Dùng khắp các component. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
