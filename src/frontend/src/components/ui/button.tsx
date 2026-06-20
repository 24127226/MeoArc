import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-2xl text-sm font-medium transition-all duration-200 ease-spring outline-none focus-visible:ring-2 focus-visible:ring-ring/55 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 cursor-pointer select-none active:translate-y-0 active:scale-[0.96]",
  {
    variants: {
      variant: {
        // Nút chính — terracotta đặc, bóng "căng mọng", hover nâng nhẹ + sheen lướt
        primary:
          'gloss gloss-sweep bg-primary text-primary-foreground shadow-soft hover:-translate-y-0.5 hover:shadow-float hover:brightness-[1.05]',
        emphasis:
          'gloss gloss-sweep bg-emphasis text-emphasis-foreground shadow-soft hover:-translate-y-0.5 hover:shadow-float hover:brightness-110',
        accent:
          'gloss gloss-sweep bg-accent text-accent-foreground shadow-soft hover:-translate-y-0.5 hover:shadow-float hover:brightness-[1.04]',
        // Nút phụ — viền mảnh, nền trong suốt
        outline:
          'border border-border/80 bg-transparent text-foreground hover:bg-secondary/50 hover:border-accent/60 hover:-translate-y-0.5',
        ghost: 'text-foreground hover:bg-secondary/70',
        destructive:
          'gloss gloss-sweep bg-destructive text-destructive-foreground shadow-soft hover:-translate-y-0.5 hover:shadow-float hover:brightness-[1.05]',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-9 px-3.5 text-xs rounded-xl',
        default: 'h-10 px-5 py-2',
        lg: 'h-12 px-7 text-base',
        icon: 'size-10 rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    )
  },
)
Button.displayName = 'Button'

// eslint-disable-next-line react-refresh/only-export-components
export { Button, buttonVariants }
