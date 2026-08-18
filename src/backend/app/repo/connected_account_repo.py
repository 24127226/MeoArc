# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/repo/connected_account_repo.py — kết nối hộp thư (v6 §7)      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Một người nối được NHIỀU hộp thư (FR-01.2), và kết nối sống lâu    ║
# ║ hơn phiên đăng nhập — đăng xuất rồi vào lại không phải cấp quyền   ║
# ║ lại từ đầu.                                                       ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.connected_account import (
    ACTIVE,
    REVOKED,
    ConnectedAccount,
    ConnectedAccountScope,
    GmailAccount,
    OutlookAccount,
)

_MS = "microsoft"


def _bang_con(provider: str):
    return OutlookAccount if provider == _MS else GmailAccount


def upsert(db: Session, *, user_id: int, provider: str, provider_user_id: str,
           email_address: str = "", access_token: str | None = None,
           refresh_token: str | None = None, token_expiry: datetime | None = None,
           scopes: list[str] | None = None) -> ConnectedAccount:
    """Nối hộp thư, hoặc cập nhật nếu đã nối rồi.

    Khớp theo `(provider, provider_user_id)` chứ không theo user: cùng một hộp thư
    Gmail chỉ được tồn tại MỘT bản ghi. Nối hai lần mà tạo hai bản ghi thì đồng bộ
    chạy hai lượt và thư về gấp đôi.

    `refresh_token` chỉ ghi đè khi lần này thật sự nhận được. Google không trả nó ở
    lần cấp quyền lại — ghi đè vô điều kiện là xoá mất cái đang dùng được, và người
    dùng bị đá ra ngay khi access token hết hạn.
    """
    acc = (db.query(ConnectedAccount)
           .filter(ConnectedAccount.provider == provider,
                   ConnectedAccount.provider_user_id == provider_user_id)
           .first())
    if acc is None:
        acc = ConnectedAccount(
            account_id=uuid.uuid4().hex, user_id=user_id, provider=provider,
            provider_user_id=provider_user_id,
        )
        db.add(acc)
        db.flush()
        db.add(_bang_con(provider)(account_id=acc.account_id))

    acc.user_id = user_id
    acc.email_address = email_address or acc.email_address
    acc.status = ACTIVE                       # nối lại sau khi thu hồi → sống lại
    if access_token:
        acc.access_token = access_token
    if refresh_token:
        acc.refresh_token = refresh_token
    if token_expiry:
        acc.token_expiry = token_expiry

    if scopes:
        db.query(ConnectedAccountScope).filter(
            ConnectedAccountScope.account_id == acc.account_id).delete()
        for sc in dict.fromkeys(scopes):
            db.add(ConnectedAccountScope(account_id=acc.account_id, scope=sc))

    db.commit()
    db.refresh(acc)
    return acc


def list_for_user(db: Session, user_id: int, *, chi_dang_hoat_dong: bool = True):
    q = db.query(ConnectedAccount).filter(ConnectedAccount.user_id == user_id)
    if chi_dang_hoat_dong:
        q = q.filter(ConnectedAccount.status == ACTIVE)
    return q.order_by(ConnectedAccount.created_at).all()


def get_owned(db: Session, account_id: str, user_id: int) -> ConnectedAccount | None:
    a = db.get(ConnectedAccount, account_id)
    return a if a is not None and a.user_id == user_id else None


def primary_for(db: Session, user_id: int, provider: str | None = None) -> ConnectedAccount | None:
    """Hộp thư dùng mặc định cho người này (kết nối còn hoạt động, cũ nhất).

    Chọn CŨ NHẤT chứ không phải mới nhất: nối thêm hộp thư phụ không được lặng lẽ
    đổi hộp thư chính mà người dùng vẫn đang dùng hằng ngày.
    """
    q = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id, ConnectedAccount.status == ACTIVE)
    if provider:
        q = q.filter(ConnectedAccount.provider == provider)
    return q.order_by(ConnectedAccount.created_at).first()


def revoke(db: Session, acc: ConnectedAccount) -> None:
    """Thu hồi quyền (UC002): xoá token, đổi trạng thái — KHÔNG xoá bản ghi.

    Giữ bản ghi để nhật ký cũ vẫn còn chỗ trỏ về. Xoá đi là mất luôn dấu vết ai đã
    làm gì trên hộp thư nào.
    """
    acc.access_token = None
    acc.refresh_token = None
    acc.token_expiry = None
    acc.status = REVOKED
    db.commit()


def update_access_token(db: Session, acc: ConnectedAccount, token: str,
                        expires_at: datetime | None) -> None:
    acc.access_token = token
    acc.token_expiry = expires_at
    db.commit()


def sync_state(db: Session, acc: ConnectedAccount):
    """Bản ghi con giữ con trỏ đồng bộ của nhà cung cấp tương ứng."""
    row = db.get(_bang_con(acc.provider), acc.account_id)
    if row is None:                            # bản ghi cũ thiếu bảng con → dựng bù
        row = _bang_con(acc.provider)(account_id=acc.account_id)
        db.add(row)
        db.commit()
    return row


def scopes_of(db: Session, account_id: str) -> list[str]:
    return [r.scope for r in db.query(ConnectedAccountScope)
            .filter(ConnectedAccountScope.account_id == account_id).all()]


def to_dict(acc: ConnectedAccount) -> dict:
    """Khuôn cho FE. KHÔNG phơi token ra ngoài."""
    return {
        "accountId": acc.account_id,
        "provider": acc.provider,
        "emailAddress": acc.email_address,
        "status": acc.status,
        "createdAt": acc.created_at.isoformat() if acc.created_at else None,
    }
