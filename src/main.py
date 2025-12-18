import os

from dynaconf import Dynaconf, Validator
import logging.config

try:
    settings = Dynaconf(
        envvar_prefix="FW",
        settings_files=[ "settings.yaml"],
        validators=[
            Validator("log_level", required=True, is_type_of=str,
                      is_in=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      default="INFO", apply_default_on_none=True),
            Validator("watch_dirs", required=True, is_type_of=list)
        ]
    )
except Exception as e:
    print(f"Failed to load configuration: {e}")
    exit(1)

print("Config:", settings.as_dict())

os.makedirs('log', exist_ok=True)
logging_conf = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'file': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'console': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': settings.log_level.upper(),
            'formatter': 'console',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'level': settings.log_level.upper(),
            'formatter': 'file',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/filewatcher.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': settings.log_level.upper(),
            'propagate': True
        }
    }
}

logging.config.dictConfig(logging_conf)
log = logging.getLogger(__name__)

from .ws_api import create_app
ctx = create_app(watch_dirs=settings.watch_dirs)
log.info("Starting background worker thread")
ctx["start_background_worker"]()
ctx["watcher"].start()

app = ctx["app"]