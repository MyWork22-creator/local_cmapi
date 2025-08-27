#!/bin/bash
set -e

# Usage: ./restore_backup.sh <backup_file> [database_name]
# Example: ./restore_backup.sh crm_full_backup_2024-01-15_10-30-00.tar.gz

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [database_name]"
    echo "Example: $0 crm_full_backup_2024-01-15_10-30-00.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${2:-${DB_NAME}}"
DB_CONTAINER=cm-mysql
DB_USER=${DB_USER}
DB_PASS=${DB_ROOT_PASSWORD}
RESTORE_DIR="/tmp/restore_$(date +%s)"

echo "🔄 Starting restore from: $BACKUP_FILE"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create restore directory
mkdir -p "$RESTORE_DIR"
cd "$RESTORE_DIR"

# Extract backup
echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE"

# Find the extracted directory
EXTRACTED_DIR=$(ls -d crm_full_backup_* | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "❌ Could not find extracted backup directory"
    exit 1
fi

cd "$EXTRACTED_DIR"

# Restore database
echo "📊 Restoring database..."
DB_FILE=$(ls *.sql | head -1)
if [ -n "$DB_FILE" ]; then
    docker exec -i "$DB_CONTAINER" mysql -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$DB_FILE"
    echo "✅ Database restored from: $DB_FILE"
else
    echo "⚠️  No database file found in backup"
fi

# Restore uploads
echo "📁 Restoring uploads..."
UPLOAD_FILE=$(ls uploads_*.tar.gz | head -1)
if [ -n "$UPLOAD_FILE" ]; then
    # Extract uploads to temporary location
    tar -xzf "$UPLOAD_FILE"
    UPLOAD_DIR=$(ls -d uploads_* | head -1)
    
    if [ -n "$UPLOAD_DIR" ]; then
        # Copy to app static directory
        cp -r "$UPLOAD_DIR"/* /app/static/
        echo "✅ Uploads restored from: $UPLOAD_FILE"
    fi
else
    echo "⚠️  No uploads file found in backup"
fi

# Cleanup
cd /
rm -rf "$RESTORE_DIR"

echo "✅ Restore completed successfully!"
