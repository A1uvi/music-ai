import { HTMLAttributes } from 'react'
import clsx from 'clsx'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined'
}

export function Card({ children, variant = 'default', className, ...props }: CardProps) {
  const baseStyles = 'rounded p-4 bg-bg'

  const variantStyles = {
    default: 'shadow-md',
    outlined: 'border border-border',
  }

  return (
    <div
      className={clsx(baseStyles, variantStyles[variant], className)}
      {...props}
    >
      {children}
    </div>
  )
}
