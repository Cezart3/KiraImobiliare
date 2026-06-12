import { SearchX, AlertTriangle, RefreshCw } from 'lucide-react'

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
