#!/bin/bash
set -e

DATE=$(date +%F_%H-%M-%S)
BACKUP_DIR=/backups
DB_CONTAINER=cm-mysql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_ROOT_PASSWORD}

echo "🚀 Starting full backup at $(date)"

# Create backup directories
mkdir -p "$BACKUP_DIR/mysql"
mkdir -p "$BACKUP_DIR/uploads"

# 1. Database Backup
echo "📊 Backing up database..."
docker exec -i "$DB_CONTAINER" \
  mysqldump -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_DIR/mysql/${DB_NAME}_${DATE}.sql"

# 2. Uploads Backup
echo "📁 Backing up uploads..."
SOURCE_DIR=/app/static
UPLOAD_BACKUP_PATH="$BACKUP_DIR/uploads/uploads_${DATE}"

if command -v rsync &> /dev/null; then
    rsync -av --delete "$SOURCE_DIR/" "$UPLOAD_BACKUP_PATH/"
else
    cp -r "$SOURCE_DIR" "$UPLOAD_BACKUP_PATH"
fi

# Create compressed archive for uploads
tar -czf "${UPLOAD_BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR/uploads" "uploads_${DATE}"
rm -rf "$UPLOAD_BACKUP_PATH"

# 3. Create full backup archive
echo "📦 Creating full backup archive..."
FULL_BACKUP_NAME="crm_full_backup_${DATE}"
FULL_BACKUP_PATH="$BACKUP_DIR/${FULL_BACKUP_NAME}"

mkdir -p "$FULL_BACKUP_PATH"
cp "$BACKUP_DIR/mysql/${DB_NAME}_${DATE}.sql" "$FULL_BACKUP_PATH/"
cp "${UPLOAD_BACKUP_PATH}.tar.gz" "$FULL_BACKUP_PATH/"

# Create final compressed archive
tar -czf "${FULL_BACKUP_PATH}.tar.gz" -C "$BACKUP_DIR" "$FULL_BACKUP_NAME"
rm -rf "$FULL_BACKUP_PATH"

# 4. Cleanup old backups
echo "🧹 Cleaning up old backups..."
# Keep last 7 days of database backups
find "$BACKUP_DIR/mysql" -type f -mtime +7 -delete

# Keep last 30 days of upload backups
find "$BACKUP_DIR/uploads" -name "uploads_*.tar.gz" -type f -mtime +30 -delete

# Keep last 7 days of full backups
find "$BACKUP_DIR" -name "crm_full_backup_*.tar.gz" -type f -mtime +7 -delete

echo "✅ Full backup completed: ${FULL_BACKUP_PATH}.tar.gz"
echo "📊 Database: ${DB_NAME}_${DATE}.sql"
echo "📁 Uploads: uploads_${DATE}.tar.gz"
