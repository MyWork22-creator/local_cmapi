#!/bin/bash
set -e

DATE=$(date +%F_%H-%M-%S)
BACKUP_DIR=/backups/mysql
DB_CONTAINER=cm-mysql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_ROOT_PASSWORD}

mkdir -p "$BACKUP_DIR"

docker exec -i "$DB_CONTAINER" \
  mysqldump -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "✅ DB backup done: $BACKUP_DIR/${DB_NAME}_${DATE}.sql"
