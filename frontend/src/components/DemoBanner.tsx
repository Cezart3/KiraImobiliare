import { useMode } from '@/api/queries'

const LOCAL_GUIDE = 'https://github.com/Cezart3/KiraImobiliare/blob/main/README.ro.md'
const WRITE_UP = 'https://cezart3.vercel.app/work/kira'

/**
 * Stays on screen for the whole session on the public demo. The listings here
 * are invented, and someone landing on the page from a link has no other way to
 * know that — so it is not dismissible.
 */
export function DemoBanner() {
  const { data } = useMode()
  if (!data?.demo) return null

  return (
    <div className="border-b border-amber-300 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/40">
      <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-2.5 text-sm text-amber-900 dark:text-amber-200 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <p>
          <span className="font-semibold">Demo public.</span> Anunțurile de aici sunt
          inventate — generate ca să poți încerca filtrele. Nu se scrapează nimic de pe
          acest site.
        </p>
        <p className="flex shrink-0 gap-3 text-xs">
          <a
            href={LOCAL_GUIDE}
            target="_blank"
            rel="noreferrer"
            className="font-medium underline underline-offset-2 hover:no-underline"
          >
            Rulează-l local pentru anunțuri reale
          </a>
          <a
            href={WRITE_UP}
            target="_blank"
            rel="noreferrer"
            className="font-medium underline underline-offset-2 hover:no-underline"
          >
            Cum e făcut
          </a>
        </p>
      </div>
    </div>
  )
}
