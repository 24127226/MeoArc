import type { Email } from '@/data/emails'

/** Bỏ dấu tiếng Việt + thường hoá để so khớp không phân biệt dấu/hoa-thường. */
export function normalize(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .toLowerCase()
}

/** Gom toàn bộ trường có thể tìm của 1 email thành 1 chuỗi đã chuẩn hoá. */
export function emailHaystack(e: Email): string {
  return normalize(
    [e.sender, e.senderEmail, e.subject, e.preview, e.body.join(' '), e.label ?? ''].join(' '),
  )
}

/** Khớp khi MỌI từ khoá đều xuất hiện trong haystack. */
export function matchText(hay: string, query: string): boolean {
  const tokens = normalize(query).split(/\s+/).filter(Boolean)
  return tokens.every((t) => hay.includes(t))
}

export type NLResult = {
  unread?: boolean
  starred?: boolean
  attachment?: boolean
  /** Phần chữ còn lại sau khi rút các tiêu chí. */
  text: string
  /** Các tiêu chí đã "hiểu" được, để hiển thị cho người dùng. */
  criteria: string[]
}

/** Bộ "hiểu" ngôn ngữ tự nhiên (mock) — rút tiêu chí lọc từ câu hỏi.
 *  Backend thật sẽ thay bằng semantic search; ở đây minh hoạ cho SRS/demo. */
export function interpretNL(raw: string): NLResult {
  let text = ` ${normalize(raw)} `
  const criteria: string[] = []
  const result: NLResult = { text: '', criteria }

  const rules: { re: RegExp; key: 'unread' | 'starred' | 'attachment'; label: string }[] = [
    { re: /\b(chua doc|chua xem|unread|moi)\b/g, key: 'unread', label: 'Chưa đọc' },
    { re: /\b(gan sao|co sao|danh dau|quan trong|starred|important)\b/g, key: 'starred', label: 'Gắn sao' },
    { re: /\b(dinh kem|tep|file|attachment|attach)\b/g, key: 'attachment', label: 'Có đính kèm' },
  ]

  for (const r of rules) {
    if (r.re.test(text)) {
      result[r.key] = true
      criteria.push(r.label)
      text = text.replace(r.re, ' ')
    }
  }

  // Bỏ vài từ nối vô nghĩa cho phần tìm theo nội dung.
  text = text.replace(/\b(thu|email|tim|loc|cac|nhung|co|tu|trong|cua|va|giup)\b/g, ' ')
  result.text = text.replace(/\s+/g, ' ').trim()
  return result
}
