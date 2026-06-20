import * as React from 'react'
import { cn } from '@/lib/utils'

/** Textarea chuẩn shadcn — token-driven. Mặc định có nền/bóng riêng,
 *  nhưng cho phép override qua className (vd nhúng trong thanh chat). */
function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'flex min-h-16 w-full rounded-xl bg-elevated/70 px-3 py-2 text-sm text-foreground shadow-subtle',
        'outline-none transition-[box-shadow] placeholder:text-muted-foreground',
        'focus-visible:ring-2 focus-visible:ring-ring/40',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}

export { Textarea }
