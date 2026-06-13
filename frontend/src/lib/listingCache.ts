// Module-level cache of every listing the user has seen rendered this
// session (id -> Listing). Used by the "Favorite" view to show full listing
// data for saved ids without needing a "/listings?ids=" backend endpoint.
//
// This is intentionally a plain module-level Map (not React state/context):
// it's a passive cache that many components write to as they render, and the
// "Favorite" view reads a filtered snapshot of it on demand.

import type { Listing } from '@/api/types'

const cache = new Map<number, Listing>()

/** Stores/updates the cached copy of each listing (e.g. after a page loads). */
export function cacheListings(listings: Listing[]): void {
  for (const listing of listings) {
    cache.set(listing.id, listing)
  }
}

/** Returns the cached listings whose id is in `ids`, preserving the order of `ids`. */
export function getCachedListings(ids: Iterable<number>): Listing[] {
  const out: Listing[] = []
  for (const id of ids) {
    const listing = cache.get(id)
    if (listing) out.push(listing)
  }
  return out
}

/** Returns the cached listing for a single id, if seen this session. */
export function getCachedListing(id: number): Listing | undefined {
  return cache.get(id)
}
