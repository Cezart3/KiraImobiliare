import { useMemo } from 'react'
import { Sparkles } from 'lucide-react'
import type { Listing } from '@/api/types'
import { scoreFavorites } from '@/lib/recommendation'
import { formatPriceMonthly, formatWalkDistance } from '@/lib/format'

interface BestFavoriteProps {
  listings: Listing[]
  persons: number
  hasAddress: boolean
}

/**
 * "Cea mai bună din favorite": ranks the saved listings against each other
 * (price, distance to the user's address, parking, heating/size fit) and
 * highlights the winner so the user doesn't have to eyeball each card.
 */
export function BestFavorite({ listings, persons, hasAddress }: BestFavoriteProps) {
  const top = useMemo(() => {
    const ranked = scoreFavorites(listings, persons)
    return ranked[0] ?? null
  }, [listings, persons])

  if (!top || listings.length < 2) return null

  const { listing, reasons } = top
  const walk = formatWalkDistance(
    listing.distance_to_origin_m,
    listing.distance_to_origin_walk_min,
  )

  return (
    <div className="mb-4 rounded-xl border border-emerald-300 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm dark:border-emerald-800/60 dark:from-emerald-950/40 dark:to-neutral-900">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white">
          <Sparkles className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="flex-1">
          <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Cea mai bună alegere din favoritele tale
          </p>
          <a
            href={listing.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 block text-base font-bold text-slate-900 hover:underline dark:text-neutral-50"
          >
            {listing.title}
          </a>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600 dark:text-neutral-300">
            <span className="font-semibold text-slate-900 dark:text-neutral-100">
              {formatPriceMonthly(listing.price_eur)}
            </span>
            {walk && <span>{walk}</span>}
          </div>
          {reasons.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {reasons.map((r) => (
                <span
                  key={r}
                  className="inline-flex items-center rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300"
                >
                  {r}
                </span>
              ))}
            </div>
          )}
          {!hasAddress && (
            <p className="mt-2 text-xs text-slate-500 dark:text-neutral-400">
              Adaugă adresa ta la „Distanța față de tine” ca să includem și cât de
              aproape e fiecare anunț în recomandare.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
