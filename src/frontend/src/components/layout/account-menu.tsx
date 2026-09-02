import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, ShieldOff, AlertTriangle, UserPlus } from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { api, duongDanApi, apiBaseUrlDaCauHinh } from '@/lib/api'
import type { SubscriptionStatus } from '@/lib/api'
import { UsageSummary } from '@/components/layout/subscription-dialog'
import { PricingScreen } from '@/components/layout/pricing-screen'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

type TaiKhoan = {
  user_id: number; email: string; name: string; provider: string; dang_dung: boolean
}

export function AccountMenu() {
  const { user, logout, revokeAccess } = useAuth()
  /** Các tài khoản trình duyệt này đang đăng nhập. Nạp khi MỞ hộp thoại chứ không
   *  nạp sẵn: đây là thông tin chỉ dùng khi người ta thật sự định đổi tài khoản. */
  const [dsTaiKhoan, setDsTaiKhoan] = useState<TaiKhoan[]>([])
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState<'menu' | 'revoke'>('menu')
  // Gói + token đã dùng: nạp khi mở menu, hiện ngay dưới thẻ tài khoản.
  const [sub, setSub] = useState<SubscriptionStatus | null>(null)
  const [plansOpen, setPlansOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    let alive = true
    api.subscription().then((s) => alive && setSub(s)).catch(() => {})
    return () => { alive = false }
  }, [open])

  if (!user) return null

  // Đăng xuất → về TRANG GIỚI THIỆU (không phải màn đăng nhập): người vừa thoát
  // thường chưa muốn đăng nhập lại ngay, đưa họ về đúng cửa vào của sản phẩm.
  const handleLogout = () => {
    setOpen(false)
    logout()
    navigate('/', { replace: true })
  }

  const handleRevoke = () => {
    // Thu hồi quyền = backend gọi Google bỏ quyền Gmail + xoá phiên (khác hẳn logout).
    setOpen(false)
    revokeAccess()
    navigate('/', { replace: true })
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o)
        if (!o) setStep('menu')
        if (o && apiBaseUrlDaCauHinh) {
          fetch(duongDanApi('/auth/accounts'), { credentials: 'include' })
            .then((r) => r.json())
            .then((d) => setDsTaiKhoan(d.ket_qua ?? []))
            .catch(() => setDsTaiKhoan([]))
        }
      }}
    >
      <DialogTrigger asChild>
        <button
          title={user.name}
          className="flex size-10 items-center justify-center rounded-full bg-elevated font-serif text-sm font-semibold text-active shadow-subtle ring-1 ring-accent/50 transition-all hover:-translate-y-0.5 hover:shadow-soft"
        >
          {user.initial}
        </button>
      </DialogTrigger>

      <DialogContent className="max-w-sm">
        {step === 'menu' ? (
          <>
            <DialogHeader>
              <DialogTitle>Tài khoản</DialogTitle>
              <DialogDescription>Phiên đăng nhập Google hiện tại của bạn.</DialogDescription>
            </DialogHeader>

            {/* Thẻ tài khoản */}
            <div className="flex items-center gap-3 rounded-2xl bg-popover-foreground/5 p-3">
              <div className="flex size-11 items-center justify-center rounded-full bg-active font-serif text-base font-semibold text-active-foreground">
                {user.initial}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-popover-foreground">{user.name}</p>
                <p className="truncate text-xs text-popover-foreground/70">{user.email}</p>
              </div>
            </div>

            {/* ĐỔI TÀI KHOẢN KHÔNG CẦN ĐĂNG XUẤT — đúng cách Google làm.
                Chỉ hiện khi CÓ tài khoản khác; một danh sách một dòng thì chỉ tổ
                chiếm chỗ và làm người dùng tưởng mình bỏ sót thao tác gì đó. */}
            {dsTaiKhoan.filter((t) => !t.dang_dung).length > 0 && (
              <div className="flex flex-col gap-1">
                <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-popover-foreground/50">
                  Chuyển sang
                </p>
                {dsTaiKhoan.filter((t) => !t.dang_dung).map((t) => (
                  <button
                    key={t.user_id}
                    onClick={() => {
                      // Đổi xong TẢI LẠI trang: cookie phiên đã khác, mà mọi dữ liệu
                      // đang giữ trong bộ nhớ (thư, hội thoại, cam kết) là của tài
                      // khoản cũ. Trộn hai hộp thư trên cùng một màn hình còn tệ hơn
                      // hẳn một nhịp chờ.
                      fetch(duongDanApi(`/auth/switch/${t.user_id}`),
                            { method: 'POST', credentials: 'include' })
                        .then((r) => { if (r.ok) window.location.reload() })
                        .catch(() => {})
                    }}
                    className="flex items-center gap-3 rounded-xl p-2 text-left transition-colors hover:bg-popover-foreground/8"
                  >
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-popover-foreground/10 font-serif text-xs font-semibold">
                      {(t.name || t.email).slice(0, 1).toUpperCase()}
                    </span>
                    <span className="min-w-0">
                      <span className="block truncate text-[13px] font-medium text-popover-foreground">{t.name}</span>
                      <span className="block truncate text-[11px] text-popover-foreground/60">{t.email}</span>
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Gói dịch vụ + mức tiêu thụ token */}
            <UsageSummary
              status={sub}
              onOpenPlans={() => {
                setOpen(false)
                setPlansOpen(true)
              }}
            />

            <div className="flex flex-col gap-2">
              {/* THÊM tài khoản, không thay thế: đăng nhập lần nữa sẽ NỐI vào danh
                  sách, nên tài khoản đang mở vẫn còn nguyên khi quay lại. */}
              <Button variant="outline" onClick={() => { window.location.href = duongDanApi('/auth/google/start') }}>
                <UserPlus className="size-4" />
                Thêm tài khoản khác
              </Button>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="size-4" />
                Đăng xuất tài khoản này
              </Button>
              <Button variant="ghost" onClick={() => setStep('revoke')}>
                <ShieldOff className="size-4" />
                Thu hồi quyền Gmail
              </Button>
            </div>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="size-5 text-destructive" />
                Thu hồi quyền Gmail?
              </DialogTitle>
              <DialogDescription>
                MeoArc sẽ mất toàn bộ quyền đọc &amp; quản lý thư trên Gmail của bạn và bạn sẽ bị
                đăng xuất. Lần sau muốn dùng lại phải cấp quyền từ đầu.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('menu')}>
                Huỷ
              </Button>
              <Button variant="destructive" onClick={handleRevoke}>
                <ShieldOff className="size-4" />
                Thu hồi &amp; đăng xuất
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>

      <PricingScreen
        open={plansOpen}
        onClose={() => setPlansOpen(false)}
        status={sub}
        onChanged={setSub}
      />
    </Dialog>
  )
}
