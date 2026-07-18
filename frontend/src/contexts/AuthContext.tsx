import { createContext, useContext, useState, ReactNode } from 'react'
import { User } from '../types'
import api from '../api/client'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  hasPermission: (modulo: string, accion: string) => boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('token')
  )
  const [user, setUser] = useState<User | null>(() => {
    try {
      const u = localStorage.getItem('user')
      return u ? JSON.parse(u) : null
    } catch {
      return null
    }
  })

  const login = async (username: string, password: string) => {
    const form = new FormData()
    form.append('username', username)
    form.append('password', password)

    const res = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    const { access_token, usuario } = res.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(usuario))
    setToken(access_token)
    setUser(usuario)
  }

  const logout = async () => {
    try { await api.post('/auth/logout') } catch {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    window.location.replace('/login')
  }

  const hasPermission = (modulo: string, accion: string): boolean => {
    if (!user) return false
    const perms = user.permisos as Record<string, string[]>
    if ('todos' in perms) return perms['todos'].includes(accion)
    if (modulo in perms) return perms[modulo].includes(accion)
    return false
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
