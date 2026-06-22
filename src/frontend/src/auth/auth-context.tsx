import { createContext, useContext, useEffect, useState } from 'react'
import { api, apiBaseUrl } from '@/lib/api'

export type User = {
  name: string
  email: string
  initial: string
}

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  /** Mock: giả lập luồng OAuth Google (backend thật là repo khác). */
  loginWithGoogle: () => Promise<void>
  /** Đăng xuất khỏi phiên (UC002). */
  logout: () => void
}

const STORAGE_KEY = 'meoarc-auth'

// Có VITE_API_BASE_URL → dùng backend THẬT; không có → chạy mock như cũ.
const USE_BACKEND = !!apiBaseUrl

/** Tài khoản demo dùng cho ảnh SRS / demo. */
const DEMO_USER: User = {
  name: 'Phạm Trần Anh Quân',
  email: 'quanpta.meoarc@gmail.com',
  initial: 'Q',
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(USE_BACKEND ? null : readStoredUser)
  // http mode: ban đầu CHƯA biết đã đăng nhập chưa → đang "kiểm tra phiên".
  const [isLoading, setIsLoading] = useState<boolean>(USE_BACKEND)

  // Chế độ BACKEND THẬT: khi mở app, hỏi /me xem còn phiên đăng nhập không.
  useEffect(() => {
    if (!USE_BACKEND) return
    let alive = true
    api
      .me()
      .then((u) => alive && setUser(u))
      .catch(() => alive && setUser(null))
      .finally(() => alive && setIsLoading(false))
    return () => {
      alive = false
    }
  }, [])

  // Chế độ MOCK: lưu user vào localStorage như cũ (không có backend).
  useEffect(() => {
    if (USE_BACKEND) return
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else localStorage.removeItem(STORAGE_KEY)
  }, [user])

  const loginWithGoogle = async () => {
    if (USE_BACKEND) {
      // Đăng nhập THẬT: điều hướng cả trang sang backend → backend đẩy sang Google.
      window.location.href = `${apiBaseUrl}/auth/google/start`
      return new Promise<void>(() => {}) // trang sẽ rời đi, không cần resolve
    }
    // Mock: giả lập độ trễ redirect OAuth rồi gán tài khoản demo.
    setIsLoading(true)
    await new Promise((r) => setTimeout(r, 1100))
    setUser(DEMO_USER)
    setIsLoading(false)
  }

  const logout = () => {
    if (USE_BACKEND) void api.logout().catch(() => {})
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải dùng bên trong <AuthProvider>')
  return ctx
}
