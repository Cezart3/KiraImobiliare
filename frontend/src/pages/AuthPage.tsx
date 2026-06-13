import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Home } from 'lucide-react'
import { apiClient, ApiError } from '@/api/client'
import type { MeOut } from '@/api/types'
import { useMe, useInvalidateMeAndListings } from '@/hooks/useMe'
import { Footer } from '@/components/Footer'
import { SITE_NAME } from '@/lib/site'

type Mode = 'login' | 'register'

const GOOGLE_SCRIPT_POLL_MS = 300
const GOOGLE_SCRIPT_POLL_ATTEMPTS = 20

/** Dedicated full-page login/register screen at `/cont`. Replaces the
 * cramped AuthModal: roomy inputs, a visible "Creează cont" tab, and a
 * prominent Google sign-in option (no password needed). */
export function AuthPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const initialMode: Mode = searchParams.get('mode') === 'register' ? 'register' : 'login'
  const [mode, setMode] = useState<Mode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const { data: me } = useMe()
  const invalidateMeAndListings = useInvalidateMeAndListings()
  const emailInputRef = useRef<HTMLInputElement>(null)
  const googleButtonRef = useRef<HTMLDivElement>(null)

  const goNext = () => {
    const next = searchParams.get('next')
    navigate(next || '/')
  }

  const handleSuccess = () => {
    invalidateMeAndListings()
    goNext()
  }

  const loginMutation = useMutation({
    mutationFn: () => apiClient.post<MeOut>('/auth/login', { email, password }),
    onSuccess: handleSuccess,
  })

  const registerMutation = useMutation({
    mutationFn: () => apiClient.post<MeOut>('/auth/register', { email, password }),
    onSuccess: handleSuccess,
  })

  const googleMutation = useMutation({
    mutationFn: (credential: string) => apiClient.post<MeOut>('/auth/google', { credential }),
    onSuccess: handleSuccess,
  })

  const activeMutation = mode === 'login' ? loginMutation : registerMutation
  const isPending = activeMutation.isPending || googleMutation.isPending

  const errorMessage = (() => {
    const err = activeMutation.error ?? googleMutation.error
    if (!err) return null
    return err instanceof ApiError ? err.message : 'A apărut o eroare. Încearcă din nou.'
  })()

  // Switching tabs clears any previous error/pending state for the other mode.
  const handleModeChange = (next: Mode) => {
    setMode(next)
    loginMutation.reset()
    registerMutation.reset()
    googleMutation.reset()
  }

  // Autofocus the email field on load.
  useEffect(() => {
    emailInputRef.current?.focus()
  }, [])

  // Render the Google Sign-In button. The GSI script (loaded async/defer in
  // index.html) may not be ready yet, so poll briefly until window.google
  // is available.
  useEffect(() => {
    const clientId = me?.google_client_id
    if (!clientId) return

    let attempts = 0
    let cancelled = false

    const tryRender = () => {
      if (cancelled) return
      const google = window.google
      const container = googleButtonRef.current
      if (!google || !container) {
        attempts += 1
        if (attempts < GOOGLE_SCRIPT_POLL_ATTEMPTS) {
          window.setTimeout(tryRender, GOOGLE_SCRIPT_POLL_MS)
        }
        return
      }

      google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          googleMutation.mutate(response.credential)
        },
      })
      container.innerHTML = ''
      google.accounts.id.renderButton(container, {
        theme: document.documentElement.classList.contains('dark') ? 'filled_black' : 'outline',
        size: 'large',
        width: 360,
        text: 'continue_with',
        locale: 'ro',
      })
    }

    tryRender()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me?.google_client_id])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (isPending) return
    activeMutation.mutate()
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-neutral-950">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col px-4 py-10 sm:px-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 self-center"
          aria-label={`${SITE_NAME} — acasă`}
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <Home className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-neutral-50">
            {SITE_NAME}
          </span>
        </Link>

        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-neutral-800 dark:bg-neutral-900">
          <h1 className="text-xl font-bold text-slate-900 dark:text-neutral-50">
            {mode === 'login' ? 'Autentificare' : 'Creează un cont'}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-neutral-400">
            {mode === 'login'
              ? 'Intră în cont pentru a-ți gestiona abonamentul.'
              : 'Durează doar câteva secunde.'}
          </p>

          <div className="mt-5 inline-flex w-full rounded-lg border border-slate-200 bg-slate-100 p-1 dark:border-neutral-700 dark:bg-neutral-800">
            <button
              type="button"
              onClick={() => handleModeChange('login')}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === 'login'
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-neutral-900 dark:text-neutral-100'
                  : 'text-slate-500 hover:text-slate-700 dark:text-neutral-400 dark:hover:text-neutral-200'
              }`}
            >
              Autentificare
            </button>
            <button
              type="button"
              onClick={() => handleModeChange('register')}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === 'register'
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-neutral-900 dark:text-neutral-100'
                  : 'text-slate-500 hover:text-slate-700 dark:text-neutral-400 dark:hover:text-neutral-200'
              }`}
            >
              Cont nou
            </button>
          </div>

          {me?.google_client_id && (
            <div className="mt-6">
              <div ref={googleButtonRef} className="flex justify-center" />
              <p className="mt-2 text-center text-xs text-slate-400 dark:text-neutral-500">
                Continuă cu Google — fără parolă. Funcționează și pentru autentificare, și pentru cont nou.
              </p>

              <div className="my-6 flex items-center gap-3">
                <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-700" />
                <span className="text-xs font-medium uppercase text-slate-400 dark:text-neutral-500">sau</span>
                <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-700" />
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <div>
              <label htmlFor="auth-email" className="mb-1 block text-sm font-medium text-slate-700 dark:text-neutral-300">
                Email
              </label>
              <input
                ref={emailInputRef}
                id="auth-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
              />
            </div>

            <div>
              <label htmlFor="auth-password" className="mb-1 block text-sm font-medium text-slate-700 dark:text-neutral-300">
                Parolă
              </label>
              <input
                id="auth-password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                minLength={mode === 'register' ? 8 : undefined}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
              />
              {mode === 'register' && (
                <p className="mt-1 text-xs text-slate-400 dark:text-neutral-500">Minim 8 caractere.</p>
              )}
            </div>

            {errorMessage && (
              <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                {errorMessage}
              </p>
            )}

            <button
              type="submit"
              disabled={isPending}
              className="mt-1 inline-flex h-11 w-full items-center justify-center rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isPending
                ? 'Se procesează...'
                : mode === 'login'
                  ? 'Autentificare'
                  : 'Creează cont'}
            </button>

            {mode === 'login' ? (
              <p className="text-center text-sm text-slate-500 dark:text-neutral-400">
                Nu ai cont?{' '}
                <button
                  type="button"
                  onClick={() => handleModeChange('register')}
                  className="font-medium text-emerald-600 transition-colors hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  Creează unul
                </button>
              </p>
            ) : (
              <p className="text-center text-sm text-slate-500 dark:text-neutral-400">
                Ai deja cont?{' '}
                <button
                  type="button"
                  onClick={() => handleModeChange('login')}
                  className="font-medium text-emerald-600 transition-colors hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
                >
                  Autentifică-te
                </button>
              </p>
            )}
          </form>
        </div>

        <Link
          to="/cauta"
          className="mt-6 inline-flex items-center gap-1.5 self-center text-sm font-medium text-emerald-600 transition-colors hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Înapoi la anunțuri
        </Link>
      </div>

      <Footer />
    </div>
  )
}
