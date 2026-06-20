import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { CATEGORY, CATEGORY_OPTIONS } from '@/data/categories'
import type { Category } from '@/data/emails'

/** Dialog chọn nhãn để gán cho email (UC006). Controlled. */
export function LabelDialog({
  open,
  onOpenChange,
  count,
  onPick,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  count: number
  onPick: (category: Category, label: string) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Gắn nhãn</DialogTitle>
          <DialogDescription>
            Chọn nhãn áp dụng cho {count} thư đã chọn.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-2">
          {CATEGORY_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => {
                onPick(opt.key, opt.label)
                onOpenChange(false)
              }}
              className="flex items-center gap-2 rounded-xl bg-popover-foreground/5 px-3 py-2 text-sm text-popover-foreground transition-colors hover:bg-popover-foreground/10"
            >
              <span
                className="size-3 shrink-0 rounded-full"
                style={{ backgroundColor: CATEGORY[opt.key].bar }}
              />
              {opt.label}
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
