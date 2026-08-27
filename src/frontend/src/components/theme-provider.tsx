import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

type ThemeContextValue = {
  theme: Theme
  setTheme: (t: Theme) => void
  toggleTheme: () => void
}

const STORAGE_KEY = 'meoarc-theme'

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

function getInitialTheme(): Theme {
  // MẶC ĐỊNH TỐI, không theo cài đặt hệ điều hành.
  //
  // Không phải chuyện sở thích. Ngôn ngữ thị giác của sản phẩm này là neon, mà neon
  // là hiện tượng TƯƠNG PHẢN: một nguồn sáng bão hoà trên nền gần như đen. Đặt nó
  // lên nền sáng thì ánh sáng không còn chỗ để phát ra — chỉ còn lại màu mè.
  //
  // Người dùng vẫn đổi sang sáng được trong Cài đặt, và lựa chọn đó được nhớ.
  // Chỉ có mặc định là đổi: lần đầu vào phải thấy đúng bộ mặt của sản phẩm.
  if (typeof window === 'undefined') return 'dark'
  const stored = localStorage.getItem(STORAGE_KEY) as Theme | null
  if (stored === 'light' || stored === 'dark') return stored
  return 'dark'
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  // Đồng bộ class .dark trên <html> mỗi khi theme đổi
  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', theme === 'dark')
    localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  const value: ThemeContextValue = {
    theme,
    setTheme: setThemeState,
    toggleTheme: () => setThemeState((t) => (t === 'dark' ? 'light' : 'dark')),
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme phải dùng bên trong <ThemeProvider>')
  return ctx
}
