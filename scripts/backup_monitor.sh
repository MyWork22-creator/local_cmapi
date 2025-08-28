#!/bin/bash

BACKUP_DIR=/backups
DB_CONTAINER=cm-mysql

echo "🔍 Backup System Health Check - $(date)"
echo "=========================================="

# Check if backup directories exist
echo "📁 Checking backup directories..."
if [ -d "$BACKUP_DIR/mysql" ]; then
    echo "✅ MySQL backup directory exists"
else
    echo "❌ MySQL backup directory missing"
fi

if [ -d "$BACKUP_DIR/uploads" ]; then
    echo "✅ Uploads backup directory exists"
else
    echo "❌ Uploads backup directory missing"
fi

# Check recent database backups
echo ""
echo "📊 Recent database backups:"
if [ -d "$BACKUP_DIR/mysql" ]; then
    ls -la "$BACKUP_DIR/mysql"/*.sql 2>/dev/null | tail -5 || echo "No database backups found"
else
    echo "No database backup directory"
fi

# Check recent upload backups
echo ""
echo "📁 Recent upload backups:"
if [ -d "$BACKUP_DIR/uploads" ]; then
    ls -la "$BACKUP_DIR/uploads"/*.tar.gz 2>/dev/null | tail -5 || echo "No upload backups found"
else
    echo "No upload backup directory"
fi

# Check full backups
echo ""
echo "📦 Recent full backups:"
ls -la "$BACKUP_DIR"/crm_full_backup_*.tar.gz 2>/dev/null | tail -3 || echo "No full backups found"

# Check backup service status
echo ""
echo "🔧 Backup service status:"
if docker ps | grep -q backup-service; then
    echo "✅ Backup service is running"
else
    echo "❌ Backup service is not running"
fi

# Check MySQL container status
echo ""
echo "🗄️ MySQL container status:"
if docker ps | grep -q cm-mysql; then
    echo "✅ MySQL container is running"
else
    echo "❌ MySQL container is not running"
fi

# Check disk space
echo ""
echo "💾 Disk space usage:"
df -h "$BACKUP_DIR" 2>/dev/null || echo "Cannot check disk space for backup directory"

# Check cron logs
echo ""
echo "📋 Recent cron logs:"
if [ -f /var/log/cron.log ]; then
    tail -10 /var/log/cron.log
else
    echo "No cron log file found"
fi

echo ""
echo "✅ Health check completed"
