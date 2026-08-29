/**
 * MeoArc — cầu nối Gemini vượt rào chặn theo vùng.
 *
 * ── VẤN ĐỀ ─────────────────────────────────────────────────────────────────
 * Google chặn `generativelanguage.googleapis.com` theo vị trí của MÁY CHỦ GỌI,
 * không phải vị trí trình duyệt người dùng. Bản triển khai MeoArc nằm trên Azure
 * "East Asia" — thực địa là HONG KONG — nằm trong danh sách không phục vụ. Cùng
 * một khoá, cùng một dòng mã: chạy ở máy nhà thì HTTP 200, chạy trên Azure thì
 * FAILED_PRECONDITION "User location is not supported".
 *
 * ── VÌ SAO KHÔNG PHẢI MỘT WORKER THƯỜNG ────────────────────────────────────
 * Worker Cloudflare chạy ở PoP GẦN NGƯỜI GỌI NHẤT. Người gọi ở đây là Azure Hong
 * Kong, nên Worker sẽ chạy ở PoP Hong Kong và lời gọi ra Google vẫn ĐI RA TỪ HONG
 * KONG. Dựng proxy kiểu đó là tốn công mà không đổi được gì — đây đúng là chỗ dễ
 * làm nhầm nhất, vì nhìn thì có vẻ "đã qua proxy rồi".
 *
 * ── CÁCH LÀM ĐÚNG ──────────────────────────────────────────────────────────
 * Durable Object CÓ vị trí cố định. `locationHint` khi tạo sẽ ghim nó vào một
 * vùng địa lý, và mọi lời gọi ra ngoài phát đi TỪ vùng đó. Nên Worker chỉ nhận
 * rồi đẩy sang Durable Object đặt ở Bắc Mỹ; chính Durable Object mới gọi Google.
 * Google nhìn thấy một lời gọi từ Mỹ → phục vụ bình thường.
 *
 * Đổi lại là thêm một chặng mạng (~150–200ms với `wnam`). Không đáng kể so với
 * vài giây một lượt sinh văn bản, và đây là cái giá rẻ nhất trong ba lựa chọn:
 * dựng lại App Service ở vùng khác thì URL đổi → phải khai báo lại OAuth redirect
 * với Google; đổi sang Vertex AI thì phải bật thanh toán GCP.
 */

/** Chỉ cho đi qua đúng hai tiền tố API của Gemini.
 *  Thiếu chặn này thì đây là một proxy mở — ai biết URL cũng chuyển tiếp được tới
 *  BẤT KỲ đâu, và nó mang tên miền Cloudflare của bạn khi làm việc đó. */
const DUONG_HOP_LE = ['/v1beta/', '/v1/', '/v1alpha/']

const DICH = 'https://generativelanguage.googleapis.com'

/** Chỉ chuyển tiếp đúng những header Gemini cần.
 *  Danh sách CHO PHÉP chứ không phải danh sách cấm: cách này thì một header nhạy
 *  cảm mới xuất hiện sẽ tự động bị giữ lại, thay vì âm thầm lọt sang Google. Đặc
 *  biệt `x-meoarc-proxy` (bí mật của riêng ta) KHÔNG bao giờ được đi tiếp. */
const HEADER_CHO_PHEP = new Set([
  'content-type',
  'accept',
  'x-goog-api-key',
  'x-goog-api-client',
  'x-goog-user-project',
  'authorization',
])

const VUNG_HOP_LE = new Set(['wnam', 'enam', 'sam', 'weur', 'eeur', 'apac', 'oc', 'afr', 'me'])

function loi(ma, thong_diep) {
  // Trả JSON đúng dáng lỗi của Google để phía backend phân loại được như thường,
  // không phải viết thêm nhánh riêng cho proxy.
  return new Response(
    JSON.stringify({ error: { code: ma, message: thong_diep, status: 'PROXY_ERROR' } }),
    { status: ma, headers: { 'content-type': 'application/json' } },
  )
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)

    // Tiện cho việc kiểm tra sau khi triển khai: mở URL này trên trình duyệt là
    // biết Worker sống chưa và đang ghim ở vùng nào, KHÔNG cần khoá API.
    if (url.pathname === '/__suckhoe') {
      return new Response(
        JSON.stringify({ ok: true, vung: env.VUNG || 'wnam', dich: DICH }),
        { headers: { 'content-type': 'application/json' } },
      )
    }

    if (!DUONG_HOP_LE.some((p) => url.pathname.startsWith(p))) {
      return loi(404, `Đường dẫn không thuộc Gemini API: ${url.pathname}`)
    }

    // Bí mật dùng chung — CHỈ bắt buộc khi đã đặt. Để trống thì proxy vẫn chạy
    // (đỡ một bước lúc dựng gấp), nhưng khi đó ai biết URL cũng mượn được hạn
    // mức Cloudflare của bạn. Khoá Gemini thì KHÔNG lộ: proxy không giữ khoá,
    // nó chuyển tiếp khoá của người gọi.
    if (env.PROXY_SECRET && request.headers.get('x-meoarc-proxy') !== env.PROXY_SECRET) {
      return loi(401, 'Sai hoặc thiếu header x-meoarc-proxy.')
    }

    const vung = VUNG_HOP_LE.has(env.VUNG) ? env.VUNG : 'wnam'

    // Tên cố định → luôn cùng MỘT Durable Object, nên nó chỉ được tạo một lần và
    // ở nguyên chỗ cũ. `locationHint` CHỈ có tác dụng lúc tạo lần đầu: đổi vùng
    // sau này phải đổi luôn cái tên, nếu không thì cấu hình mới bị lờ đi trong im
    // lặng — cạm bẫy đúng nghĩa, vì file cấu hình trông như đã đổi rồi.
    const id = env.CHUYEN_TIEP.idFromName(`gemini-${vung}`)
    const stub = env.CHUYEN_TIEP.get(id, { locationHint: vung })
    return stub.fetch(request)
  },
}

/**
 * Durable Object — chỗ THẬT SỰ gọi Google. Nó nằm ở vùng đã ghim, nên lời gọi ra
 * ngoài mang địa chỉ vùng đó. Đối tượng này không lưu gì cả; ta chỉ mượn tính
 * "có địa chỉ cố định" của nó.
 */
export class ChuyenTiep {
  constructor(state, env) {
    this.env = env
  }

  async fetch(request) {
    const vao = new URL(request.url)
    const ra = new URL(DICH + vao.pathname + vao.search)

    const headers = new Headers()
    for (const [ten, gia_tri] of request.headers) {
      if (HEADER_CHO_PHEP.has(ten.toLowerCase())) headers.set(ten, gia_tri)
    }

    // Đọc thân ra bộ đệm thay vì chuyển tiếp dạng luồng. Chuyển luồng thì phải khai
    // `duplex: 'half'` và hành vi lệ thuộc phiên bản runtime — trong khi thân một lời
    // gọi Gemini chỉ là JSON vài chục KB, đệm lại không tốn gì. Đổi lấy sự chắc chắn.
    // ĐÁP ỨNG thì vẫn giữ nguyên luồng (xem bên dưới) vì đó mới là chỗ cần chảy dần.
    const than = ['GET', 'HEAD'].includes(request.method)
      ? undefined
      : await request.arrayBuffer()

    try {
      const dap = await fetch(ra.toString(), {
        method: request.method,
        headers,
        body: than,
      })
      // Trả nguyên đáp ứng, giữ cả luồng (Gemini phát dần khi stream) và mã lỗi
      // gốc — backend đã có sẵn nhánh phân loại 429/503/403, đừng làm nhiễu nó.
      return new Response(dap.body, { status: dap.status, headers: dap.headers })
    } catch (e) {
      return loi(502, `Không gọi được Gemini từ proxy: ${e}`)
    }
  }
}
