import { create } from 'zustand'
import { api } from './api-client'

interface AuthState {
  user: any | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  updateUser: (data: any) => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const tokens = await api.login({ email, password })
    api.setToken(tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    const user = await api.getMe()
    set({ user, isAuthenticated: true, isLoading: false })
  },

  register: async (email, password, name) => {
    const tokens = await api.register({ email, password, name })
    api.setToken(tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    const user = await api.getMe()
    set({ user, isAuthenticated: true, isLoading: false })
  },

  logout: () => {
    api.setToken(null)
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false })
      return
    }
    try {
      api.setToken(token)
      const user = await api.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch {
      api.setToken(null)
      localStorage.removeItem('refresh_token')
      set({ isLoading: false })
    }
  },

  updateUser: async (data) => {
    const user = await api.updateSettings(data)
    set({ user })
  },
}))
