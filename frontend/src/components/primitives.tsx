import type { ReactNode } from 'react'

interface ChipProps {
  active: boolean
  onClick: () => void
  children: ReactNode
  className?: string
}

/** A pill-shaped toggle button used for room counts, zones, etc. */
export function Chip({ active, onClick, children, className = '' }: ChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? 'border-emerald-600 bg-emerald-600 text-white'
          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:border-neutral-600 dark:hover:bg-neutral-800'
      } ${className}`}
    >
      {children}
    </button>
  )
}

interface SegmentedOption<T extends string> {
  value: T
  label: string
}

interface SegmentedControlProps<T extends string> {
  value: T
  options: SegmentedOption<T>[]
  onChange: (value: T) => void
  name: string
}

/** A segmented (single-choice) control, e.g. for the heating filter. */
export function SegmentedControl<T extends string>({
  value,
  options,
  onChange,
  name,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={name}
      className="inline-flex w-full rounded-lg border border-slate-200 bg-slate-100 p-1 dark:border-neutral-700 dark:bg-neutral-800"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          onClick={() => onChange(option.value)}
          className={`flex-1 rounded-md px-2 py-1.5 text-sm font-medium transition-colors ${
            value === option.value
              ? 'bg-white text-slate-900 shadow-sm dark:bg-neutral-900 dark:text-neutral-100'
              : 'text-slate-500 hover:text-slate-700 dark:text-neutral-400 dark:hover:text-neutral-200'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

interface BadgeProps {
  children: ReactNode
  className?: string
}

/** A small rounded label, used for image-count, source name, etc. */
export function Badge({ children, className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {children}
    </span>
  )
}

interface FilterSectionProps {
  title: string
  children: ReactNode
}

/** A labeled group within the filter sidebar/drawer. */
export function FilterSection({ title, children }: FilterSectionProps) {
  return (
    <div className="border-b border-slate-100 py-4 first:pt-0 last:border-b-0 last:pb-0 dark:border-neutral-800">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-neutral-100">{title}</h3>
      {children}
    </div>
  )
}
