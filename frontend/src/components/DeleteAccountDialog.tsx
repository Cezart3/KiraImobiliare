import { useEffect } from 'react'

interface DeleteAccountDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  isPending: boolean
  error: string | null
}

/** Confirmation dialog for the irreversible "Șterge contul" action. */
export function DeleteAccountDialog({ open, onClose, onConfirm, isPending, error }: DeleteAccountDialogProps) {
  // Close on Escape and lock body scroll while open.
  useEffect(() => {
    if (!open) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isPending) onClose()
    }
    document.addEventListener('keydown', handleKeyDown)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, isPending, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Închide"
        onClick={() => !isPending && onClose()}
        className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Ștergi contul definitiv?"
        className="relative flex w-full max-w-sm flex-col rounded-xl bg-white p-6 shadow-xl dark:bg-neutral-900"
      >
        <h2 className="text-lg font-bold text-slate-900 dark:text-neutral-50">Ștergi contul definitiv?</h2>

        <p className="mt-2 text-sm text-slate-600 dark:text-neutral-300">
          Se anulează automat și abonamentul. Acțiunea nu poate fi anulată.
        </p>

        {error && (
          <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={isPending}
            className="inline-flex h-10 items-center justify-center rounded-lg border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
          >
            Renunță
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isPending}
            className="inline-flex h-10 items-center justify-center rounded-lg bg-red-600 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPending ? 'Se șterge...' : 'Da, șterge contul'}
          </button>
        </div>
      </div>
    </div>
  )
}
