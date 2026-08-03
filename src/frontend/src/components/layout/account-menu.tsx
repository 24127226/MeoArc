import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, ShieldOff, AlertTriangle } from 'lucide-react'
import { useAuth } from '@/auth/auth-context'
import { api } from '@/lib/api'
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

export function AccountMenu() {
  const { user, logout, revokeAccess } = useAuth()
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

            {/* Gói dịch vụ + mức tiêu thụ token */}
            <UsageSummary
              status={sub}
              onOpenPlans={() => {
                setOpen(false)
                setPlansOpen(true)
              }}
            />

            <div className="flex flex-col gap-2">
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="size-4" />
                Đăng xuất
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
