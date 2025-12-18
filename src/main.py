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
    print("Config:", settings.as_dict())
except Exception as e:
    raise Exception(f"Failed to load configuration: {e}")

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

def validate_paths(path_list: list[str]) -> list[str]:
    valid = []
    for path in path_list:
        if path:
            if not os.path.isdir(path):
                log.warning(f"Path does not exist or is not a directory: {path}")
            elif not os.access(path, os.R_OK):
                log.warning(f"Path is not readable: {path}")
            else:
                valid.append(os.path.abspath(path))
    if not valid:
        log.critical("No valid directories to watch. Use settings.yaml or FW_WATCH_DIR env variable.")
        raise Exception("No valid directories to watch. Please specify valid directories via settings.yaml or FW_WATCH_DIR env variable Exiting.")
    return valid

valid_paths: list[str] = validate_paths(settings.watch_dirs)

from .ws_api import create_app
ctx = create_app(watch_dirs=valid_paths)
log.info("Starting background worker thread")
ctx["start_background_worker"]()
ctx["watcher"].start()

app = ctx["app"]

if __name__ == "__main__":
    import eventlet
    import eventlet.wsgi

    log.info("Starting local test server on http://127.0.0.1:5000")
    eventlet.wsgi.server(eventlet.listen(("127.0.0.1", 5000)), app)