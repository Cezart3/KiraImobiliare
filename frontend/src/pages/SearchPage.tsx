import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Heart, LayoutGrid, Scale, SlidersHorizontal, X } from 'lucide-react'
import { useCities, useHasData, useListings } from '@/api/queries'
import {
  clearedFilters,
  countActiveFilters,
  filtersFromSearchParams,
  filtersToSearchParams,
  type Filters,
} from '@/lib/searchParams'
import { getCachedListings } from '@/lib/listingCache'
import { useFavorites } from '@/hooks/useFavorites'
import { useCompare } from '@/hooks/useCompare'
import { useScrape } from '@/hooks/useScrape'
import { Header } from '@/components/Header'
import { FilterSidebar } from '@/components/FilterSidebar'
import { ListingGrid } from '@/components/ListingGrid'
import { ListingGridSkeleton } from '@/components/Skeletons'
import { EmptyState, ErrorState, FirstRunState } from '@/components/EmptyState'
import { Pagination } from '@/components/Pagination'
import { ParkingDrawer } from '@/components/ParkingDrawer'
import { CompareDrawer } from '@/components/CompareDrawer'
import { BestFavorite } from '@/components/BestFavorite'
import { Footer } from '@/components/Footer'
import { RefreshControl } from '@/components/RefreshControl'
import { ApiError } from '@/api/client'

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = filtersFromSearchParams(searchParams)

  const [filtersOpen, setFiltersOpen] = useState(false)
  const [parkingListingId, setParkingListingId] = useState<number | null>(null)
  const [favoritesView, setFavoritesView] = useState(false)
  const [compareOpen, setCompareOpen] = useState(false)

  const favorites = useFavorites()
  const compare = useCompare()
  const scrape = useScrape()

  const { data: cities, isLoading: citiesLoading } = useCities()
  const {
    data: listingsData,
    isLoading: listingsLoading,
    isFetching: listingsFetching,
    isError: listingsError,
    error: listingsErrorObj,
    refetch: refetchListings,
  } = useListings(filters)
  const { data: hasDataInfo } = useHasData(filters.city)

  const currentCity = cities?.find((c) => c.slug === filters.city)

  // True once we know for certain the city has zero listings at all (not just
  // an over-filtered search). Distinguishes the first-run welcome panel from
  // the regular "nothing found, adjust filters" empty state.
  const isFirstRun = hasDataInfo?.count === 0

  // "Favorite" view renders saved listings from the session listing cache,
  // filtered by favorite ids (no backend favorites endpoint — local only).
  const favoriteListings = getCachedListings(favorites.ids)

  // compare can mix favorites + browsed listings; fall back to the session cache
  const compareListings = getCachedListings(compare.selectedIds)

  // Gentle hint when `near` was supplied but nothing could be geocoded.
  const showNoOriginNotice =
    !favoritesView &&
    filters.near.length > 0 &&
    !listingsLoading &&
    (listingsData?.items.length ?? 0) > 0 &&
    (listingsData?.items.every((item) => item.distance_to_origin_m === null) ?? false)

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
          <div className="mb-4 flex items-center justify-between gap-3 lg:hidden">
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

          {/* "Toate" / "Favorite" view toggle + refresh control */}
          <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
            <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 dark:border-neutral-700 dark:bg-neutral-900">
              <button
                type="button"
                onClick={() => setFavoritesView(false)}
                aria-pressed={!favoritesView}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  !favoritesView
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-600 hover:text-slate-800 dark:text-neutral-300 dark:hover:text-neutral-100'
                }`}
              >
                <LayoutGrid className="h-3.5 w-3.5" aria-hidden="true" />
                Toate
              </button>
              <button
                type="button"
                onClick={() => setFavoritesView(true)}
                aria-pressed={favoritesView}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  favoritesView
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-600 hover:text-slate-800 dark:text-neutral-300 dark:hover:text-neutral-100'
                }`}
              >
                <Heart className="h-3.5 w-3.5" aria-hidden="true" />
                Favorite ({favorites.count})
              </button>
            </div>

            <RefreshControl scrape={scrape} city={filters.city} />
          </div>

          <p className="mb-4 text-xs text-slate-400 dark:text-neutral-500">
            Datele sunt pe calculatorul tău. Apasă „Actualizează" oricând pentru anunțuri proaspete.
          </p>

          {showNoOriginNotice && (
            <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-400">
              Nu am putut localiza adresa — încearcă să fii mai specific.
            </p>
          )}

          {favoritesView ? (
            favoriteListings.length > 0 ? (
              <>
                <BestFavorite
                  listings={favoriteListings}
                  persons={filters.persons}
                  hasAddress={filters.near.length > 0}
                />
                <ListingGrid
                  listings={favoriteListings}
                  onOpenParking={setParkingListingId}
                  persons={filters.persons}
                />
              </>
            ) : (
              <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center dark:border-neutral-700 dark:bg-neutral-900">
                <Heart className="mb-3 h-10 w-10 text-slate-300 dark:text-neutral-600" aria-hidden="true" />
                <p className="text-base font-medium text-slate-700 dark:text-neutral-300">
                  Anunțurile salvate apar aici
                </p>
                <p className="mt-1 text-sm text-slate-400 dark:text-neutral-500">
                  Apasă inima de pe un anunț ca să-l salvezi.
                </p>
              </div>
            )
          ) : listingsLoading ? (
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
                  persons={filters.persons}
                />
              </div>

              <div className="mt-8">
                <Pagination
                  page={listingsData.page}
                  pages={listingsData.pages}
                  total={listingsData.total}
                  onPageChange={handlePageChange}
                />
              </div>
            </>
          ) : isFirstRun ? (
            <FirstRunState
              cityName={currentCity?.name ?? filters.city}
              citySlug={filters.city}
              scrape={scrape}
            />
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

      <CompareDrawer
        listings={compareOpen ? compareListings : []}
        persons={filters.persons}
        onClose={() => setCompareOpen(false)}
      />

      {/* Floating "Compară" bar — appears once 2+ listings are selected.
          Positioned above the cookie notice (which also sits at the bottom). */}
      {compare.selectedIds.length >= 2 && !compareOpen && (
        <div className="fixed inset-x-0 bottom-20 z-40 flex justify-center px-4">
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-lg dark:border-neutral-700 dark:bg-neutral-900">
            <span className="text-sm font-medium text-slate-700 dark:text-neutral-200">
              {compare.selectedIds.length} anunțuri selectate
            </span>
            <button
              type="button"
              onClick={() => setCompareOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
            >
              <Scale className="h-3.5 w-3.5" aria-hidden="true" />
              Compară ({compare.selectedIds.length})
            </button>
            <button
              type="button"
              onClick={compare.clear}
              className="text-sm font-medium text-slate-500 transition-colors hover:text-slate-700 dark:text-neutral-400 dark:hover:text-neutral-200"
            >
              Renunță
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
