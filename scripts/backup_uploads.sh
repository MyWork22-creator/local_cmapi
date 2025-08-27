#!/bin/bash
set -e

DATE=$(date +%F_%H-%M-%S)
BACKUP_DIR=/backups/uploads
SOURCE_DIR=/app/static

mkdir -p "$BACKUP_DIR"

# Create timestamped backup directory
BACKUP_PATH="$BACKUP_DIR/uploads_${DATE}"

# Copy static files with rsync (if available) or cp
if command -v rsync &> /dev/null; then
    rsync -av --delete "$SOURCE_DIR/" "$BACKUP_PATH/"
else
    cp -r "$SOURCE_DIR" "$BACKUP_PATH"
fi

# Create compressed archive
tar -czf "${BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "uploads_${DATE}"
rm -rf "$BACKUP_PATH"

# Keep only last 30 days of upload backups
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -type f -mtime +30 -delete

echo "✅ Uploads backup done: ${BACKUP_PATH}.tar.gz"
