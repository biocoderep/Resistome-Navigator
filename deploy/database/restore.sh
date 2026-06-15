#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

if [ "$1" != "--force" ]; then
    echo "ERROR: Restore will overwrite the current database!"
    echo "You must provide the --force flag and the backup file path."
    echo "Usage: ./restore.sh --force /backups/amrdb_backup_TIMESTAMP.dump"
    exit 1
fi

BACKUP_FILE="$2"
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

PGHOST=${PGHOST:-postgres}
PGPORT=${PGPORT:-5432}
PGDATABASE=${POSTGRES_DB:-amrdb}
PGUSER=${POSTGRES_USER:-amruser}
export PGPASSWORD=${POSTGRES_PASSWORD:-amrpass}

echo "============================================================"
echo "WARNING: About to OVERWRITE database: $PGDATABASE — proceeding"
echo "============================================================"

echo "[$(date -u)] Restoring database from $BACKUP_FILE..."
# Clean (-c) and ignore errors if objects don't exist (--if-exists)
set +e
pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c --if-exists "$BACKUP_FILE"
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -ne 1 ]; then
    echo "[$(date -u)] ERROR: Restore failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
elif [ $EXIT_CODE -eq 1 ]; then
    echo "[$(date -u)] Restore completed with warnings (this is common for non-existent objects)."
else
    echo "[$(date -u)] Restore completed successfully."
fi
