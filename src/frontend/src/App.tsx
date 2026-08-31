import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider, useAuth } from '@/auth/auth-context'
import { ToastProvider } from '@/components/ui/toast'
import { AppShell } from '@/components/layout/app-shell'
import { SchedulePage } from '@/pages/schedule'
import { LoginPage } from '@/pages/login'
import { LandingPage } from '@/pages/landing'

/** Route được bảo vệ — chưa đăng nhập thì đẩy về /login (UC001). */
function RequireAuth({ children }: { children: React.ReactElement }) {
  const { isAuthenticated, isLoading } = useAuth()
  // Đang hỏi backend xem còn phiên không → chờ, đừng vội đẩy về /login (tránh nháy).
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-muted-foreground">
        Đang kiểm tra phiên…
      </div>
    )
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              {/* Trang giới thiệu (công khai) là cửa vào — nút đăng nhập mới dẫn tới /login. */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/app"
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              />
              {/* Lịch trình là TRANG RIÊNG, không phải một tab trong hộp thư.
                  Hộp thư cố ý chiếm một cột hẹp vì người ta không vào MeoArc để
                  đọc thư như Gmail. Lịch trình thì ngược lại — đó chính là thứ
                  MeoArc làm mà Gmail không làm, nên nhét nó vào một cột giữa ba
                  cột là tự hạ nó xuống ngang hàng với "Thùng rác". */}
              <Route
                path="/lich"
                element={
                  <RequireAuth>
                    <SchedulePage />
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
