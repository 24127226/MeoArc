import { useEffect, useState, type CSSProperties } from 'react'
import { flushSync } from 'react-dom'
import { NavRail } from '@/components/layout/nav-rail'
import { EmailList } from '@/components/layout/email-list'
import { EmailDetail } from '@/components/layout/email-detail'
import { ChatPanel } from '@/components/layout/chat-panel'
import { CommandPalette } from '@/components/layout/command-palette'
import { Onboarding } from '@/components/layout/onboarding'
import { useTheme } from '@/components/theme-provider'
import { emails as seedEmails } from '@/data/emails'
import type { EmailActions } from '@/lib/email-actions'

/** Đổi state có morph mượt qua View Transitions.
 *  Dùng flushSync để DOM cập nhật ĐỒNG BỘ trong callback (chuẩn React 19 + VT),
 *  tránh snapshot che mất panel. Thoái lui an toàn + tôn trọng reduced-motion. */
function withTransition(fn: () => void) {
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const doc = document as unknown as { startViewTransition?: (cb: () => void) => unknown }
  if (reduce || typeof doc.startViewTransition !== 'function') {
    fn()
    return
  }
  try {
    doc.startViewTransition(() => flushSync(fn))
  } catch {
    fn()
  }
}

/** Layout 3 phần: nav rail trái · email list giữa · (chi tiết email | AI chat) phải */
export function AppShell() {
  const [emails, setEmails] = useState(seedEmails)
  const [openedId, setOpenedId] = useState<string | null>(null)
  // Lệnh do nút ngữ cảnh (UC016) / Command Palette đẩy sang ChatPanel
  const [pendingCommand, setPendingCommand] = useState<string | null>(null)
  const [commandOpen, setCommandOpen] = useState(false)
  const [activeNav, setActiveNav] = useState('inbox') // tab nav trái
  const { theme, toggleTheme } = useTheme()

  // Tab nav → thư mục lọc danh sách ('agent' chỉ chuyển focus sang chat)
  const folder = activeNav === 'agent' ? 'inbox' : activeNav
  const selectNav = (id: string) => {
    setActiveNav(id)
    withTransition(() => setOpenedId(null))
  }
  const inboxUnread = emails.filter((e) => (e.folder ?? 'inbox') === 'inbox' && e.unread).length

  // Mở email = chuyển panel phải sang chi tiết + đánh dấu đã đọc (UC004)
  const openEmail = (id: string) => {
    withTransition(() => setOpenedId(id))
    setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, unread: false } : e)))
  }
  const closeEmail = () => withTransition(() => setOpenedId(null))

  // Nút "đoán trước ý định" / palette: đóng chi tiết → mở canvas AI → tự gửi lệnh
  const runAgentAction = (command: string) => {
    withTransition(() => setOpenedId(null))
    setPendingCommand(command)
  }

  // ⌘K / Ctrl+K mở Command Palette
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setCommandOpen((v) => !v)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // Hành động quản lý email (UC006) — nhận mảng id để dùng được cho cả bulk
  const actions: EmailActions = {
    markRead: (ids, read) =>
      setEmails((prev) => prev.map((e) => (ids.includes(e.id) ? { ...e, unread: !read } : e))),
    setImportant: (ids, value) =>
      setEmails((prev) => prev.map((e) => (ids.includes(e.id) ? { ...e, starred: value } : e))),
    applyLabel: (ids, category, label) =>
      setEmails((prev) => prev.map((e) => (ids.includes(e.id) ? { ...e, category, label } : e))),
    removeEmails: (ids) => {
      setEmails((prev) => prev.filter((e) => !ids.includes(e.id)))
      if (openedId && ids.includes(openedId)) setOpenedId(null)
    },
  }

  const openedEmail = emails.find((e) => e.id === openedId) ?? null

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <NavRail activeId={activeNav} onSelect={selectNav} badges={{ inbox: inboxUnread }} />
      <EmailList
        emails={emails}
        folder={folder}
        openedId={openedId}
        onOpen={openEmail}
        actions={actions}
      />
      {/* Panel phải — morph qua View Transitions nhờ view-transition-name cố định */}
      <div
        className="flex min-w-0 flex-1"
        style={{ ['viewTransitionName' as keyof CSSProperties]: 'rightpanel' } as CSSProperties}
      >
        {openedEmail ? (
          <EmailDetail
            email={openedEmail}
            onClose={closeEmail}
            actions={actions}
            onAgentAction={runAgentAction}
          />
        ) : (
          <ChatPanel
            emails={emails}
            actions={actions}
            injectedCommand={pendingCommand}
            onInjectConsumed={() => setPendingCommand(null)}
          />
        )}
      </div>

      {/* Command Palette (⌘K) */}
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        onRun={runAgentAction}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Onboarding coachmark — chỉ hiện lần đầu */}
      <Onboarding />
    </div>
  )
}
