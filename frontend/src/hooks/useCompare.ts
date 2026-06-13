import { useContext } from 'react'
import { CompareContext, type CompareContextValue } from '@/context/compareContextValue'

export function useCompare(): CompareContextValue {
  const ctx = useContext(CompareContext)
  if (!ctx) throw new Error('useCompare must be used within a CompareProvider')
  return ctx
}
