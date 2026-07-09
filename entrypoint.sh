#!/bin/sh
set -e

if [ "$ENV" = "dev" ] && [ "$QUIET" != "true" ]; then
  echo "Running in development mode..."
elif [ "$QUIET" != "true" ]; then
  echo "Running in production mode..."
fi

wait_for() {
  if [ "$QUIET" = "true" ]; then
    ./wait-for-it.sh "$1" --timeout=30 --strict > /dev/null 2>&1
  else
    ./wait-for-it.sh "$1" --timeout=30 --strict
  fi
}

wait_for "$POSTGRESQL_HOST:$POSTGRESQL_PORT"
wait_for "$REDIS_HOST:$REDIS_PORT"

exec "$@"