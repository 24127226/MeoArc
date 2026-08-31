#!/usr/bin/env python
# ╔══════════════════════════════════════════════════════════════════╗
# ║ scripts/backup_db.py — SAO LƯU & KHÔI PHỤC DATABASE               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║ Bản sao lưu CHƯA TỪNG KHÔI PHỤC THỬ thì coi như chưa có. Rất nhiều  ║
# ║ đội chỉ phát hiện file sao lưu hỏng đúng lúc cần tới nó nhất.       ║
# ║ Vì vậy script này có sẵn lệnh `verify`: khôi phục vào một database  ║
# ║ tạm rồi đối chiếu số dòng — chứng minh bản sao dùng được thật.      ║
# ║                                                                    ║
# ║   python scripts/backup_db.py create      # tạo bản sao lưu        ║
# ║   python scripts/backup_db.py list        # xem các bản đang có     ║
# ║   python scripts/backup_db.py verify      # KHÔI PHỤC THỬ bản mới nhất ║
# ║   python scripts/backup_db.py restore F   # khôi phục thật từ file F║
# ║                                                                    ║
# ║ Cần `pg_dump`/`pg_restore` (đi kèm PostgreSQL) nằm trong PATH.      ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", Path(__file__).resolve().parents[1] / "backups"))
GIU_LAI = int(os.getenv("BACKUP_KEEP", "14"))  # giữ N bản gần nhất, xoá dần bản cũ


def _thong_tin_ket_noi() -> dict:
    u = urlparse(settings.database_url.replace("postgresql+psycopg://", "postgresql://"))
    return {
        "host": u.hostname or "localhost",
        "port": str(u.port or 5432),
        "user": u.username or "postgres",
        "password": u.password or "",
        "db": (u.path or "/").lstrip("/"),
    }


def _env_pg(cfg: dict) -> dict:
    env = dict(os.environ)
    if cfg["password"]:
        env["PGPASSWORD"] = cfg["password"]  # truyền qua biến môi trường, không đưa vào dòng lệnh
    return env


def _can_lenh(ten: str) -> str:
    duong_dan = shutil.which(ten)
    if not duong_dan:
        print(f"KHONG TIM THAY '{ten}'. Cai PostgreSQL client hoac them vao PATH.")
        sys.exit(2)
    return duong_dan


def create() -> Path:
    cfg = _thong_tin_ket_noi()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ten = f"meoarc_{datetime.now():%Y%m%d_%H%M%S}.dump"
    dich = BACKUP_DIR / ten

    # -Fc = định dạng nén của Postgres, khôi phục chọn lọc được từng bảng
    cmd = [_can_lenh("pg_dump"), "-h", cfg["host"], "-p", cfg["port"],
           "-U", cfg["user"], "-d", cfg["db"], "-Fc", "-f", str(dich)]
    r = subprocess.run(cmd, env=_env_pg(cfg), capture_output=True, text=True)
    if r.returncode != 0:
        print("SAO LUU THAT BAI:", r.stderr[:400])
        sys.exit(1)

    mb = dich.stat().st_size / 1024 / 1024
    print(f"Da tao ban sao luu: {dich}  ({mb:.2f} MB)")
    _don_ban_cu()
    return dich


def _don_ban_cu() -> None:
    """Giữ N bản gần nhất. Không dọn thì ổ đĩa đầy — và ổ đầy thì lần sao lưu
    kế tiếp thất bại đúng lúc ta cần nó nhất."""
    files = sorted(BACKUP_DIR.glob("meoarc_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    for cu in files[GIU_LAI:]:
        cu.unlink()
        print(f"  da xoa ban cu: {cu.name}")


def danh_sach() -> list[Path]:
    files = sorted(BACKUP_DIR.glob("meoarc_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"Chua co ban sao luu nao trong {BACKUP_DIR}")
    for p in files:
        mb = p.stat().st_size / 1024 / 1024
        khi = datetime.fromtimestamp(p.stat().st_mtime)
        print(f"  {p.name:38s} {mb:7.2f} MB   {khi:%Y-%m-%d %H:%M}")
    return files


def verify(duong_dan: Path | None = None) -> None:
    """Khôi phục bản sao vào database TẠM rồi đối chiếu số dòng với database thật.

    Đây là bước hay bị bỏ qua nhất. Một file .dump nằm im trên ổ đĩa không chứng
    minh được điều gì cho tới khi có người khôi phục thử.
    """
    import psycopg
    from psycopg import sql

    files = sorted(BACKUP_DIR.glob("meoarc_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    ban = duong_dan or (files[0] if files else None)
    if not ban:
        print("Khong co ban sao luu de kiem chung.")
        sys.exit(1)

    cfg = _thong_tin_ket_noi()
    tmp_db = "meoarc_verify_tmp"
    admin = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/postgres"

    print(f"Kiem chung ban: {ban.name}")
    with psycopg.connect(admin, autocommit=True) as cn, cn.cursor() as cur:
        cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", (tmp_db,))
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(tmp_db)))
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(tmp_db)))

    r = subprocess.run(
        [_can_lenh("pg_restore"), "-h", cfg["host"], "-p", cfg["port"], "-U", cfg["user"],
         "-d", tmp_db, "--no-owner", "--no-privileges", str(ban)],
        env=_env_pg(cfg), capture_output=True, text=True,
    )
    # pg_restore hay cảnh báo lặt vặt (quyền, owner) mà vẫn khôi phục đủ → chỉ dừng khi thật sự lỗi
    if r.returncode != 0 and "error" in (r.stderr or "").lower():
        print("KHOI PHUC THAT BAI:", r.stderr[:500])
        sys.exit(1)

    BANG = ["users", "emails", "audit_logs", "notifications", "sessions", "subscriptions"]
    that = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['db']}"
    tam = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{tmp_db}"

    def dem(url: str) -> dict:
        out = {}
        with psycopg.connect(url) as cn, cn.cursor() as cur:
            for t in BANG:
                try:
                    cur.execute(f"SELECT count(*) FROM {t}")
                    out[t] = cur.fetchone()[0]
                except Exception:
                    out[t] = None
        return out

    a, b = dem(that), dem(tam)
    print(f"\n  {'bang':16s} {'that':>8s} {'khoi phuc':>10s}")
    lech = []
    for t in BANG:
        dau = "OK" if a[t] == b[t] else "LECH"
        if a[t] != b[t]:
            lech.append(t)
        print(f"  {t:16s} {str(a[t]):>8s} {str(b[t]):>10s}  {dau}")

    with psycopg.connect(admin, autocommit=True) as cn, cn.cursor() as cur:
        cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", (tmp_db,))
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(tmp_db)))

    if lech:
        print(f"\nBAN SAO LUU KHONG DUNG DUOC — lech o: {lech}")
        sys.exit(1)
    print("\nBan sao luu KHOI PHUC DUOC va du du lieu.")


def restore(duong_dan: str) -> None:
    """Khôi phục THẬT — ghi đè database đang chạy. Hỏi xác nhận trước."""
    ban = Path(duong_dan)
    if not ban.exists():
        print(f"Khong thay file: {ban}")
        sys.exit(1)
    cfg = _thong_tin_ket_noi()
    print(f"SAP GHI DE database '{cfg['db']}' bang {ban.name}")
    print("Go dung chu 'KHOI PHUC' de xac nhan: ", end="")
    if input().strip() != "KHOI PHUC":
        print("Da huy.")
        return
    r = subprocess.run(
        [_can_lenh("pg_restore"), "-h", cfg["host"], "-p", cfg["port"], "-U", cfg["user"],
         "-d", cfg["db"], "--clean", "--if-exists", "--no-owner", str(ban)],
        env=_env_pg(cfg), capture_output=True, text=True,
    )
    print(r.stderr[-400:] if r.returncode != 0 else "Khoi phuc xong.")


if __name__ == "__main__":
    lenh = sys.argv[1] if len(sys.argv) > 1 else "create"
    if lenh == "create":
        create()
    elif lenh == "list":
        danh_sach()
    elif lenh == "verify":
        verify(Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif lenh == "restore":
        if len(sys.argv) < 3:
            print("Dung: python scripts/backup_db.py restore <duong-dan-file.dump>")
            sys.exit(1)
        restore(sys.argv[2])
    else:
        print(__doc__ or "Lenh: create | list | verify | restore <file>")
