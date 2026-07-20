#!/bin/sh

set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${READONLY_DB_USER:?READONLY_DB_USER is required}"
: "${READONLY_DB_PASSWORD:?READONLY_DB_PASSWORD is required}"

echo "Configuring PostgreSQL read-only role: ${READONLY_DB_USER}"

psql \
    --username "${POSTGRES_USER}" \
    --dbname "${POSTGRES_DB}" \
    --set=ON_ERROR_STOP=1 \
    --set=readonly_user="${READONLY_DB_USER}" \
    --set=readonly_password="${READONLY_DB_PASSWORD}" <<'EOSQL'

SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
    :'readonly_user',
    :'readonly_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = :'readonly_user'
)
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
    :'readonly_user',
    :'readonly_password'
)
\gexec

SELECT format(
    'ALTER ROLE %I SET default_transaction_read_only = on',
    :'readonly_user'
)
\gexec

SELECT format(
    'GRANT CONNECT ON DATABASE %I TO %I',
    current_database(),
    :'readonly_user'
)
\gexec

SELECT format(
    'GRANT USAGE ON SCHEMA public TO %I',
    :'readonly_user'
)
\gexec

SELECT format(
    'REVOKE CREATE ON SCHEMA public FROM %I',
    :'readonly_user'
)
\gexec

SELECT format(
    'GRANT SELECT ON ALL TABLES IN SCHEMA public TO %I',
    :'readonly_user'
)
\gexec

SELECT format(
    'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO %I',
    :'readonly_user'
)
\gexec

EOSQL

echo "Read-only PostgreSQL role configured successfully."