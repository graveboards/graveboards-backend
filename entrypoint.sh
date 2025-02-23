#!/bin/sh
set -e

if [ "$ENV" = "dev" ]; then
  echo "Running in development mode..."
  DB_HOST="graveboards-postgresql-dev"
  REDIS_HOST="graveboards-redis-dev"
else
  echo "Running in production mode..."
  DB_HOST="graveboards-postgresql-prod"
  REDIS_HOST="graveboards-redis-prod"
fi

./wait-for-it.sh $DB_HOST:5432 --timeout=30 --strict -- echo "PostgreSQL is up."
./wait-for-it.sh $REDIS_HOST:6379 --timeout=30 --strict -- echo "Redis is up."

python setup.py
exec "$@"

