import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cookie, X } from 'lucide-react'

const STORAGE_KEY = 'cookie-choice' // 'accepted' | 'rejected'

/**
 * Cookie consent notice.
 *
 * We currently set exactly ONE cookie: `rs_session` — a strictly necessary,
 * httpOnly cookie that exists ONLY to keep you logged in, and is set only when
 * you sign in. We use NO analytics, advertising or tracking cookies.
 *
 * Under ePrivacy/GDPR a strictly-necessary cookie needs no opt-in. We still
 * offer Accept / Reject for transparency ("better safe than sorry"):
 *  - Accept: fine, the login cookie may be used when you sign in.
 *  - Reject: we record your choice; since the only cookie is the login one,
 *    rejecting simply means "I don't want the login cookie" — you can keep
 *    browsing without an account (no cookie is set unless you log in). We also
 *    point you to the Cookies page where you can clear it anytime in one click.
 *
 * The choice itself is stored in localStorage (a device preference, not sent to
 * us, not a cookie).
 */
export function CookieNotice() {
  const navigate = useNavigate()
  const [decided, setDecided] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) !== null
    } catch {
      return false
    }
  })

  if (decided) return null

  const choose = (choice: 'accepted' | 'rejected') => {
    try {
      localStorage.setItem(STORAGE_KEY, choice)
    } catch {
      // ignore (private mode etc.) — banner just reappears next visit
    }
    setDecided(true)
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 px-3 pb-3 sm:px-4 sm:pb-4">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 rounded-xl border border-slate-200 bg-white/95 px-4 py-3 text-sm text-slate-600 shadow-lg backdrop-blur-sm sm:flex-row sm:items-center dark:border-neutral-700 dark:bg-neutral-900/95 dark:text-neutral-300">
        <div className="flex flex-1 items-start gap-3">
          <Cookie className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <p className="flex-1 leading-relaxed">
            Folosim un singur cookie, strict pentru sesiunea de logare — fără
            urmărire și fără publicitate. Îl poți accepta sau refuza, iar dacă
            te răzgândești îl poți dezactiva oricând din{' '}
            <button
              type="button"
              onClick={() => {
                choose('rejected')
                navigate('/cookies')
              }}
              className="font-medium text-emerald-700 underline underline-offset-2 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-300"
            >
              pagina de cookie-uri
            </button>
            .
          </p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={() => choose('rejected')}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-neutral-600 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            Refuz
          </button>
          <button
            type="button"
            onClick={() => choose('accepted')}
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-700"
          >
            Accept
          </button>
          <button
            type="button"
            onClick={() => choose('rejected')}
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
