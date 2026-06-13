import { useEffect, type ReactNode } from 'react'
import { ExternalLink, Home, X } from 'lucide-react'
import type { Listing } from '@/api/types'
import { imageProxyUrl } from '@/api/client'
import {
  formatFloor,
  formatPrice,
  formatPriceMonthly,
  formatRooms,
  formatSurface,
  formatWalkDistance,
  HEATING_LABELS,
  PARKING_STATUS_LABELS,
} from '@/lib/format'
import { pricePerPerson } from '@/lib/recommendation'

interface CompareDrawerProps {
  listings: Listing[]
  persons: number
  onClose: () => void
}

/** Highlight style applied to the "best" cell in a row, e.g. lowest price. */
const BEST_CELL = 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300'

export function CompareDrawer({ listings, persons, onClose }: CompareDrawerProps) {
  const open = listings.length >= 2

  useEffect(() => {
    if (!open) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  // Indices of the listing(s) with the lowest price / own-boiler heating —
  // used to apply a subtle "best value" highlight.
  const prices = listings.map((l) => l.price_eur)
  const minPrice = prices.some((p) => p !== null) ? Math.min(...prices.filter((p): p is number => p !== null)) : null
  const bestPriceIdx = new Set(listings.map((l, i) => (l.price_eur !== null && l.price_eur === minPrice ? i : -1)).filter((i) => i >= 0))

  const surfaces = listings.map((l) => l.surface_m2)
  const maxSurface = surfaces.some((s) => s !== null) ? Math.max(...surfaces.filter((s): s is number => s !== null)) : null
  const bestSurfaceIdx = new Set(listings.map((l, i) => (l.surface_m2 !== null && l.surface_m2 === maxSurface ? i : -1)).filter((i) => i >= 0))

  const distances = listings.map((l) => l.distance_to_origin_m)
  const minDistance = distances.some((d) => d !== null) ? Math.min(...distances.filter((d): d is number => d !== null)) : null
  const bestDistanceIdx = new Set(listings.map((l, i) => (l.distance_to_origin_m !== null && l.distance_to_origin_m === minDistance ? i : -1)).filter((i) => i >= 0))

  const hasDistances = listings.some((l) => l.distance_to_origin_m !== null)
  const hasPricePerPerson = persons > 1 && listings.some((l) => l.price_eur !== null)

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        type="button"
        aria-label="Închide"
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Compară anunțuri"
        className="relative flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-2xl bg-white shadow-xl sm:rounded-2xl dark:bg-neutral-900"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-neutral-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-neutral-50">
            Compară anunțuri ({listings.length})
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Închide"
            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:text-neutral-500 dark:hover:bg-neutral-800 dark:hover:text-neutral-300"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4">
          <table className="w-full min-w-[480px] border-collapse text-sm">
            <tbody>
              <tr>
                <RowLabel>Foto</RowLabel>
                {listings.map((listing) => (
                  <td key={listing.id} className="border-t border-slate-100 p-2 align-top dark:border-neutral-800">
                    <div className="aspect-[4/3] w-28 overflow-hidden rounded-lg bg-slate-100 dark:bg-neutral-800">
                      {listing.images.length > 0 ? (
                        <img
                          src={imageProxyUrl(listing.images[0])}
                          alt={listing.title}
                          loading="lazy"
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center">
                          <Home className="h-6 w-6 text-slate-300 dark:text-neutral-600" aria-hidden="true" />
                        </div>
                      )}
                    </div>
                    <p className="mt-1.5 line-clamp-2 w-28 text-xs font-medium leading-snug text-slate-700 dark:text-neutral-300">
                      {listing.title}
                    </p>
                  </td>
                ))}
              </tr>

              <tr>
                <RowLabel>Preț</RowLabel>
                {listings.map((listing, i) => (
                  <Cell key={listing.id} highlight={bestPriceIdx.has(i)}>
                    {formatPriceMonthly(listing.price_eur)}
                  </Cell>
                ))}
              </tr>

              {hasPricePerPerson && (
                <tr>
                  <RowLabel>Preț / persoană</RowLabel>
                  {listings.map((listing) => {
                    const pp = pricePerPerson(listing.price_eur, persons)
                    return <Cell key={listing.id}>{pp !== null ? `${formatPrice(pp)} €` : '—'}</Cell>
                  })}
                </tr>
              )}

              <tr>
                <RowLabel>Camere</RowLabel>
                {listings.map((listing) => (
                  <Cell key={listing.id}>{formatRooms(listing.rooms) ?? '—'}</Cell>
                ))}
              </tr>

              <tr>
                <RowLabel>Suprafață</RowLabel>
                {listings.map((listing, i) => (
                  <Cell key={listing.id} highlight={bestSurfaceIdx.has(i)}>
                    {formatSurface(listing.surface_m2) ?? '—'}
                  </Cell>
                ))}
              </tr>

              <tr>
                <RowLabel>Etaj</RowLabel>
                {listings.map((listing) => (
                  <Cell key={listing.id}>{formatFloor(listing.floor) ?? '—'}</Cell>
                ))}
              </tr>

              <tr>
                <RowLabel>Zonă</RowLabel>
                {listings.map((listing) => (
                  <Cell key={listing.id}>{listing.zone_slug ?? '—'}</Cell>
                ))}
              </tr>

              <tr>
                <RowLabel>Încălzire</RowLabel>
                {listings.map((listing) => (
                  <Cell key={listing.id} highlight={listing.heating === 'centrala_proprie'}>
                    {HEATING_LABELS[listing.heating] ?? '—'}
                  </Cell>
                ))}
              </tr>

              <tr>
                <RowLabel>Parcare</RowLabel>
                {listings.map((listing) => (
                  <Cell key={listing.id}>{PARKING_STATUS_LABELS[listing.parking_status] ?? '—'}</Cell>
                ))}
              </tr>

              {hasDistances && (
                <tr>
                  <RowLabel>Distanță</RowLabel>
                  {listings.map((listing, i) => {
                    const walk = formatWalkDistance(listing.distance_to_origin_m, listing.distance_to_origin_walk_min)
                    return (
                      <Cell key={listing.id} highlight={bestDistanceIdx.has(i)}>
                        {walk ?? '—'}
                      </Cell>
                    )
                  })}
                </tr>
              )}

              <tr>
                <RowLabel>Link</RowLabel>
                {listings.map((listing) => (
                  <td key={listing.id} className="border-t border-slate-100 p-2 align-top dark:border-neutral-800">
                    <a
                      href={listing.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    >
                      <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                      Vezi anunțul
                    </a>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function RowLabel({ children }: { children: ReactNode }) {
  return (
    <th className="sticky left-0 z-10 border-t border-slate-100 bg-white p-2 text-left text-xs font-semibold text-slate-500 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400">
      {children}
    </th>
  )
}

interface CellProps {
  children: ReactNode
  highlight?: boolean
}

function Cell({ children, highlight }: CellProps) {
  return (
    <td
      className={`border-t border-slate-100 p-2 align-top text-slate-700 dark:border-neutral-800 dark:text-neutral-300 ${
        highlight ? BEST_CELL : ''
      }`}
    >
      {children}
    </td>
  )
}
