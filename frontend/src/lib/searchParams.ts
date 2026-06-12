// Helpers for reading/writing the search page's filter state to/from URL
// search params. All filter state lives in the URL so it's shareable and
// back/forward navigation works.

import type { Heating, ParkingFilter, SortOption } from '@/api/types'

export const DEFAULT_CITY = 'cluj-napoca'
export const DEFAULT_SORT: SortOption = 'newest'
export const DEFAULT_PAGE_SIZE = 24

export interface Filters {
  city: string
  q: string
  priceMin: number | null
  priceMax: number | null
  rooms: number[]
  zones: string[]
  heating: Heating | null
  parking: ParkingFilter[]
  includeNearby: boolean
  sites: string[]
  sort: SortOption
  page: number
}

const PARKING_VALUES: ParkingFilter[] = [
  'included',
  'likely_included',
  'area_possible',
  'rentable_nearby',
]

const SORT_VALUES: SortOption[] = ['newest', 'price_asc', 'price_desc', 'parking']

const HEATING_VALUES: Heating[] = ['centrala_proprie', 'termoficare']

function parseIntOrNull(value: string | null): number | null {
  if (value === null || value === '') return null
  const n = Number.parseInt(value, 10)
  return Number.isFinite(n) ? n : null
}

function parseIntList(values: string[]): number[] {
  const out: number[] = []
  for (const v of values) {
    const n = Number.parseInt(v, 10)
    if (Number.isFinite(n) && !out.includes(n)) out.push(n)
  }
  return out
}

function dedupe(values: string[]): string[] {
  return Array.from(new Set(values.filter((v) => v.length > 0)))
}

/** Reads the full filter state from URLSearchParams, applying defaults. */
export function filtersFromSearchParams(params: URLSearchParams): Filters {
  const heatingRaw = params.get('heating')
  const heating = HEATING_VALUES.includes(heatingRaw as Heating)
    ? (heatingRaw as Heating)
    : null

  const sortRaw = params.get('sort')
  const sort = SORT_VALUES.includes(sortRaw as SortOption)
    ? (sortRaw as SortOption)
    : DEFAULT_SORT

  const parking = dedupe(params.getAll('parking')).filter((v): v is ParkingFilter =>
    PARKING_VALUES.includes(v as ParkingFilter),
  )

  const page = parseIntOrNull(params.get('page'))

  return {
    city: params.get('city') || DEFAULT_CITY,
    q: params.get('q') ?? '',
    priceMin: parseIntOrNull(params.get('price_min')),
    priceMax: parseIntOrNull(params.get('price_max')),
    rooms: parseIntList(params.getAll('rooms')),
    zones: dedupe(params.getAll('zones')),
    heating,
    parking,
    includeNearby: params.get('include_nearby') === 'true',
    sites: dedupe(params.getAll('sites')),
    sort,
    page: page && page > 0 ? page : 1,
  }
}

/**
 * Serializes filter state back into URLSearchParams, omitting params that
 * are at their default value so the URL stays clean.
 */
export function filtersToSearchParams(filters: Filters): URLSearchParams {
  const params = new URLSearchParams()

  params.set('city', filters.city)

  if (filters.q.trim()) params.set('q', filters.q)
  if (filters.priceMin !== null) params.set('price_min', String(filters.priceMin))
  if (filters.priceMax !== null) params.set('price_max', String(filters.priceMax))
  for (const r of filters.rooms) params.append('rooms', String(r))
  for (const z of filters.zones) params.append('zones', z)
  if (filters.heating) params.set('heating', filters.heating)
  for (const p of filters.parking) params.append('parking', p)
  if (filters.includeNearby) params.set('include_nearby', 'true')
  for (const s of filters.sites) params.append('sites', s)
  if (filters.sort !== DEFAULT_SORT) params.set('sort', filters.sort)
  if (filters.page > 1) params.set('page', String(filters.page))

  return params
}

/** Builds the URLSearchParams to send to GET /api/listings. */
export function filtersToApiParams(filters: Filters, pageSize = DEFAULT_PAGE_SIZE): URLSearchParams {
  const params = new URLSearchParams()

  params.set('city', filters.city)
  if (filters.q.trim()) params.set('q', filters.q.trim())
  if (filters.priceMin !== null) params.set('price_min', String(filters.priceMin))
  if (filters.priceMax !== null) params.set('price_max', String(filters.priceMax))
  for (const r of filters.rooms) params.append('rooms', String(r))
  for (const z of filters.zones) params.append('zones', z)
  if (filters.heating) params.set('heating', filters.heating)
  for (const p of filters.parking) params.append('parking', p)
  if (filters.includeNearby) params.set('include_nearby', 'true')
  for (const s of filters.sites) params.append('sites', s)
  params.set('sort', filters.sort)
  params.set('page', String(filters.page))
  params.set('page_size', String(pageSize))

  return params
}

/** Counts how many filters (besides city/q/sort/page) are currently active. */
export function countActiveFilters(filters: Filters): number {
  let count = 0
  if (filters.priceMin !== null) count++
  if (filters.priceMax !== null) count++
  if (filters.rooms.length > 0) count++
  if (filters.zones.length > 0) count++
  if (filters.heating) count++
  if (filters.parking.length > 0) count++
  if (filters.includeNearby) count++
  if (filters.sites.length > 0) count++
  return count
}

/** True if any filter other than city/sort/page/q is active. */
export function hasActiveFilters(filters: Filters): boolean {
  return countActiveFilters(filters) > 0 || filters.q.trim().length > 0
}

/** Returns filters reset to defaults but keeping the current city. */
export function clearedFilters(filters: Filters): Filters {
  return {
    city: filters.city,
    q: '',
    priceMin: null,
    priceMax: null,
    rooms: [],
    zones: [],
    heating: null,
    parking: [],
    includeNearby: false,
    sites: [],
    sort: DEFAULT_SORT,
    page: 1,
  }
}
