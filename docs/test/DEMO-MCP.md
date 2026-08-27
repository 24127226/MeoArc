# Demo MCP — Claude Desktop điều khiển hộp thư qua MeoArc

> **Đây là nước đi lời nhất trong buổi thuyết trình: 0 dòng code, 30 phút tập.**
>
> Nó đổi cách người xem định vị sản phẩm — từ *"một web app có AI"* thành *"một nền tảng
> mà các AI khác gọi vào được"*. Đó là một tuyên bố kiến trúc, và bạn chứng minh được nó
> ngay trên màn hình.

Đã kiểm ngày 20/08: server khởi động tốt, phơi đúng **9 tool** và **3 prompt**.

```
search_emails · semantic_search · categorize_emails · get_email · list_labels
send_email · reply_email · apply_labels · bulk_action
prompt: daily_digest · triage_inbox · meeting_brief
```

---

## Bước 1 · Nối Claude Desktop vào MeoArc

Mở file cấu hình của Claude Desktop. Trên Windows, dán đường dẫn này vào thanh địa chỉ
File Explorer:

```
%APPDATA%\Claude
```

Tìm file `claude_desktop_config.json` — chưa có thì tạo mới. Dán nội dung:

```json
{
  "mcpServers": {
    "meoarc": {
      "command": "D:\\meoarc-integration\\src\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.mcp.server"],
      "cwd": "D:\\meoarc-integration\\src\\backend"
    }
  }
}
```

**Tắt hẳn Claude Desktop rồi mở lại** — nó chỉ đọc file này lúc khởi động.

Mở lại xong, tìm biểu tượng công cụ (🔨) ở khung soạn tin. Bấm vào phải thấy **9 tool của
MeoArc**. Thấy rồi là xong bước này.

---

## Bước 2 · Điều kiện để nó chạy được

MCP server lấy quyền truy cập Gmail từ **phiên đăng nhập mới nhất trong database**. Nghĩa là:

1. Mở app MeoArc trên trình duyệt, **đăng nhập Google** bình thường
2. Xong rồi mới sang Claude Desktop ra lệnh

Không đăng nhập web trước thì Claude Desktop gọi tool sẽ báo không có quyền.

⚠️ **Nhớ đăng nhập lại ngay trước buổi demo.** Consent screen đang ở chế độ Testing nên
Google chỉ cho refresh token sống **7 ngày**.

---

## Bước 3 · Kịch bản demo — 90 giây

Ba lệnh, tăng dần độ ấn tượng. Gõ vào Claude Desktop, **không phải vào app MeoArc**.

### Lệnh 1 — chứng minh nó thật sự nối được *(20 giây)*

> `Dùng MeoArc liệt kê giúp tôi 5 thư mới nhất trong hộp thư`

Claude Desktop sẽ xin phép gọi tool `search_emails`. **Bấm cho phép.** Thư thật hiện ra
trong Claude Desktop.

**Câu nói kèm:** *"Đây là Claude Desktop, không phải app của nhóm em. Nó đang đọc hộp thư
thật qua giao thức MCP mà MeoArc phơi ra."*

### Lệnh 2 — chứng minh nó làm được việc, không chỉ đọc *(30 giây)*

> `Phân loại giúp tôi các thư đó rồi gắn nhãn Công việc cho những thư liên quan đến công việc`

Nó gọi `categorize_emails` rồi `apply_labels`. **Mở Gmail thật lên cho thấy nhãn đã xuất
hiện.** Đây là chỗ người xem tin rằng không phải dàn dựng.

### Lệnh 3 — ⭐ chứng minh hàng rào vẫn đứng *(40 giây)*

> `Gửi giúp tôi một thư cảm ơn tới thầy`

**Nó sẽ KHÔNG gửi.** Tool `send_email` thuộc nhóm không đảo ngược được, nên MeoArc chặn
lại và trả về một phiếu chờ duyệt.

**Câu nói kèm — đây là câu quan trọng nhất cả buổi:**

> *"Chỗ này mới là điều em muốn nhấn. Lệnh không đến từ giao diện của nhóm em — nó đến từ
> một AI khác, qua một giao thức mở. Nếu hàng rào xác nhận chỉ nằm ở tầng giao diện thì
> lúc này nó đã bị đi vòng qua rồi. Nhưng nó nằm ở **tầng registry của tool**, nên cửa nào
> vào cũng phải qua. Đó là lý do nhóm em đặt nó ở đó chứ không đặt ở nút bấm."*

---

## Chuẩn bị trước buổi — checklist

- [ ] `claude_desktop_config.json` đã dán, đã khởi động lại Claude Desktop
- [ ] Bấm biểu tượng 🔨 → thấy đủ 9 tool MeoArc
- [ ] Đã đăng nhập Google trên web MeoArc **trong vòng 7 ngày**
- [ ] Hộp thư có sẵn vài thư thật để demo *(đừng dùng hộp thư trống)*
- [ ] Đã chạy thử **cả ba lệnh** ít nhất một lần
- [ ] Gmail mở sẵn ở một tab khác để chứng minh nhãn thật sự được gắn

## Nếu hỏng giữa chừng

| Hiện tượng | Nguyên nhân |
| :---- | :---- |
| Không thấy tool nào | Chưa khởi động lại Claude Desktop, hoặc sai đường dẫn trong config |
| Tool báo không có quyền | Chưa đăng nhập web MeoArc, hoặc phiên đã quá 7 ngày |
| Gọi tool xong báo lỗi Gemini | Hết hạn ngạch — không phải lỗi MCP, nói rõ điều đó |

**Phương án dự phòng:** quay sẵn một clip 90 giây làm đúng ba lệnh trên. Demo trực tiếp
hỏng thì mở clip, buổi thuyết trình không đứt mạch.
