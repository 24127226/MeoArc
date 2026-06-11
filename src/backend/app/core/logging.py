import logging
import logging.config
import logging.handlers
from pathlib import Path

class BelowWarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.WARNING

config = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
        "detailed": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    },

    "filters": {
        "below_warning": {
            "()": BelowWarningFilter
        }
    },

    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
            "filters": ["below_warning"]
        },

        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stderr",
            "level": "WARNING"
        },

        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 3,
            # "delay": False,
            "encoding": "utf-8"
        }
    },

    "root": {
        "level": "INFO",
        "handlers": [
            "stdout",
            "stderr",
            "file"
        ]
    },

    "loggers": {
        "src": {
            "level": "DEBUG",
            "propagate": True
        }
    }
}


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.config.dictConfig(config)
