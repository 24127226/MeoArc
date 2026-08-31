import type { Category } from '@/data/emails'

/** Tập hành động quản lý email (UC006) — dùng chung cho list (bulk) và detail (đơn). */
export type EmailActions = {
  markRead: (ids: string[], read: boolean) => void
  setImportant: (ids: string[], value: boolean) => void
  applyLabel: (ids: string[], category: Category, label: string) => void
  /** Gỡ thư khỏi danh sách. `mode` phân biệt hệ quả trên Gmail:
   *  'archive' = bỏ nhãn INBOX (thư vẫn còn); 'delete' = chuyển vào thùng rác.
   *  Mặc định 'delete' để các nút Xoá cũ vẫn đúng nếu chưa truyền mode. */
  removeEmails: (ids: string[], mode?: 'archive' | 'delete') => void
}
