/**
 * Kiểm tra Worker mà KHÔNG cần Cloudflare: nạp thẳng `worker.js` vào Node, dựng
 * `env` giả và thay `fetch` toàn cục bằng một "Google" giả để xem thứ gì THẬT SỰ
 * được gửi đi.
 *
 * Chạy: npm test  (trong infra/cf-gemini-proxy)
 *
 * Vì sao đáng có: mọi lỗi ở tầng này đều hỏng theo kiểu IM LẶNG. Chuyển tiếp
 * thiếu header khoá thì Google trả 401 — trông y như khoá hỏng. Để lọt bí mật
 * proxy sang Google thì chẳng có dấu hiệu nào cả. Còn đọc mã bằng mắt thì không
 * bắt được mấy chuyện đó.
 */

import assert from 'node:assert/strict'
import { test } from 'node:test'

import worker, { ChuyenTiep } from '../src/worker.js'

const FETCH_THAT = globalThis.fetch

/** Dựng env giả. Durable Object được thay bằng chính lớp thật, chạy tại chỗ —
 *  ta không kiểm chứng được việc GHIM VÙNG ở đây (chỉ Cloudflare làm được), nhưng
 *  kiểm chứng được rằng Worker CÓ đi qua Durable Object và CÓ xin đúng vùng. */
function dungEnv({ bi_mat = null, vung = 'wnam' } = {}) {
  const ghi = { locationHint: null, ten_do: null }
  const env = {
    VUNG: vung,
    ...(bi_mat ? { PROXY_SECRET: bi_mat } : {}),
    CHUYEN_TIEP: {
      idFromName(ten) {
        ghi.ten_do = ten
        return { ten }
      },
      get(_id, tuy_chon) {
        ghi.locationHint = tuy_chon?.locationHint ?? null
        const doi_tuong = new ChuyenTiep({}, env)
        return { fetch: (req) => doi_tuong.fetch(req) }
      },
    },
  }
  return { env, ghi }
}

/** Thay `fetch` toàn cục bằng "Google" giả, ghi lại y nguyên thứ nhận được. */
function gaGoogle({ status = 200, than = '{"ok":true}' } = {}) {
  const nhan = {}
  globalThis.fetch = async (url, tuy_chon) => {
    nhan.url = url
    nhan.method = tuy_chon.method
    nhan.headers = Object.fromEntries(new Headers(tuy_chon.headers))
    nhan.than = tuy_chon.body ? new TextDecoder().decode(tuy_chon.body) : null
    return new Response(than, { status, headers: { 'content-type': 'application/json' } })
  }
  return nhan
}

function goi(duong_dan, { method = 'POST', headers = {}, than = '{"contents":[]}' } = {}) {
  return new Request(`https://proxy.workers.dev${duong_dan}`, {
    method,
    headers,
    ...(method === 'GET' ? {} : { body: than }),
  })
}

const KHOA = { 'x-goog-api-key': 'khoa-gemini-cua-toi', 'content-type': 'application/json' }
const DUONG_THAT = '/v1beta/models/gemini-2.5-flash-lite:generateContent'

test.afterEach(() => {
  globalThis.fetch = FETCH_THAT
})

// ── Đường sống ─────────────────────────────────────────────────────────────

test('kiểm tra sức khoẻ trả về vùng đang ghim, không cần khoá', async () => {
  const { env } = dungEnv()
  const dap = await worker.fetch(goi('/__suckhoe', { method: 'GET' }), env)
  assert.equal(dap.status, 200)
  const body = await dap.json()
  assert.equal(body.ok, true)
  assert.equal(body.vung, 'wnam')
})

test('đường dẫn thật của SDK được chuyển tiếp nguyên vẹn tới Google', async () => {
  // Đường dẫn này KHÔNG phải phỏng đoán: đã đo bằng máy chủ giả, SDK
  // langchain-google-genai 4.2.6 gọi đúng chuỗi này.
  const nhan = gaGoogle()
  const { env } = dungEnv()
  const dap = await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)

  assert.equal(dap.status, 200)
  assert.equal(nhan.url, `https://generativelanguage.googleapis.com${DUONG_THAT}`)
  assert.equal(nhan.method, 'POST')
  assert.equal(nhan.than, '{"contents":[]}')
})

test('giữ nguyên query string (SDK dùng ?alt=sse khi phát dần)', async () => {
  const nhan = gaGoogle()
  const { env } = dungEnv()
  await worker.fetch(goi(`${DUONG_THAT}?alt=sse`, { headers: KHOA }), env)
  assert.ok(nhan.url.endsWith('?alt=sse'), `mất query: ${nhan.url}`)
})

test('khoá API đi tiếp — thiếu là Google trả 401 trông y như khoá hỏng', async () => {
  const nhan = gaGoogle()
  const { env } = dungEnv()
  await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(nhan.headers['x-goog-api-key'], 'khoa-gemini-cua-toi')
})

test('đi qua Durable Object và xin ĐÚNG vùng đã cấu hình', async () => {
  // Đây là CỐT LÕI. Worker thường chạy ở PoP gần người gọi nhất — tức Hong Kong —
  // nên vẫn bị chặn. Mất chỗ này thì proxy "chạy" mà không chữa được gì.
  gaGoogle()
  const { env, ghi } = dungEnv({ vung: 'enam' })
  await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(ghi.locationHint, 'enam')
  assert.ok(ghi.ten_do.includes('enam'), 'tên DO phải kèm vùng, nếu không đổi vùng sẽ bị lờ đi')
})

test('vùng lạ thì lùi về wnam chứ không chuyển tiếp bừa', async () => {
  gaGoogle()
  const { env, ghi } = dungEnv({ vung: 'hongkong' })
  await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(ghi.locationHint, 'wnam')
})

// ── Chặn đúng chỗ ──────────────────────────────────────────────────────────

test('KHÔNG chuyển bí mật proxy sang Google', async () => {
  // `x-meoarc-proxy` là chuyện riêng giữa backend và Worker. Lọt sang bên thứ ba
  // là rò rỉ, mà lại rò không một dấu hiệu.
  const nhan = gaGoogle()
  const { env } = dungEnv({ bi_mat: 'bi-mat-cua-toi' })
  await worker.fetch(
    goi(DUONG_THAT, { headers: { ...KHOA, 'x-meoarc-proxy': 'bi-mat-cua-toi' } }),
    env,
  )
  assert.equal(nhan.headers['x-meoarc-proxy'], undefined)
  assert.equal(nhan.headers['x-goog-api-key'], 'khoa-gemini-cua-toi')
})

test('đường dẫn ngoài Gemini bị chặn — không làm proxy mở', async () => {
  const nhan = gaGoogle()
  const { env } = dungEnv()
  const dap = await worker.fetch(goi('/dau-do-khac', { headers: KHOA }), env)
  assert.equal(dap.status, 404)
  assert.equal(nhan.url, undefined, 'không được gọi ra ngoài khi đã chặn')
})

test('có đặt bí mật thì thiếu/sai đều bị từ chối 401', async () => {
  const nhan = gaGoogle()
  const { env } = dungEnv({ bi_mat: 'dung' })

  const thieu = await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(thieu.status, 401)

  const sai = await worker.fetch(
    goi(DUONG_THAT, { headers: { ...KHOA, 'x-meoarc-proxy': 'sai' } }), env,
  )
  assert.equal(sai.status, 401)
  assert.equal(nhan.url, undefined)
})

test('không đặt bí mật thì vẫn chạy — đỡ một bước lúc dựng gấp', async () => {
  gaGoogle()
  const { env } = dungEnv()
  const dap = await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(dap.status, 200)
})

// ── Lỗi phải đi xuyên qua, không bị proxy nuốt ─────────────────────────────

test('mã lỗi của Google giữ nguyên để backend phân loại đúng', async () => {
  // Backend có sẵn nhánh riêng cho 429 (hết lượt) và 503 (quá tải). Proxy mà đổi
  // hết thành 502 thì người dùng nhận thông báo sai bệnh.
  for (const ma of [429, 503, 403]) {
    const { env } = dungEnv()
    gaGoogle({ status: ma, than: '{"error":{"code":' + ma + '}}' })
    const dap = await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
    assert.equal(dap.status, ma)
  }
})

test('Google không gọi được thì trả 502 kèm lý do, không ném trần', async () => {
  const { env } = dungEnv()
  globalThis.fetch = async () => {
    throw new Error('mạng đứt')
  }
  const dap = await worker.fetch(goi(DUONG_THAT, { headers: KHOA }), env)
  assert.equal(dap.status, 502)
  const body = await dap.json()
  assert.match(body.error.message, /mạng đứt/)
})
