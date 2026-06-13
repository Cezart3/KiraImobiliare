import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/api/queries'

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

export interface UseFavoritesResult {
  ids: Set<number>
  isFavorite: (id: number) => boolean
  toggle: (id: number) => void
  count: number
}

/**
 * Favorites (saved listings) — purely client-side, stored as a JSON array of
 * listing ids in localStorage under "favorites". Kept in the query cache so
 * every component sharing this hook reacts to the same value (plain
 * useState would be per-instance and wouldn't sync e.g. a card's heart with
 * the header count).
 */
export function useFavorites(): UseFavoritesResult {
  const queryClient = useQueryClient()

  const localFavoritesQuery = useQuery({
    queryKey: queryKeys.localFavorites,
    queryFn: () => readLocalFavorites(),
    initialData: () => readLocalFavorites(),
    staleTime: Infinity,
  })

  const toggle = (id: number) => {
    const current = localFavoritesQuery.data ?? []
    const next = current.includes(id) ? current.filter((v) => v !== id) : [...current, id]
    writeLocalFavorites(next)
    queryClient.setQueryData(queryKeys.localFavorites, next)
  }

  const ids = new Set(localFavoritesQuery.data ?? [])

  return {
    ids,
    isFavorite: (id: number) => ids.has(id),
    toggle,
    count: ids.size,
  }
}
