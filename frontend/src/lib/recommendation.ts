// Simple client-side "fit for you" heuristic based on the declared number of
// tenants. No backend involvement — purely a UI nicety.

import type { Listing } from '@/api/types'

export const PERSON_OPTIONS = [
  { value: 1, label: '1 persoană' },
  { value: 2, label: '2 persoane' },
  { value: 3, label: '3+ persoane' },
] as const

/**
 * Whether a listing is a good fit for the declared number of tenants.
 * - 1 person: own-boiler heating (or unknown) AND surface <= 55 mp (or unknown)
 * - 2 persons: at least 2 rooms
 * - 3+ persons: at least 3 rooms
 */
export function recommendationFor(persons: number, listing: Listing): boolean {
  if (persons <= 1) {
    const surfaceOk = listing.surface_m2 == null || listing.surface_m2 <= 55
    return listing.heating === 'centrala_proprie' && surfaceOk
  }
  if (persons === 2) {
    return listing.rooms !== null && listing.rooms >= 2
  }
  return listing.rooms !== null && listing.rooms >= 3
}

/** "preț / persoană" — only meaningful when persons > 1 and price is known. */
export function pricePerPerson(priceEur: number | null, persons: number): number | null {
  if (priceEur === null || persons <= 1) return null
  return Math.round(priceEur / persons)
}

// ---- "best of my favorites" scoring --------------------------------------
//
// Ranks a set of saved listings so the user can pick a winner without manually
// eyeballing each one. Pure client-side, relative scoring (each factor compared
// against the others in the set). Higher score = better.

export interface ScoredListing {
  listing: Listing
  score: number
  reasons: string[]
}

/**
 * Score favorites relative to each other on: price (cheaper is better),
 * distance to the user's address (closer is better, if available), parking,
 * heating fit for the tenant count, and surface fit. Returns them sorted best
 * first, each with a short list of human reasons for why it ranked well.
 */
export function scoreFavorites(listings: Listing[], persons: number): ScoredListing[] {
  if (listings.length === 0) return []

  const prices = listings.map((l) => l.price_eur).filter((p): p is number => p != null)
  const minPrice = prices.length ? Math.min(...prices) : null
  const maxPrice = prices.length ? Math.max(...prices) : null

  const dists = listings
    .map((l) => l.distance_to_origin_m)
    .filter((d): d is number => d != null)
  const minDist = dists.length ? Math.min(...dists) : null
  const maxDist = dists.length ? Math.max(...dists) : null

  const norm = (v: number, lo: number, hi: number) => (hi === lo ? 1 : (hi - v) / (hi - lo))

  const scored = listings.map<ScoredListing>((listing) => {
    let score = 0
    const reasons: string[] = []

    // price: cheaper ranks higher (weight 3)
    if (listing.price_eur != null && minPrice != null && maxPrice != null) {
      const p = norm(listing.price_eur, minPrice, maxPrice)
      score += p * 3
      if (listing.price_eur === minPrice) reasons.push('cel mai mic preț')
    }

    // distance: closer ranks higher (weight 3) — only when addresses were given
    if (listing.distance_to_origin_m != null && minDist != null && maxDist != null) {
      const d = norm(listing.distance_to_origin_m, minDist, maxDist)
      score += d * 3
      if (listing.distance_to_origin_m === minDist) reasons.push('cel mai aproape')
    }

    // parking (weight 2)
    if (listing.parking_status === 'included') {
      score += 2
      reasons.push('parcare inclusă')
    } else if (listing.parking_status === 'likely_included') {
      score += 1
    }

    // heating fit for 1 tenant (weight 1.5)
    if (listing.heating === 'centrala_proprie') {
      score += 1.5
      if (persons <= 1) reasons.push('centrală proprie')
    }

    // fits the declared tenant count (weight 1.5)
    if (recommendationFor(persons, listing)) {
      score += 1.5
      reasons.push('potrivit ca mărime')
    }

    return { listing, score, reasons }
  })

  return scored.sort((a, b) => b.score - a.score)
}
