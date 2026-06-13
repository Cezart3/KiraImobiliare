import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from './client'
import type {
  City,
  CityStats,
  Listing,
  ListingDetail,
  ListingsResponse,
  ScrapeHasData,
  ScrapeStartResponse,
  ScrapeStatus,
} from './types'
import type { Filters } from '@/lib/searchParams'
import { filtersToApiParams, DEFAULT_PAGE_SIZE } from '@/lib/searchParams'

export const queryKeys = {
  cities: ['cities'] as const,
  listings: (params: URLSearchParams) => ['listings', params.toString()] as const,
  listing: (id: number) => ['listing', id] as const,
  stats: ['stats'] as const,
  localFavorites: ['localFavorites'] as const,
  scrapeStatus: ['scrapeStatus'] as const,
  hasData: (city: string) => ['hasData', city] as const,
}

export function useCities() {
  return useQuery({
    queryKey: queryKeys.cities,
    queryFn: () => apiClient.get<City[]>('/cities'),
    staleTime: 30 * 60 * 1000,
  })
}

export function useListings(filters: Filters, pageSize: number = DEFAULT_PAGE_SIZE) {
  const params = filtersToApiParams(filters, pageSize)

  return useQuery({
    queryKey: queryKeys.listings(params),
    queryFn: () => apiClient.get<ListingsResponse>('/listings', params),
    placeholderData: (previousData) => previousData,
    enabled: Boolean(filters.city),
  })
}

export function useListingDetail(id: number | null) {
  return useQuery({
    queryKey: queryKeys.listing(id ?? -1),
    queryFn: () => apiClient.get<ListingDetail>(`/listings/${id}`),
    enabled: id !== null,
  })
}

export function useCityStats(enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: () => apiClient.get<CityStats[]>('/stats'),
    staleTime: 5 * 60 * 1000,
    enabled,
  })
}

/** Starts a scrape for a city. The backend runs it in the background; poll
 * `useScrapeStatus` for progress. */
export function useStartScrape() {
  return useMutation({
    mutationFn: (params: { city: string; maxPages?: number }) =>
      apiClient.post<ScrapeStartResponse>('/scrape', {
        city: params.city,
        max_pages: params.maxPages,
      }),
  })
}

/** Polls the current scrape status. Re-polls every ~3s while the last known
 * status says a scrape is running, and stops on its own once it finishes —
 * no manual interval bookkeeping needed. */
export function useScrapeStatus(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.scrapeStatus,
    queryFn: () => apiClient.get<ScrapeStatus>('/scrape/status'),
    enabled,
    refetchInterval: (query) => (query.state.data?.running ? 3000 : false),
  })
}

/** Whether a city already has any listings — used to tell "first run, no data
 * yet" apart from "filters returned nothing". */
export function useHasData(city: string) {
  return useQuery({
    queryKey: queryKeys.hasData(city),
    queryFn: () => apiClient.get<ScrapeHasData>('/scrape/has-data', new URLSearchParams({ city })),
    enabled: Boolean(city),
    staleTime: 30 * 1000,
  })
}

export type { Listing, ListingDetail, City, CityStats }
