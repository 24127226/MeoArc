# ╔══════════════════════════════════════════════════════════════════╗
# ║ app/api/spa.py — backend phục vụ luôn frontend đã build (tuỳ chọn) ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Vì sao có thứ này, trong khi frontend vẫn đặt ở Vercel:            ║
# ║                                                                    ║
# ║  Tách hai nơi thì FE và BE nằm ở hai TÊN MIỀN khác nhau, kéo theo   ║
# ║  hai lớp phức tạp: CORS phải khai đúng origin, và cookie phiên      ║
# ║  phải mang SameSite=None; Secure. Sai bất kỳ cái nào cũng cho ra    ║
# ║  cùng một triệu chứng — đăng nhập xong mọi lệnh gọi trả 401 —       ║
# ║  và nhìn từ ngoài giống hệt lỗi xác thực.                          ║
# ║                                                                    ║
# ║  Phục vụ từ CÙNG một tiến trình thì hai lớp đó biến mất: cùng      ║
# ║  origin nên không có gọi chéo, cookie mặc định chạy bình thường.    ║
# ║                                                                    ║
# ║ KHÔNG bắt buộc: không có thư mục build thì hàm này lặng lẽ bỏ qua,  ║
# ║ backend chạy y như trước. Nhờ vậy Vercel vẫn là đường chính, còn    ║
# ║ đây là đường dự phòng khi cần một URL duy nhất (chạy sau tunnel,    ║
# ║ demo ngoại tuyến, hoặc gói cả hệ vào một dịch vụ).                 ║
# ╚══════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("app.spa")

# Tiền tố của API. Đường dẫn bắt đầu bằng một trong số này mà không khớp route nào
# thì phải trả 404 JSON — KHÔNG được trả trang HTML.
#
# Vì sao cần danh sách này: bộ bắt-tất-cả bên dưới tồn tại để React Router xử lý được
# các đường dẫn sâu (/app, /settings) — trình duyệt hỏi thẳng server những đường đó và
# server phải trả index.html. Nhưng nếu bắt tất cả thật sự thì một lệnh gọi API hỏng
# (sai phương thức, hoặc route bị xoá khi tái cấu trúc) sẽ nhận về HTML kèm mã 200;
# client `fetch` cố đọc JSON rồi ngã ở chỗ khác hẳn, và người sửa lỗi đi nhầm hướng.
#
# GIỚI HẠN đã biết: chỉ chặn được tiền tố VIẾT ĐÚNG. Gõ nhầm hẳn tên (/emials) thì với
# server nó không khác gì một đường dẫn của React Router, nên vẫn trả index.html. Đây là
# hành vi chung của mọi nơi phục vụ SPA — Vercel và Netlify cũng vậy. Muốn triệt để thì
# phải gom toàn bộ API dưới một tiền tố riêng (/api/...), việc đó đổi cả hợp đồng API
# lẫn tài liệu nên không làm ở đây.
API_PREFIXES = (
    "auth", "me", "emails", "agent", "confirmations", "notifications",
    "subscription", "audit", "contacts", "uploads", "sync", "gmail",
    "admin", "dev", "health", "metrics", "docs", "redoc", "openapi.json",
)


def _tim_thu_muc_build(duong_dan: str | None) -> Path | None:
    """Tìm thư mục frontend đã build. Trả None nếu chưa build.

    Khai rõ đường dẫn thì CHỈ dùng đúng đường đó — không âm thầm rơi về chỗ khác.
    Người khai `FRONTEND_DIST` là đang nói "phục vụ từ đây"; lặng lẽ phục vụ một
    thư mục khác khi đường dẫn sai thì bản build cũ vẫn chạy ngon lành và không ai
    hiểu vì sao sửa giao diện mãi mà không thấy đổi.
    """
    if duong_dan:
        p = Path(duong_dan)
        if (p / "index.html").is_file():
            return p
        logger.warning("FRONTEND_DIST trỏ tới %s nhưng không thấy index.html ở đó.", p)
        return None

    # Không khai gì → tự dò theo layout quen thuộc.
    ung_vien = [
        # Layout của repo này: src/backend/app/api/spa.py → src/frontend/dist
        Path(__file__).resolve().parents[3] / "frontend" / "dist",
        # Trong ảnh Docker, frontend thường được chép vào cạnh code backend
        Path(__file__).resolve().parents[2] / "static",
    ]
    for p in ung_vien:
        if (p / "index.html").is_file():
            return p
    return None


def gan_frontend(app: FastAPI, duong_dan: str | None = None) -> bool:
    """Gắn frontend đã build vào app. Trả True nếu có gắn.

    PHẢI gọi SAU khi mọi route API đã khai báo: Starlette duyệt route theo đúng thứ tự
    đăng ký, nên bộ bắt-tất-cả đăng ký trước sẽ nuốt sạch API.
    """
    dist = _tim_thu_muc_build(duong_dan)
    if dist is None:
        logger.info("Không thấy frontend đã build — chỉ chạy API. "
                    "Chạy `npm run build` trong src/frontend nếu muốn gộp.")
        return False

    # ── CACHE: hai loại tệp, hai chính sách ngược nhau ────────────────────────
    #
    # Trước đây không đặt Cache-Control cho tệp nào cả. Nghe thì tưởng "không đặt =
    # không cache", nhưng đặc tả HTTP quy định ngược lại: thiếu chỉ thị thì trình
    # duyệt được phép TỰ SUY ĐOÁN thời hạn (heuristic caching), thường lấy khoảng
    # 10% quãng thời gian từ Last-Modified. Hệ quả là sau khi triển khai bản mới,
    # người dùng cũ mở trang vẫn thấy y nguyên bản cũ và không cách nào biết —
    # trình duyệt không thèm hỏi lại server.
    #
    # Vite đặt mã băm nội dung vào TÊN tệp trong dist/assets, nên mỗi lần sửa code
    # là ra tên khác. Nhờ vậy có thể chia dứt khoát:
    #   • /assets/*  — tên đã đổi theo nội dung → cache vĩnh viễn, immutable.
    #   • index.html — tên KHÔNG đổi, lại là nơi ghi tên các tệp assets kia →
    #     bắt buộc hỏi lại server mỗi lần. Có ETag nên lần hỏi lại thường chỉ tốn
    #     một phản hồi 304 rỗng, gần như không tốn băng thông.
    #
    # Tóm lại: index.html là bản đồ, assets là địa điểm. Cache bản đồ cũ thì mọi
    # địa điểm mới đều vô hình.
    CACHE_BAT_BIEN = "public, max-age=31536000, immutable"
    CACHE_LUON_HOI_LAI = "no-cache, must-revalidate"

    class TaiNguyenBam(StaticFiles):
        """StaticFiles nhưng gắn thêm Cache-Control vĩnh viễn cho tệp có mã băm."""

        def file_response(self, *args, **kwargs):  # type: ignore[override]
            resp = super().file_response(*args, **kwargs)
            resp.headers["Cache-Control"] = CACHE_BAT_BIEN
            return resp

    thu_muc_assets = dist / "assets"
    if thu_muc_assets.is_dir():
        app.mount("/assets", TaiNguyenBam(directory=str(thu_muc_assets)), name="assets")

    index = dist / "index.html"

    # Go route "/" cu (tra JSON "backend dang chay") de bo bat-tat-ca ben duoi nhan
    # luon dia chi goc. Starlette duyet route theo thu tu dang ky nen route "/" khai
    # trong app.py se thang neu khong go ra.
    #
    # Vi sao dang lam: nguoi ta gui link TRAN cho nhau, khong ai gui kem "/app".
    # Mo dia chi goc ma thay mot cuc JSON thi tuong san pham hong. Cau bao "backend
    # dang chay" chi co ich khi CHUA gop frontend — luc do van con nguyen.
    app.router.routes = [
        r for r in app.router.routes
        if not (getattr(r, "path", None) == "/" and "GET" in getattr(r, "methods", set()))
    ]

    @app.get("/{duong_dan_day_du:path}", include_in_schema=False)
    async def phuc_vu_spa(duong_dan_day_du: str):
        goc = duong_dan_day_du.split("/", 1)[0].lower()
        if goc in API_PREFIXES:
            # Đường dẫn API không khớp route nào → 404 thật, không trả HTML.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không có endpoint này.")

        # Tệp tĩnh nằm ở gốc dist (favicon, robots.txt, thư mục landing…).
        # resolve() rồi kiểm nằm trong dist: chặn đường dẫn kiểu ../../ đọc trộm tệp
        # ngoài thư mục build — lỗ hổng path traversal kinh điển.
        if duong_dan_day_du:
            ung_vien = (dist / duong_dan_day_du).resolve()
            if ung_vien.is_file() and ung_vien.is_relative_to(dist.resolve()):
                # Tệp ở gốc dist (favicon, video, ảnh landing…) KHÔNG có mã băm trong
                # tên, nên chỉ cache một giờ rồi hỏi lại — đủ để đỡ tải lặp, mà thay
                # ảnh xong không phải chờ hết một năm mới thấy.
                return FileResponse(ung_vien, headers={"Cache-Control": "public, max-age=3600"})

        # Còn lại là đường dẫn của React Router (/app, /settings…) → trả index.html
        # để trình duyệt nạp ứng dụng rồi tự định tuyến bên trong.
        return FileResponse(index, headers={"Cache-Control": CACHE_LUON_HOI_LAI})

    logger.info("Đang phục vụ frontend từ %s", dist)
    return True
