import { HTMLAttributes } from 'react'
import clsx from 'clsx'

interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
}

export function Container({ children, size = 'lg', className, ...props }: ContainerProps) {
  const sizeClasses = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
  }

  return (
    <div
      className={clsx('mx-auto px-4 py-8', sizeClasses[size], className)}
      {...props}
    >
      {children}
    </div>
  )
}
