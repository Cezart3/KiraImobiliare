import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SlidersHorizontal, X } from 'lucide-react'
import { useCities, useListings } from '@/api/queries'
import {
  clearedFilters,
  countActiveFilters,
  filtersFromSearchParams,
  filtersToSearchParams,
  type Filters,
} from '@/lib/searchParams'
import { Header } from '@/components/Header'
import { FilterSidebar } from '@/components/FilterSidebar'
import { ListingGrid } from '@/components/ListingGrid'
import { ListingGridSkeleton } from '@/components/Skeletons'
import { EmptyState, ErrorState } from '@/components/EmptyState'
import { Pagination } from '@/components/Pagination'
import { ParkingDrawer } from '@/components/ParkingDrawer'
import { Footer } from '@/components/Footer'
import { PaywallBanner } from '@/components/PaywallBanner'
import { CheckoutReturnBanner } from '@/components/CheckoutReturnBanner'
import { ApiError } from '@/api/client'
import { usePostCheckoutReturn } from '@/hooks/usePostCheckoutReturn'

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = filtersFromSearchParams(searchParams)

  const [filtersOpen, setFiltersOpen] = useState(false)
  const [parkingListingId, setParkingListingId] = useState<number | null>(null)

  const checkoutReturn = usePostCheckoutReturn(searchParams, setSearchParams)

  const { data: cities, isLoading: citiesLoading } = useCities()
  const {
    data: listingsData,
    isLoading: listingsLoading,
    isFetching: listingsFetching,
    isError: listingsError,
    error: listingsErrorObj,
    refetch: refetchListings,
  } = useListings(filters)

  const currentCity = cities?.find((c) => c.slug === filters.city)

  const updateFilters = useCallback(
    (patch: Partial<Filters>, options?: { replace?: boolean }) => {
      const next = { ...filters, ...patch }
      const nextParams = filtersToSearchParams(next)
      setSearchParams(nextParams, { replace: options?.replace })
    },
    [filters, setSearchParams],
  )

  const handleCityChange = (citySlug: string) => {
    // Changing city resets all other filters since zones/sites are city-specific.
    const next = clearedFilters({ ...filters, city: citySlug })
    setSearchParams(filtersToSearchParams(next))
  }

  const handleQChange = (q: string) => {
    updateFilters({ q, page: 1 })
  }

  const handlePageChange = (page: number) => {
    updateFilters({ page })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleReset = () => {
    setSearchParams(filtersToSearchParams(clearedFilters(filters)))
  }

  const activeFilterCount = countActiveFilters(filters)

  const errorMessage =
    listingsErrorObj instanceof ApiError ? listingsErrorObj.message : undefined

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-neutral-950">
      <Header
        cities={cities ?? []}
        citiesLoading={citiesLoading}
        city={filters.city}
        onCityChange={handleCityChange}
        q={filters.q}
        onQChange={handleQChange}
        total={listingsData?.total}
        isLoading={listingsLoading}
      />

      <CheckoutReturnBanner status={checkoutReturn.status} onDismiss={checkoutReturn.dismiss} />

      <main className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6 sm:px-6 lg:px-8">
        {/* Desktop sidebar */}
        <aside className="hidden w-[290px] flex-shrink-0 lg:block">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
            <FilterSidebar
              city={currentCity}
              filters={filters}
              onChange={updateFilters}
              onReset={handleReset}
            />
          </div>
        </aside>

        <div className="flex-1">
          {/* Mobile filter toggle */}
          <div className="mb-4 lg:hidden">
            <button
              type="button"
              onClick={() => setFiltersOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
            >
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              Filtre
              {activeFilterCount > 0 && (
                <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-600 px-1.5 text-xs font-semibold text-white">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>

          {listingsLoading ? (
            <ListingGridSkeleton />
          ) : listingsError ? (
            <ErrorState message={errorMessage} onRetry={() => void refetchListings()} />
          ) : listingsData && listingsData.items.length > 0 ? (
            <>
              <div className={listingsFetching ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
                <ListingGrid
                  listings={listingsData.items}
                  onOpenParking={setParkingListingId}
                  openBestParking={filters.parking.includes('rentable_nearby')}
                />
              </div>

              {listingsData.locked ? (
                <PaywallBanner total={listingsData.total} visibleLimit={listingsData.visible_limit} />
              ) : (
                <div className="mt-8">
                  <Pagination
                    page={listingsData.page}
                    pages={listingsData.pages}
                    total={listingsData.total}
                    onPageChange={handlePageChange}
                  />
                </div>
              )}
            </>
          ) : (
            <EmptyState />
          )}
        </div>
      </main>

      <Footer citySlug={filters.city} />

      {/* Mobile filter drawer */}
      {filtersOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <button
            type="button"
            aria-label="Închide filtrele"
            onClick={() => setFiltersOpen(false)}
            className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Filtre"
            className="relative ml-auto flex h-full w-full max-w-sm flex-col bg-white shadow-xl dark:bg-neutral-900"
          >
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 dark:border-neutral-800">
              <h2 className="text-base font-semibold text-slate-900 dark:text-neutral-50">Filtre</h2>
              <button
                type="button"
                onClick={() => setFiltersOpen(false)}
                aria-label="Închide"
                className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:text-neutral-500 dark:hover:bg-neutral-800 dark:hover:text-neutral-300"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <FilterSidebar
                city={currentCity}
                filters={filters}
                onChange={updateFilters}
                onReset={handleReset}
              />
            </div>
            <div className="border-t border-slate-100 px-5 py-4 dark:border-neutral-800">
              <button
                type="button"
                onClick={() => setFiltersOpen(false)}
                className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
              >
                Vezi rezultatele
              </button>
            </div>
          </div>
        </div>
      )}

      <ParkingDrawer listingId={parkingListingId} onClose={() => setParkingListingId(null)} />
    </div>
  )
}
