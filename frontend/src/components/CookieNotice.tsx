import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Cookie, X } from 'lucide-react'

const STORAGE_KEY = 'cookie-notice-dismissed'

/**
 * Honest, non-blocking cookie notice.
 *
 * We only ever set ONE cookie: `rs_session` — a strictly necessary, httpOnly
 * login cookie, and only after the user signs in. No analytics, ads or tracking
 * cookies exist, so under the ePrivacy Directive no prior consent is required.
 * This banner therefore only *informs*; it is not a consent wall. Dismissal is
 * remembered in localStorage (a device preference, not transmitted to us).
 */
export function CookieNotice() {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1'
    } catch {
      return false
    }
  })

  if (dismissed) return null

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, '1')
    } catch {
      // ignore (private mode etc.) — banner just reappears next visit
    }
    setDismissed(true)
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 px-3 pb-3 sm:px-4 sm:pb-4">
      <div className="mx-auto flex w-full max-w-3xl items-start gap-3 rounded-xl border border-slate-200 bg-white/95 px-4 py-3 text-sm text-slate-600 shadow-lg backdrop-blur-sm dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-neutral-300">
        <Cookie className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
        <p className="flex-1 leading-relaxed">
          Folosim un singur cookie esențial, pentru autentificare — fără
          urmărire, fără publicitate.{' '}
          <Link
            to="/cookies"
            className="font-medium text-emerald-700 underline underline-offset-2 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-300"
          >
            Detalii
          </Link>
          .
        </p>
        <button
          type="button"
          onClick={dismiss}
          className="flex-shrink-0 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-700"
        >
          Am înțeles
        </button>
        <button
          type="button"
          onClick={dismiss}
          aria-label="Închide"
          className="flex-shrink-0 rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 dark:text-neutral-500 dark:hover:bg-neutral-800"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
