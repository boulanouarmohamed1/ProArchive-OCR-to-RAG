#!/usr/bin/env sh
set -eu

if [ "${SKIP_DB_INIT:-0}" != "1" ]; then
  python -m app.database.init_db
fi
exec "$@"
