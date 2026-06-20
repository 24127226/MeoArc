import { cn } from '@/lib/utils'

/** AI Orb — avatar trợ lý gradient chuyển động nhẹ. `thinking` làm nó sống động hơn. */
export function AiOrb({
  className,
  thinking = false,
  children,
}: {
  className?: string
  thinking?: boolean
  children?: React.ReactNode
}) {
  return (
    <div
      className={cn('ai-orb flex items-center justify-center', thinking && 'is-thinking', className)}
      aria-hidden="true"
    >
      {children}
    </div>
  )
}
