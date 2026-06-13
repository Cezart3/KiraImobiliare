import { useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { queryKeys } from '@/api/queries'
import type { FavoritesResponse } from '@/api/types'
import { useMe } from './useMe'

const STORAGE_KEY = 'favorites'

function readLocalFavorites(): number[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter((v): v is number => typeof v === 'number')
  } catch {
    return []
  }
}

function writeLocalFavorites(ids: number[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
  } catch {
    // ignore (private mode, quota, etc.)
  }
}

function clearLocalFavorites(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}

export interface UseFavoritesResult {
  ids: Set<number>
  isFavorite: (id: number) => boolean
  toggle: (id: number) => void
  count: number
}

/**
 * Favorites (saved listings), hybrid account/localStorage source of truth.
 *
 * - Anonymous: ids live in localStorage under "favorites" (JSON array of numbers).
 * - Logged in: ids come from GET /api/favorites, mutated via PUT/DELETE
 *   /api/favorites/{id} with optimistic updates.
 * - On the anonymous -> logged-in transition, any localStorage ids are pushed
 *   via POST /api/favorites/sync (merge), then the local copy is cleared and
 *   the server list becomes the source of truth.
 */
export function useFavorites(): UseFavoritesResult {
  const { data: me } = useMe()
  const authenticated = me?.authenticated ?? false
  const queryClient = useQueryClient()

  const favoritesQuery = useQuery({
    queryKey: queryKeys.favorites,
    queryFn: () => apiClient.get<FavoritesResponse>('/favorites'),
    enabled: authenticated,
    staleTime: 60 * 1000,
  })

  // Local (anonymous) ids, kept in the query cache so every component
  // sharing this hook reacts to the same value (plain useState would be
  // per-instance and wouldn't sync e.g. a card's heart with the header count).
  const localFavoritesQuery = useQuery({
    queryKey: queryKeys.localFavorites,
    queryFn: () => readLocalFavorites(),
    initialData: () => readLocalFavorites(),
    enabled: !authenticated,
    staleTime: Infinity,
  })

  // Detect the anonymous -> authenticated transition and sync local ids up.
  const wasAuthenticatedRef = useRef(authenticated)
  useEffect(() => {
    const wasAuthenticated = wasAuthenticatedRef.current
    wasAuthenticatedRef.current = authenticated

    if (!wasAuthenticated && authenticated) {
      const pending = readLocalFavorites()
      if (pending.length > 0) {
        void apiClient
          .post<FavoritesResponse>('/favorites/sync', { ids: pending })
          .then((res) => {
            clearLocalFavorites()
            queryClient.setQueryData(queryKeys.localFavorites, [])
            queryClient.setQueryData(queryKeys.favorites, res)
          })
          .catch(() => {
            // leave local copy in place; user can retry by toggling again
          })
      }
    }
  }, [authenticated, queryClient])

  const toggle = (id: number) => {
    if (authenticated) {
      const current = favoritesQuery.data?.ids ?? []
      const isSaved = current.includes(id)
      const optimistic = isSaved ? current.filter((v) => v !== id) : [...current, id]

      queryClient.setQueryData(queryKeys.favorites, { ids: optimistic } satisfies FavoritesResponse)

      const request = isSaved
        ? apiClient.delete<{ ok: boolean }>(`/favorites/${id}`)
        : apiClient.put<{ ok: boolean }>(`/favorites/${id}`)

      request
        .catch(() => {
          // revert on failure
          queryClient.setQueryData(queryKeys.favorites, { ids: current } satisfies FavoritesResponse)
        })
        .finally(() => {
          void queryClient.invalidateQueries({ queryKey: queryKeys.favorites })
        })
      return
    }

    const current = localFavoritesQuery.data ?? []
    const next = current.includes(id) ? current.filter((v) => v !== id) : [...current, id]
    writeLocalFavorites(next)
    queryClient.setQueryData(queryKeys.localFavorites, next)
  }

  const ids = new Set(authenticated ? favoritesQuery.data?.ids ?? [] : localFavoritesQuery.data ?? [])

  return {
    ids,
    isFavorite: (id: number) => ids.has(id),
    toggle,
    count: ids.size,
  }
}
