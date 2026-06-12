import { formatDistanceToNow, format } from 'date-fns'
import { ro } from 'date-fns/locale'
import type { Heating, ParkingKind, ParkingStatus } from '@/api/types'

/** Formats a price in EUR per month, e.g. "450 € / lună". */
export function formatPriceMonthly(price: number | null): string {
  if (price === null) return 'Preț la cerere'
  return `${formatPrice(price)} € / lună`
}

/** Formats a bare price in EUR, e.g. "450 €". */
export function formatPrice(price: number | null): string {
  if (price === null) return '—'
  return new Intl.NumberFormat('ro-RO').format(price)
}

/** Relative time string, e.g. "acum 2 zile". Returns null if no date given. */
export function formatRelativeTime(dateString: string | null): string | null {
  if (!dateString) return null
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return null
  return formatDistanceToNow(date, { addSuffix: true, locale: ro })
}

/** Absolute date/time string for use in a title="" tooltip. */
export function formatAbsoluteTime(dateString: string | null): string | undefined {
  if (!dateString) return undefined
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return undefined
  return format(date, "d MMMM yyyy, HH:mm", { locale: ro })
}

export function formatRooms(rooms: number | null): string | null {
  if (rooms === null) return null
  if (rooms >= 4) return '4+ camere'
  return `${rooms} ${rooms === 1 ? 'cameră' : 'camere'}`
}

export function formatRoomsShort(rooms: number | null): string | null {
  if (rooms === null) return null
  if (rooms >= 4) return '4+ cam'
  return `${rooms} cam`
}

export function formatSurface(surface: number | null): string | null {
  if (surface === null) return null
  return `${surface} mp`
}

export function formatFloor(floor: string | null): string | null {
  if (!floor) return null
  return `et. ${floor}`
}

export const HEATING_LABELS: Record<Heating, string | null> = {
  centrala_proprie: 'Centrală proprie',
  termoficare: 'Termoficare',
  unknown: null,
}

export const PARKING_STATUS_LABELS: Record<ParkingStatus, string | null> = {
  included: 'Parcare inclusă',
  likely_included: 'Probabil parcare',
  area_possible: 'Parcare în zonă',
  none: 'Fără parcare',
  unknown: null,
}

export const PARKING_KIND_LABELS: Record<ParkingKind, string> = {
  subteran: 'Subteran',
  garaj: 'Garaj',
  exterior: 'Exterior',
  unknown: '—',
}

/** Formats a walking distance/time, e.g. "~350 m · ~5 min pe jos". */
export function formatWalkDistance(
  distanceM: number | null,
  walkMin: number | null,
): string | null {
  const parts: string[] = []
  if (distanceM !== null) parts.push(`~${Math.round(distanceM)} m`)
  if (walkMin !== null) parts.push(`~${Math.round(walkMin)} min pe jos`)
  if (parts.length === 0) return null
  return parts.join(' · ')
}

/** Capitalizes the first letter of a site identifier, e.g. "storia" -> "Storia". */
export function formatSiteName(site: string): string {
  if (!site) return site
  return site.charAt(0).toUpperCase() + site.slice(1)
}

/**
 * Formats a count of listings with the Romanian numeral rule: numbers >= 20
 * take "de" before the noun, e.g. "5 anunțuri" vs "20 de anunțuri".
 */
export function formatAnunturiCount(total: number): string {
  const formatted = new Intl.NumberFormat('ro-RO').format(total)
  return total >= 20 ? `${formatted} de anunțuri` : `${formatted} anunțuri`
}
