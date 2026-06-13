import { Link } from 'react-router-dom'
import { Home, SearchX } from 'lucide-react'
import { SITE_NAME } from '@/lib/site'
import { Footer } from '@/components/Footer'

/** 404 — shown for any unknown route. */
export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-neutral-950">
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center px-4 py-16 text-center">
        <SearchX className="mb-4 h-12 w-12 text-slate-300 dark:text-neutral-600" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-slate-900 dark:text-neutral-50 sm:text-3xl">
          Pagina nu a fost găsită
        </h1>
        <p className="mt-2 text-slate-500 dark:text-neutral-400">
          Linkul pe care l-ai urmat nu există sau a fost mutat.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            Acasă pe {SITE_NAME}
          </Link>
          <Link
            to="/cauta"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-neutral-600 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            Vezi anunțurile
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
