# Ảnh & video nền cho Landing / Login

| File                      | Dùng ở đâu                                  | Sau khi nén |
|---------------------------|---------------------------------------------|------------|
| `flower-field.mp4` + `-poster.jpg` | Landing — Hero (cánh đồng hoa phát sáng) | 4.4 MB |
| `metal-human.mp4` + `.jpg`         | Landing — khối "Là một agent thật sự"    | 1.3 MB |
| `purple-desert.mp4` + `.jpg`       | Landing — khối CTA cuối (chân trời)      | 2.4 MB |
| `flower-arc.mp4` + `.jpg`          | **Trang đăng nhập** — cổng vòm hoa        | 5.5 MB |
| `sea-storm.mp4` + `.jpg`           | Hiện KHÔNG dùng (giữ làm dự phòng)        | 1.0 MB |

Thiếu file nào thì chỗ đó tự lùi về ảnh poster rồi tới nền gradient (không vỡ layout).
Không cần restart Vite — copy xong F5 là thấy.

## Vì sao đặt từng cảnh vào chỗ đó

- **Cánh đồng hoa** mở đầu: rực rỡ, có sẵn vệt sáng bay ngang — hợp lời hứa "hộp thư biết nghe lời".
- **Tượng kim loại** cho khối agent: hình tượng trí tuệ vô diện, nền đen tuyền ghép liền mạch vào trang.
- **Sa mạc tím** cho CTA cuối: chân trời rộng, giữa khung trống nên chữ và nút nổi bật.
- **Vòm hoa** cho đăng nhập: đúng nghĩa một cánh cổng để bước qua; vòm nằm bên phải khung hình
  nên thẻ đăng nhập đặt lệch trái, không che mất hoa.

## Bảng màu rút từ chính các video

    nền     #06060B   đen ngả xanh
    violet  #8B7BF0   hoa, sa mạc tím, vòm hoa
    cyan    #4FD1C5   vệt sáng lam, tượng kim loại
    amber   #F0A848   dành RIÊNG cho nút hành động

Ba video đều tông lạnh, nên nút amber là điểm ấm duy nhất — mắt tìm thấy nút ngay.

## Nếu thay video khác

Bản gốc từ getlayers rất nặng (flower-field 55.6 MB · metal-human 54.7 MB · flower-arc 56.5 MB),
phải nén trước khi bỏ vào đây:

    ffmpeg -i goc.mp4 -vf "scale=1920:-2" -c:v libx264 -crf 25 -preset slow \
           -pix_fmt yuv420p -profile:v high -an -movflags +faststart ten-file.mp4

    ffmpeg -i goc.mp4 -vf "scale=1280:-2" -frames:v 1 -q:v 6 ten-file.jpg

`-an` bỏ tiếng (video nền luôn muted), `+faststart` cho phép phát khi mới tải một phần.
CRF càng lớn càng nhẹ và càng vỡ hạt: 25 ≈ đẹp, 30 ≈ nhẹ hơn nửa nhưng dễ thấy vỡ khối.
