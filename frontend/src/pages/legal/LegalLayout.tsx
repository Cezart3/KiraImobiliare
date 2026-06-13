import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Footer } from '@/components/Footer'
import { LEGAL_LAST_UPDATED } from '@/lib/site'

interface LegalLayoutProps {
  title: string
  children: ReactNode
}

/** Shared layout for legal pages (privacy, terms, cookies): a simple
 * prose-like article with a back link, title and "last updated" date,
 * plus the site footer. */
export function LegalLayout({ title, children }: LegalLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-neutral-950">
      <div className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <Link
          to="/cauta"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600 transition-colors hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Înapoi la anunțuri
        </Link>

        <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 dark:text-neutral-50 sm:text-3xl">
          {title}
        </h1>

        <p className="mt-1 text-sm text-slate-400 dark:text-neutral-500">
          Ultima actualizare: {LEGAL_LAST_UPDATED}
        </p>

        <div className="mt-6 flex flex-col gap-6 text-sm leading-relaxed text-slate-600 dark:text-neutral-300">
          {children}
        </div>
      </div>

      <Footer />
    </div>
  )
}

/** Section heading + body used by every legal page. */
export function LegalSection({ title, children }: LegalLayoutProps) {
  return (
    <section>
      <h2 className="mb-2 text-lg font-semibold text-slate-900 dark:text-neutral-50">{title}</h2>
      <div className="flex flex-col gap-2">{children}</div>
    </section>
  )
}

/** Bulleted list styled to match the prose body text. */
export function LegalList({ items }: { items: ReactNode[] }) {
  return (
    <ul className="ml-5 list-disc space-y-1.5 marker:text-slate-400 dark:marker:text-neutral-600">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  )
}
