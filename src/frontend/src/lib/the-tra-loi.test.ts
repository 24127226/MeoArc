/* MỘT TIN NHẮN CŨ THIẾU DỮ LIỆU KHÔNG ĐƯỢC GIẾT CẢ APP.
 *
 * ── CHUYỆN ĐÃ XẢY RA ──
 * Người dùng báo "vào phần thư thì màn hình đen". Máy chủ trả 200, mọi tệp tải được.
 * Lưới an toàn vừa dựng bắt được nguyên văn:
 *
 *     Cannot read properties of undefined (reading 'map')
 *       at Fp  ← component vẽ MỘT tin nhắn của trợ lý
 *       at aside
 *       at jp  ← ChatPanel
 *
 * Gốc: thẻ trả lời được LƯU NGUYÊN VĂN xuống DB rồi dựng lại y hệt khi mở app
 * (`toLocalMsg` truyền thẳng `m.reply`). Một thẻ cũ thiếu một mảng — ví dụ thẻ `plan`
 * chỉ gán `emails` khi danh sách không rỗng — là `.map` trên `undefined`, và vì React
 * không có ranh giới lỗi ở giữa, CẢ CÂY bị tháo sạch.
 *
 * Điều đáng sợ ở đây không phải một thẻ vẽ hỏng, mà là MỘT dòng dữ liệu cũ trong DB
 * làm sập toàn bộ ứng dụng — và không có cách nào chữa từ phía người dùng, kể cả xoá
 * cache, vì dữ liệu nằm ở máy chủ.
 *
 * Nên luật là: mọi truy cập mảng trên `reply` phải chịu được `undefined`. Lịch sử trò
 * chuyện là dữ liệu CŨ, và mã mới không bao giờ được quyền giả định nó đủ trường.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const TEP = new URL('../components/layout/chat-panel.tsx', import.meta.url).pathname
  .replace(/^\/([A-Za-z]:)/, '$1')

test('mọi truy cập mảng trên `reply` đều chịu được dữ liệu cũ thiếu trường', () => {
  const dong = readFileSync(TEP, 'utf8').split('\n')
  const loi: string[] = []

  dong.forEach((l, i) => {
    if (l.trim().startsWith('//') || l.trim().startsWith('*')) return
    // `reply.<truong>.map(` / `.length` / `.reduce(` … mà KHÔNG bọc `?? []`
    const m = l.match(/reply\.[a-zA-Z_]+\.(map|length|reduce|some|every|filter|slice|flatMap)\b/)
    if (!m) return
    // Bọc đúng cách: `(reply.x ?? []).map` — hoặc đã chặn sẵn bằng `reply.x &&`
    const truong = m[0].split('.')[1]
    if (l.includes(`(reply.${truong} ?? [])`)) return
    if (l.includes(`reply.${truong} && `)) return
    loi.push(`chat-panel.tsx:${i + 1}  ${l.trim().slice(0, 84)}`)
  })

  assert.deepEqual(
    loi, [],
    'Truy cập mảng không có lưới — một tin nhắn cũ thiếu trường này sẽ làm ĐEN cả app:\n  ' +
      loi.join('\n  '),
  )
})
