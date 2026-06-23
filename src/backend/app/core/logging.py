# app/core/logging.py
import logging
import logging.config
import logging.handlers
import uuid
from contextvars import ContextVar
from pathlib import Path

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class BelowWarningFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.WARNING


def set_request_id(request_id: str | None = None) -> str:
    rid = request_id or uuid.uuid4().hex[:8]
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get()


_config = {
    "version": 1,
    "disable_existing_loggers": False,

    "filters": {
        "below_warning": {"()": "app.core.logging.BelowWarningFilter"},
        "request_id":    {"()": "app.core.logging.RequestIdFilter"},
    },

    "formatters": {
        "simple": {
            "format": "[%(levelname)s|rid=%(request_id)s] %(message)s"
        },
        "detailed": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d|rid=%(request_id)s] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },

    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
            "filters": ["below_warning", "request_id"],
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stderr",
            "level": "WARNING",
            "filters": ["request_id"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 3,
            "encoding": "utf-8",
            "filters": ["request_id"],
        },
    },

    "root": {
        "level": "INFO",
        "handlers": ["stdout", "stderr", "file"],
    },

    "loggers": {
        "app": {"level": "DEBUG", "propagate": True},
        # Tắt noise từ thư viện ngoài
        "uvicorn.access": {"level": "WARNING", "propagate": False},
        "httpx":          {"level": "WARNING", "propagate": False},
    },
}


def setup_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.config.dictConfig(_config)