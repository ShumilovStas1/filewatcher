# Filewatcher

Filewatcher is a Python-based server that monitors filesystem changes in specified directories and sends real-time notifications about these events via WebSockets. It’s designed for use cases where clients need instant updates on filesystem activity, such as file creation, modification, deletion, or movement.

## Features

- **Real-time Monitoring:** Uses [watchdog](https://github.com/gorakhargosh/watchdog) to track file and directory changes.
- **WebSocket API:** Broadcasts filesystem events to all connected clients using [python-socketio](https://python-socketio.readthedocs.io/).
- **Configurable:** Directories to watch and logging levels are controlled via a simple YAML config.
- **Multi-Directory Support:** Watch as many directories as you like, recursively.
- **Docker-ready:** Includes Dockerfile and docker-compose setup for easy deployment.

## Requirements

- Python 3.12+
- [Dynaconf](https://www.dynaconf.com/)
- [eventlet](http://eventlet.net/)
- [gunicorn](https://gunicorn.org/)
- [python-socketio](https://python-socketio.readthedocs.io/)
- [watchdog](https://github.com/gorakhargosh/watchdog)

Alternatively, run using Docker/Docker Compose.

## How to run

### Clone the repository

```bash
git clone https://github.com/ShumilovStas1/filewatcher.git
cd filewatcher
```

### Locally using uv

Install [`uv` tool](https://github.com/astral-sh/uv)

```bash
uv run gunicorn -w 1 --bind 0.0.0.0:5000 src.main:app 
```

### Using Docker

Build the container:

```bash
docker build -t filewatcher .
```

Run docker-compose:

```bash
docker-compose up
```

## Configuration

Modify the `settings.yaml` file to suit your needs:

```yaml
log_level: INFO
watch_dirs:
  - /your/directory/path1
  - /your/directory/path2
```

Or use environment variables to override settings:

```bash
export FW_WATCH_DIRS="['/your/directory/path1','/your/directory/path']"
export FW_LOG_LEVEL="DEBUG"
```

The server will start and listen on `http://127.0.0.1:5000` by default.

### Connecting clients

Use filewatcher-client repo https://github.com/ShumilovStas1/filewatcher-client for accessing the WebSocket API and receiving real-time filesystem event notifications.
