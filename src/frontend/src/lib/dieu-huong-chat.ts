/**
 * Nhận ra câu "đưa tôi sang màn khác" NGAY TRONG KHUNG CHAT — và làm việc đó
 * TRƯỚC KHI gọi mô hình.
 *
 * ── VÌ SAO KHÔNG ĐỂ AGENT LÀM ──
 * Cách hiển nhiên là thêm một tool `dieu_huong` cho agent gọi. Nó chạy được, nhưng
 * mỗi câu "cho tôi xem lịch trình" sẽ tốn một lượt gọi model — mà gói Gemini free chỉ
 * 20 lượt/NGÀY. Đốt hạn mức cho một việc mà một biểu thức chính quy làm được là đổi
 * thứ khan hiếm lấy thứ sẵn có.
 *
 * Khớp tại chỗ thì tốn 0 lượt, phản hồi TỨC THÌ (không có nhịp chờ "đang nghĩ"), và
 * không bao giờ hỏng vì hết quota — tức là nó vẫn chạy đúng lúc buổi trình bày đã
 * dùng cạn lượt hỏi.
 *
 * ── VÌ SAO PHẢI CHẶT TAY ──
 * Rủi ro duy nhất của cách này là CƯỚP MẤT câu hỏi thật. "Tuần này lịch trình tôi thế
 * nào?" có chữ "lịch trình" nhưng là câu hỏi về NỘI DUNG — nhảy trang thay vì trả lời
 * là làm hỏng đúng tính năng chính. Nên luật là:
 *
 *   • phải có ĐỘNG TỪ điều hướng (mở / chuyển / dẫn / cho tôi xem…)
 *   • phải có ĐÍCH ĐẾN
 *   • KHÔNG được chứa dấu hiệu hỏi về nội dung (có gì, thế nào, bao nhiêu…)
 *   • câu phải NGẮN — mô tả dài gần như luôn là yêu cầu thật, không phải lệnh đi lại
 *
 * Nghi ngờ thì NHƯỜNG cho agent. Bỏ sót một lệnh điều hướng chỉ tốn một lượt gọi;
 * cướp nhầm một câu hỏi thì người dùng mất câu trả lời và không hiểu vì sao.
 */

export type DichDen = { duong_dan: string; ten: string }

const DICH: { re: RegExp; dich: DichDen }[] = [
  {
    re: /(lịch trình|lich trinh|lịch của tôi|lich cua toi|thời khoá biểu|thoi khoa bieu|calendar|deadline của tôi)/i,
    dich: { duong_dan: '/lich', ten: 'Lịch trình' },
  },
  {
    re: /(hộp thư|hop thu|hòm thư|hom thu|inbox|danh sách thư|danh sach thu|trang chính|trang chinh)/i,
    dich: { duong_dan: '/app', ten: 'Hộp thư' },
  },
]

/** Động từ cho thấy người dùng muốn ĐI ĐÂU ĐÓ, không phải hỏi về nội dung. */
const DONG_TU_DI = new RegExp(
  '(mở|mo\\b|chuyển|chuyen|đi (tới|đến|qua)|di (toi|den|qua)|dẫn|dan\\b|' +
    'qua (phần|phan|màn|man|trang)|vào (phần|phan|màn|man|trang)|vao (phan|man|trang)|' +
    'cho (tôi|toi|mình|minh|tớ) (xem|coi|tới|toi|đến|den)|đưa (tôi|toi|mình|minh)|dua (toi|minh)|' +
    'xem (phần|phan|màn|man|trang)|quay (lại|lai) (phần|phan|màn|man|trang)|' +
    'about:|goto|navigate)',
  'i',
)

/** Dấu hiệu người dùng đang hỏi VỀ NỘI DUNG, không phải xin đổi màn. */
const HOI_NOI_DUNG =
  /(có gì|co gi|thế nào|the nao|ra sao|bao nhiêu|bao nhieu|quá tải|qua tai|khi nào|khi nao|mấy giờ|may gio|liệt kê|liet ke|tóm tắt|tom tat|còn gì|con gi|những gì|nhung gi|\?)/i

/** Câu dài gần như luôn là yêu cầu thật. Ngưỡng thô nhưng tách đúng hai loại. */
const DAI_TOI_DA = 60

/**
 * Trả đích đến nếu câu này RÕ RÀNG là lệnh điều hướng, ngược lại trả null để
 * nhường cho agent.
 */
export function doDieuHuong(text: string): DichDen | null {
  const s = (text || '').trim()
  if (!s || s.length > DAI_TOI_DA) return null
  if (HOI_NOI_DUNG.test(s)) return null
  if (!DONG_TU_DI.test(s)) return null

  for (const { re, dich } of DICH) {
    if (re.test(s)) return dich
  }
  return null
}
