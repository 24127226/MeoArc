import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { LuoiAnToan } from './components/luoi-an-toan'
import { NhaCungCapNgonNgu } from './lib/ngon-ngu'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Lưới an toàn NẰM NGOÀI CÙNG, ngoài cả lớp ngôn ngữ: nếu chính lớp ngôn ngữ
        hỏng thì vẫn còn thứ bắt được lỗi. Đặt nó bên trong thì lỗi ở lớp bao ngoài
        vẫn cho ra màn hình đen — đúng cái nó sinh ra để chặn. */}
    <LuoiAnToan>
      {/* Bọc NGOÀI CÙNG: mọi màn đều đọc được ngôn ngữ, kể cả trang đăng nhập và
          trang lịch trình vốn nằm ngoài AppShell. */}
      <NhaCungCapNgonNgu>
        <App />
      </NhaCungCapNgonNgu>
    </LuoiAnToan>
  </StrictMode>,
)
