import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { queryKeys } from '@/api/queries'
import type { MeOut } from '@/api/types'

/** Current session info: auth state, subscription status, paywall config. */
export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiClient.get<MeOut>('/auth/me'),
    staleTime: 60 * 1000,
  })
}

/** Returns a function that invalidates the cached session info (e.g. after
 * login, logout, register, or returning from Stripe checkout). */
export function useInvalidateMe() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: queryKeys.me })
}

/** Invalidates both the session info and all listings queries — used after
 * any auth or subscription change since the paywall affects listing results. */
export function useInvalidateMeAndListings() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.me })
    void queryClient.invalidateQueries({ queryKey: queryKeys.listingsAll })
  }
}
