#!/usr/bin/env bash
set -e

DATABASE=hawkentracker
REMOTE_SSH_HOST=cobalt.mjolnirdev.com
REMOTE_SSH_USER=ashtools
REMOTE_USER=hwktracker

echo Dropping database
dropdb --if-exists ${DATABASE}
echo Importing live database
echo ${REMOTE_PASSWORD} | ssh ${REMOTE_SSH_USER}@${REMOTE_SSH_HOST} pg_dump -COvxZ 6 -U ${REMOTE_USER} ${DATABASE} | tee instance/${DATABASE}.sql.gz | gunzip | psql postgres
echo Vacuuming database
psql -c "VACUUM ANALYZE" ${DATABASE}
