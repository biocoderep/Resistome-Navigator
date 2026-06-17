#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# Default to docker-compose environment variables if not set
PGHOST=${PGHOST:-postgres}
PGPORT=${PGPORT:-5432}
PGDATABASE=${POSTGRES_DB:-amrdb}
PGUSER=${POSTGRES_USER:-amruser}
export PGPASSWORD=${POSTGRES_PASSWORD:-amrpass}

BACKUP_DIR="/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_FILE="$BACKUP_DIR/${PGDATABASE}_backup_$TIMESTAMP.tmp"
BACKUP_FILE="$BACKUP_DIR/${PGDATABASE}_backup_$TIMESTAMP.dump"

echo "[$(date -u)] Starting database backup to temporary file $TEMP_FILE..."
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -F c -f "$TEMP_FILE"

echo "[$(date -u)] Validating dump file..."
if ! pg_restore -l "$TEMP_FILE" >/dev/null 2>&1; then
    echo "ERROR: Dump validation failed. The backup may be corrupted." >&2
    rm -f "$TEMP_FILE"
    exit 1
fi

if [ ! -s "$TEMP_FILE" ]; then
    echo "ERROR: Dump file is empty." >&2
    rm -f "$TEMP_FILE"
    exit 1
fi

mv "$TEMP_FILE" "$BACKUP_FILE"
echo "[$(date -u)] Backup completed and validated successfully: $BACKUP_FILE"

# Retention policy: keep last 7 backups, delete the rest
echo "Cleaning up old backups (keeping the latest 7)..."
shopt -s nullglob
dumps=("$BACKUP_DIR"/*.dump)
if [ ${#dumps[@]} -gt 7 ]; then
    printf "%s\n" "${dumps[@]}" | sort -r | tail -n +8 | xargs -r rm -f
fi
shopt -u nullglob
echo "Cleanup complete."
