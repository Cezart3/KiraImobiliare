import { useNavigate } from 'react-router-dom'
import { Lock, ShieldCheck } from 'lucide-react'
import { useMe } from '@/hooks/useMe'
import { useCheckoutMutation } from '@/hooks/useBilling'
import { ApiError } from '@/api/client'
import { formatAnunturiCount } from '@/lib/format'

interface PaywallBannerProps {
  total: number
  visibleLimit: number | null
}

/** Shown after the visible listing cards when the backend reports that
 * results were cut by the freemium paywall (`locked: true`). */
export function PaywallBanner({ total, visibleLimit }: PaywallBannerProps) {
  const { data: me } = useMe()
  const navigate = useNavigate()
  const checkoutMutation = useCheckoutMutation()

  const errorMessage =
    checkoutMutation.error instanceof ApiError ? checkoutMutation.error.message : null

  const handleUnlock = () => {
    if (!me?.authenticated) {
      const next = `${window.location.pathname}${window.location.search}`
      navigate(`/cont?next=${encodeURIComponent(next)}`)
      return
    }
    checkoutMutation.mutate()
  }

  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-emerald-50 p-6 text-center shadow-sm dark:border-emerald-900/50 dark:from-emerald-950/40 dark:via-neutral-900 dark:to-emerald-950/40 sm:p-8">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600 text-white">
        <Lock className="h-6 w-6" aria-hidden="true" />
      </div>

      <h2 className="mt-4 text-lg font-bold text-slate-900 dark:text-neutral-50 sm:text-xl">
        Am găsit {formatAnunturiCount(total)}
      </h2>

      <p className="mx-auto mt-2 max-w-xl text-sm text-slate-600 dark:text-neutral-400">
        {visibleLimit !== null && (
          <>Vezi primele {visibleLimit} gratuit. </>
        )}
        Deblochează toate anunțurile pentru 15 lei/lună — anulezi oricând, la fel de simplu.
      </p>

      <button
        type="button"
        onClick={handleUnlock}
        disabled={checkoutMutation.isPending}
        className="mt-5 inline-flex h-11 items-center justify-center rounded-lg bg-emerald-600 px-6 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {checkoutMutation.isPending ? 'Se redirecționează...' : 'Deblochează tot — 15 lei/lună'}
      </button>

      {errorMessage && (
        <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">
          {errorMessage}
        </p>
      )}

      <p className="mt-3 inline-flex items-center justify-center gap-1.5 text-xs text-slate-400 dark:text-neutral-500">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Plată securizată prin Stripe · Card sau Apple Pay
      </p>
    </div>
  )
}
