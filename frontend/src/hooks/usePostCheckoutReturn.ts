import { useEffect, useState } from 'react'
import type { SetURLSearchParams } from 'react-router-dom'
import { useSyncMutation } from './useBilling'

export type CheckoutReturnStatus = 'success' | 'cancelled' | null

function readStatus(searchParams: URLSearchParams): CheckoutReturnStatus {
  const plata = searchParams.get('plata')
  if (plata === 'succes') return 'success'
  if (plata === 'anulat') return 'cancelled'
  return null
}

/**
 * Handles the return from Stripe Checkout: looks for `?plata=succes` or
 * `?plata=anulat` in the URL (captured once on mount), syncs payment status
 * (on success), strips the `plata` param while preserving all other filter
 * params, and returns a status for the caller to render a dismissible
 * banner/toast.
 */
export function usePostCheckoutReturn(
  searchParams: URLSearchParams,
  setSearchParams: SetURLSearchParams,
): { status: CheckoutReturnStatus; dismiss: () => void } {
  // Lazy initializer reads the URL only once on first render.
  const [status, setStatus] = useState<CheckoutReturnStatus>(() => readStatus(searchParams))
  const syncMutation = useSyncMutation()

  useEffect(() => {
    if (!status) return

    if (status === 'success') {
      syncMutation.mutate()
    }

    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        next.delete('plata')
        return next
      },
      { replace: true },
    )
    // Runs once: `status` is fixed after the initial render, and mutate/
    // setSearchParams are stable across renders.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { status, dismiss: () => setStatus(null) }
}
