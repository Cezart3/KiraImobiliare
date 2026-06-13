import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { CheckoutResponse, SyncResponse } from '@/api/types'
import { useInvalidateMeAndListings } from './useMe'

/** Starts a one-time Stripe Checkout (15 lei / 30 days) and redirects there. */
export function useCheckoutMutation() {
  return useMutation({
    mutationFn: () => apiClient.post<CheckoutResponse>('/billing/checkout'),
    onSuccess: (data) => {
      window.location.href = data.url
    },
  })
}

/** Credits the payment + refreshes access state after returning from Checkout. */
export function useSyncMutation() {
  const invalidateMeAndListings = useInvalidateMeAndListings()
  return useMutation({
    mutationFn: () => apiClient.post<SyncResponse>('/billing/sync'),
    onSuccess: invalidateMeAndListings,
  })
}

/** Logs the user out and refreshes session + listings state. */
export function useLogoutMutation() {
  const invalidateMeAndListings = useInvalidateMeAndListings()
  return useMutation({
    mutationFn: () => apiClient.post<{ ok: true }>('/auth/logout'),
    onSuccess: invalidateMeAndListings,
  })
}

/** Permanently deletes the account (GDPR right to erasure), then refreshes
 * session + listings state. */
export function useDeleteAccountMutation() {
  const invalidateMeAndListings = useInvalidateMeAndListings()
  return useMutation({
    mutationFn: () => apiClient.post<{ ok: true }>('/auth/delete-account'),
    onSuccess: invalidateMeAndListings,
  })
}
