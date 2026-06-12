import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { apiClient, ApiError } from '@/api/client'
import type { MeOut } from '@/api/types'
import { useMe, useInvalidateMeAndListings } from '@/hooks/useMe'

type Mode = 'login' | 'register'

interface AuthModalProps {
  open: boolean
  onClose: () => void
  /** Called after a successful login/register/Google sign-in. */
  onSuccess?: (me: MeOut) => void
}

const GOOGLE_SCRIPT_POLL_MS = 300
const GOOGLE_SCRIPT_POLL_ATTEMPTS = 20

export function AuthModal({ open, onClose, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const { data: me } = useMe()
  const invalidateMeAndListings = useInvalidateMeAndListings()
  const emailInputRef = useRef<HTMLInputElement>(null)
  const googleButtonRef = useRef<HTMLDivElement>(null)

  const handleSuccess = (data: MeOut) => {
    invalidateMeAndListings()
    onClose()
    onSuccess?.(data)
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

  // Reset form state whenever the modal transitions from closed to open.
  // Adjusting state during render (rather than in an effect) avoids an extra
  // render pass and the cascading-setState lint warning.
  const [prevOpen, setPrevOpen] = useState(open)
  if (open !== prevOpen) {
    setPrevOpen(open)
    if (open) {
      setEmail('')
      setPassword('')
      setMode('login')
      loginMutation.reset()
      registerMutation.reset()
      googleMutation.reset()
    }
  }

  // Focus the email field whenever the modal opens.
  useEffect(() => {
    if (!open) return
    const id = window.setTimeout(() => emailInputRef.current?.focus(), 0)
    return () => window.clearTimeout(id)
  }, [open])

  // Close on Escape and lock body scroll while open.
  useEffect(() => {
    if (!open) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  // Render the Google Sign-In button. The GSI script (loaded async/defer in
  // index.html) may not be ready yet, so poll briefly until window.google
  // is available.
  useEffect(() => {
    const clientId = me?.google_client_id
    if (!open || !clientId) return

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
        width: 320,
        text: 'continue_with',
        locale: 'ro',
      })
    }

    tryRender()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, me?.google_client_id])

  if (!open) return null

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (isPending) return
    activeMutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Închide"
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label={mode === 'login' ? 'Autentificare' : 'Cont nou'}
        className="relative flex w-full max-w-sm flex-col rounded-xl bg-white p-6 shadow-xl dark:bg-neutral-900"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Închide"
          className="absolute right-3 top-3 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:text-neutral-500 dark:hover:bg-neutral-800 dark:hover:text-neutral-300"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>

        <div className="mb-5 inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1 dark:border-neutral-700 dark:bg-neutral-800">
          <button
            type="button"
            onClick={() => setMode('login')}
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
            onClick={() => setMode('register')}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              mode === 'register'
                ? 'bg-white text-slate-900 shadow-sm dark:bg-neutral-900 dark:text-neutral-100'
                : 'text-slate-500 hover:text-slate-700 dark:text-neutral-400 dark:hover:text-neutral-200'
            }`}
          >
            Cont nou
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
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
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
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
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm transition-colors placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100 dark:placeholder:text-neutral-500"
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
            className="mt-1 inline-flex h-10 w-full items-center justify-center rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPending
              ? 'Se procesează...'
              : mode === 'login'
                ? 'Autentificare'
                : 'Creează cont'}
          </button>
        </form>

        {me?.google_client_id && (
          <>
            <div className="my-4 flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-700" />
              <span className="text-xs font-medium uppercase text-slate-400 dark:text-neutral-500">sau</span>
              <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-700" />
            </div>
            <div ref={googleButtonRef} className="flex justify-center" />
          </>
        )}
      </div>
    </div>
  )
}
