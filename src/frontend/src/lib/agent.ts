import { normalize } from '@/lib/search'
import { CATEGORY_OPTIONS } from '@/data/categories'
import type { Category, Email } from '@/data/emails'

/** Thao tác lên hộp thư mà 1 plan sẽ thực thi sau khi user Approve. */
export type PlanOp =
  | { type: 'archive'; ids: string[] }
  | { type: 'delete'; ids: string[] }
  | { type: 'markRead'; ids: string[]; read: boolean }
  | { type: 'label'; ids: string[]; category: Category; label: string }
  | { type: 'autoLabel'; items: { id: string; category: Category; label: string }[] }

/** Phản hồi của agent — quyết định canvas hiển thị gì. */
export type AgentReply =
  | { kind: 'text'; text: string }
  | { kind: 'done'; text: string }
  | { kind: 'result'; title: string; intro: string; lines: string[] }
  | { kind: 'plan'; intro: string; steps: string[]; warn?: string; confirmLabel: string; op: PlanOp }
  | { kind: 'draft'; intro: string; to: string; subject: string; body: string }
  // --- Generative widgets (UC014/015/016) — render bento tương tác ---
  | {
      kind: 'brief'
      intro: string
      title: string
      when: string
      deadline?: string
      attendees: { name: string; initial: string }[]
      actions: string[]
      points: string[]
    }
  | {
      kind: 'triage'
      intro: string
      title: string
      groups: {
        level: 'high' | 'normal'
        label: string
        items: { sender: string; initial: string; subject: string; suggest: string }[]
      }[]
    }
  | {
      kind: 'digest'
      intro: string
      title: string
      stats: { label: string; value: number }[]
      breakdown: { label: string; count: number }[]
      highlights: string[]
    }
  | {
      kind: 'categorize'
      intro: string
      title: string
      items: { id: string; sender: string; subject: string; category: Category; label: string }[]
    }
  // --- Inbox Autopilot (UC017) — hộp thư tự lái, ambient + reversible ---
  | { kind: 'autopilot'; intro: string; title: string; plan: AutopilotStep[] }

/** Hành động Mèo tự đề xuất cho từng thư khi tự lái. */
export type AutopilotAction = 'archive' | 'markRead' | 'flag' | 'reply' | 'keep'

/** Một bước trong kế hoạch tự lái (1 thư → 1 quyết định + lý do). */
export type AutopilotStep = {
  id: string
  sender: string
  initial: string
  subject: string
  tldr: string
  category: Category
  label: string
  action: AutopilotAction
  reason: string
  /** true = hành động không hoàn tác (gửi đi) → cần user duyệt. */
  risky: boolean
}

/** Ra quyết định cho 1 thư dựa trên priority / category / người gửi. */
function decideAutopilot(e: Email): { action: AutopilotAction; reason: string; risky: boolean } {
  const isBot = /(noreply|no-reply|notification|donotreply|do-not-reply)/i.test(e.senderEmail)
  if (e.priority === 'action') {
    return isBot
      ? { action: 'flag', reason: 'Việc cần làm → gắn sao để bạn không quên', risky: false }
      : { action: 'reply', reason: 'Cần bạn phản hồi → Mèo đã soạn sẵn nháp', risky: true }
  }
  if (e.category === 'terra' || e.label === 'Bản tin')
    return { action: 'archive', reason: 'Bản tin định kỳ → lưu trữ cho gọn', risky: false }
  if (e.priority === 'waiting')
    return { action: 'keep', reason: 'Đang chờ phản hồi → giữ lại theo dõi', risky: false }
  if (e.category === 'sky' || e.label === 'Deploy')
    return { action: 'archive', reason: 'Thông báo hệ thống đã cũ → lưu trữ', risky: false }
  if (e.priority === 'fyi')
    return { action: 'markRead', reason: 'Chỉ để bạn biết → đánh dấu đã đọc', risky: false }
  return { action: 'keep', reason: 'Cần bạn xem kỹ → giữ lại', risky: false }
}

/** Dựng kế hoạch tự lái cho 1 tập email. */
function buildAutopilot(emails: Email[]): AutopilotStep[] {
  return emails.map((e) => {
    const d = decideAutopilot(e)
    return {
      id: e.id,
      sender: e.sender,
      initial: e.senderInitial,
      subject: e.subject,
      tldr: e.tldr ?? e.preview,
      category: e.category,
      label: e.label ?? CATEGORY_OPTIONS.find((o) => o.key === e.category)?.label ?? 'Khác',
      action: d.action,
      reason: d.reason,
      risky: d.risky,
    }
  })
}

const CAT_KEYWORDS: { re: RegExp; cat: Category }[] = [
  { re: /(quang cao|khuyen mai|promo|ban tin|newsletter)/, cat: 'terra' },
  { re: /(giao vu|hoc tap|truong|lop|srs)/, cat: 'moss' },
  { re: /(dev|github|code|pull request|\bpr\b)/, cat: 'sea' },
  { re: /(deploy|vercel|build)/, cat: 'sky' },
  { re: /(ca nhan|ban be)/, cat: 'cherry' },
  { re: /(he thong|cloud|api|gemini)/, cat: 'sun' },
]

/** Chọn các email khớp yêu cầu theo category / người gửi / trạng thái. */
function selectTargets(q: string, emails: Email[]): Email[] {
  let t = emails
  let matched = false

  const catHit = CAT_KEYWORDS.find((k) => k.re.test(q))
  if (catHit) {
    t = t.filter((e) => e.category === catHit.cat)
    matched = true
  } else {
    const senderHit = emails.filter((e) => {
      const s = normalize(e.sender)
      return (
        s.split(/\s+/).some((w) => w.length > 2 && q.includes(w)) ||
        q.includes(normalize(e.senderEmail.split('@')[0]))
      )
    })
    if (senderHit.length) {
      t = senderHit
      matched = true
    }
  }

  if (/(chua doc|unread|moi)/.test(q)) {
    t = t.filter((e) => e.unread)
    matched = true
  }
  if (/(gan sao|quan trong|starred|important)/.test(q)) {
    t = t.filter((e) => e.starred)
    matched = true
  }
  return matched ? t : []
}

const fmtNames = (list: Email[]) =>
  `${list.slice(0, 3).map((e) => e.sender).join(', ')}${list.length > 3 ? '…' : ''}`

/** Diễn giải câu lệnh NL → ý định agent (mock — backend thật dùng LLM + MCP). */
export function interpretCommand(raw: string, emails: Email[]): AgentReply {
  const q = normalize(raw)

  // --- Inbox Autopilot (UC017) — hộp thư tự lái (đặt trước để không lọt vào nhánh "dọn") ---
  if (/(tu lai|autopilot|de meo lo|don ca hop thu|don het hop thu|don tu dong|don sach hop thu)/.test(q)) {
    const inbox = emails.filter((e) => (e.folder ?? 'inbox') === 'inbox')
    if (!inbox.length) return { kind: 'text', text: 'Hộp thư trống — không có gì để tự lái 🎉' }
    return {
      kind: 'autopilot',
      title: `Tự lái ${inbox.length} thư trong hộp thư`,
      intro:
        'Để Mèo lo nhé! Mình lướt từng thư — việc an toàn làm luôn, việc cần gửi đi sẽ hỏi bạn duyệt. Mọi thao tác đều tua lại được.',
      plan: buildAutopilot(inbox),
    }
  }

  // --- Daily Digest (UC014) ---
  if (/(digest|diem tin|bao cao|tom luoc ngay)/.test(q)) {
    const unread = emails.filter((e) => e.unread).length
    const starred = emails.filter((e) => e.starred).length
    const byLabel = new Map<string, number>()
    for (const e of emails) if (e.label) byLabel.set(e.label, (byLabel.get(e.label) ?? 0) + 1)
    return {
      kind: 'digest',
      title: 'Daily Digest — hôm nay',
      intro: 'Đây là báo cáo nhanh hộp thư của bạn:',
      stats: [
        { label: 'Tổng thư', value: emails.length },
        { label: 'Chưa đọc', value: unread },
        { label: 'Quan trọng', value: starred },
      ],
      breakdown: Array.from(byLabel.entries()).map(([label, count]) => ({ label, count })),
      highlights: emails
        .filter((e) => e.starred || e.unread)
        .slice(0, 3)
        .map((e) => `${e.sender}: ${e.subject}`),
    }
  }

  // --- Meeting Brief (UC016) ---
  if (/(brief|cuoc hop|meeting|\bhop\b|lich hop)/.test(q)) {
    return {
      kind: 'brief',
      title: 'Meeting Brief — Nhóm 7',
      intro: 'Mình đã phân tích thread liên quan và dựng brief cuộc họp:',
      when: 'Cuối tuần này · chưa chốt giờ',
      deadline: 'Nộp SRS: 23:59 thứ Sáu',
      attendees: [
        { name: 'Quân (FE)', initial: 'Q' },
        { name: 'Khoa (BE)', initial: 'K' },
      ],
      actions: [
        'Bổ sung đặc tả Use Case',
        'Vẽ sơ đồ Use Case',
        'Chèn mockup giao diện',
        'Chia phần MCP (UC012)',
      ],
      points: [
        'Nhóm cần hoàn thiện & nộp bản SRS đúng hạn.',
        'Buổi họp chốt phân chia phần MCP còn lại.',
      ],
    }
  }

  // --- Read-only: tóm tắt (UC008) ---
  if (/(tom tat|summar|tong hop)/.test(q)) {
    const scopeUnread = /(chua doc|unread|moi)/.test(q)
    const list = scopeUnread ? emails.filter((e) => e.unread) : emails
    if (!list.length) return { kind: 'text', text: 'Không có thư nào để tóm tắt 👍' }
    return {
      kind: 'result',
      title: scopeUnread ? `Tóm tắt ${list.length} thư chưa đọc` : `Tóm tắt ${list.length} thư`,
      intro: 'Mình đã đọc và rút gọn các thư:',
      lines: list.slice(0, 6).map((e) => `${e.sender} — ${e.subject}`),
    }
  }

  // --- Triage (UC015) ---
  if (/(trieu|triage|uu tien|sap xep)/.test(q)) {
    const unread = emails.filter((e) => e.unread)
    if (!unread.length) return { kind: 'text', text: 'Hộp thư đã sạch — không còn thư chưa đọc 🎉' }
    const isHigh = (e: Email) => e.priority === 'action' || e.starred
    const suggestOf = (e: Email) =>
      e.priority === 'action'
        ? 'Trả lời / xử lý ngay'
        : e.priority === 'waiting'
          ? 'Đang chờ phản hồi'
          : 'Đọc nhanh khi rảnh'
    const toItem = (e: Email) => ({
      sender: e.sender,
      initial: e.senderInitial,
      subject: e.subject,
      suggest: suggestOf(e),
    })
    const high = unread.filter(isHigh).map(toItem)
    const normal = unread.filter((e) => !isHigh(e)).map(toItem)
    return {
      kind: 'triage',
      title: `Triage ${unread.length} thư chưa đọc`,
      intro: 'Mình đã phân loại theo độ ưu tiên kèm gợi ý hành động:',
      groups: [
        ...(high.length ? [{ level: 'high' as const, label: 'Ưu tiên cao', items: high }] : []),
        ...(normal.length
          ? [{ level: 'normal' as const, label: 'Bình thường', items: normal }]
          : []),
      ],
    }
  }

  // --- Compose / reply (UC010) ---
  if (/(soan|tra loi|phuc dap|compose|reply)/.test(q)) {
    const target =
      emails.find((e) => {
        const s = normalize(e.sender)
        return s.split(/\s+/).some((w) => w.length > 2 && q.includes(w))
      }) ?? emails[0]
    if (!target) return { kind: 'text', text: 'Không tìm thấy thư để trả lời.' }
    return {
      kind: 'draft',
      intro: `Mình đã soạn một bản nháp trả lời ${target.sender}:`,
      to: `${target.sender} <${target.senderEmail}>`,
      subject: `Re: ${target.subject}`,
      body: `Dạ em chào ${target.sender},\n\nEm đã nhận được email và sẽ phản hồi sớm ạ. Em cảm ơn anh/chị.\n\nTrân trọng,\nAnh Quân`,
    }
  }

  // --- Mark read ---
  if (/(danh dau.*doc|mark.*read|doc het)/.test(q)) {
    const t = emails.filter((e) => e.unread)
    if (!t.length) return { kind: 'text', text: 'Không còn thư chưa đọc nào 👍' }
    return {
      kind: 'plan',
      intro: `Mình sẽ đánh dấu đã đọc cho ${t.length} thư chưa đọc.`,
      steps: [
        `Xác định ${t.length} thư chưa đọc: ${fmtNames(t)}`,
        `Đánh dấu đã đọc ${t.length} thư`,
      ],
      confirmLabel: 'Đánh dấu đã đọc',
      op: { type: 'markRead', ids: t.map((e) => e.id), read: true },
    }
  }

  // --- Phân loại tự động toàn bộ (UC009) ---
  if (/(phan loai tu dong|tu dong phan loai|tu dong gan nhan|categorize all|sap xep nhan)/.test(q)) {
    const items = emails.map((e) => ({
      id: e.id,
      sender: e.sender,
      subject: e.subject,
      category: e.category,
      label: CATEGORY_OPTIONS.find((o) => o.key === e.category)?.label ?? 'Khác',
    }))
    if (!items.length) return { kind: 'text', text: 'Không có thư nào để phân loại.' }
    return {
      kind: 'categorize',
      title: `Đề xuất nhãn cho ${items.length} thư`,
      intro: 'Mình đã phân tích nội dung và đề xuất nhãn — bạn chỉnh lại trước khi áp dụng nhé:',
      items,
    }
  }

  // --- Gắn nhãn (thủ công) ---
  if (/(gan nhan|label|phan loai|categor)/.test(q)) {
    const catHit = CAT_KEYWORDS.find((k) => k.re.test(q))
    const t = selectTargets(q, emails)
    if (!t.length || !catHit) {
      return {
        kind: 'text',
        text: 'Bạn muốn gắn nhãn gì cho thư nào? Ví dụ: “gắn nhãn bản tin cho thư từ newsletter”.',
      }
    }
    const label = CATEGORY_OPTIONS.find((o) => o.key === catHit.cat)?.label ?? 'Nhãn'
    return {
      kind: 'plan',
      intro: `Gắn nhãn “${label}” cho ${t.length} thư.`,
      steps: [`Áp nhãn “${label}” cho ${t.length} thư: ${fmtNames(t)}`],
      confirmLabel: 'Gắn nhãn',
      op: { type: 'label', ids: t.map((e) => e.id), category: catHit.cat, label },
    }
  }

  // --- Lưu trữ / Xoá (bulk, cần xác nhận) ---
  const isDelete = /(xoa|delete|thung rac)/.test(q)
  const isArchive = /(luu tru|archive|don|dep|clean)/.test(q)
  if (isDelete || isArchive) {
    const t = selectTargets(q, emails)
    if (!t.length) {
      return {
        kind: 'text',
        text: `Bạn muốn ${isDelete ? 'xoá' : 'lưu trữ'} những thư nào? Ví dụ: “${
          isDelete ? 'xoá' : 'lưu trữ'
        } thư bản tin” hoặc “từ Vercel”.`,
      }
    }
    const verb = isDelete ? 'Xoá' : 'Lưu trữ'
    return {
      kind: 'plan',
      intro: `Mình tìm thấy ${t.length} thư khớp yêu cầu. Đây là kế hoạch đề xuất:`,
      steps: [
        `Quét hộp thư & xác định ${t.length} thư khớp: ${fmtNames(t)}`,
        isDelete ? `Chuyển ${t.length} thư vào thùng rác` : `Lưu trữ ${t.length} thư khỏi hộp thư`,
        'Cập nhật hộp thư & ghi nhật ký',
      ],
      warn: isDelete
        ? 'Xoá hàng loạt không thể hoàn tác — cần bạn xác nhận trước khi thực thi.'
        : undefined,
      confirmLabel: `${verb} ${t.length} thư`,
      op: isDelete
        ? { type: 'delete', ids: t.map((e) => e.id) }
        : { type: 'archive', ids: t.map((e) => e.id) },
    }
  }

  // --- Không rõ → hỏi lại ---
  return {
    kind: 'text',
    text: 'Mình chưa rõ yêu cầu. Thử ví dụ: “tóm tắt thư chưa đọc”, “lưu trữ thư bản tin”, “soạn trả lời giáo vụ”, hoặc “triage hộp thư”.',
  }
}
