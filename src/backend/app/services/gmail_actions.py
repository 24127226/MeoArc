# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/services/gmail_actions.py — GHI vào Gmail (Nấc 6a)             ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ MỤC ĐÍCH: thực hiện các HÀNH ĐỘNG làm THAY ĐỔI thư trên Gmail:     ║
# ║   đánh dấu đã/chưa đọc · gắn/bỏ sao · lưu trữ · xoá (thùng rác).   ║
# ║ Ý TƯỞNG CỐT LÕI: trong Gmail, gần như mọi thao tác chỉ là          ║
# ║   THÊM hoặc BỚT một "nhãn" (label) trên thư:                       ║
# ║     • đã đọc    = BỚT nhãn UNREAD                                  ║
# ║     • chưa đọc  = THÊM nhãn UNREAD                                 ║
# ║     • gắn sao   = THÊM nhãn STARRED                                ║
# ║     • lưu trữ   = BỚT nhãn INBOX (thư rời hộp thư đến, vẫn còn)     ║
# ║   Riêng "xoá" dùng endpoint trash (chuyển vào TRASH).             ║
# ║ KHÁC gmail_service.py: file kia chỉ ĐỌC; file này GHI → cần quyền  ║
# ║   gmail.modify và phải DỌN CACHE sau mỗi lần ghi.                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import httpx
from app.services import gmail_service  # để gọi invalidate_cache sau khi ghi

# Hai địa chỉ Gmail API dùng để GHI (khác địa chỉ đọc ở gmail_service):
#   /modify → thêm/bớt nhãn cho 1 thư    ·   /trash → chuyển 1 thư vào thùng rác
GMAIL_MODIFY = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/modify"
GMAIL_TRASH = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/trash"
GMAIL_LABELS = "https://gmail.googleapis.com/gmail/v1/users/me/labels"  # liệt kê/tạo nhãn


class GmailPermissionError(Exception):
    """Ném ra khi Gmail trả 403 = TOKEN THIẾU QUYỀN ghi.

    VÌ SAO CẦN LỚP LỖI RIÊNG: người đã đăng nhập từ Nấc 5 chỉ có quyền 'đọc'
    (gmail.readonly). Sau khi ta đổi scope sang gmail.modify, token CŨ vẫn chỉ
    đọc được → mọi lệnh ghi bị Gmail từ chối (403). Bắt riêng lỗi này để tầng
    API dịch thành thông báo rõ ràng "hãy đăng nhập lại", thay vì lỗi 500 khó hiểu.
    """


def modify_labels(
    access_token: str,
    ids: list[str],
    add: list[str] | None = None,
    remove: list[str] | None = None,
) -> int:
    """Thêm/bớt nhãn cho MỘT HOẶC NHIỀU thư cùng lúc (dùng chung cho mọi hành động nhãn).

    Tham số:
      • ids    : danh sách id thư cần đổi (1 thư hay hàng loạt đều dùng hàm này).
      • add    : các nhãn cần THÊM   (vd ["STARRED"] để gắn sao, ["UNREAD"] để đánh dấu chưa đọc).
      • remove : các nhãn cần BỚT    (vd ["UNREAD"] để đánh dấu đã đọc, ["INBOX"] để lưu trữ).
    Trả về: SỐ thư đổi thành công (để FE biết "đã tác động lên mấy thư").
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    # Thân request gửi cho Gmail: chỉ kèm khoá nào THỰC SỰ có giá trị
    # (không gửi addLabelIds rỗng cho gọn và đúng chuẩn API).
    payload: dict = {}
    if add:
        payload["addLabelIds"] = add
    if remove:
        payload["removeLabelIds"] = remove

    affected = 0
    # Mở 1 kết nối HTTP rồi tái dùng cho cả vòng lặp (nhanh hơn mở lại mỗi thư).
    with httpx.Client(timeout=15) as client:
        for mid in ids:
            r = client.post(GMAIL_MODIFY.format(id=mid), headers=headers, json=payload)
            if r.status_code == 403:        # token thiếu quyền ghi → dừng ngay, báo lên trên
                raise GmailPermissionError()
            if r.status_code == 200:        # Gmail xác nhận đã đổi nhãn thư này
                affected += 1
            # các mã khác (vd 404 thư không tồn tại) → bỏ qua thư đó, không tính vào affected

    # ĐÃ GHI XONG → dọn cache của người này để lần đọc kế tiếp lấy trạng thái MỚI.
    gmail_service.invalidate_cache(access_token)
    return affected


def _get_or_create_label(client: httpx.Client, headers: dict, name: str) -> str:
    """Trả về ID nhãn Gmail tên `name`; CHƯA có thì TẠO mới.
    VÌ SAO cần bước này: Gmail thao tác theo ID nhãn, không theo tên. Mà nhãn do người
    dùng tạo (vd "Học tập") thì ID là chuỗi riêng → phải tra danh sách nhãn để lấy/đặt."""
    r = client.get(GMAIL_LABELS, headers=headers)
    if r.status_code == 403:
        raise GmailPermissionError()
    r.raise_for_status()
    for lb in r.json().get("labels", []):
        if lb.get("name", "").lower() == name.lower():
            return lb["id"]                    # đã có nhãn trùng tên → dùng lại
    # Chưa có → tạo nhãn mới (hiện trong cả danh sách nhãn lẫn từng thư).
    cr = client.post(
        GMAIL_LABELS, headers=headers,
        json={"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
    )
    if cr.status_code == 403:
        raise GmailPermissionError()
    cr.raise_for_status()
    return cr.json()["id"]


def apply_label(access_token: str, ids: list[str], label_name: str) -> int:
    """Gắn nhãn tên `label_name` cho các thư (tạo nhãn nếu chưa có). Trả số thư gắn được."""
    headers = {"Authorization": f"Bearer {access_token}"}
    affected = 0
    with httpx.Client(timeout=15) as client:
        label_id = _get_or_create_label(client, headers, label_name)  # 1 lần cho cả lô
        for mid in ids:
            r = client.post(
                GMAIL_MODIFY.format(id=mid), headers=headers,
                json={"addLabelIds": [label_id]},
            )
            if r.status_code == 403:
                raise GmailPermissionError()
            if r.status_code == 200:
                affected += 1
    gmail_service.invalidate_cache(access_token)
    return affected


def trash(access_token: str, ids: list[str]) -> int:
    """Chuyển một hoặc nhiều thư vào THÙNG RÁC (xoá "mềm", có thể khôi phục).

    VÌ SAO KHÔNG XOÁ HẲN: gmail.modify CỐ TÌNH không cho xoá vĩnh viễn (an toàn);
    chuyển vào thùng rác là đủ cho nút "Xoá" của app và còn cứu được nếu lỡ tay.
    Endpoint /trash khác /modify: không cần thân request, chỉ POST tới id thư.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    affected = 0
    with httpx.Client(timeout=15) as client:
        for mid in ids:
            r = client.post(GMAIL_TRASH.format(id=mid), headers=headers)
            if r.status_code == 403:
                raise GmailPermissionError()
            if r.status_code == 200:
                affected += 1
    gmail_service.invalidate_cache(access_token)
    return affected
