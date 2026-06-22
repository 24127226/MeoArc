# Đánh dấu app/services/ là package. Tầng "services" = LOGIC nghiệp vụ
# (lấy/đổi dữ liệu). Route ở app/api gọi xuống đây; nhờ tách lớp, sau
# này đổi "dữ liệu giả" → "gọi Gmail thật" chỉ cần sửa ở tầng này.
