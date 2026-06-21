import type { Category } from '@/data/emails'

/** Tập hành động quản lý email (UC006) — dùng chung cho list (bulk) và detail (đơn). */
export type EmailActions = {
  markRead: (ids: string[], read: boolean) => void
  setImportant: (ids: string[], value: boolean) => void
  applyLabel: (ids: string[], category: Category, label: string) => void
  removeEmails: (ids: string[]) => void
}
