import { createContext, useContext, useEffect, useState } from 'react'

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
  const [user, setUser] = useState<User | null>(readStoredUser)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else localStorage.removeItem(STORAGE_KEY)
  }, [user])

  const loginWithGoogle = async () => {
    setIsLoading(true)
    // Giả lập độ trễ redirect OAuth để màn hình trông thật khi demo/chụp.
    await new Promise((r) => setTimeout(r, 1100))
    setUser(DEMO_USER)
    setIsLoading(false)
  }

  const logout = () => setUser(null)

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
