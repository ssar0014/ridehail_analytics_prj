import { useEffect, useState } from 'react'
import type { Token } from './types'

const TOKEN_KEY = 'ridehail.token'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

// AuthProvider registers this so any 401 (expired token, deactivated account) signs the user out
let onUnauthorized: () => void = () => {}
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`/api${path}`, { ...init, headers })
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized()
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : res.statusText
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export function login(email: string, password: string): Promise<Token> {
  return api<Token>('/auth/login', {
    method: 'POST',
    body: new URLSearchParams({ username: email, password }),
  })
}

export interface ApiState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

/** Fetch `path` on mount (and whenever it changes). */
export function useApi<T>(path: string): ApiState<T> {
  // Tagged with the path it answers, so a path change reads as loading without a reset
  const [result, setResult] = useState<{ path: string; data: T | null; error: string | null } | null>(null)

  useEffect(() => {
    let cancelled = false
    api<T>(path)
      .then((data) => !cancelled && setResult({ path, data, error: null }))
      .catch((e: Error) => !cancelled && setResult({ path, data: null, error: e.message }))
    return () => {
      cancelled = true
    }
  }, [path])

  if (result?.path !== path) return { data: null, error: null, loading: true }
  return { data: result.data, error: result.error, loading: false }
}
