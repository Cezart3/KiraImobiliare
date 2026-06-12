import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { SearchPage } from '@/pages/SearchPage'
import { PrivacyPage } from '@/pages/legal/PrivacyPage'
import { TermsPage } from '@/pages/legal/TermsPage'
import { CookiesPage } from '@/pages/legal/CookiesPage'
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

const router = createBrowserRouter([
  {
    path: '/',
    element: <SearchPage />,
  },
  {
    path: '/confidentialitate',
    element: <PrivacyPage />,
  },
  {
    path: '/termeni',
    element: <TermsPage />,
  },
  {
    path: '/cookies',
    element: <CookiesPage />,
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
