#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "graveboards_dev" <<EOF
CREATE DATABASE graveboards_test;
EOF
