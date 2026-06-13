import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cookie, X } from 'lucide-react'

const STORAGE_KEY = 'cookie-notice-dismissed'

/**
 * Cookie notice.
 *
 * We only ever set ONE cookie: `rs_session` — a strictly necessary, httpOnly
 * login cookie, set only after the user signs in. We use NO analytics, ads or
 * tracking cookies, so under the ePrivacy Directive / GDPR no opt-in consent is
 * legally required and there is nothing non-essential to "reject".
 *
 * To stay transparent (and compliant) the banner therefore:
 *  - states plainly that only an essential cookie is used,
 *  - gives a clear, direct way to manage/delete it ("Gestionează / dezactivează"
 *    -> the Cookies page, which has a one-click clear button),
 *  - lets the user dismiss the banner ("Am înțeles").
 *
 * Dismissal is stored in localStorage (a device preference, never sent to us).
 */
export function CookieNotice() {
  const navigate = useNavigate()
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

  const manage = () => {
    dismiss()
    navigate('/cookies')
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 px-3 pb-3 sm:px-4 sm:pb-4">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 rounded-xl border border-slate-200 bg-white/95 px-4 py-3 text-sm text-slate-600 shadow-lg backdrop-blur-sm sm:flex-row sm:items-center dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-neutral-300">
        <div className="flex flex-1 items-start gap-3">
          <Cookie className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <p className="flex-1 leading-relaxed">
            Folosim un singur cookie esențial, pentru autentificare — fără
            urmărire și fără publicitate. Nu sunt necesare cookie-uri pentru care
            să-ți cerem acordul. Le poți vedea și dezactiva oricând din pagina de
            cookie-uri.
          </p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={manage}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-neutral-600 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            Gestionează / dezactivează
          </button>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-700"
          >
            Am înțeles
          </button>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Închide"
            className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 dark:text-neutral-500 dark:hover:bg-neutral-800"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
