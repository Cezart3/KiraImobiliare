import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Home, Search } from 'lucide-react'
import type { City } from '@/api/types'
import { SITE_NAME } from '@/lib/site'
import { CitySelect } from './CitySelect'
import { ThemeToggle } from './ThemeToggle'

interface HeaderProps {
  cities: City[]
  citiesLoading: boolean
  city: string
  onCityChange: (citySlug: string) => void
  q: string
  onQChange: (q: string) => void
  total: number | undefined
  isLoading: boolean
}

const DEBOUNCE_MS = 400

export function Header({
  cities,
  citiesLoading,
  city,
  onCityChange,
  q,
  onQChange,
  total,
  isLoading,
}: HeaderProps) {
  const [localQ, setLocalQ] = useState(q)

  // Keep local input in sync if the URL-driven value changes externally
  // (e.g. browser back/forward or "Resetează filtrele"). Adjusting state
  // during render (rather than in an effect) avoids an extra render pass.
  const [prevQ, setPrevQ] = useState(q)
  if (q !== prevQ) {
    setPrevQ(q)
    setLocalQ(q)
  }

  useEffect(() => {
    if (localQ === q) return
    const timeout = setTimeout(() => {
      onQChange(localQ)
    }, DEBOUNCE_MS)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localQ])

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur-sm dark:border-neutral-800 dark:bg-neutral-950/95">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:px-6 lg:px-8">
        {/* Row 1 (mobile): brand on the left, theme + account on the right.
            On sm+ this row becomes part of the single flex row below. */}
        <div className="flex items-center justify-between gap-3 sm:contents">
          <Link to="/" className="flex items-center gap-2" aria-label={`${SITE_NAME} — acasă`}>
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
              <Home className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-neutral-50">
              {SITE_NAME}
            </span>
          </Link>

          <div className="flex items-center gap-3 sm:order-last">
            <ThemeToggle />
          </div>
        </div>

        {/* Row 2 (mobile): city selector + search, search takes remaining width.
            On sm+ this becomes the flex-1 segment between the brand and the
            count/theme/account, with the search input filling its remainder. */}
        <div className="flex items-center gap-3 sm:flex-1">
          <CitySelect
            cities={cities}
            value={city}
            onChange={onCityChange}
            isLoading={citiesLoading}
          />

          <div className="relative min-w-[180px] flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 dark:text-neutral-500"
              aria-hidden="true"
            />
            <input
              type="search"
              value={localQ}
              onChange={(e) => setLocalQ(e.target.value)}
              placeholder="Caută în titlu sau descriere..."
              aria-label="Căutare text liber"
              className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 hover:border-slate-300 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:placeholder:text-neutral-500 dark:hover:border-neutral-600"
            />
          </div>
        </div>

        <div className="whitespace-nowrap text-sm text-slate-500 sm:ml-auto dark:text-neutral-400">
          {isLoading ? (
            <span className="inline-block h-4 w-24 animate-pulse rounded bg-slate-200 dark:bg-neutral-800" />
          ) : total !== undefined ? (
            <span>
              <span className="font-semibold text-slate-900 dark:text-neutral-100">
                {new Intl.NumberFormat('ro-RO').format(total)}
              </span>{' '}
              anunțuri
            </span>
          ) : null}
        </div>
      </div>
    </header>
  )
}
