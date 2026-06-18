"use client"
import { useEffect, createContext, useContext } from "react"
import { useAuth } from "@/lib/auth"

const AuthContext = createContext<any>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { checkAuth, isLoading, isAuthenticated, user } = useAuth()

  useEffect(() => {
    checkAuth()
  }, [])

  return (
    <AuthContext.Provider value={{ isLoading, isAuthenticated, user }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuthContext = () => {
  const ctx = useContext(AuthContext)
  return ctx ?? { user: null, isLoading: true, isAuthenticated: false }
}
