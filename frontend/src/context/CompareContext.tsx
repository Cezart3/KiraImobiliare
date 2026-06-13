import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { CompareContext, MAX_COMPARE, type CompareContextValue } from './compareContextValue'

/** Holds the set of listing ids currently selected for the "Compară" view. */
export function CompareProvider({ children }: { children: ReactNode }) {
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const toggle = useCallback((id: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((v) => v !== id)
      if (prev.length >= MAX_COMPARE) return prev
      return [...prev, id]
    })
  }, [])

  const clear = useCallback(() => setSelectedIds([]), [])

  const value = useMemo<CompareContextValue>(
    () => ({
      selectedIds,
      isSelected: (id: number) => selectedIds.includes(id),
      toggle,
      clear,
      atMax: selectedIds.length >= MAX_COMPARE,
    }),
    [selectedIds, toggle, clear],
  )

  return <CompareContext.Provider value={value}>{children}</CompareContext.Provider>
}
