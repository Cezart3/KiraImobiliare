import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom'
import { LandingPage } from '@/pages/LandingPage'
import { SearchPage } from '@/pages/SearchPage'
import { AuthPage } from '@/pages/AuthPage'
import { PrivacyPage } from '@/pages/legal/PrivacyPage'
import { TermsPage } from '@/pages/legal/TermsPage'
import { CookiesPage } from '@/pages/legal/CookiesPage'
import { AboutPage } from '@/pages/legal/AboutPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { CookieNotice } from '@/components/CookieNotice'
import { CompareProvider } from '@/context/CompareContext'
import { ApiError } from '@/api/client'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // never retry client errors (429 rate limit, 401, 404...) — retrying
      // only amplifies the load; retry network/5xx once
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status < 500) return false
        return failureCount < 1
      },
      refetchOnWindowFocus: false,
    },
  },
})

/** Root layout: renders the active route plus the global cookie notice. */
function RootLayout() {
  return (
    <CompareProvider>
      <Outlet />
      <CookieNotice />
    </CompareProvider>
  )
}

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <LandingPage /> },
      { path: '/cauta', element: <SearchPage /> },
      { path: '/cont', element: <AuthPage /> },
      { path: '/confidentialitate', element: <PrivacyPage /> },
      { path: '/termeni', element: <TermsPage /> },
      { path: '/cookies', element: <CookiesPage /> },
      { path: '/despre', element: <AboutPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}

export default App
