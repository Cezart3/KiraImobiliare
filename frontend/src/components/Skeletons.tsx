export function ListingCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-neutral-900">
      <div className="aspect-[4/3] w-full animate-pulse bg-slate-200 dark:bg-neutral-800" />
      <div className="flex flex-col gap-3 p-4">
        <div className="flex items-baseline justify-between gap-2">
          <div className="h-5 w-24 animate-pulse rounded bg-slate-200 dark:bg-neutral-800" />
          <div className="h-3 w-16 animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
        </div>
        <div className="h-4 w-full animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
        <div className="flex gap-3 pt-1">
          <div className="h-3 w-12 animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
          <div className="h-3 w-12 animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
          <div className="h-3 w-12 animate-pulse rounded bg-slate-100 dark:bg-neutral-800/60" />
        </div>
      </div>
    </div>
  )
}

interface ListingGridSkeletonProps {
  count?: number
}

export function ListingGridSkeleton({ count = 12 }: ListingGridSkeletonProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <ListingCardSkeleton key={i} />
      ))}
    </div>
  )
}
