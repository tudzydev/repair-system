#!/bin/sh
set -eu
if [ "${1:-}" = "gunicorn" ]; then
  python -m flask --app app:create_app init-production
fi
exec "$@"
