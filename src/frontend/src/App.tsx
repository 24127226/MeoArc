import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider, useAuth } from '@/auth/auth-context'
import { ToastProvider } from '@/components/ui/toast'
import { AppShell } from '@/components/layout/app-shell'
import { LoginPage } from '@/pages/login'

/** Route được bảo vệ — chưa đăng nhập thì đẩy về /login (UC001). */
function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
