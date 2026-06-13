import { Bug, Lightbulb } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCityStats } from '@/api/queries'
import { formatRelativeTime, formatSiteName } from '@/lib/format'
import { CONTACT_EMAIL, OPERATOR, SITE_NAME } from '@/lib/site'

interface FooterProps {
  /** When provided (e.g. on the search page), shows a per-site freshness row
   * for that city above the main footer content. */
  citySlug?: string
}

const IDEA_MAILTO = `mailto:${CONTACT_EMAIL}?subject=%5BKira%5D%20Idee%20de%20func%C8%9Bionalitate`
const BUG_MAILTO = `mailto:${CONTACT_EMAIL}?subject=%5BKira%5D%20Bug%20g%C4%83sit`

export function Footer({ citySlug }: FooterProps) {
  const { data, isLoading } = useCityStats(Boolean(citySlug))

  const cityStats = citySlug ? data?.find((c) => c.city_slug === citySlug) : undefined
  const runs = cityStats?.last_runs ?? []

  // Keep only the most recent run per source.
  const latestBySite = new Map<string, (typeof runs)[number]>()
  for (const run of runs) {
    const existing = latestBySite.get(run.site)
    if (!existing || (run.finished_at ?? '') > (existing.finished_at ?? '')) {
      latestBySite.set(run.site, run)
    }
  }
  const freshness = Array.from(latestBySite.values())

  return (
    <footer className="mt-8 border-t border-slate-200 bg-slate-50 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {citySlug && !isLoading && freshness.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-neutral-400">
            {freshness.map((run) => {
              const relative = formatRelativeTime(run.finished_at)
              return (
                <span key={run.site}>
                  <span className="font-medium text-slate-600 dark:text-neutral-300">{formatSiteName(run.site)}</span>
                  {relative && <> · {relative}</>}
                  {run.items_upserted !== null && (
                    <> · {new Intl.NumberFormat('ro-RO').format(run.items_upserted)} anunțuri</>
                  )}
                </span>
              )
            })}
          </div>
        )}

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          <div>
            <p className="text-lg font-bold tracking-tight text-slate-900 dark:text-neutral-50">{SITE_NAME}</p>
            <p className="mt-2 text-sm text-slate-500 dark:text-neutral-400">
              Toate chiriile din orașul tău, într-un singur loc.
            </p>
            <p className="mt-4 text-xs text-slate-400 dark:text-neutral-500">© 2026 {OPERATOR}</p>
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-neutral-50">Legal</p>
            <ul className="mt-3 flex flex-col gap-2 text-sm text-slate-500 dark:text-neutral-400">
              <li>
                <Link to="/despre" className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400">
                  Despre
                </Link>
              </li>
              <li>
                <Link to="/confidentialitate" className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400">
                  Politica de confidențialitate
                </Link>
              </li>
              <li>
                <Link to="/termeni" className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400">
                  Termeni și condiții
                </Link>
              </li>
              <li>
                <Link to="/cookies" className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400">
                  Politica de cookie-uri
                </Link>
              </li>
              <li>
                <a
                  href="https://anpc.ro/ce-este-sal/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  ANPC — SAL
                </a>
              </li>
              <li>
                <a
                  href="https://ec.europa.eu/consumers/odr"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="transition-colors hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Soluționarea online a litigiilor (SOL)
                </a>
              </li>
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-neutral-50">Feedback &amp; contact</p>
            <p className="mt-3 text-sm text-slate-500 dark:text-neutral-400">
              Ai o idee de funcționalitate utilă sau ai găsit un bug? Scrie-mi — chiar citesc fiecare mesaj.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href={IDEA_MAILTO}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
              >
                <Lightbulb className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                Propune o idee
              </a>
              <a
                href={BUG_MAILTO}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
              >
                <Bug className="h-3.5 w-3.5 text-red-500 dark:text-red-400" aria-hidden="true" />
                Raportează un bug
              </a>
            </div>
            <p className="mt-3 text-xs text-slate-400 dark:text-neutral-500">{CONTACT_EMAIL}</p>
          </div>
        </div>

        <p className="mt-8 border-t border-slate-200 pt-4 text-xs text-slate-400 dark:border-neutral-800 dark:text-neutral-500">
          Anunțurile aparțin site-urilor sursă; fiecare card trimite către anunțul original.
        </p>
      </div>
    </footer>
  )
}
