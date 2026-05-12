#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

python - "$DB_HOST" "$DB_PORT" "$DB_WAIT_TIMEOUT" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
timeout_seconds = int(sys.argv[3])

deadline = time.time() + timeout_seconds

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Database is reachable at {host}:{port}")
            break
    except OSError:
        print(f"Waiting for database at {host}:{port}...")
        time.sleep(1)
else:
    raise SystemExit(f"Timed out waiting for database at {host}:{port}")
PY

exec "$@"
