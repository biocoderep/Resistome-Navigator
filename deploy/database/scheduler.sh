#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -euo pipefail

echo "[$(date -u)] Initializing backup scheduler..."

# Run an initial backup immediately upon startup
echo "[$(date -u)] Running initial startup backup..."
bash /scripts/backup.sh && touch /tmp/backup_success || echo "[$(date -u)] ERROR: Startup backup failed. Continuing to schedule..." >&2

echo "[$(date -u)] Entering daily backup schedule loop."
while true; do
  # Calculate exact seconds until the next 02:00 AM (server time)
  now=$(date +%s)
  today_2am=$(date -d "02:00:00" +%s)
  
  if [ "$now" -lt "$today_2am" ]; then
    # If it is currently before 2 AM, target 2 AM today
    sleep_time=$((today_2am - now))
  else
    # If it is already past 2 AM, target 2 AM tomorrow
    tomorrow_2am=$(date -d "tomorrow 02:00:00" +%s)
    sleep_time=$((tomorrow_2am - now))
  fi
  
  hours=$((sleep_time / 3600))
  minutes=$(((sleep_time % 3600) / 60))
  
  echo "[$(date -u)] Next scheduled backup is in $hours hours and $minutes minutes. Sleeping..."
  sleep $sleep_time
  
  echo "[$(date -u)] Executing scheduled backup..."
  bash /scripts/backup.sh && touch /tmp/backup_success || echo "[$(date -u)] ERROR: Scheduled backup failed. Will retry next cycle." >&2
done
