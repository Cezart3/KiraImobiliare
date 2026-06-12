import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

function getInitialIsDark(): boolean {
  if (typeof document === 'undefined') return false
  return document.documentElement.classList.contains('dark')
}

/** Light/dark theme toggle. Persists to localStorage and toggles the `dark`
 * class on <html>; see the inline script in index.html for the initial value
 * applied before first paint. */
export function ThemeToggle() {
  const [isDark, setIsDark] = useState(getInitialIsDark)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  return (
    <button
      type="button"
      onClick={() => setIsDark((v) => !v)}
      aria-label={isDark ? 'Comută la tema luminoasă' : 'Comută la tema întunecată'}
      title={isDark ? 'Tema luminoasă' : 'Tema întunecată'}
      className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800"
    >
      {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
    </button>
  )
}
