import type { Listing } from '@/api/types'
import { ListingCard } from './ListingCard'

interface ListingGridProps {
  listings: Listing[]
  onOpenParking: (listingId: number) => void
  openBestParking?: boolean
}

export function ListingGrid({ listings, onOpenParking, openBestParking }: ListingGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-3">
      {listings.map((listing) => (
        <ListingCard
          key={listing.id}
          listing={listing}
          onOpenParking={onOpenParking}
          openBestParking={openBestParking}
        />
      ))}
    </div>
  )
}
