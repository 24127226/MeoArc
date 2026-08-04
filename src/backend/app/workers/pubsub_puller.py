# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/workers/pubsub_puller.py — WORKER KÉO (PULL) Pub/Sub            ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Nhận Gmail Push mà KHÔNG cần URL public / ngrok / webhook mở ra     ║
# ║ Internet. Luồng:                                                    ║
# ║   Gmail đổi → publish lên topic → subscription PULL ← worker này    ║
# ║   tự KÉO thông báo về → sync_service.handle_pubsub → incremental.   ║
# ║                                                                    ║
# ║ CHẠY:  uv run python -m app.workers.pubsub_puller                   ║
# ║ CẦN:   uv add google-cloud-pubsub                                  ║
# ║        + xác thực: gcloud auth application-default login            ║
# ║          (hoặc GOOGLE_APPLICATION_CREDENTIALS trỏ tới key SA)       ║
# ║        + GMAIL_PUBSUB_PULL_SUBSCRIPTION trong .env                  ║
# ║        + đã gọi POST /gmail/watch để Gmail bắt đầu publish.         ║
# ╚══════════════════════════════════════════════════════════════════╝

import json
import logging
import threading
import time

from app.core.config import settings
from app.core.db import SessionLocal
from app.services import sync_service

logger = logging.getLogger("app.pubsub")


def _renew_loop() -> None:
    """Thread nền: gia hạn Gmail watch NGAY khi worker chạy, rồi lặp mỗi 24h → watch không
    bao giờ hết hạn chừng nào worker còn chạy (khỏi phải bấm /gmail/watch mỗi 7 ngày)."""
    while True:
        db = SessionLocal()
        try:
            n = sync_service.renew_watches(db)
            if n:
                logger.info("Đã gia hạn watch cho %d hộp thư", n)
        except Exception as exc:
            logger.warning("Gia hạn watch lỗi: %s", exc)
        finally:
            db.close()
        time.sleep(24 * 3600)   # mỗi ngày


def _handle(message) -> None:
    """1 thông báo Pub/Sub: data = JSON {emailAddress, historyId} của Gmail → đồng bộ hộp thư đó.
    LUÔN ack (kể cả lỗi) để Pub/Sub khỏi gửi lại mãi 1 message hỏng; sync lỗi đã tự log riêng."""
    db = SessionLocal()
    try:
        payload = json.loads(message.data.decode("utf-8"))
        email = payload.get("emailAddress")
        if email:
            n = sync_service.handle_pubsub(db, email)
            logger.info("Pull sync %s: %d thư", email, n)
    except Exception as exc:
        logger.warning("Pull message lỗi (bỏ qua): %s", exc)
    finally:
        db.close()
        message.ack()


def main() -> None:
    sub = settings.gmail_pubsub_pull_subscription
    if not sub:
        raise SystemExit(
            "Chưa đặt GMAIL_PUBSUB_PULL_SUBSCRIPTION trong .env "
            "(vd projects/<PROJECT_ID>/subscriptions/gmail-pull-sub)."
        )
    try:
        from google.cloud import pubsub_v1
    except ImportError:
        raise SystemExit("Thiếu thư viện Pub/Sub. Chạy:  uv add google-cloud-pubsub")

    # Thread tự gia hạn watch mỗi ngày (daemon → tắt cùng worker).
    threading.Thread(target=_renew_loop, daemon=True).start()

    subscriber = pubsub_v1.SubscriberClient()
    future = subscriber.subscribe(sub, callback=_handle)
    print(f"[pubsub_puller] Đang lắng nghe {sub} … (tự gia hạn watch mỗi ngày; Ctrl+C để dừng)")
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()
        future.result()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
