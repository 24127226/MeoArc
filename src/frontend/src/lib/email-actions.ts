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
  /** Đưa thư từ thùng rác trở lại hộp thư — đường lùi cho `removeEmails('delete')`. */
  restoreEmails: (ids: string[]) => void
}

/** Một mục cache thư mục (stale-while-revalidate) — chỉ cần `items` để suy luận. */
type MucCache<T> = { items: T[]; cursor: string | null }

/**
 * Áp một sửa đổi lạc quan lên CẢ danh sách đang hiện LẪN mọi mục `folderCache`.
 *
 * Vì sao phải đụng tới cache: cache trả bản cũ ra màn hình ngay khi đổi thư mục rồi
 * mới nạp bản mới đè lên. Nếu chỉ sửa danh sách đang hiện thì xoá một thư ở Hộp thư,
 * bấm sang Thùng rác rồi bấm về Hộp thư sẽ thấy thư vừa xoá HIỆN LẠI một nhịp — đủ
 * lâu để người xem tin là app xoá hụt. Lỗi này KHÔNG lộ ở chế độ mock (không có
 * cache) nên chỉ bộ test này giữ được nó.
 *
 * `boCache` xoá hẳn mục của thư mục ĐÍCH khi thư chuyển chỗ: thư mới tới không nằm
 * trong bản cache cũ của thư mục đó, và tự chèn vào là đoán — thà nạp lại cho thật.
 */
export function apDungSuaLacQuan<T extends { id: string }>(
  cache: Map<string, MucCache<T>>,
  ids: string[],
  sua: (e: T) => T,
  boCache?: string,
): (ds: T[]) => T[] {
  const bien = (ds: T[]) => ds.map((e) => (ids.includes(e.id) ? sua(e) : e))
  for (const [k, v] of cache) cache.set(k, { ...v, items: bien(v.items) })
  if (boCache) cache.delete(boCache)
  return bien
}

/** Thư mục thư sẽ tới sau mỗi hành động — nguồn sự thật DUY NHẤT cho vòng lùi. */
export const THU_MUC_DICH = {
  archive: 'archive',
  delete: 'trash',
  restore: 'inbox',
} as const
