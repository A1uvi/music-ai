interface ProgressBarProps {
  value: number
  max?: number
  label?: string
}

export function ProgressBar({ value, max = 100, label }: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm text-text-secondary">{label}</span>
          <span className="text-sm text-text-secondary">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="w-full h-2 bg-bg-secondary rounded overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300 ease-base"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
