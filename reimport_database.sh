#!/usr/bin/env bash
set -e

DATABASE=hawkentracker

echo Dropping database
dropdb --if-exists ${DATABASE}
echo Importing live database
gunzip -ck instance/${DATABASE}.sql.gz | psql postgres
echo Vacuuming database
psql -c "VACUUM ANALYZE" ${DATABASE}
