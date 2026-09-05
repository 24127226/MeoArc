import { Component, type ErrorInfo, type ReactNode } from 'react'

/* ══════════════════════════════════════════════════════════════════════════════
   LƯỚI AN TOÀN — một component ném lỗi KHÔNG được làm cả app biến mất.

   ── VẤN ĐỀ ĐO ĐƯỢC ──
   Người dùng báo: trang giới thiệu vào được, nhưng vào phần thư thì "màn hình đen".
   Không có `ErrorBoundary` nào trong cây, nên một lỗi lúc vẽ làm React tháo sạch
   gốc — còn lại đúng nền tối `#0A0718` của theme. Nhìn ra y hệt "web sập", trong
   khi máy chủ vẫn trả 200 và mọi tệp vẫn tải được.

   Đó là kiểu hỏng tệ nhất trong ba kiểu:
     · báo lỗi rõ  → sửa được ngay
     · trắng/đen KHÔNG chữ → không biết bắt đầu từ đâu, và giữa buổi bảo vệ thì
       không có cách nào chữa tại chỗ
     · chạy sai âm thầm → tệ hơn nữa, nhưng ít nhất còn thấy màn hình

   ── VÌ SAO IN CẢ LỖI RA MÀN HÌNH ──
   Thường thì phơi stack cho người dùng cuối là dở. Ở đây thì ngược lại: người dùng
   là chính nhóm làm ra nó, và thứ họ cần nhất lúc hỏng là MỘT DÒNG CHỮ ĐỂ CHỤP GỬI
   ĐI. Bắt họ mở DevTools giữa lúc đang trình bày là không thực tế.

   ── NÚT "DỌN TRẠNG THÁI CỤC BỘ" ──
   Kha khá lỗi kiểu này đến từ một giá trị cũ còn nằm trong `localStorage` (ngôn ngữ,
   độ rộng cột, phiên đăng nhập cũ) không còn khớp mã mới. Xoá tay thì phải mở
   DevTools; nên đặt sẵn một nút — nó là cách tự chữa nhanh nhất, và cũng loại trừ
   được một nhóm nguyên nhân trước khi đi tìm chỗ khác.
   ══════════════════════════════════════════════════════════════════════════════ */

type Props = { children: ReactNode }
type State = { loi: Error | null; noi: string }

export class LuoiAnToan extends Component<Props, State> {
  state: State = { loi: null, noi: '' }

  static getDerivedStateFromError(loi: Error): Partial<State> {
    return { loi }
  }

  componentDidCatch(loi: Error, info: ErrorInfo) {
    // Vẫn ghi ra console: người mở được DevTools thì có đủ stack gốc của React,
    // chi tiết hơn hẳn phần rút gọn hiện trên màn hình.
    console.error('[MeoArc] lỗi khi vẽ giao diện:', loi, info.componentStack)
    this.setState({ noi: (info.componentStack || '').trim().split('\n').slice(0, 6).join('\n') })
  }

  render() {
    if (!this.state.loi) return this.props.children

    return (
      <div className="flex min-h-dvh items-center justify-center bg-background p-6 text-foreground">
        <div className="w-full max-w-2xl space-y-4 rounded-2xl border border-destructive/40 bg-popover-foreground/5 p-6">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-destructive">
              Giao diện gặp lỗi
            </p>
            <h1 className="mt-1 font-serif text-2xl font-semibold">
              MeoArc dừng lại thay vì hiện một màn hình trống
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Máy chủ có thể vẫn chạy bình thường — đây là lỗi ở phần chạy trong trình
              duyệt. Chụp lại khung dưới đây là đủ để tìm ra nguyên nhân.
            </p>
          </div>

          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-background/70 p-3 font-mono text-[11.5px] leading-relaxed text-foreground/85">
            {this.state.loi.message}
            {this.state.noi ? `\n\n${this.state.noi}` : ''}
          </pre>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => window.location.reload()}
              className="rounded-xl bg-active px-4 py-2 text-sm font-semibold text-active-foreground"
            >
              Tải lại trang
            </button>
            <button
              onClick={() => {
                // CHỈ xoá khoá của MeoArc. `localStorage.clear()` sẽ xoá luôn dữ liệu
                // của trang khác dùng chung origin — không phải thứ mình được phép làm.
                try {
                  for (const k of Object.keys(localStorage)) {
                    if (k.startsWith('meoarc')) localStorage.removeItem(k)
                  }
                } catch {
                  /* trình duyệt chặn lưu trữ thì thôi — nút kia vẫn dùng được */
                }
                window.location.href = '/'
              }}
              className="rounded-xl border border-border/50 px-4 py-2 text-sm font-medium"
            >
              Dọn trạng thái cục bộ rồi về trang chính
            </button>
          </div>
        </div>
      </div>
    )
  }
}
