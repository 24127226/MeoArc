/* Bộ trích cam kết (bản TS) chạy qua BỘ CA DÙNG CHUNG.
 *
 * Cùng file `src/shared/ca-cam-ket.json` mà bản Python ở backend cũng phải chạy qua
 * (`src/backend/tests/test_cam_ket.py`). Hai bản cài đặt cùng một logic thì chắc chắn
 * lệch nhau theo thời gian — một dòng chú thích "nhớ sửa cả hai bên" không phải ràng
 * buộc, nó chỉ là lời nhắc mà người ta quên. File ca kiểm thử chung MỚI là ràng buộc.
 *
 * Chạy:  npm run test:camket
 */

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

import { docHan, docKhoang, trichCamKet, TRAN_NGAY_RO_RANG, TRAN_NGAY_SUY_RA } from './cam-ket.ts'
import type { Email } from '@/data/emails'

const thuMuc = dirname(fileURLToPath(import.meta.url))
// lib → src → frontend → src(gốc). Bộ ca nằm ở src/shared/.
const CA = JSON.parse(readFileSync(join(thuMuc, '..', '..', '..', 'shared', 'ca-cam-ket.json'), 'utf-8'))
const MOC = new Date(CA.moc)

function iso(d: Date | null | undefined): string | null {
  if (!d) return null
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

for (const c of CA.doc_han) {
  test(`docHan · ${c.ten}`, () => {
    const ra = docHan(c.van, MOC)
    if (c.han === null) {
      assert.equal(ra, null, `đáng lẽ không đọc ra mốc nào, lại ra ${JSON.stringify(ra)}`)
      return
    }
    assert.ok(ra, 'không đọc ra mốc nào')
    assert.equal(iso(ra.han), c.han)
    assert.equal(
      ra.suyRa, c.suy_ra,
      "sai cờ 'suy ra' — cờ này quyết định giao diện HỎI hay tự khẳng định",
    )
  })
}

for (const c of CA.doc_khoang) {
  test(`docKhoang · ${c.ten}`, () => {
    const ra = docKhoang(c.van, MOC)
    if (c.han === null) {
      assert.equal(ra, null)
      return
    }
    assert.ok(ra)
    assert.equal(iso(ra.batDau), c.bat_dau)
    assert.equal(iso(ra.han), c.han)
  })
}

for (const c of CA.trich) {
  test(`trichCamKet · ${c.ten}`, () => {
    const thu = {
      id: '1', sender: 'Ai đó', senderEmail: 'a@b.c', senderInitial: 'A', to: 'tôi',
      subject: c.subject, preview: '', body: c.body, time: '', date: '',
      unread: false, starred: false, category: 'sea',
      // Ca nào không nói thư mục thì là hộp thư đến. Ca CÓ nói là đang kiểm bộ lọc
      // thư mục — cùng một nội dung, chỉ đổi chỗ nó nằm, và kết quả phải đổi theo.
      folder: (c as { folder?: string }).folder ?? 'inbox',
      priority: c.priority ?? undefined,
    } as unknown as Email
    const ra = trichCamKet([thu], MOC)
    assert.equal(
      ra.length === 1, c.nhan,
      c.nhan ? 'phải nhận thư này' : 'phải BỎ QUA thư này',
    )
    if (c.nhan && 'khoang_ro_rang' in c) {
      assert.equal(ra[0].khoangRoRang, c.khoang_ro_rang)
    }
  })
}

test('trần ngày RÕ RÀNG rộng hơn trần SUY RA', () => {
  assert.ok(TRAN_NGAY_RO_RANG > TRAN_NGAY_SUY_RA)
})
