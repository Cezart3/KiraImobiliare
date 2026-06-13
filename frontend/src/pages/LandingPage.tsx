import { useNavigate } from 'react-router-dom'
import { Flame, Footprints, Home, MapPin, ParkingCircle } from 'lucide-react'
import { useCities } from '@/api/queries'
import { DEFAULT_CITY } from '@/lib/searchParams'
import { SITE_NAME, SITE_TAGLINE } from '@/lib/site'
import { ThemeToggle } from '@/components/ThemeToggle'
import { AccountMenu } from '@/components/AccountMenu'
import { Footer } from '@/components/Footer'

const FEATURES = [
  {
    icon: Flame,
    text: 'Centrală proprie vs termoficare — separate automat din anunț',
  },
  {
    icon: ParkingCircle,
    text: 'Parcare inclusă sau loc de parcare de închiriat în apropiere',
  },
  {
    icon: Footprints,
    text: 'Distanța pe jos până la adresa ta + link direct cu autobuzul',
  },
] as const

/** Marketing landing page at `/`: hero, value proposition and a city picker
 * that leads into the listings grid at `/cauta?city=<slug>`. */
export function LandingPage() {
  const navigate = useNavigate()
  const { data: cities, isLoading: citiesLoading } = useCities()

  const handleCityClick = (citySlug: string) => {
    navigate(`/cauta?city=${citySlug}`)
  }

  const browseAllSlug = cities?.[0]?.slug ?? DEFAULT_CITY

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-neutral-950">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur-sm dark:border-neutral-800 dark:bg-neutral-950/95">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white">
              <Home className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-neutral-50">
              {SITE_NAME}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <AccountMenu />
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto w-full max-w-3xl text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-neutral-50">
            {SITE_TAGLINE}
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-500 sm:text-lg dark:text-neutral-400">
            {SITE_NAME} adună anunțurile de pe Storia, OLX, Imobiliare, Publi24 și altele — cu
            filtre pe care site-urile normale nu le au.
          </p>
        </div>

        {/* City picker */}
        <div className="mx-auto mt-10 w-full max-w-3xl">
          <p className="mb-3 text-center text-sm font-semibold text-slate-700 dark:text-neutral-300">
            Alege orașul tău
          </p>
          {citiesLoading ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-20 animate-pulse rounded-xl border border-slate-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-neutral-900"
                />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {(cities ?? []).map((city) => (
                <button
                  key={city.slug}
                  type="button"
                  onClick={() => handleCityClick(city.slug)}
                  className="flex flex-col items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-5 text-center shadow-sm transition-colors hover:border-emerald-500 hover:bg-emerald-50 dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-emerald-500 dark:hover:bg-emerald-950/30"
                >
                  <MapPin className="h-5 w-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-neutral-50">
                    {city.name}
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={() => navigate(`/cauta?city=${browseAllSlug}`)}
              className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
            >
              Vezi anunțurile
            </button>
          </div>
        </div>

        {/* Feature points */}
        <div className="mx-auto mt-14 grid w-full max-w-4xl grid-cols-1 gap-4 sm:grid-cols-3">
          {FEATURES.map(({ icon: Icon, text }) => (
            <div
              key={text}
              className="flex flex-col items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-5 text-center shadow-sm dark:border-neutral-800 dark:bg-neutral-900"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <p className="text-sm text-slate-600 dark:text-neutral-300">{text}</p>
            </div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  )
}
