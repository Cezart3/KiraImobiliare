// Domain types matching the RentScalper backend API contract.

export type Heating = 'centrala_proprie' | 'termoficare' | 'unknown'

export type ParkingStatus =
  | 'included'
  | 'likely_included'
  | 'area_possible'
  | 'none'
  | 'unknown'

/** Parking filter values accepted by /api/listings (OR semantics). */
export type ParkingFilter =
  | 'included'
  | 'likely_included'
  | 'area_possible'
  | 'rentable_nearby'

export type ParkingKind = 'subteran' | 'garaj' | 'exterior' | 'unknown'

export type SortOption = 'newest' | 'price_asc' | 'price_desc' | 'parking'

export interface CityZone {
  slug: string
  name: string
}

export interface CityTown {
  slug: string
  name: string
}

export interface City {
  slug: string
  name: string
  zones: CityZone[]
  nearby_towns: CityTown[]
  sites: string[]
}

export interface ParkingSpot {
  id: number
  site: string
  url: string
  title: string
  price_eur: number | null
  kind: ParkingKind
  is_numbered: boolean
  zone_slug: string | null
  address_extracted: string | null
  lat: number | null
  lon: number | null
}

export interface ParkingMatch {
  parking: ParkingSpot
  distance_m: number | null
  walk_min: number | null
  is_approx: boolean
  maps_url: string | null
}

export interface Listing {
  id: number
  site: string
  url: string
  title: string
  snippet: string | null
  price_eur: number | null
  price_negotiable: boolean
  rooms: number | null
  surface_m2: number | null
  floor: string | null
  city_slug: string
  zone_slug: string | null
  in_nearby_town: boolean
  town_slug: string | null
  address_extracted: string | null
  parking_status: ParkingStatus
  parking_confidence: number | null
  heating: Heating
  images: string[]
  lat: number | null
  lon: number | null
  geo_precision: string | null
  posted_at: string | null
  first_seen_at: string | null
  last_seen_at: string | null
  dedup_group: string | null
  parking_match_count: number
  best_parking: ParkingMatch | null
}

export interface ListingDetail extends Listing {
  description: string | null
  parking_matches: ParkingMatch[]
}

export interface ListingsResponse {
  items: Listing[]
  total: number
  page: number
  page_size: number
  pages: number
  locked: boolean
  visible_limit: number | null
}

export interface SiteRunInfo {
  site: string
  kind: string
  status: string
  finished_at: string | null
  items_found: number | null
  items_upserted: number | null
}

export interface CityStats {
  city_slug: string
  active_listings: number
  active_parking: number
  last_runs: SiteRunInfo[]
}

export interface MeOut {
  authenticated: boolean
  email: string | null
  subscribed: boolean
  sub_status: string | null
  paywall_enabled: boolean
  free_listing_limit: number
  google_client_id: string | null
}

export interface CheckoutResponse {
  url: string
}

export interface PortalResponse {
  url: string
}

export interface SyncResponse {
  subscribed: boolean
  sub_status: string | null
}
