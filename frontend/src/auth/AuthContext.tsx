import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, login as apiLogin, setUnauthorizedHandler, tokenStore } from '../api/client'
import type { CurrentUser } from '../api/types'

interface AuthState {
  user: CurrentUser | null
  /** True until a stored token has been checked against /auth/me */
  restoring: boolean
  signIn: (email: string, password: string) => Promise<CurrentUser>
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [restoring, setRestoring] = useState(() => tokenStore.get() !== null)

  const signOut = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(signOut)
    if (!tokenStore.get()) return
    api<CurrentUser>('/auth/me')
      .then(setUser)
      .catch(signOut)
      .finally(() => setRestoring(false))
  }, [signOut])

  const signIn = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password)
    tokenStore.set(access_token)
    const me = await api<CurrentUser>('/auth/me')
    setUser(me)
    return me
  }, [])

  const value = useMemo(() => ({ user, restoring, signIn, signOut }), [user, restoring, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
