import { RefreshCw } from 'lucide-react'
import type { UseScrapeResult } from '@/hooks/useScrape'

interface RefreshControlProps {
  scrape: UseScrapeResult
  city: string
}

/**
 * "Actualizează anunțuri" button + live progress line + success/error notes.
 * Shared between the normal search view and the first-run welcome panel.
 */
export function RefreshControl({ scrape, city }: RefreshControlProps) {
  const { start, running, progress, error, justFinished } = scrape

  return (
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={() => start(city)}
        disabled={running || !city}
        className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-70 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
      >
        <RefreshCw className={`h-4 w-4 ${running ? 'animate-spin' : ''}`} aria-hidden="true" />
        {running ? 'Se actualizează… (poate dura câteva minute)' : 'Actualizează anunțuri'}
      </button>

      {running && progress && (
        <p className="text-xs text-slate-500 dark:text-neutral-400">{progress}</p>
      )}

      {!running && justFinished && (
        <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
          Anunțuri actualizate.
        </p>
      )}

      {!running && error && (
        <p className="text-xs font-medium text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  )
}
