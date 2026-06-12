import { useState } from 'react'
import { Home, MapPin, Maximize2, Layers, Images, ParkingCircle } from 'lucide-react'
import type { Listing } from '@/api/types'
import { imageProxyUrl } from '@/api/client'
import {
  formatAbsoluteTime,
  formatFloor,
  formatPriceMonthly,
  formatRelativeTime,
  formatRoomsShort,
  formatSiteName,
  formatSurface,
  HEATING_LABELS,
  PARKING_STATUS_LABELS,
} from '@/lib/format'
import { Badge } from './primitives'

interface ListingCardProps {
  listing: Listing
  onOpenParking: (listingId: number) => void
  /** With the "rentable_nearby" filter active, a card click also opens the
   * nearest rentable parking ad alongside the listing. */
  openBestParking?: boolean
}

const PARKING_STATUS_STYLES: Record<string, string> = {
  included: 'bg-emerald-600 text-white border border-emerald-600',
  likely_included: 'border border-emerald-600 text-emerald-700 bg-white dark:bg-neutral-900 dark:text-emerald-400',
  area_possible: 'border border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900 dark:bg-sky-950/50 dark:text-sky-400',
  none: 'border border-slate-200 bg-slate-50 text-slate-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400',
}

export function ListingCard({ listing, onOpenParking, openBestParking }: ListingCardProps) {
  const [imgError, setImgError] = useState(false)

  const hasImage = listing.images.length > 0 && !imgError
  const relativeTime = formatRelativeTime(listing.posted_at ?? listing.first_seen_at)
  const absoluteTime = formatAbsoluteTime(listing.posted_at ?? listing.first_seen_at)
  const heatingLabel = HEATING_LABELS[listing.heating]
  const parkingLabel = PARKING_STATUS_LABELS[listing.parking_status]
  const roomsLabel = formatRoomsShort(listing.rooms)
  const surfaceLabel = formatSurface(listing.surface_m2)
  const floorLabel = formatFloor(listing.floor)

  const handleOpen = () => {
    window.open(listing.url, '_blank', 'noopener,noreferrer')
    if (openBestParking && listing.best_parking) {
      const w = window.open(listing.best_parking.parking.url, '_blank', 'noopener,noreferrer')
      if (!w) {
        // popup blocked: show the parking matches in the drawer instead
        onOpenParking(listing.id)
      }
    }
  }

  return (
    <article
      onClick={handleOpen}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleOpen()
        }
      }}
      className="group flex cursor-pointer flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-neutral-800 dark:bg-neutral-900"
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-slate-100 dark:bg-neutral-800">
        {hasImage ? (
          <img
            src={imageProxyUrl(listing.images[0])}
            alt={listing.title}
            loading="lazy"
            onError={() => setImgError(true)}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-slate-100 dark:bg-neutral-800">
            <Home className="h-10 w-10 text-slate-300 dark:text-neutral-600" aria-hidden="true" />
          </div>
        )}

        <div className="absolute left-2 top-2">
          <Badge className="bg-white/90 text-slate-700 shadow-sm backdrop-blur-sm dark:bg-neutral-900/90 dark:text-neutral-200">
            {formatSiteName(listing.site)}
          </Badge>
        </div>

        {listing.images.length > 1 && (
          <div className="absolute right-2 top-2">
            <Badge className="bg-black/55 text-white">
              <Images className="mr-1 h-3 w-3" aria-hidden="true" />
              {listing.images.length} foto
            </Badge>
          </div>
        )}

        {listing.in_nearby_town && (
          <div className="absolute bottom-2 left-2">
            <Badge className="bg-amber-500/90 text-white shadow-sm">
              {listing.town_slug
                ? listing.town_slug.charAt(0).toUpperCase() + listing.town_slug.slice(1)
                : 'Localitate vecină'}
            </Badge>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-lg font-bold text-slate-900 dark:text-neutral-50">
            {formatPriceMonthly(listing.price_eur)}
          </span>
          {relativeTime && (
            <span className="whitespace-nowrap text-xs text-slate-400 dark:text-neutral-500" title={absoluteTime}>
              {relativeTime}
            </span>
          )}
        </div>

        <h3 className="line-clamp-2 text-sm font-medium leading-snug text-slate-800 dark:text-neutral-200">
          {listing.title}
        </h3>

        <div className="mt-auto flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-neutral-400">
          {roomsLabel && (
            <span className="inline-flex items-center gap-1">
              <Layers className="h-3.5 w-3.5" aria-hidden="true" />
              {roomsLabel}
            </span>
          )}
          {surfaceLabel && (
            <span className="inline-flex items-center gap-1">
              <Maximize2 className="h-3.5 w-3.5" aria-hidden="true" />
              {surfaceLabel}
            </span>
          )}
          {floorLabel && (
            <span className="inline-flex items-center gap-1">
              <Layers className="h-3.5 w-3.5" aria-hidden="true" />
              {floorLabel}
            </span>
          )}
          {listing.zone_slug && (
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 dark:bg-neutral-800 dark:text-neutral-300">
              <MapPin className="h-3 w-3" aria-hidden="true" />
              {listing.zone_slug}
            </span>
          )}
        </div>

        {(heatingLabel || parkingLabel || listing.parking_match_count > 0) && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            {heatingLabel && (
              <Badge
                className={
                  listing.heating === 'centrala_proprie'
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400'
                    : 'bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-400'
                }
              >
                {heatingLabel}
              </Badge>
            )}

            {parkingLabel && (
              <Badge className={PARKING_STATUS_STYLES[listing.parking_status] ?? ''}>
                {parkingLabel}
              </Badge>
            )}

            {listing.parking_match_count > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onOpenParking(listing.id)
                }}
                className="inline-flex items-center gap-1 rounded-md border border-violet-200 bg-violet-50 px-2 py-0.5 text-xs font-medium text-violet-700 transition-colors hover:bg-violet-100 dark:border-violet-900 dark:bg-violet-950/50 dark:text-violet-400 dark:hover:bg-violet-950"
              >
                <ParkingCircle className="h-3 w-3" aria-hidden="true" />
                P · {listing.parking_match_count} parcări
                {listing.best_parking?.walk_min !== null &&
                  listing.best_parking?.walk_min !== undefined && (
                    <> · ~{Math.round(listing.best_parking.walk_min)} min</>
                  )}
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  )
}
