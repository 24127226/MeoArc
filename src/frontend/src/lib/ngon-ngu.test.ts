/* KHOÁ DỊCH KHÔNG ĐƯỢC LỌT RA MÀN HÌNH.
 *
 * Khi đổi hàng loạt chuỗi sang `t('khoa')`, kiểu hỏng dễ nhất là thay đúng chuỗi
 * nhưng QUÊN bọc lời gọi: `{editing ? 'ch.editDraft' : 'ch.replyDraft'}`. Nó hợp lệ
 * với TypeScript (vẫn là string), build vẫn xanh, và trên màn hình hiện ra đúng chữ
 * "ch.replyDraft". Đã lọt thật một lần, ở ngay tiêu đề thẻ bản nháp — chỗ người dùng
 * nhìn lâu nhất trước khi bấm gửi.
 *
 * Đây là lý do `t()` trả về CHÍNH KHOÁ khi thiếu: hỏng thì nhìn thấy được. Nhưng
 * "nhìn thấy được" chỉ có tác dụng nếu có người mở đúng màn hình đó ra xem — nên
 * kiểm bằng máy, mỗi lần chạy test.
 *
 * Đọc thẳng mã nguồn thay vì dựng cây React: không cần trình duyệt, chạy trong một
 * nốt nhạc, và bắt được cả những nhánh chỉ hiện ra trong trạng thái hiếm.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const GOC = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')

function moiTepNguon(thuMuc: string): string[] {
  const ra: string[] = []
  for (const m of readdirSync(thuMuc, { withFileTypes: true })) {
    const duong = join(thuMuc, m.name)
    if (m.isDirectory()) ra.push(...moiTepNguon(duong))
    else if (m.name.endsWith('.tsx')) ra.push(duong)
  }
  return ra
}

/** Tiền tố khoá đang dùng trong từ điển. */
const TIEN_TO = String.raw`act|nav|mail|chat|ch|st|cal|auto|toast|det|fld|sc|tv|cmd|cmp|vo|set|tone|plan|auth|sub|tok|al|ck|gy|tm|notif|onb|pref|skill|sug|flt|travel|voice|settings|theme|scope|acct`

test('không có khoá dịch nào bị in thẳng ra giao diện', () => {
  const loi: string[] = []
  for (const tep of moiTepNguon(join(GOC, 'components'))
    .concat(moiTepNguon(join(GOC, 'pages')))) {
    const dong = readFileSync(tep, 'utf8').split('\n')
    dong.forEach((l, i) => {
      // Chỉ soi VỊ TRÍ HIỂN THỊ: `{... 'khoa' ...}` trong JSX hoặc thuộc tính
      // title/aria-label/label/placeholder. Khoá nằm trong mảng dữ liệu
      // (`label: 'nav.inbox'`) là hợp lệ — nơi vẽ mới gọi t().
      const m = l.match(
        new RegExp(String.raw`(title|aria-label|label|placeholder)=\{[^}]*'(?:${TIEN_TO})\.[A-Za-z0-9]+'|^\s*\{[^}]*\?[^}]*'(?:${TIEN_TO})\.[A-Za-z0-9]+'`),
      )
      if (!m) return
      // Bọc trong t(...) hoặc dich(...) là đúng.
      if (/\b(t|dich)\(/.test(m[0])) return
      loi.push(`${tep.split(/[\\/]/).pop()}:${i + 1}  ${l.trim().slice(0, 88)}`)
    })
  }
  assert.deepEqual(loi, [], `Khoá dịch lọt ra màn hình:\n  ${loi.join('\n  ')}`)
})
