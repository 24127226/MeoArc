import { test } from 'node:test'
import assert from 'node:assert/strict'
import { doDieuHuong } from './dieu-huong-chat.ts'

/* Rủi ro DUY NHẤT của việc khớp tại chỗ là CƯỚP MẤT câu hỏi thật. Nên tệp này canh
   hai hướng bằng số lượng ngang nhau: nhận đúng lệnh đi lại, và TUYỆT ĐỐI không
   nhận nhầm câu hỏi về nội dung. */

test('nhận lệnh điều hướng rõ ràng sang Lịch trình', () => {
  for (const s of [
    'mở lịch trình',
    'cho tôi xem lịch trình',
    'chuyển sang phần lịch trình',
    'dẫn tôi qua phần lịch trình',
    'đưa mình tới lịch trình',
    'cho minh xem lich trinh',
  ]) {
    assert.equal(doDieuHuong(s)?.duong_dan, '/lich', `hỏng ở: ${s}`)
  }
})

test('nhận lệnh quay về Hộp thư', () => {
  for (const s of ['mở hộp thư', 'quay lại trang hộp thư', 'cho tôi xem inbox']) {
    assert.equal(doDieuHuong(s)?.duong_dan, '/app', `hỏng ở: ${s}`)
  }
})

test('KHÔNG cướp câu hỏi về nội dung', () => {
  // Đây là phần quan trọng hơn. Bỏ sót một lệnh điều hướng chỉ tốn một lượt gọi;
  // cướp nhầm một câu hỏi thì người dùng mất câu trả lời và không hiểu vì sao.
  for (const s of [
    'tuần này lịch trình tôi thế nào?',
    'lịch trình có gì gấp không',
    'tôi có bao nhiêu việc trong lịch trình',
    'liệt kê lịch trình tuần sau',
    'tóm tắt hộp thư hôm nay',
    'hộp thư có gì mới',
    'trong hộp thư còn gì chưa đọc',
    'mấy giờ mình phải nộp báo cáo',
  ]) {
    assert.equal(doDieuHuong(s), null, `CƯỚP NHẦM: ${s}`)
  }
})

test('không có động từ đi lại thì không nhận', () => {
  assert.equal(doDieuHuong('lịch trình'), null)
  assert.equal(doDieuHuong('hộp thư'), null)
})

test('câu dài thì nhường cho agent', () => {
  const dai =
    'mở lịch trình rồi tìm giúp mình chuyến bay đi Hà Nội để dự sự kiện tuần sau nhé'
  assert.equal(doDieuHuong(dai), null)
})

test('chuỗi rỗng hoặc rác không làm vỡ', () => {
  for (const s of ['', '   ', '???', 'asdkjfh']) {
    assert.equal(doDieuHuong(s), null)
  }
})
