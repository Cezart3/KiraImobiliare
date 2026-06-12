import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { CheckoutResponse, PortalResponse, SyncResponse } from '@/api/types'
import { useInvalidateMeAndListings } from './useMe'

/** Starts a Stripe Checkout session and redirects the browser there. */
export function useCheckoutMutation() {
  return useMutation({
    mutationFn: () => apiClient.post<CheckoutResponse>('/billing/checkout'),
    onSuccess: (data) => {
      window.location.href = data.url
    },
  })
}

/** Opens the Stripe Billing Portal (manage/cancel subscription). */
export function usePortalMutation() {
  return useMutation({
    mutationFn: () => apiClient.post<PortalResponse>('/billing/portal'),
    onSuccess: (data) => {
      window.location.href = data.url
    },
  })
}

/** Re-syncs subscription status after returning from Stripe Checkout. */
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

/** Permanently deletes the account (GDPR right to erasure). Cancels any live
 * Stripe subscription first, then refreshes session + listings state. */
export function useDeleteAccountMutation() {
  const invalidateMeAndListings = useInvalidateMeAndListings()
  return useMutation({
    mutationFn: () => apiClient.post<{ ok: true }>('/auth/delete-account'),
    onSuccess: invalidateMeAndListings,
  })
}
