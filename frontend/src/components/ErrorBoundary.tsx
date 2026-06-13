import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

/**
 * Catches any render-time error in the tree and shows a friendly fallback
 * instead of a blank white screen. Last-resort safety net for production.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // surfaced in the browser console for debugging; no third-party reporting
    console.error('Eroare neașteptată în interfață:', error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-6 text-center dark:bg-neutral-950">
        <h1 className="text-xl font-bold text-slate-900 dark:text-neutral-50">
          A apărut o eroare neașteptată
        </h1>
        <p className="max-w-md text-sm text-slate-500 dark:text-neutral-400">
          Ne pare rău — încearcă să reîncarci pagina. Dacă problema persistă,
          scrie-ne și o rezolvăm.
        </p>
        <button
          type="button"
          onClick={() => window.location.assign('/')}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
        >
          Înapoi la pagina principală
        </button>
      </div>
    )
  }
}
