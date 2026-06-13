import { CheckCircle2, Info, X } from 'lucide-react'
import type { CheckoutReturnStatus } from '@/hooks/usePostCheckoutReturn'

interface CheckoutReturnBannerProps {
  status: CheckoutReturnStatus
  onDismiss: () => void
}

/** Dismissible banner shown after returning from Stripe Checkout
 * (`?plata=succes` or `?plata=anulat`, already stripped from the URL by
 * usePostCheckoutReturn). */
export function CheckoutReturnBanner({ status, onDismiss }: CheckoutReturnBannerProps) {
  if (!status) return null

  if (status === 'success') {
    return (
      <div className="mx-auto mt-4 flex w-full max-w-7xl items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 shadow-sm sm:px-6 lg:px-8 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
        <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0" aria-hidden="true" />
        <p className="flex-1">
          <span className="font-semibold">Acces activ — mulțumim!</span> Ai acces complet 30 de
          zile. Acum vezi toate anunțurile.
        </p>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Închide"
          className="rounded-lg p-1 text-emerald-600 transition-colors hover:bg-emerald-100 dark:text-emerald-400 dark:hover:bg-emerald-900/50"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto mt-4 flex w-full max-w-7xl items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm sm:px-6 lg:px-8 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300">
      <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-slate-400 dark:text-neutral-500" aria-hidden="true" />
      <p className="flex-1">Plata a fost anulată.</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Închide"
        className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 dark:text-neutral-500 dark:hover:bg-neutral-800"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  )
}
