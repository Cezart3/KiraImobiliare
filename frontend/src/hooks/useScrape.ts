import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useScrapeStatus, useStartScrape, queryKeys } from '@/api/queries'
import { ApiError } from '@/api/client'

export interface UseScrapeResult {
  /** Starts a fresh scrape for the given city. */
  start: (city: string) => void
  /** True while a scrape is running (either just started, or detected via polling). */
  running: boolean
  /** Short "site: found · upserted" progress line built from recent_runs, or null. */
  progress: string | null
  /** Error message (from the start request, or reported by the backend), or null. */
  error: string | null
  /** True once a scrape just finished successfully — cleared on the next `start`. */
  justFinished: boolean
}

/**
 * Drives the "Actualizează anunțuri" flow:
 * - POSTs /api/scrape to start a run for a city.
 * - Polls GET /api/scrape/status every ~3s while running (react-query decides
 *   whether to keep polling based on the last fetched `running` flag, so the
 *   interval stops itself once the run finishes — no manual cleanup needed).
 * - When the run finishes, invalidates the listings/has-data queries so fresh
 *   data shows, and surfaces a brief "justFinished" flag.
 */
export function useScrape(): UseScrapeResult {
  const queryClient = useQueryClient()
  const startMutation = useStartScrape()

  // Optimistic flag: set immediately when the user clicks "start", before the
  // first status poll confirms the backend has picked it up.
  const [optimisticRunning, setOptimisticRunning] = useState(false)
  const [justFinished, setJustFinished] = useState(false)

  // Always poll once; react-query's refetchInterval (configured in
  // useScrapeStatus) keeps polling every 3s only while `running` is true.
  const statusQuery = useScrapeStatus(true)

  const serverRunning = statusQuery.data?.running ?? false
  const running = optimisticRunning || serverRunning

  // Detect the running -> finished transition (adjusting state during render,
  // same pattern as Header.tsx, to avoid an extra effect-driven render pass).
  const [prevServerRunning, setPrevServerRunning] = useState(serverRunning)
  if (serverRunning !== prevServerRunning) {
    setPrevServerRunning(serverRunning)
    if (!serverRunning) {
      setOptimisticRunning(false)
      setJustFinished(!statusQuery.data?.error)
    }
  }

  // Side effect only (no setState): once finished, refresh the data the rest
  // of the page depends on. A ref (rather than the render-adjusted state
  // above) tracks the previous value so the transition is still visible once
  // this effect runs.
  const wasRunningRef = useRef(serverRunning)
  useEffect(() => {
    if (wasRunningRef.current && !serverRunning) {
      void queryClient.invalidateQueries({ queryKey: ['listings'] })
      void queryClient.invalidateQueries({ queryKey: ['hasData'] })
      void queryClient.invalidateQueries({ queryKey: queryKeys.stats })
    }
    wasRunningRef.current = serverRunning
  }, [serverRunning, queryClient])

  const start = (city: string) => {
    setJustFinished(false)
    setOptimisticRunning(true)
    startMutation.mutate(
      { city },
      {
        onSuccess: () => {
          void queryClient.invalidateQueries({ queryKey: queryKeys.scrapeStatus })
        },
        onError: () => {
          setOptimisticRunning(false)
        },
      },
    )
  }

  const startError =
    startMutation.error instanceof ApiError ? startMutation.error.message : null

  const statusError = statusQuery.data?.error ?? null

  const progress = (() => {
    const runs = statusQuery.data?.recent_runs
    if (!runs || runs.length === 0) return null
    return runs
      .map((r) => `${r.site}: ${r.found ?? 0} · ${r.upserted ?? 0}`)
      .join('  ·  ')
  })()

  return {
    start,
    running,
    progress: running ? progress : null,
    error: startError ?? statusError,
    justFinished,
  }
}
