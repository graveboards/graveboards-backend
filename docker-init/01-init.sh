#!/bin/bash
set -e

for db in graveboards_dev graveboards_prod graveboards_test; do
    exists=$(psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname = '$db'")
    if [ "$exists" != "1" ]; then
        psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" -c "CREATE DATABASE $db"
    fi
done
