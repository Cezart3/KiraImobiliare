import { createContext } from 'react'

export const MAX_COMPARE = 4

export interface CompareContextValue {
  selectedIds: number[]
  isSelected: (id: number) => boolean
  toggle: (id: number) => void
  clear: () => void
  /** True once the max selection has been reached (used to disable other checkboxes). */
  atMax: boolean
}

export const CompareContext = createContext<CompareContextValue | null>(null)
