import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { NhaCungCapNgonNgu } from './lib/ngon-ngu'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Bọc NGOÀI CÙNG: mọi màn đều đọc được ngôn ngữ, kể cả trang đăng nhập và
        trang lịch trình vốn nằm ngoài AppShell. */}
    <NhaCungCapNgonNgu>
      <App />
    </NhaCungCapNgonNgu>
  </StrictMode>,
)
