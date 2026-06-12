import { useEffect } from 'react'
import { X, ParkingCircle, ExternalLink, Navigation } from 'lucide-react'
import { useListingDetail } from '@/api/queries'
import type { ParkingMatch } from '@/api/types'
import {
  formatPrice,
  formatWalkDistance,
  PARKING_KIND_LABELS,
} from '@/lib/format'

interface ParkingDrawerProps {
  listingId: number | null
  onClose: () => void
}

export function ParkingDrawer({ listingId, onClose }: ParkingDrawerProps) {
  const open = listingId !== null
  const { data, isLoading, isError } = useListingDetail(listingId)

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

  const matches = data?.parking_matches ?? []

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Închide"
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Locuri de parcare în apropiere"
        className="relative flex h-full w-full max-w-md flex-col bg-white shadow-xl dark:bg-neutral-900"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-neutral-800">
          <div className="flex items-center gap-2">
            <ParkingCircle className="h-5 w-5 text-violet-600 dark:text-violet-400" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-neutral-50">
              Locuri de parcare în apropiere
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Închide"
            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:text-neutral-500 dark:hover:bg-neutral-800 dark:hover:text-neutral-300"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading && (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-28 animate-pulse rounded-xl bg-slate-100 dark:bg-neutral-800" />
              ))}
            </div>
          )}

          {isError && (
            <p className="text-sm text-red-600 dark:text-red-400">
              Nu am putut încărca locurile de parcare. Încearcă din nou.
            </p>
          )}

          {!isLoading && !isError && matches.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-neutral-400">
              Nu am găsit locuri de parcare asociate acestui anunț.
            </p>
          )}

          <div className="flex flex-col gap-3">
            {matches.map((match) => (
              <ParkingMatchRow key={match.parking.id} match={match} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

interface ParkingMatchRowProps {
  match: ParkingMatch
}

function ParkingMatchRow({ match }: ParkingMatchRowProps) {
  const { parking, distance_m, walk_min, is_approx, maps_url } = match
  const walkDistance = formatWalkDistance(distance_m, walk_min)
  const kindLabel = PARKING_KIND_LABELS[parking.kind]

  return (
    <div className="rounded-xl border border-slate-200 p-4 dark:border-neutral-800">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium leading-snug text-slate-800 dark:text-neutral-200">{parking.title}</h3>
        {parking.price_eur !== null && (
          <span className="whitespace-nowrap text-sm font-bold text-slate-900 dark:text-neutral-50">
            {formatPrice(parking.price_eur)} €/lună
          </span>
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-neutral-800 dark:text-neutral-300">
          {kindLabel}
        </span>
        {parking.is_numbered && (
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400">
            loc numerotat
          </span>
        )}
      </div>

      {walkDistance && <p className="mt-2 text-xs text-slate-500 dark:text-neutral-400">{walkDistance}</p>}

      {is_approx && (
        <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          distanță aproximativă (estimată pe zonă)
        </p>
      )}

      <div className="mt-3 flex gap-2">
        <a
          href={parking.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          Vezi anunțul
        </a>
        {maps_url && (
          <a
            href={maps_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            <Navigation className="h-3.5 w-3.5" aria-hidden="true" />
            Rută pe jos
          </a>
        )}
      </div>
    </div>
  )
}
