import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, ChevronDown, CreditCard, LogOut, Trash2, User, Unlock, X } from 'lucide-react'
import { useMe } from '@/hooks/useMe'
import {
  useCheckoutMutation,
  useDeleteAccountMutation,
  useLogoutMutation,
  usePortalMutation,
} from '@/hooks/useBilling'
import { ApiError } from '@/api/client'
import { AuthModal } from './AuthModal'
import { DeleteAccountDialog } from './DeleteAccountDialog'

/** Top-right account area: "Intră în cont" when anonymous, or a dropdown
 * with subscription/account actions when authenticated. */
export function AccountMenu() {
  const { data: me } = useMe()
  const [authOpen, setAuthOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const checkoutMutation = useCheckoutMutation()
  const portalMutation = usePortalMutation()
  const logoutMutation = useLogoutMutation()
  const deleteAccountMutation = useDeleteAccountMutation()

  const actionError = (() => {
    const err = checkoutMutation.error ?? portalMutation.error
    if (!err) return null
    return err instanceof ApiError ? err.message : 'A apărut o eroare. Încearcă din nou.'
  })()

  // Close the dropdown on outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return

    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false)
    }

    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [menuOpen])

  const handleConfirmDelete = () => {
    deleteAccountMutation.mutate(undefined, {
      onSuccess: () => {
        setDeleteOpen(false)
        setMenuOpen(false)
        setDeleted(true)
      },
    })
  }

  const deletedNotice = deleted && (
    <div
      role="status"
      className="fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 shadow-lg dark:border-emerald-900/50 dark:bg-emerald-950/90 dark:text-emerald-300"
    >
      <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0" aria-hidden="true" />
      <p className="flex-1">Contul a fost șters.</p>
      <button
        type="button"
        onClick={() => setDeleted(false)}
        aria-label="Închide"
        className="rounded-lg p-1 text-emerald-600 transition-colors hover:bg-emerald-100 dark:text-emerald-400 dark:hover:bg-emerald-900/50"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  )

  if (!me?.authenticated) {
    return (
      <>
        <button
          type="button"
          onClick={() => setAuthOpen(true)}
          className="inline-flex h-10 items-center rounded-lg bg-emerald-600 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
        >
          Intră în cont
        </button>
        <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
        {deletedNotice}
      </>
    )
  }

  const showUnlock = !me.subscribed && me.paywall_enabled

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setMenuOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        className="inline-flex h-10 max-w-[220px] items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
      >
        <User className="h-4 w-4 flex-shrink-0 text-slate-400 dark:text-neutral-500" aria-hidden="true" />
        <span className="truncate">{me.email}</span>
        {me.subscribed && (
          <span className="inline-flex flex-shrink-0 items-center rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
            Plus
          </span>
        )}
        <ChevronDown className="h-3.5 w-3.5 flex-shrink-0 text-slate-400 dark:text-neutral-500" aria-hidden="true" />
      </button>

      {menuOpen && (
        <div
          role="menu"
          className="absolute right-0 top-full z-40 mt-2 w-64 rounded-xl border border-slate-200 bg-white py-1.5 shadow-lg dark:border-neutral-700 dark:bg-neutral-900"
        >
          <div className="border-b border-slate-100 px-3 py-2 dark:border-neutral-800">
            <p className="truncate text-sm font-medium text-slate-700 dark:text-neutral-200" title={me.email ?? undefined}>
              {me.email}
            </p>
          </div>

          {me.subscribed && (
            <button
              type="button"
              role="menuitem"
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:text-neutral-200 dark:hover:bg-neutral-800"
            >
              <CreditCard className="h-4 w-4 text-slate-400 dark:text-neutral-500" aria-hidden="true" />
              {portalMutation.isPending ? 'Se redirecționează...' : 'Gestionează abonamentul'}
            </button>
          )}

          {showUnlock && (
            <button
              type="button"
              role="menuitem"
              onClick={() => checkoutMutation.mutate()}
              disabled={checkoutMutation.isPending}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-emerald-700 transition-colors hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60 dark:text-emerald-400 dark:hover:bg-emerald-900/30"
            >
              <Unlock className="h-4 w-4" aria-hidden="true" />
              {checkoutMutation.isPending ? 'Se redirecționează...' : 'Deblochează tot — 15 lei/lună'}
            </button>
          )}

          {actionError && (
            <p role="alert" className="px-3 py-1.5 text-xs text-red-600 dark:text-red-400">
              {actionError}
            </p>
          )}

          <button
            type="button"
            role="menuitem"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
            className="flex w-full items-center gap-2 border-t border-slate-100 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            <LogOut className="h-4 w-4 text-slate-400 dark:text-neutral-500" aria-hidden="true" />
            {logoutMutation.isPending ? 'Se deconectează...' : 'Deconectare'}
          </button>

          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setMenuOpen(false)
              setDeleteOpen(true)
            }}
            className="flex w-full items-center gap-2 border-t border-slate-100 px-3 py-2 text-left text-sm text-red-600 transition-colors hover:bg-red-50 dark:border-neutral-800 dark:text-red-400 dark:hover:bg-red-950/30"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Șterge contul
          </button>
        </div>
      )}

      <DeleteAccountDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleConfirmDelete}
        isPending={deleteAccountMutation.isPending}
        error={
          deleteAccountMutation.error instanceof ApiError
            ? deleteAccountMutation.error.message
            : deleteAccountMutation.isError
              ? 'A apărut o eroare. Încearcă din nou.'
              : null
        }
      />

      {deletedNotice}
    </div>
  )
}
