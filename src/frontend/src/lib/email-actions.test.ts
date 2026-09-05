import test from 'node:test'
import assert from 'node:assert/strict'
import { apDungSuaLacQuan, THU_MUC_DICH } from './email-actions.ts'

type Thu = { id: string; folder: string; unread?: boolean }
const thu = (id: string, folder: string): Thu => ({ id, folder, unread: true })

/** Dựng lại đúng hình dạng `folderCache` trong app-shell. */
function dungCache(map: Record<string, Thu[]>) {
  return new Map(Object.entries(map).map(([k, items]) => [k, { items, cursor: null }]))
}

test('sửa lạc quan áp lên danh sách đang hiện', () => {
  const cache = dungCache({})
  const bien = apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, folder: 'trash' }))
  const sau = bien([thu('a', 'inbox'), thu('b', 'inbox')])
  assert.equal(sau[0].folder, 'trash')
  assert.equal(sau[1].folder, 'inbox', 'thư không nằm trong ids thì không được đụng tới')
})

test('MỌI mục cache đều được sửa, không riêng thư mục đang xem', () => {
  // Đây là lỗi thật đã gặp: chỉ sửa danh sách đang hiện thì bản cache của Hộp thư
  // vẫn giữ lá thư vừa xoá, và bấm quay lại Hộp thư sẽ thấy nó HIỆN LẠI một nhịp.
  const cache = dungCache({
    inbox: [thu('a', 'inbox'), thu('b', 'inbox')],
    starred: [thu('a', 'inbox')],
  })
  apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, folder: 'trash' }))
  assert.equal(cache.get('inbox')!.items[0].folder, 'trash')
  assert.equal(cache.get('starred')!.items[0].folder, 'trash', 'cache thư mục khác cũng phải theo')
  assert.equal(cache.get('inbox')!.items[1].folder, 'inbox')
})

test('cache thư mục ĐÍCH bị xoá hẳn để nạp lại, không tự đoán thêm thư vào', () => {
  const cache = dungCache({ inbox: [thu('a', 'inbox')], trash: [thu('z', 'trash')] })
  apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, folder: 'trash' }), 'trash')
  assert.equal(cache.has('trash'), false, 'phải nạp lại Thùng rác từ máy chủ')
  assert.equal(cache.has('inbox'), true, 'thư mục nguồn thì giữ, đã sửa đúng rồi')
})

test('không truyền boCache thì không mục nào bị xoá', () => {
  const cache = dungCache({ inbox: [thu('a', 'inbox')] })
  apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, unread: false }))
  assert.deepEqual([...cache.keys()], ['inbox'])
})

test('cursor của mỗi mục cache được giữ nguyên', () => {
  const cache = new Map([['inbox', { items: [thu('a', 'inbox')], cursor: 'trang-2' }]])
  apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, unread: false }))
  assert.equal(cache.get('inbox')!.cursor, 'trang-2', 'mất cursor là mất nút Tải thêm')
})

test('vòng lùi khép kín: xoá vào Thùng rác, khôi phục về Hộp thư', () => {
  // Bản trước `removeEmails` LỌC BỎ thư khỏi mảng nên nó không bao giờ tới được
  // Thùng rác — vòng "xoá rồi lấy lại" đứt ngay ở giữa dù nút khôi phục vẫn hiện.
  const cache = dungCache({})
  let ds = [thu('a', 'inbox')]
  ds = apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, folder: THU_MUC_DICH.delete }))(ds)
  assert.equal(ds[0].folder, 'trash')
  ds = apDungSuaLacQuan(cache, ['a'], (e) => ({ ...e, folder: THU_MUC_DICH.restore }))(ds)
  assert.equal(ds[0].folder, 'inbox')
  assert.equal(ds.length, 1, 'thư không được biến mất ở bất kỳ chặng nào')
})

test('lưu trữ đi lối riêng, KHÔNG rơi vào Thùng rác', () => {
  assert.equal(THU_MUC_DICH.archive, 'archive')
  assert.notEqual(THU_MUC_DICH.archive, THU_MUC_DICH.delete)
})
