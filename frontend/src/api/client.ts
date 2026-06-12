// Thin fetch wrapper for the RentScalper backend API.
// In dev, Vite proxies "/api" -> http://127.0.0.1:8000 (see vite.config.ts).

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, params?: URLSearchParams): Promise<T> {
  const query = params?.toString()
  const url = `/api${path}${query ? `?${query}` : ''}`

  const res = await fetch(url)
  return handleResponse<T>(res)
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Cererea a eșuat (${res.status})`
    try {
      const body = (await res.json()) as { detail?: string }
      if (body?.detail) message = body.detail
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(res.status, message)
  }

  return (await res.json()) as T
}

export const apiClient = {
  get: request,
  post,
}

/** Builds the image-proxy URL for a listing image. */
export function imageProxyUrl(src: string): string {
  return `/api/img?u=${encodeURIComponent(src)}`
}
