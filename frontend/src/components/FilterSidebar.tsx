import { useState } from 'react'
import { RotateCcw } from 'lucide-react'
import type { City } from '@/api/types'
import type { Filters } from '@/lib/searchParams'
import { hasActiveFilters } from '@/lib/searchParams'
import { formatSiteName } from '@/lib/format'
import { Chip, SegmentedControl, FilterSection } from './primitives'

interface FilterSidebarProps {
  city: City | undefined
  filters: Filters
  onChange: (patch: Partial<Filters>) => void
  onReset: () => void
}

const ROOM_OPTIONS = [
  { value: 1, label: '1' },
  { value: 2, label: '2' },
  { value: 3, label: '3' },
  { value: 4, label: '4+' },
]

const HEATING_OPTIONS = [
  { value: '' as const, label: 'Toate' },
  { value: 'centrala_proprie' as const, label: 'Centrală proprie' },
  { value: 'termoficare' as const, label: 'Termoficare' },
]

const PARKING_OPTIONS = [
  { value: 'included' as const, label: 'Parcare inclusă' },
  { value: 'likely_included' as const, label: 'Probabil inclusă' },
  { value: 'area_possible' as const, label: 'Posibilitate de parcare în zonă' },
  { value: 'rentable_nearby' as const, label: 'Pot închiria un loc de parcare în apropiere' },
]

const SORT_OPTIONS = [
  { value: 'newest' as const, label: 'Cele mai noi' },
  { value: 'price_asc' as const, label: 'Preț crescător' },
  { value: 'price_desc' as const, label: 'Preț descrescător' },
  { value: 'parking' as const, label: 'Șanse parcare' },
]

const ZONE_SEARCH_THRESHOLD = 10

export function FilterSidebar({ city, filters, onChange, onReset }: FilterSidebarProps) {
  const [priceMinInput, setPriceMinInput] = useState(filters.priceMin?.toString() ?? '')
  const [priceMaxInput, setPriceMaxInput] = useState(filters.priceMax?.toString() ?? '')
  const [zoneFilter, setZoneFilter] = useState('')

  // Re-sync local price inputs when the URL-driven filters change externally
  // (e.g. "Resetează filtrele" or browser back/forward). Adjusting state
  // during render (rather than in an effect) avoids an extra render pass.
  const [prevPriceMin, setPrevPriceMin] = useState(filters.priceMin)
  if (filters.priceMin !== prevPriceMin) {
    setPrevPriceMin(filters.priceMin)
    setPriceMinInput(filters.priceMin?.toString() ?? '')
  }

  const [prevPriceMax, setPrevPriceMax] = useState(filters.priceMax)
  if (filters.priceMax !== prevPriceMax) {
    setPrevPriceMax(filters.priceMax)
    setPriceMaxInput(filters.priceMax?.toString() ?? '')
  }

  const commitPriceMin = () => {
    const n = priceMinInput.trim() === '' ? null : Number.parseInt(priceMinInput, 10)
    onChange({ priceMin: n !== null && Number.isFinite(n) && n >= 0 ? n : null, page: 1 })
  }

  const commitPriceMax = () => {
    const n = priceMaxInput.trim() === '' ? null : Number.parseInt(priceMaxInput, 10)
    onChange({ priceMax: n !== null && Number.isFinite(n) && n >= 0 ? n : null, page: 1 })
  }

  const toggleRoom = (room: number) => {
    const rooms = filters.rooms.includes(room)
      ? filters.rooms.filter((r) => r !== room)
      : [...filters.rooms, room]
    onChange({ rooms, page: 1 })
  }

  const toggleZone = (slug: string) => {
    const zones = filters.zones.includes(slug)
      ? filters.zones.filter((z) => z !== slug)
      : [...filters.zones, slug]
    onChange({ zones, page: 1 })
  }

  const toggleParking = (value: Filters['parking'][number]) => {
    const parking = filters.parking.includes(value)
      ? filters.parking.filter((p) => p !== value)
      : [...filters.parking, value]
    onChange({ parking, page: 1 })
  }

  const toggleSite = (site: string) => {
    const sites = filters.sites.includes(site)
      ? filters.sites.filter((s) => s !== site)
      : [...filters.sites, site]
    onChange({ sites, page: 1 })
  }

  const zones = city?.zones ?? []
  const visibleZones =
    zones.length > ZONE_SEARCH_THRESHOLD && zoneFilter.trim()
      ? zones.filter((z) => z.name.toLowerCase().includes(zoneFilter.trim().toLowerCase()))
      : zones

  const nearbyTownNames = (city?.nearby_towns ?? []).map((t) => t.name).join(', ')

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between pb-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-neutral-400">
          Filtre
        </h2>
        {hasActiveFilters(filters) && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-300"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Resetează filtrele
          </button>
        )}
      </div>

      <FilterSection title="Preț (€)">
        <div className="flex items-center gap-2">
          <input
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="Min"
            aria-label="Preț minim"
            value={priceMinInput}
            onChange={(e) => setPriceMinInput(e.target.value)}
            onBlur={commitPriceMin}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitPriceMin()
            }}
            className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
          />
          <span className="text-slate-400 dark:text-neutral-500">–</span>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="Max"
            aria-label="Preț maxim"
            value={priceMaxInput}
            onChange={(e) => setPriceMaxInput(e.target.value)}
            onBlur={commitPriceMax}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitPriceMax()
            }}
            className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
          />
        </div>
      </FilterSection>

      <FilterSection title="Camere">
        <div className="flex flex-wrap gap-2">
          {ROOM_OPTIONS.map((opt) => (
            <Chip key={opt.value} active={filters.rooms.includes(opt.value)} onClick={() => toggleRoom(opt.value)}>
              {opt.label}
            </Chip>
          ))}
        </div>
      </FilterSection>

      {zones.length > 0 && (
        <FilterSection title="Zone">
          {zones.length > ZONE_SEARCH_THRESHOLD && (
            <input
              type="text"
              placeholder="Caută zonă..."
              aria-label="Caută zonă"
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="mb-3 h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
            />
          )}
          <div className="flex max-h-56 flex-wrap gap-2 overflow-y-auto pr-1">
            {visibleZones.map((zone) => (
              <Chip key={zone.slug} active={filters.zones.includes(zone.slug)} onClick={() => toggleZone(zone.slug)}>
                {zone.name}
              </Chip>
            ))}
            {visibleZones.length === 0 && (
              <p className="text-sm text-slate-400 dark:text-neutral-500">Nicio zonă găsită.</p>
            )}
          </div>
        </FilterSection>
      )}

      <FilterSection title="Încălzire">
        <SegmentedControl
          name="Încălzire"
          value={filters.heating ?? ''}
          onChange={(value) => onChange({ heating: value === '' ? null : value, page: 1 })}
          options={HEATING_OPTIONS}
        />
      </FilterSection>

      <FilterSection title="Parcare">
        <p className="mb-2 text-xs text-slate-400 dark:text-neutral-500">bifezi ce accepți</p>
        <div className="flex flex-col gap-2">
          {PARKING_OPTIONS.map((opt) => (
            <label key={opt.value} className="flex items-start gap-2 text-sm text-slate-700 dark:text-neutral-300">
              <input
                type="checkbox"
                checked={filters.parking.includes(opt.value)}
                onChange={() => toggleParking(opt.value)}
                className="mt-0.5 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/30 dark:border-neutral-600 dark:bg-neutral-800"
              />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </FilterSection>

      {(city?.nearby_towns?.length ?? 0) > 0 && (
        <FilterSection title="Localități">
          <label className="flex items-start gap-2 text-sm text-slate-700 dark:text-neutral-300">
            <input
              type="checkbox"
              checked={filters.includeNearby}
              onChange={(e) => onChange({ includeNearby: e.target.checked, page: 1 })}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/30 dark:border-neutral-600 dark:bg-neutral-800"
            />
            <span>
              Include localități învecinate
              {nearbyTownNames && (
                <span className="mt-0.5 block text-xs text-slate-400 dark:text-neutral-500">{nearbyTownNames}</span>
              )}
            </span>
          </label>
        </FilterSection>
      )}

      {(city?.sites?.length ?? 0) > 0 && (
        <FilterSection title="Surse">
          <div className="flex flex-col gap-2">
            {city?.sites.map((site) => (
              <label key={site} className="flex items-center gap-2 text-sm text-slate-700 dark:text-neutral-300">
                <input
                  type="checkbox"
                  checked={filters.sites.includes(site)}
                  onChange={() => toggleSite(site)}
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/30 dark:border-neutral-600 dark:bg-neutral-800"
                />
                <span>{formatSiteName(site)}</span>
              </label>
            ))}
          </div>
        </FilterSection>
      )}

      <FilterSection title="Sortare">
        <select
          value={filters.sort}
          onChange={(e) => onChange({ sort: e.target.value as Filters['sort'], page: 1 })}
          aria-label="Sortare"
          className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </FilterSection>
    </div>
  )
}
