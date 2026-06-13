import { SearchX, AlertTriangle, RefreshCw, DownloadCloud } from 'lucide-react'
import type { UseScrapeResult } from '@/hooks/useScrape'

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center dark:border-neutral-700 dark:bg-neutral-900">
      <SearchX className="mb-3 h-10 w-10 text-slate-300 dark:text-neutral-600" aria-hidden="true" />
      <p className="text-base font-medium text-slate-700 dark:text-neutral-300">
        Niciun anunț — încearcă filtre mai largi
      </p>
    </div>
  )
}

interface FirstRunStateProps {
  cityName: string
  scrape: UseScrapeResult
  citySlug: string
}

/** Welcome panel shown when a city has no data yet at all (vs. an
 * over-filtered search). Lets the user kick off the first scrape. */
export function FirstRunState({ cityName, scrape, citySlug }: FirstRunStateProps) {
  const { start, running, progress, error, justFinished } = scrape

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center dark:border-neutral-700 dark:bg-neutral-900">
      <DownloadCloud className="mb-3 h-10 w-10 text-emerald-500 dark:text-emerald-400" aria-hidden="true" />
      <p className="text-base font-medium text-slate-700 dark:text-neutral-300">
        Bun venit! Încă nu ai anunțuri pentru {cityName}.
      </p>
      <p className="mt-2 max-w-md text-sm text-slate-500 dark:text-neutral-400">
        Apasă butonul de mai jos ca să aduci anunțurile. Prima actualizare durează mai mult
        (aprox. <strong>10–15 minute</strong>, variază în funcție de oraș) pentru că aduce
        <strong> toate</strong> anunțurile de la 6 surse, politicos, ca să nu fim blocați.
        Vezi progresul live mai jos — nu e blocat, doar lucrează. După prima rulare, totul e instant.
      </p>

      <button
        type="button"
        onClick={() => start(citySlug)}
        disabled={running || !citySlug}
        className="mt-5 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-70"
      >
        <RefreshCw className={`h-4 w-4 ${running ? 'animate-spin' : ''}`} aria-hidden="true" />
        {running ? 'Se actualizează… (10–15 min prima dată)' : 'Adu anunțurile acum'}
      </button>

      {running && progress && (
        <p className="mt-3 text-xs text-slate-500 dark:text-neutral-400">{progress}</p>
      )}

      {!running && justFinished && (
        <p className="mt-3 text-xs font-medium text-emerald-600 dark:text-emerald-400">
          Anunțuri actualizate.
        </p>
      )}

      {!running && error && (
        <p className="mt-3 text-xs font-medium text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  )
}

interface ErrorStateProps {
  message?: string
  onRetry: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-red-200 bg-red-50 px-6 py-16 text-center dark:border-red-900/50 dark:bg-red-950/30">
      <AlertTriangle className="mb-3 h-10 w-10 text-red-400 dark:text-red-500" aria-hidden="true" />
      <p className="mb-1 text-base font-medium text-red-700 dark:text-red-400">
        A apărut o eroare la încărcarea anunțurilor
      </p>
      {message && <p className="mb-4 text-sm text-red-500 dark:text-red-400/80">{message}</p>}
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex items-center gap-2 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm transition-colors hover:bg-red-50 dark:border-red-800 dark:bg-neutral-900 dark:text-red-400 dark:hover:bg-red-950/50"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" />
        Reîncearcă
      </button>
    </div>
  )
}
