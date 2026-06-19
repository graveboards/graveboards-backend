#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<EOF
CREATE DATABASE graveboards_dev;
CREATE DATABASE graveboards_prod;
CREATE DATABASE graveboards_test;
EOF
