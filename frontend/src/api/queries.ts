import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'
import type { City, CityStats, Listing, ListingDetail, ListingsResponse } from './types'
import type { Filters } from '@/lib/searchParams'
import { filtersToApiParams, DEFAULT_PAGE_SIZE } from '@/lib/searchParams'

export const queryKeys = {
  cities: ['cities'] as const,
  listings: (params: URLSearchParams) => ['listings', params.toString()] as const,
  listingsAll: ['listings'] as const,
  listing: (id: number) => ['listing', id] as const,
  stats: ['stats'] as const,
  me: ['me'] as const,
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

export type { Listing, ListingDetail, City, CityStats }
