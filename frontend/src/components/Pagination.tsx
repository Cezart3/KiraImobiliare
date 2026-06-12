import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

interface PaginationProps {
  page: number
  pages: number
  total: number
  onPageChange: (page: number) => void
}

/** Builds a compact list of page numbers with `null` gaps for ellipses. */
function buildPageList(current: number, total: number): (number | null)[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages = new Set<number>([1, total, current])
  for (let d = 1; d <= 1; d++) {
    if (current - d >= 1) pages.add(current - d)
    if (current + d <= total) pages.add(current + d)
  }

  const sorted = Array.from(pages).sort((a, b) => a - b)
  const result: (number | null)[] = []
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) result.push(null)
    result.push(sorted[i])
  }
  return result
}

export function Pagination({ page, pages, total, onPageChange }: PaginationProps) {
  if (pages <= 1) {
    return (
      <p className="text-center text-sm text-slate-500 dark:text-neutral-400">
        {new Intl.NumberFormat('ro-RO').format(total)} anunțuri
      </p>
    )
  }

  const pageList = buildPageList(page, pages)

  const buttonClass =
    'inline-flex h-9 min-w-9 items-center justify-center rounded-lg border border-slate-200 bg-white px-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800'

  return (
    <div className="flex flex-col items-center gap-3">
      <nav className="flex items-center gap-1" aria-label="Paginare">
        <button
          type="button"
          className={buttonClass}
          onClick={() => onPageChange(1)}
          disabled={page <= 1}
          aria-label="Prima pagină"
        >
          <ChevronsLeft className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={buttonClass}
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Pagina anterioară"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </button>

        {pageList.map((p, i) =>
          p === null ? (
            <span key={`ellipsis-${i}`} className="px-1 text-sm text-slate-400 dark:text-neutral-500">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              onClick={() => onPageChange(p)}
              aria-current={p === page ? 'page' : undefined}
              className={
                p === page
                  ? 'inline-flex h-9 min-w-9 items-center justify-center rounded-lg bg-emerald-600 px-2 text-sm font-semibold text-white'
                  : buttonClass
              }
            >
              {p}
            </button>
          ),
        )}

        <button
          type="button"
          className={buttonClass}
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          aria-label="Pagina următoare"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={buttonClass}
          onClick={() => onPageChange(pages)}
          disabled={page >= pages}
          aria-label="Ultima pagină"
        >
          <ChevronsRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </nav>
      <p className="text-sm text-slate-500 dark:text-neutral-400">
        {new Intl.NumberFormat('ro-RO').format(total)} anunțuri
      </p>
    </div>
  )
}
