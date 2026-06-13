import { useState } from 'react'
import { apiClient } from '@/api/client'
import { LegalLayout } from './LegalLayout'

export function CookiesPage() {
  const [cleared, setCleared] = useState(false)

  const clearAll = async () => {
    // clear the session cookie server-side (logout) + any local preferences
    try {
      await apiClient.post('/auth/logout', {})
    } catch {
      // not logged in / offline — local clear below is what matters
    }
    try {
      localStorage.clear()
    } catch {
      // ignore
    }
    setCleared(true)
  }

  return (
    <LegalLayout title="Politica de cookie-uri">
      <p>
        Folosim un singur cookie: <code>rs_session</code> — cookie esențial de autentificare
        (httpOnly), strict necesar funcționării contului; expiră după 30 de zile sau la
        deconectare. Pentru cookie-urile strict necesare nu este cerut consimțământul
        (Directiva ePrivacy). Preferința de temă (mod întunecat) se salvează local în browserul
        tău (localStorage) și nu ne este transmisă. Nu folosim cookie-uri de publicitate,
        tracking sau analytics. La plata prin Stripe, pagina de checkout aparține Stripe și
        folosește propriile cookie-uri (vezi politica Stripe).
      </p>

      <h2 className="mt-6 text-lg font-semibold text-slate-900 dark:text-neutral-100">
        Ștergerea datelor din browser
      </h2>
      <p>
        Poți șterge oricând cookie-ul de sesiune și preferințele salvate local, cu un singur
        click. Acțiunea te deconectează și readuce setările la valorile implicite.
      </p>
      {cleared ? (
        <p className="mt-3 font-medium text-emerald-700 dark:text-emerald-400">
          Gata — cookie-ul de sesiune și preferințele locale au fost șterse.
        </p>
      ) : (
        <button
          type="button"
          onClick={clearAll}
          className="mt-3 inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
        >
          Șterge cookie-urile și datele locale
        </button>
      )}
    </LegalLayout>
  )
}
