# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/schemas/email.py — HÌNH DẠNG của một Email (Nấc 1)              ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: mô tả CHÍNH XÁC một Email gồm những trường gì, kiểu gì.   ║
# ║ VÌ SAO: Frontend đã chốt shape ở docs/interface/01-DATA-MODEL.      ║
# ║         BE phải trả đúng tên trường đó thì FE mới hiểu.             ║
# ║ Pydantic giúp: (1) TỰ kiểm tra dữ liệu sai kiểu → báo lỗi sớm,      ║
# ║                (2) TỰ đổi object Python ↔ JSON.                     ║
# ╚══════════════════════════════════════════════════════════════════╝

from typing import Literal
from pydantic import BaseModel

# `Literal[...]` = "chỉ được nhận đúng các giá trị này". Nếu lỡ gán
# category="xyz", Pydantic sẽ BÁO LỖI ngay — chặn dữ liệu rác.
Category = Literal["moss", "sea", "sun", "cherry", "sky", "terra", "wine"]
Priority = Literal["action", "waiting", "fyi"]
Folder = Literal["inbox", "sent", "drafts", "archive", "trash"]


class Attachment(BaseModel):
    name: str   # tên tệp, vd "Mau_SRS.docx"
    size: str   # cỡ ở dạng chữ để hiển thị, vd "248 KB"


class Email(BaseModel):
    # GHI CHÚ: mình đặt tên trường y hệt FE (camelCase như senderEmail)
    # để JSON trả ra KHỚP 100% cái FE đợi — đỡ phải ánh xạ qua lại.
    # (Trong dự án lớn người ta hay dùng alias để giữ snake_case bên Python,
    #  nhưng ở đây ưu tiên dễ đối chiếu với hợp đồng.)
    id: str
    sender: str             # tên hiển thị người gửi
    senderEmail: str        # email người gửi
    senderInitial: str      # 1 ký tự cho avatar tròn
    to: str                 # người nhận (hiển thị)
    subject: str
    preview: str            # 1 dòng snippet
    body: list[str]         # các đoạn văn; mỗi phần tử = 1 đoạn <p> bên FE
    time: str               # nhãn ngắn ở danh sách, vd "08:42"
    date: str               # nhãn đầy đủ ở chi tiết, vd "Hôm nay, 08:42"
    unread: bool
    starred: bool
    category: Category

    # Các trường có dấu "?" bên FE = KHÔNG bắt buộc → cho giá trị mặc định None.
    label: str | None = None
    attachments: list[Attachment] | None = None
    priority: Priority | None = None        # do AI Triage gán; ban đầu có thể trống
    tldr: str | None = None                 # tóm tắt do AI; ban đầu có thể trống
    folder: Folder | None = None            # thiếu = coi như "inbox"
