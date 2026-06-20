import * as React from 'react'
import { cn } from '@/lib/utils'

/** Input chuẩn shadcn — đọc màu từ token (foreground/muted-foreground/ring). */
function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'flex h-11 w-full rounded-xl bg-elevated/70 px-3 py-1 text-sm text-foreground shadow-subtle',
        'outline-none transition-[box-shadow] placeholder:text-muted-foreground',
        'focus-visible:ring-2 focus-visible:ring-ring/40',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}

export { Input }
