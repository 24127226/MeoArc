import type { Email } from '@/data/emails'

/* ══════════════════════════════════════════════════════════════════════════════
   TRÍCH CAM KẾT TỪ THƯ

   Đây là Giai đoạn 1 của hướng "quản lý lịch trình": đọc thư ra danh sách việc,
   hiển thị trong app, KHÔNG ghi gì vào Google Calendar — nên không cần thêm một
   quyền OAuth nào.

   ── VÌ SAO LƯU "CAM KẾT" CHỨ KHÔNG LƯU "SỰ KIỆN" ──
   Một sự kiện lịch là một khối thời gian: có bắt đầu, có kết thúc, hết. Một cam
   kết có thêm ba thứ mà khối thời gian không có: TRẠNG THÁI (chưa làm / đang đợi
   / xong), NGƯỜI ĐANG CHỜ, và NGUỒN GỐC — lá thư sinh ra nó.

   Khác biệt đó là toàn bộ khoảng cách giữa một cuốn lịch và một người trợ lý.
   Cuốn lịch nói "9 giờ sáng mai có việc". Trợ lý nói "việc này thầy Sơn đang chờ,
   bạn hứa từ thứ Ba, và bạn chưa bắt đầu".

   ── VÌ SAO LÀM BẰNG LUẬT TRƯỚC, KHÔNG GỌI MÔ HÌNH NGAY ──
   Trích cam kết nghĩa là xử lý MỌI thư đến, không chỉ khi người dùng hỏi. Gọi mô
   hình cho mọi thư thì một hộp thư thật đốt sạch hạn mức trong vài giờ. Nên lọc
   trước bằng luật rẻ tiền (có dấu hiệu ngày tháng, có động từ cam kết) rồi mới
   đưa phần còn lại cho mô hình — đúng cách giảm chi phí đã nêu trong kế hoạch.

   ── GIỚI HẠN, NÓI THẲNG ──
   Bộ luật ở đây KHÔNG hiểu ngôn ngữ. Nó nhận diện được "trước 23:59 ngày 30/8"
   và "hạn chót thứ Sáu", nhưng bó tay với "nộp sau khi thầy duyệt đề cương".
   Đó chính là phần dành cho mô hình ở bước sau. Mọi cam kết vì thế đều mang
   `doTinCay`, và dưới ngưỡng thì giao diện phải HỎI chứ không tự ghi —
   một hạn nộp bị đọc sai ngày còn tệ hơn hẳn không có hạn nào.
   ══════════════════════════════════════════════════════════════════════════════ */

/** Mức hậu quả nếu việc này hỏng. Ánh xạ thẳng sang thang sáng trong CSS. */
export type MucRuiRo = 1 | 2 | 3

export type CamKet = {
  id: string
  /** Việc phải làm, viết lại thành câu người đọc hiểu. */
  noiDung: string
  /** Hạn — null nghĩa là có việc nhưng không có thời điểm (vẫn phải theo dõi). */
  han: Date | null
  /** Ngày BẮT ĐẦU nên làm, suy ra từ ước lượng thời lượng. Null = làm gọn trong
   *  đúng ngày hạn.
   *
   *  Đây là phần "lịch ngầm" đã nêu trong kế hoạch: một hạn nộp thứ Sáu KHÔNG
   *  phải một việc của thứ Sáu — nếu nó cần sáu tiếng thì nó là việc của cả thứ
   *  Tư và thứ Năm nữa. Cuốn lịch thường vẽ nó thành một chấm ở thứ Sáu, và đó
   *  chính là lý do người ta hay vỡ kế hoạch: họ nhìn thấy một chấm, không nhìn
   *  thấy khối lượng. */
  batDau: Date | null
  /** Hạn được SUY RA chứ không ghi trong thư (vd "trong 3 ngày làm việc"). */
  hanSuyRa: boolean
  trangThai: 'chua_lam' | 'dang_doi' | 'xong'
  /** Ai sẽ thất vọng nếu việc này trượt. */
  nguoiCho: string
  /** Luôn quay ngược về được lá thư sinh ra nó — không có nguồn thì không kiểm
   *  được, và không kiểm được thì không tin. */
  emailId: string
  /** 0–1. Dưới ngưỡng thì hỏi lại, đừng tự ghi. */
  doTinCay: number
  /** Ước lượng thô số phút cần làm — nền cho phần cảnh báo quá tải. */
  uocLuongPhut: number
  mucRuiRo: MucRuiRo
  /** "Làm cái nào trước" — TRỤC KHÁC `mucRuiRo` ("hỏng thì mất gì").
   *  Xem `mucUuTien()` để biết vì sao phải tách. */
  mucUuTien: 1 | 2 | 3
}

/** Động từ báo hiệu một nghĩa vụ. Chỉ có ngày tháng thì chưa đủ — "hẹn gặp lại
 *  bạn tháng sau" có ngày nhưng không phải việc phải làm. */
const DONG_TU_CAM_KET =
  /\b(nộp|gửi|hoàn thành|hoàn tất|phản hồi|trả lời|xác nhận|đăng ký|thanh toán|đóng|bảo vệ|trình bày|báo cáo|deadline|hạn chót|hạn cuối|due)\b/i

/** Dấu hiệu có mốc thời gian. Gộp cả dạng số lẫn dạng chữ tiếng Việt. */
const DAU_HIEU_THOI_GIAN =
  /(\d{1,2}\s*[/-]\s*\d{1,2}(\s*[/-]\s*\d{2,4})?|\d{1,2}\s*(giờ|h|:)\s*\d{0,2}|ngày\s+\d{1,2}|thứ\s*(hai|ba|tư|năm|sáu|bảy)|chủ\s*nhật|hôm\s*nay|ngày\s*mai|tuần\s*(này|sau|tới)|trong\s+vòng\s+\d+\s*ngày)/i

/** Ngày giờ tuyệt đối: "30/8", "30/08/2026", kèm "23:59" nếu có. */
const NGAY_TUYET_DOI = /(\d{1,2})\s*[/-]\s*(\d{1,2})(?:\s*[/-]\s*(\d{2,4}))?(?:[^\d]{0,12}?(\d{1,2})\s*[:h]\s*(\d{2})?)?/

/** "trong vòng N ngày (làm việc)" — hạn phải TÍNH RA, không có sẵn trong thư. */
const TRONG_VONG = /trong\s+vòng\s+(\d+)\s*ngày(\s*làm\s*việc)?/i

/** Thứ trong tuần, kèm "tuần này / tuần sau" nếu có.
 *  Đây là dạng nói PHỔ BIẾN NHẤT trong thư tiếng Việt — "trước 23:59 thứ Sáu
 *  tuần này" — và cũng là dạng Google Calendar bỏ qua hoàn toàn. Bỏ sót nó thì
 *  bộ trích này mất phần lớn giá trị của chính nó. */
const THU_TRONG_TUAN =
  /(thứ\s*(hai|ba|tư|tv|năm|sáu|bảy)|chủ\s*nhật)(\s*(tuần)\s*(này|sau|tới))?/i
const NGAY_TUONG_DOI = /(hôm\s*nay|ngày\s*mai|ngày\s*kia|cuối\s*tuần)/i
/** Giờ phút đứng riêng: "23:59", "8h", "17h30". */
const GIO_RIENG = /(\d{1,2})\s*(?::|h|giờ)\s*(\d{2})?/i

const SO_THU: Record<string, number> = {
  hai: 1, ba: 2, 'tư': 3, tv: 3, 'năm': 4, 'sáu': 5, 'bảy': 6,
}

/** Ngày gần nhất TỪ `moc` TRỞ ĐI rơi vào thứ `dich` (0=CN…6=T7).
 *  Trùng chính hôm nay thì vẫn tính là hôm nay — "nộp trước 23:59 thứ Sáu" gửi
 *  vào sáng thứ Sáu nói về tối HÔM ĐÓ, không phải tuần sau. */
function thuGanNhat(moc: Date, dich: number, tuanSau: boolean): Date {
  const d = new Date(moc)
  let cach = (dich - d.getDay() + 7) % 7
  if (tuanSau) cach += 7
  d.setDate(d.getDate() + cach)
  return d
}

/** Cộng N ngày, BỎ QUA thứ Bảy và Chủ nhật khi đề bài nói "ngày làm việc".
 *  Đây đúng là loại chi tiết mà một bộ lọc ẩu bỏ qua, rồi cho ra hạn sai hai ngày. */
export function congNgay(tu: Date, soNgay: number, chiNgayLamViec: boolean): Date {
  const d = new Date(tu)
  let con = soNgay
  while (con > 0) {
    d.setDate(d.getDate() + 1)
    if (chiNgayLamViec) {
      const thu = d.getDay()
      if (thu === 0 || thu === 6) continue
    }
    con--
  }
  return d
}

/** Đọc mốc thời gian trong một đoạn văn. Trả null nếu không đọc ra. */
export function docHan(van: string, moc = new Date()): { han: Date; suyRa: boolean } | null {
  const tv = van.match(TRONG_VONG)
  if (tv) {
    return { han: congNgay(moc, Number(tv[1]), Boolean(tv[2])), suyRa: true }
  }

  // Thứ trong tuần / ngày tương đối — xét TRƯỚC ngày tuyệt đối, vì một câu như
  // "trước 23:59 thứ Sáu" có số nhưng số đó là GIỜ, không phải ngày tháng.
  const gio = van.match(GIO_RIENG)
  const gioSo = gio ? Math.min(23, Number(gio[1])) : 23
  const phutSo = gio && gio[2] ? Number(gio[2]) : gio ? 0 : 59

  const td = van.match(NGAY_TUONG_DOI)
  if (td) {
    const d = new Date(moc)
    const t = td[1].replace(/\s+/g, '').toLowerCase()
    if (t.startsWith('ngàymai')) d.setDate(d.getDate() + 1)
    else if (t.startsWith('ngàykia')) d.setDate(d.getDate() + 2)
    else if (t.startsWith('cuốituần')) d.setDate(d.getDate() + ((6 - d.getDay() + 7) % 7))
    d.setHours(gioSo, phutSo, 0, 0)
    return { han: d, suyRa: true }
  }

  const tt = van.match(THU_TRONG_TUAN)
  if (tt) {
    const ten = (tt[2] ?? '').toLowerCase()
    const dich = tt[1].toLowerCase().includes('chủ') ? 0 : (SO_THU[ten] ?? -1)
    if (dich >= 0) {
      const tuanSau = /sau|tới/i.test(tt[5] ?? '')
      const d = thuGanNhat(moc, dich, tuanSau)
      d.setHours(gioSo, phutSo, 0, 0)
      // Có giờ rõ ràng thì độ chắc cao hơn hẳn — "thứ Sáu" suông vẫn là suy ra.
      return { han: d, suyRa: !gio }
    }
  }

  const m = van.match(NGAY_TUYET_DOI)
  if (m) {
    const ngay = Number(m[1])
    const thang = Number(m[2])
    if (ngay >= 1 && ngay <= 31 && thang >= 1 && thang <= 12) {
      let nam = m[3] ? Number(m[3]) : moc.getFullYear()
      if (nam < 100) nam += 2000

      let gio = m[4] ? Number(m[4]) : null
      let phut = m[4] ? (m[5] ? Number(m[5]) : 0) : null

      // GIỜ CÓ THỂ ĐỨNG TRƯỚC NGÀY. `NGAY_TUYET_DOI` chỉ bắt giờ đi SAU ("16/9
      // lúc 17:00"), trong khi tiếng Việt hay viết ngược lại — "trước 17:00 ngày
      // 16/9". Thiếu nhánh này thì giờ rơi về mặc định 23:59, và giao diện hiện
      // một con số MÂU THUẪN với chính câu chữ ngay bên cạnh nó. Đo thật trên thư
      // demo SRS: thư ghi 17:00, thẻ lịch ghi 23:59.
      //
      // Một hạn sai 7 tiếng thì tệ hơn hẳn không có hạn: người dùng tin vào nó.
      if (gio === null) {
        const truoc = van.slice(Math.max(0, (m.index ?? 0) - 20), m.index ?? 0)
        // Lấy lần khớp CUỐI CÙNG — gần ngày nhất mới là giờ của ngày đó.
        const moiKhop = [...truoc.matchAll(/(\d{1,2})\s*(?::|h|giờ)\s*(\d{2})?/gi)]
        const cuoi = moiKhop[moiKhop.length - 1]
        if (cuoi) {
          const g = Number(cuoi[1])
          if (g >= 0 && g <= 23) {
            gio = g
            phut = cuoi[2] ? Number(cuoi[2]) : 0
          }
        }
      }
      // Vẫn không có giờ → 23:59, tức CUỐI ngày hạn. Chọn cuối ngày chứ không phải
      // đầu ngày: "nộp trước ngày 16/9" nghĩa là hết ngày 16 vẫn còn kịp.
      if (gio === null) { gio = 23; phut = 59 }

      const d = new Date(nam, thang - 1, ngay, gio, phut ?? 0)
      // Không ghi năm mà ngày đã qua → hiểu là năm sau. "nộp trước 15/1" gửi
      // hồi tháng 12 nói về tháng 1 năm sau, không phải tháng 1 vừa rồi.
      if (!m[3] && d.getTime() < moc.getTime() - 86400000) d.setFullYear(nam + 1)
      return { han: d, suyRa: false }
    }
  }
  return null
}

/** Mức hậu quả của một cam kết.
 *
 *  CỐ Ý GIỮ CẤP 3 CỰC HIẾM: ở Giai đoạn 1 chưa có hành động nào tiêu tiền, nên
 *  không cam kết nào đạt cấp 3. Cấp đó dành riêng cho lúc agent thật sự đặt vé,
 *  đặt phòng. Phát nó ra sớm thì tới lúc cần, nó đã mất hết sức nặng. */
export function mucRuiRo(e: Email, han: Date | null, moc = new Date()): MucRuiRo {
  if (!han) return 1
  const conLai = han.getTime() - moc.getTime()
  // Quá hạn, hoặc còn dưới một ngày, và có người đang chờ → cấp 2.
  if (conLai < 24 * 3600 * 1000 && e.priority === 'High') return 2
  if (conLai < 0) return 2
  return 1
}

/** Mức ƯU TIÊN — TRỤC KHÁC HẲN mức rủi ro, đừng gộp hai thứ.
 *
 *  `mucRuiRo` trả lời "hỏng thì mất gì" và cố ý giữ cấp 3 cực hiếm, nên ở giai
 *  đoạn này gần như mọi cam kết đều là cấp 1. Đúng với vai trò của nó — nhưng
 *  nghĩa là màn lịch không có gì để phân biệt việc gấp với việc thường, và mọi
 *  thanh hiện ra y hệt nhau. Đo thật trên bộ demo: 13/13 việc đều cấp 1.
 *
 *  `mucUuTien` trả lời câu khác: "làm cái nào trước". Nó gộp mức ưu tiên do AI
 *  gán với khoảng cách tới hạn — vì một việc High còn hai tuần thì không gấp
 *  bằng một việc Medium đến hạn ngày mai.
 *
 *  Giữ hai thang tách rời cũng để màu không nói dối: đỏ ở thang rủi ro nghĩa là
 *  "mất tiền", đỏ ở thang ưu tiên chỉ nghĩa là "làm ngay". Trộn vào nhau thì cả
 *  hai đều mất nghĩa. */
export function mucUuTien(e: Email, han: Date | null, moc = new Date()): 1 | 2 | 3 {
  if (!han) return 1
  const ngayConLai = (han.getTime() - moc.getTime()) / 86400000
  const cao = e.priority === 'High'
  if (ngayConLai < 0) return 3                    // đã trễ
  if (cao && ngayConLai <= 3) return 3            // nặng VÀ sát
  if (cao || ngayConLai <= 2) return 2            // nặng, HOẶC sát
  return 1
}

/** Suy ra ngày nên BẮT ĐẦU từ khối lượng việc.
 *
 *  Chia cho một TRẦN THẤP HƠN trần ngày (3 giờ thay vì 6): không ai dồn toàn bộ
 *  một ngày cho đúng một việc. Lấy trần thật thì cửa sổ làm việc bị tính ngắn
 *  bằng nửa, và lời khuyên "bắt đầu từ hôm nay" sẽ tới muộn một ngày.
 *
 *  Việc dưới ngưỡng đó trả null — làm gọn trong ngày, không cần trải ra. */
const GIO_MOI_NGAY_THUC_TE = 180
export function tinhBatDau(han: Date, phut: number): Date | null {
  const soNgay = Math.ceil(phut / GIO_MOI_NGAY_THUC_TE)
  if (soNgay <= 1) return null
  const d = new Date(han)
  d.setDate(d.getDate() - (soNgay - 1))
  d.setHours(0, 0, 0, 0)
  return d
}

/** Ước lượng thô thời lượng, theo độ dài thư và mức ưu tiên.
 *  Cách trung thực nhất về sau là HỎI người dùng ở vài việc đầu rồi học dần —
 *  đoán bừa rồi cho ra một kế hoạch không ai tin thì tệ hơn không có. */
function uocLuong(e: Email): number {
  const soChu = e.body.join(' ').trim().split(/\s+/).length
  // Bậc cao nhất TỪNG dừng ở 220 chữ, nên mọi việc lớn đều bị quy về cùng một
  // con số 240 phút — tức là không việc nào trải quá 2 ngày, và cái thanh dài
  // nhiều ngày (thứ màn lịch này sinh ra để cho thấy) không bao giờ xuất hiện.
  // Một đặc tả 500 chữ rõ ràng nặng hơn một lời nhắc 230 chữ; bảng cũ không phân
  // biệt được.
  const nen = soChu > 400 ? 240 : soChu > 220 ? 120 : soChu > 90 ? 60 : 30
  return e.priority === 'High' ? nen * 2 : nen
}

/** Rút một câu gọn làm nội dung việc. Ưu tiên tldr của AI, không thì lấy tiêu đề. */
function rutNoiDung(e: Email): string {
  if (e.tldr && e.tldr.length > 8) return e.tldr
  return e.subject
}

/**
 * Trích cam kết từ một danh sách thư.
 *
 * Chỉ nhận thư THẬT SỰ có dấu hiệu nghĩa vụ. Thà bỏ sót còn hơn nhồi rác vào
 * danh sách việc — một danh sách đầy thứ không phải việc thì người dùng thôi mở
 * nó, và lúc đó nó vô dụng hoàn toàn.
 */
export function trichCamKet(emails: Email[], moc = new Date()): CamKet[] {
  const ra: CamKet[] = []

  for (const e of emails) {
    if (e.folder && e.folder !== 'inbox' && e.folder !== 'sent') continue

    // ── Thư MÌNH gửi mà chưa ai trả lời: một mục lịch trình không công cụ nào
    //    theo dõi, và là loại việc hay bị quên nhất. Không cần dấu hiệu ngày giờ.
    if (e.folder === 'sent') {
      ra.push({
        id: `ck-${e.id}`,
        noiDung: `Chờ hồi âm: ${e.subject}`,
        han: null,
        batDau: null,
        hanSuyRa: false,
        trangThai: 'dang_doi',
        nguoiCho: e.to || 'người nhận',
        emailId: e.id,
        doTinCay: 0.9,
        uocLuongPhut: 0,
        mucRuiRo: 1,
        mucUuTien: 1,
      })
      continue
    }

    const van = `${e.subject} ${e.body.join(' ')}`
    const coDongTu = DONG_TU_CAM_KET.test(van)
    const coThoiGian = DAU_HIEU_THOI_GIAN.test(van)

    // CẦN CẢ HAI. Chỉ có ngày tháng thì chưa phải việc ("hẹn gặp lại tháng sau");
    // chỉ có động từ thì không biết bao giờ ("nhớ trả lời anh nhé").
    if (!coDongTu || !coThoiGian) continue

    const doc = docHan(van, moc)
    const han = doc?.han ?? null

    // Độ tin cậy: đọc được hạn tuyệt đối thì chắc; suy ra thì kém chắc hơn;
    // có dấu hiệu nhưng không đọc nổi mốc thì thấp — và giao diện sẽ HỎI.
    const doTinCay = !doc ? 0.45 : doc.suyRa ? 0.7 : 0.88

    ra.push({
      id: `ck-${e.id}`,
      noiDung: rutNoiDung(e),
      han,
      batDau: han ? tinhBatDau(han, uocLuong(e)) : null,
      hanSuyRa: doc?.suyRa ?? false,
      trangThai: e.status === 'Done' ? 'xong' : e.status === 'Waiting' ? 'dang_doi' : 'chua_lam',
      nguoiCho: e.sender,
      emailId: e.id,
      doTinCay,
      uocLuongPhut: uocLuong(e),
      mucRuiRo: mucRuiRo(e, han, moc),
      mucUuTien: mucUuTien(e, han, moc),
    })
  }

  // Có hạn thì xếp trước, gần hạn nhất lên đầu; không hạn thì xuống dưới.
  return ra.sort((a, b) => {
    if (a.han && b.han) return a.han.getTime() - b.han.getTime()
    if (a.han) return -1
    if (b.han) return 1
    return 0
  })
}

/** Tổng thời lượng ước tính theo từng ngày trong `soNgay` ngày tới.
 *  Đây là dữ liệu cho vạch áp lực — thứ trả lời câu hỏi thật của người dùng:
 *  không phải "thứ Năm còn trống không" mà "thứ Năm tôi có chết không". */
export function apLucTheoNgay(
  ds: CamKet[],
  soNgay = 5,
  moc = new Date(),
): { ngay: Date; phut: number; soViec: number }[] {
  const ra: { ngay: Date; phut: number; soViec: number }[] = []
  for (let i = 0; i < soNgay; i++) {
    const d = new Date(moc)
    d.setDate(d.getDate() + i)
    d.setHours(0, 0, 0, 0)
    const het = new Date(d)
    het.setDate(het.getDate() + 1)

    // TÍNH THEO KHOẢNG LÀM, KHÔNG THEO NGÀY HẠN.
    //
    // Bản trước chỉ cộng việc ĐẾN HẠN đúng ngày đó, nên một việc 8 tiếng hạn thứ
    // Sáu làm cho thứ Tư và thứ Năm hiện ra RỖNG — đúng cái ảo giác mà cả tính
    // năng này sinh ra để phá. Đo thật trên bộ demo: 5/7 cột trống trơn dù tuần
    // đó có việc dồn.
    //
    // Nay mỗi ngày nhận phần việc của nó (`phutMoiNgay` đã chia đều theo số ngày
    // việc trải qua), nên "hôm nay nặng bao nhiêu" mới là con số thật.
    const trong = ds.filter((c) => {
      if (!c.han || c.trangThai === 'xong') return false
      const k = khoangNgay(c)
      return !!k && k.dau < het && k.cuoi >= d
    })
    ra.push({
      ngay: d,
      phut: trong.reduce((s, c) => s + phutMoiNgay(c), 0),
      soViec: trong.length,
    })
  }
  return ra
}

/** Trần một ngày làm việc, tính bằng phút. Vượt trần = quá tải.
 *  6 tiếng chứ không phải 8: không ai làm việc tập trung 8 tiếng liền, và đặt
 *  trần theo con số lý tưởng thì cảnh báo quá tải sẽ báo quá muộn. */
export const TRAN_MOI_NGAY = 6 * 60

/** Khoá ngày dạng "2026-08-28" — dùng làm khoá gom nhóm, tránh so sánh Date. */
export function khoaNgay(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Gom cam kết theo ngày. Trả Map để tra cứu O(1) khi vẽ lưới lịch — vẽ lịch
 *  tháng là 42 ô, lọc lại cả danh sách cho từng ô thì thành O(42·n) vô ích. */
export function gomTheoNgay(ds: CamKet[]): Map<string, CamKet[]> {
  const m = new Map<string, CamKet[]>()
  for (const c of ds) {
    if (!c.han) continue
    // TRẢI QUA MỌI NGÀY TỪ `batDau` TỚI `han`, không chỉ ngày hạn.
    //
    // `batDau` vốn đã được tính (một việc 6 tiếng thì cần 3 ngày), nhưng trước đó
    // không ai dùng nó để vẽ — nên một việc trải ba ngày vẫn chỉ hiện đúng ở ngày
    // cuối. Đó lại chính là cách một cuốn lịch thường đánh lừa người dùng: họ
    // thấy MỘT chấm ở thứ Sáu và tưởng đó là việc của thứ Sáu, trong khi thực ra
    // phải bắt đầu từ thứ Tư mới kịp.
    //
    // Chặn ở 14 ngày: một ước lượng hỏng (hoặc thư nói "trong vòng 90 ngày") mà
    // không chặn thì nó bôi kín cả lưới tháng và xoá sạch mọi thứ khác.
    const cuoi = new Date(c.han); cuoi.setHours(0, 0, 0, 0)
    const dau = new Date(c.batDau ?? c.han); dau.setHours(0, 0, 0, 0)
    const soNgay = Math.min(14, Math.max(1, Math.round((cuoi.getTime() - dau.getTime()) / 86400000) + 1))
    for (let i = 0; i < soNgay; i++) {
      const d = new Date(dau)
      d.setDate(d.getDate() + i)
      const k = khoaNgay(d)
      const cu = m.get(k)
      if (cu) cu.push(c)
      else m.set(k, [c])
    }
  }
  return m
}

/** Ngày này nằm ở đâu trong đợt làm của một cam kết.
 *  Dùng để vẽ thẻ nối liền: ngày đầu mang chữ, ngày giữa/cuối chỉ là thanh nối —
 *  nếu ngày nào cũng lặp lại tiêu đề thì mắt đọc ra BA việc, không phải một việc
 *  kéo dài ba ngày. */
export function viTriTrongDot(ck: CamKet, ngay: Date): 'don' | 'dau' | 'giua' | 'cuoi' {
  if (!ck.han || !ck.batDau) return 'don'
  const d = khoaNgay(ngay)
  if (d === khoaNgay(ck.batDau)) return 'dau'
  if (d === khoaNgay(ck.han)) return 'cuoi'
  return 'giua'
}

/* ══════════════════════════════════════════════════════════════════════════════
   XẾP LÀN — biến cam kết thành các THANH nằm ngang trên từng hàng tuần

   VÌ SAO CẦN. Bản trước vẽ thẻ theo TỪNG Ô NGÀY: mỗi ô tự vẽ phần của mình rồi
   trông chờ các mảnh nằm cạnh nhau sẽ trông như một thanh liền. Chúng không liền
   — giữa hai ô có padding, có viền, có khe lưới — nên một việc ba ngày hiện ra
   thành ba viên rời rạc. Mắt đọc ra ba việc. Đó đúng là hiểu sai tai hại nhất mà
   màn lịch này sinh ra, vì cả lý do tồn tại của nó là cho thấy việc DÀI tới đâu.

   Cách chữa duy nhất là ngừng vẽ theo ô: tính sẵn mỗi việc chiếm từ cột nào tới
   cột nào trên hàng tuần, rồi vẽ MỘT phần tử trải ngang qua các cột đó.

   XẾP LÀN. Nhiều việc trùng ngày thì phải nằm chồng lớp, mỗi việc một làn ngang.
   Thuật toán tham lam: xếp việc quan trọng trước, mỗi việc rơi vào làn TRỐNG thấp
   nhất còn chỗ. Việc nào không còn làn thì không vẽ, và những ngày nó phủ qua sẽ
   mang số "+N" — thà nói thẳng "còn nữa" hơn là vẽ tràn làm méo cả lưới.
   ══════════════════════════════════════════════════════════════════════════════ */

/** Một đoạn thẻ nằm trên MỘT hàng tuần. Việc vắt qua hai tuần sinh ra hai đoạn. */
export type DoanThe = {
  ck: CamKet
  /** Cột bắt đầu trong tuần: 0 = thứ Hai … 6 = Chủ nhật. */
  cot: number
  /** Số cột chiếm (≥ 1). */
  rong: number
  /** Làn thứ mấy trong hàng (0 = trên cùng). */
  lan: number
  /** Đoạn này có chứa ngày BẮT ĐẦU thật của việc không → bo góc trái, mang chữ. */
  moDau: boolean
  /** … ngày HẠN thật → bo góc phải, là chỗ đặt dấu hạn. */
  ketThuc: boolean
}

/** Tối đa 3 làn mỗi hàng tuần. Hơn nữa thì ô cao gấp bội các ô khác và lưới méo —
 *  mà lưới méo thì mất luôn khả năng so sánh ngày này với ngày kia bằng mắt. */
export const SO_LAN_TOI_DA = 3

/** Khoảng ngày một cam kết thật sự chiếm (đã chặn 14 ngày như `gomTheoNgay`). */
function khoangNgay(c: CamKet): { dau: Date; cuoi: Date } | null {
  if (!c.han) return null
  const cuoi = new Date(c.han); cuoi.setHours(0, 0, 0, 0)
  const dau = new Date(c.batDau ?? c.han); dau.setHours(0, 0, 0, 0)
  const soNgay = Math.min(14, Math.max(1, Math.round((cuoi.getTime() - dau.getTime()) / 86400000) + 1))
  const dauChan = new Date(cuoi); dauChan.setDate(dauChan.getDate() - (soNgay - 1))
  return { dau: dauChan, cuoi }
}

/** Số phút việc này chiếm TRONG MỘT NGÀY (đã chia đều cho số ngày nó trải qua).
 *
 *  Trước đây vạch quá tải cộng thẳng `uocLuongPhut` cho mọi ngày mà việc phủ qua,
 *  nên một việc 6 tiếng trải 3 ngày bị tính 6 tiếng ở CẢ BA ngày — thành 18 tiếng.
 *  Kết quả là gần như ngày nào cũng "quá tải", mà cảnh báo lúc nào cũng bật thì
 *  chẳng còn là cảnh báo nữa. */
export function phutMoiNgay(c: CamKet): number {
  const k = khoangNgay(c)
  if (!k) return 0
  const soNgay = Math.round((k.cuoi.getTime() - k.dau.getTime()) / 86400000) + 1
  return c.uocLuongPhut / Math.max(1, soNgay)
}

/** Xếp cam kết thành các đoạn thanh cho từng hàng tuần của lưới 42 ô.
 *
 *  Trả về đúng 6 phần tử (6 hàng tuần), mỗi phần tử gồm:
 *   • `doan` — các thanh vẽ được, đã gán làn
 *   • `du`   — Map khoáNgày → số việc KHÔNG vẽ được ở ngày đó (để hiện "+N")
 *   • `soLan`— số làn thật sự dùng, để hàng nào ít việc thì không chừa chỗ thừa
 */
export function xepDoanTheoTuan(
  ds: CamKet[], o: Date[],
): { doan: DoanThe[]; du: Map<string, number>; soLan: number }[] {
  const ra: { doan: DoanThe[]; du: Map<string, number>; soLan: number }[] = []

  for (let w = 0; w < 6; w++) {
    const tuan = o.slice(w * 7, w * 7 + 7)
    if (tuan.length < 7) { ra.push({ doan: [], du: new Map(), soLan: 0 }); continue }
    const tuanDau = new Date(tuan[0]); tuanDau.setHours(0, 0, 0, 0)
    const tuanCuoi = new Date(tuan[6]); tuanCuoi.setHours(0, 0, 0, 0)

    // Cắt mỗi cam kết theo phần giao với tuần này.
    type UngVien = { ck: CamKet; cot: number; rong: number; moDau: boolean; ketThuc: boolean }
    const ung: UngVien[] = []
    for (const c of ds) {
      const k = khoangNgay(c)
      if (!k) continue
      if (k.cuoi < tuanDau || k.dau > tuanCuoi) continue
      const dau = k.dau < tuanDau ? tuanDau : k.dau
      const cuoi = k.cuoi > tuanCuoi ? tuanCuoi : k.cuoi
      const cot = Math.round((dau.getTime() - tuanDau.getTime()) / 86400000)
      const rong = Math.round((cuoi.getTime() - dau.getTime()) / 86400000) + 1
      ung.push({
        ck: c, cot, rong,
        moDau: khoaNgay(dau) === khoaNgay(k.dau),
        ketThuc: khoaNgay(cuoi) === khoaNgay(k.cuoi),
      })
    }

    // Việc NẶNG và việc DÀI lên làn trên. Thanh dài nằm trên thì mắt bắt được
    // ngay "đợt này kéo cả tuần"; nhét nó xuống dưới cùng thì nó biến thành chi
    // tiết phụ, mà nó lại chính là thứ đáng báo động nhất.
    // Xếp theo ƯU TIÊN, không phải rủi ro: rủi ro gần như luôn bằng 1 nên dùng nó
    // để xếp thì thứ tự rơi hết về tiêu chí phụ, và việc gấp có thể nằm dưới cùng.
    ung.sort((a, b) =>
      b.ck.mucUuTien - a.ck.mucUuTien || b.rong - a.rong || a.cot - b.cot ||
      (a.ck.id < b.ck.id ? -1 : a.ck.id > b.ck.id ? 1 : 0))

    const lanDaDung: { tu: number; den: number }[][] = []
    const doan: DoanThe[] = []
    const du = new Map<string, number>()

    for (const u of ung) {
      const tu = u.cot, den = u.cot + u.rong - 1
      let lan = -1
      for (let i = 0; i < SO_LAN_TOI_DA; i++) {
        const dang = lanDaDung[i]
        if (!dang) { lanDaDung[i] = []; lan = i; break }
        if (dang.every((x) => den < x.tu || tu > x.den)) { lan = i; break }
      }
      if (lan < 0) {
        // Hết làn → ghi "+1" cho MỌI ngày việc này phủ qua trong tuần, vì người
        // dùng bấm vào ngày nào cũng phải thấy nó còn ở đó.
        for (let i = tu; i <= den; i++) {
          const k = khoaNgay(tuan[i])
          du.set(k, (du.get(k) ?? 0) + 1)
        }
        continue
      }
      lanDaDung[lan].push({ tu, den })
      doan.push({ ck: u.ck, cot: u.cot, rong: u.rong, lan, moDau: u.moDau, ketThuc: u.ketThuc })
    }

    ra.push({ doan, du, soLan: lanDaDung.length })
  }
  return ra
}

/** Tháng NÊN mở khi vào trang: tháng chứa việc gần nhất còn hạn, không phải tháng
 *  hiện tại. Đo thật ngày 29/08: mọi việc rơi vào tháng 9 nên mở ra thấy tháng 8
 *  trống trơn, còn nội dung thật thì nằm ở hàng "ngoài tháng" và bị làm mờ 30% —
 *  màn hình vừa trống vừa giấu mất thứ đáng xem. Lịch phải mở ra ở CHỖ CÓ VIỆC. */
export function thangNenMo(ds: CamKet[], homNay = new Date()): Date {
  const moc = new Date(homNay.getFullYear(), homNay.getMonth(), 1)
  const conHan = ds
    .filter((c) => c.han && c.trangThai !== 'xong')
    .map((c) => c.han as Date)
    .sort((a, b) => a.getTime() - b.getTime())
  if (!conHan.length) return moc
  // Việc trong tháng này (kể cả đã qua vài ngày) thì cứ ở tháng này.
  const trongThang = conHan.find(
    (d) => d.getFullYear() === homNay.getFullYear() && d.getMonth() === homNay.getMonth(),
  )
  if (trongThang) return moc
  const sau = conHan.find((d) => d >= homNay)
  const chon = sau ?? conHan[conHan.length - 1]
  return new Date(chon.getFullYear(), chon.getMonth(), 1)
}

/** 42 ô của một lưới lịch tháng (6 tuần × 7 ngày), bắt đầu từ THỨ HAI.
 *  Bắt đầu từ thứ Hai chứ không phải Chủ nhật: đó là quy ước lịch ở Việt Nam,
 *  và đặt sai thì mọi phép đọc "cuối tuần" của người dùng đều lệch một ô. */
export function luoiThang(nam: number, thang: number): Date[] {
  const dau = new Date(nam, thang, 1)
  const lech = (dau.getDay() + 6) % 7 // CN=0 → 6; T2=1 → 0
  const bat_dau = new Date(nam, thang, 1 - lech)
  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(bat_dau)
    d.setDate(d.getDate() + i)
    return d
  })
}
