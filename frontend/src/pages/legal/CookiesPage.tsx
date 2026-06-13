import { useState } from 'react'
import { LegalLayout } from './LegalLayout'

export function CookiesPage() {
  const [cleared, setCleared] = useState(false)

  const clearAll = () => {
    try {
      localStorage.clear()
    } catch {
      // ignore (private mode etc.)
    }
    setCleared(true)
  }

  return (
    <LegalLayout title="Politica de cookie-uri">
      <p>
        {/* Local app: no auth, no server — so no cookies at all. */}
        Aplicația rulează local și <strong>nu folosește cookie-uri</strong> — nici de
        autentificare, nici de publicitate, tracking sau analytics. Salvăm doar câteva preferințe
        în <code>localStorage</code>, în browserul tău (nu sunt cookie-uri și nu ne sunt
        transmise): preferința de temă (mod întunecat), anunțurile salvate la favorite și alegerea
        ta afișată la prima vizită. Toate rămân pe dispozitivul tău.
      </p>

      <h2 className="mt-6 text-lg font-semibold text-slate-900 dark:text-neutral-100">
        Ștergerea preferințelor locale
      </h2>
      <p>
        Poți șterge oricând preferințele salvate local, cu un singur click. Acțiunea readuce
        setările la valorile implicite.
      </p>
      {cleared ? (
        <p className="mt-3 font-medium text-emerald-700 dark:text-emerald-400">
          Gata — preferințele locale au fost șterse.
        </p>
      ) : (
        <button
          type="button"
          onClick={clearAll}
          className="mt-3 inline-flex items-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
        >
          Șterge preferințele locale
        </button>
      )}
    </LegalLayout>
  )
}
