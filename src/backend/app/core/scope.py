# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/core/scope.py — PHẠM VI QUÉT HỘP THƯ THEO GÓI (NFR-08)        ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ NFR-SCO-01: các tác vụ AI quét nội dung hộp thư SẴN CÓ (tìm theo   ║
# ║ ngữ nghĩa, phân loại, tóm tắt, trích việc, lấy ngữ cảnh trả lời)   ║
# ║ chỉ được xử lý thư trong khoảng thời gian của gói:                 ║
# ║     Miễn phí 90 ngày · Pro 180 ngày · Pro Max 365 ngày             ║
# ║                                                                    ║
# ║ NFR-SCO-02: TRÍCH VIỆC luôn bị chặn ở 90 ngày dù gói nào — việc    ║
# ║ moi ra từ thư cũ hơn thế gần như chắc chắn đã hết hạn xử lý.       ║
# ║                                                                    ║
# ║ NFR-SCO-03: XEM danh sách thư và TÌM THEO TỪ KHOÁ **không** bị     ║
# ║ giới hạn — người dùng vẫn phải với tới được thư cũ của chính mình. ║
# ║ Giới hạn ở đây là giới hạn cho AI, không phải cho người dùng.      ║
# ║                                                                    ║
# ║ NFR-SCO-04: tự phân loại thư MỚI về cũng miễn trừ, vì nó chỉ chạm  ║
# ║ thư nhận sau khi bật, không bao giờ quét ngược quá khứ.            ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.core.plans import DEFAULT_TIER, TIERS

# NFR-SCO-02 — trần cứng cho trích việc, không phụ thuộc gói.
TASK_EXTRACTION_MAX_DAYS = 90


def scan_days(tier: str) -> int:
    """Số ngày hộp thư mà AI được phép quét ở gói này (gói lạ → về Miễn phí)."""
    t = TIERS.get(tier) or TIERS[DEFAULT_TIER]
    return int(t["scan_days"])


def task_scan_days(tier: str) -> int:
    """Riêng TRÍCH VIỆC: lấy giá trị NHỎ HƠN giữa cửa sổ của gói và trần 90 ngày.

    Dùng min() chứ không trả thẳng 90: gói Miễn phí vốn đã là 90, còn nếu sau này
    có gói nào hẹp hơn 90 thì trần cứng không được phép NỚI RỘNG nó ra.
    """
    return min(scan_days(tier), TASK_EXTRACTION_MAX_DAYS)


def cutoff_date(tier: str, *, today: date | None = None, days: int | None = None) -> date:
    """Ngày sớm nhất còn nằm trong phạm vi. Thư nhận ĐÚNG ngày này vẫn được tính.

    `today` cho phép test cố định mốc thời gian — không có nó thì mọi test biên
    đều phụ thuộc vào ngày chạy, tức là hôm nay xanh mai đỏ.
    """
    hom_nay = today or date.today()
    return hom_nay - timedelta(days=days if days is not None else scan_days(tier))


def is_within_scope(
    received_at: datetime | date | None,
    tier: str,
    *,
    today: date | None = None,
    days: int | None = None,
) -> bool:
    """Thư này có nằm trong phạm vi AI được quét không?

    Biên là **bao gồm**: thư nhận đúng `scan_days` ngày trước vẫn tính là trong phạm vi,
    thư nhận sớm hơn một ngày thì không. Đây chính là chỗ dễ lệch một đơn vị nhất, nên
    nó được tách thành một hàm thuần để test đóng đinh được cả hai phía của biên.

    Thư không có ngày nhận → coi như TRONG phạm vi. Thà xử lý thừa một thư còn hơn
    im lặng bỏ sót thư người dùng đang hỏi tới.
    """
    if received_at is None:
        return True
    ngay = received_at.date() if isinstance(received_at, datetime) else received_at
    return ngay >= cutoff_date(tier, today=today, days=days)


def cutoff_iso(tier: str, *, today: date | None = None, days: int | None = None) -> str:
    """Mốc cắt dạng 'YYYY-MM-DD' — đây là thứ truyền xuống tầng service.

    Cố tình truyền NGÀY trung lập chứ không truyền cú pháp của Gmail hay Graph: tầng
    trên không cần biết người dùng đang dùng hộp thư nào, còn mỗi service tự dịch sang
    cú pháp của mình. Nhét cú pháp Gmail vào tầng tool là bước đầu để Outlook âm thầm
    quét sai phạm vi.
    """
    return cutoff_date(tier, today=today, days=days).isoformat()


def gmail_after_clause(tier: str, *, today: date | None = None, days: int | None = None) -> str:
    """Toán tử Gmail cho cửa sổ này, vd `after:2026/05/09`.

    Dùng `after:` (theo NGÀY) chứ không dùng `newer_than:90d` (theo 24 giờ): mốc theo
    ngày thì tất định và khớp đúng định nghĩa biên ở `is_within_scope`, còn mốc theo giờ
    thì cùng một lá thư có thể trong phạm vi lúc sáng và ngoài phạm vi lúc tối.
    """
    return f"after:{cutoff_date(tier, today=today, days=days):%Y/%m/%d}"


def graph_filter_clause(tier: str, *, today: date | None = None, days: int | None = None) -> str:
    """Mệnh đề $filter của Microsoft Graph cho cùng cửa sổ đó."""
    moc = datetime.combine(
        cutoff_date(tier, today=today, days=days),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    return f"receivedDateTime ge {moc:%Y-%m-%dT%H:%M:%SZ}"


def scope_note(tier: str) -> str:
    """Câu báo cho người dùng khi yêu cầu của họ vượt quá cửa sổ (FR-02.7).

    Nói rõ giới hạn là của GÓI chứ không phải hộp thư trống, và chỉ luôn cách gỡ —
    người dùng bị từ chối mà không biết vì sao thì sẽ nghĩ sản phẩm hỏng.
    """
    n = scan_days(tier)
    nhan = (TIERS.get(tier) or TIERS[DEFAULT_TIER])["label"]
    return (
        f"Gói {nhan} cho mình quét {n} ngày thư gần nhất. "
        f"Thư cũ hơn {n} ngày vẫn nằm trong hộp thư của bạn và vẫn tìm được bằng từ khoá — "
        f"chỉ là mình chưa đọc tới. Nâng gói để mở rộng khoảng này."
    )
