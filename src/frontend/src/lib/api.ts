/**
 * MeoArc API adapter — LỚP HỢP ĐỒNG FE ↔ BE.
 *
 * Đây là điểm chạm DUY NHẤT giữa giao diện và "thế giới bên ngoài". Mọi màn nên
 * gọi qua `api.*` thay vì dùng trực tiếp dữ liệu/logic mock. Nhờ vậy khi backend
 * thật sẵn sàng, chỉ cần đặt biến môi trường `VITE_API_BASE_URL` là chuyển sang
 * HTTP — KHÔNG phải sửa component nào.
 *
 * - Bỏ trống `VITE_API_BASE_URL`  → dùng `createMockApi()` (chạy hoàn toàn offline cho demo/SRS).
 * - Đặt `VITE_API_BASE_URL=...`   → dùng `createHttpApi()` (gọi REST/SSE thật).
 *
 * Interface `MeoArcApi` bám sát docs/02-API-CONTRACT.md. Kiểu dữ liệu: docs/01-DATA-MODEL.md.
 */
import { interpretCommand, type AgentReply, type PlanOp } from '@/lib/agent'
import { emailHaystack, interpretNL, matchText } from '@/lib/search'
import { emails as seedEmails, type Category, type Email } from '@/data/emails'
import type { User } from '@/auth/auth-context'
import type { AutopilotResult } from '@/components/layout/autopilot-widget'

/* ----------------------------- Kiểu I/O hợp đồng ----------------------------- */

export type EmailQuery = {
  folder?: string
  category?: Category | 'all'
  unread?: boolean
  starred?: boolean
  attachment?: boolean
  /** Từ khoá hoặc câu ngôn ngữ tự nhiên (khi nl=true). */
  q?: string
  nl?: boolean
}

export type EmailListResult = {
  items: Email[]
  nextCursor?: string | null
  /** Khi nl=true: các tiêu chí BE/mock đã "hiểu" (để hiển thị "Đã hiểu: …"). */
  criteria?: string[]
}

export type SendEmailInput = {
  to: string
  cc?: string[]
  bcc?: string[]
  subject: string
  body: string
}

/** Toàn bộ năng lực backend mà FE cần. Mỗi nhóm map 1-1 với docs/02-API-CONTRACT.md. */
export interface MeoArcApi {
  // Auth — UC001/002
  me(): Promise<User | null>
  loginWithGoogle(): Promise<User>
  logout(): Promise<void>
  revokeAccess(): Promise<void>

  // Đọc & tìm — UC003/004/005
  listEmails(query?: EmailQuery): Promise<EmailListResult>
  getEmail(id: string): Promise<Email | null>
  markEmailRead(id: string, read: boolean): Promise<void>

  // Quản lý — UC006 (nhận mảng id cho cả 1 thư lẫn hàng loạt)
  markRead(ids: string[], read: boolean): Promise<void>
  setImportant(ids: string[], value: boolean): Promise<void>
  applyLabel(ids: string[], category: Category, label: string): Promise<void>
  archiveEmails(ids: string[]): Promise<void>
  deleteEmails(ids: string[]): Promise<void>

  // Soạn & gửi — UC010
  sendEmail(input: SendEmailInput): Promise<{ id: string }>

  // Agent — UC007 + mọi AI skill (008/009/014/015/016/017)
  sendAgentMessage(
    message: string,
    ctx: { emails: Email[] },
    opts?: { sessionId?: string; viaVoice?: boolean },
  ): Promise<AgentReply>
  /** Thực thi 1 PlanOp sau khi user Approve (UC006/007). */
  executePlan(op: PlanOp): Promise<void>
  /** Áp dụng kết quả tự lái vào hộp thư (UC017). */
  applyAutopilot(result: AutopilotResult): Promise<void>
}

const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

/* --------------------------------- MOCK API --------------------------------- */
/* Tái dùng đúng logic đang chạy (interpretCommand, interpretNL, matchText) để
   bản demo hành xử y hệt, đồng thời đóng vai "tham chiếu" cho backend thật. */

const STORAGE_KEY = 'meoarc-auth'
const DEMO_USER: User = {
  name: 'Phạm Trần Anh Quân',
  email: 'quanpta.meoarc@gmail.com',
  initial: 'Q',
}

/** Lọc giống EmailList: folder → category → quick/nl → từ khoá. */
function filterEmails(all: Email[], q: EmailQuery): EmailListResult {
  const folder = q.folder ?? 'inbox'
  const byFolder = all.filter((e) => {
    const f = e.folder ?? 'inbox'
    if (folder === 'starred') return e.starred && f !== 'trash'
    return f === folder
  })
  const nl = q.nl && q.q?.trim() ? interpretNL(q.q) : null
  const text = nl ? nl.text : (q.q ?? '')
  const unread = q.unread || nl?.unread
  const starred = q.starred || nl?.starred
  const attachment = q.attachment || nl?.attachment
  const items = byFolder.filter((e) => {
    if (q.category && q.category !== 'all' && e.category !== q.category) return false
    if (unread && !e.unread) return false
    if (starred && !e.starred) return false
    if (attachment && !e.attachments?.length) return false
    if (text.trim() && !matchText(emailHaystack(e), text)) return false
    return true
  })
  return { items, nextCursor: null, criteria: nl?.criteria }
}

export function createMockApi(): MeoArcApi {
  return {
    async me() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        return raw ? (JSON.parse(raw) as User) : null
      } catch {
        return null
      }
    },
    async loginWithGoogle() {
      await delay(1100) // giả lập redirect OAuth
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEMO_USER))
      return DEMO_USER
    },
    async logout() {
      localStorage.removeItem(STORAGE_KEY)
    },
    async revokeAccess() {
      localStorage.removeItem(STORAGE_KEY)
    },

    async listEmails(query = {}) {
      await delay(120)
      return filterEmails(seedEmails, query)
    },
    async getEmail(id) {
      return seedEmails.find((e) => e.id === id) ?? null
    },
    async markEmailRead() {
      /* mock: trạng thái do app-shell quản lý cục bộ */
    },

    async markRead() {},
    async setImportant() {},
    async applyLabel() {},
    async archiveEmails() {},
    async deleteEmails() {},

    async sendEmail() {
      await delay(300)
      return { id: `mock-${Date.now()}` }
    },

    async sendAgentMessage(message, ctx) {
      await delay(700) // giả lập "đang nghĩ"
      return interpretCommand(message, ctx.emails)
    },
    async executePlan() {},
    async applyAutopilot() {},
  }
}

/* --------------------------------- HTTP API --------------------------------- */
/* Khung gọi REST/SSE thật theo docs/02-API-CONTRACT.md. Bật khi có VITE_API_BASE_URL. */

export function createHttpApi(baseUrl: string): MeoArcApi {
  const base = baseUrl.replace(/\/$/, '')
  const req = async <T>(path: string, init?: RequestInit): Promise<T> => {
    const res = await fetch(`${base}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body?.error?.message ?? `HTTP ${res.status}`)
    }
    return (res.status === 204 ? undefined : await res.json()) as T
  }
  const post = <T>(path: string, body?: unknown) =>
    req<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined })

  const qs = (q: EmailQuery) => {
    const p = new URLSearchParams()
    Object.entries(q).forEach(([k, v]) => v != null && v !== '' && p.set(k, String(v)))
    const s = p.toString()
    return s ? `?${s}` : ''
  }

  return {
    me: () => req<User | null>('/me'),
    loginWithGoogle: async () => {
      // OAuth thật là luồng redirect (GET /auth/google/start). Hàm này chỉ là chỗ giữ.
      const { authUrl } = await req<{ authUrl: string }>('/auth/google/start')
      window.location.href = authUrl
      return new Promise<User>(() => {}) // không resolve — trang đã redirect
    },
    logout: () => post<void>('/auth/logout'),
    revokeAccess: () => post<void>('/auth/revoke'),

    listEmails: (query = {}) => req<EmailListResult>(`/emails${qs(query)}`),
    getEmail: (id) => req<Email | null>(`/emails/${id}`),
    markEmailRead: (id, read) => post<void>(`/emails/${id}/read`, { read }),

    markRead: (ids, read) => post<void>('/emails/actions/read', { ids, read }),
    setImportant: (ids, value) => post<void>('/emails/actions/important', { ids, value }),
    applyLabel: (ids, category, label) =>
      post<void>('/emails/actions/label', { ids, category, label }),
    archiveEmails: (ids) => post<void>('/emails/actions/archive', { ids }),
    deleteEmails: (ids) => post<void>('/emails/actions/delete', { ids }),

    sendEmail: (input) => post<{ id: string }>('/emails/send', input),

    // Production nên dùng SSE (text/event-stream); ở đây nhận reply cuối dạng JSON cho gọn.
    sendAgentMessage: (message, _ctx, opts) =>
      post<AgentReply>('/agent/chat', { message, ...opts }),
    executePlan: (op) => post<void>('/agent/plan/execute', { op }),
    applyAutopilot: (result) =>
      post<void>('/agent/autopilot/apply', {
        archive: result.archive,
        markRead: result.markRead,
        flag: result.flag,
      }),
  }
}

/* --------------------------------- Singleton -------------------------------- */

const BASE = import.meta.env.VITE_API_BASE_URL
/** Dùng ở mọi nơi: `import { api } from '@/lib/api'`. Tự chọn mock ↔ http. */
export const api: MeoArcApi = BASE ? createHttpApi(BASE) : createMockApi()
