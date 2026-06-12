import type { City } from '@/api/types'

interface CitySelectProps {
  cities: City[]
  value: string
  onChange: (citySlug: string) => void
  isLoading?: boolean
}

export function CitySelect({ cities, value, onChange, isLoading }: CitySelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={isLoading}
      aria-label="Oraș"
      className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-slate-300 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-60 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-neutral-600"
    >
      {isLoading && <option>Se încarcă...</option>}
      {cities.map((city) => (
        <option key={city.slug} value={city.slug}>
          {city.name}
        </option>
      ))}
    </select>
  )
}
