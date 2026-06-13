import { useEffect } from 'react'
import type { Listing } from '@/api/types'
import { cacheListings } from '@/lib/listingCache'
import { ListingCard } from './ListingCard'

interface ListingGridProps {
  listings: Listing[]
  onOpenParking: (listingId: number) => void
  openBestParking?: boolean
  persons?: number
}

export function ListingGrid({ listings, onOpenParking, openBestParking, persons }: ListingGridProps) {
  // Cache every listing rendered so the "Favorite" view can show full details
  // for saved ids even when they're not on the current page.
  useEffect(() => {
    cacheListings(listings)
  }, [listings])

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-3">
      {listings.map((listing) => (
        <ListingCard
          key={listing.id}
          listing={listing}
          onOpenParking={onOpenParking}
          openBestParking={openBestParking}
          persons={persons}
        />
      ))}
    </div>
  )
}
