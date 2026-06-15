#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

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
mv "$TEMP_FILE" "$BACKUP_FILE"
echo "[$(date -u)] Backup completed successfully: $BACKUP_FILE"

# Retention policy: keep last 7 backups, delete the rest
echo "Cleaning up old backups (keeping the latest 7)..."
ls -1t "$BACKUP_DIR"/*.dump 2>/dev/null | tail -n +8 | xargs -r rm --
echo "Cleanup complete."
