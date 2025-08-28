# CRM Backup System Documentation

## Overview
This directory contains comprehensive backup scripts for the CRM system, including database backups, file uploads, and full system backups.

## Backup Scripts

### 1. `backup_db.sh` - Database Backup
- **Purpose**: Creates MySQL database dumps
- **Schedule**: Daily at 1:00 AM
- **Retention**: 7 days
- **Location**: `/backups/mysql/`

### 2. `backup_uploads.sh` - File Uploads Backup
- **Purpose**: Backs up static files (bank logos, etc.)
- **Schedule**: Daily at 2:00 AM
- **Retention**: 30 days
- **Location**: `/backups/uploads/`

### 3. `backup_full.sh` - Full System Backup
- **Purpose**: Complete backup of database + uploads
- **Schedule**: Weekly (Sunday at 3:00 AM)
- **Retention**: 7 days
- **Location**: `/backups/`

### 4. `restore_backup.sh` - Restore Script
- **Purpose**: Restore data from backup files
- **Usage**: `./restore_backup.sh <backup_file> [database_name]`

### 5. `backup_monitor.sh` - Health Check
- **Purpose**: Monitor backup system health
- **Usage**: `./backup_monitor.sh`

## Backup Schedule

| Script | Frequency | Time | Retention |
|--------|-----------|------|-----------|
| Database | Daily | 1:00 AM | 7 days |
| Uploads | Daily | 2:00 AM | 30 days |
| Full | Weekly | Sunday 3:00 AM | 7 days |

## Setup Instructions

### 1. Create Environment File
```bash
cp env.example .env
# Edit .env with your database credentials
```

### 2. Create Backup Directory
```bash
sudo mkdir -p /srv/backups/mysql
sudo mkdir -p /srv/backups/uploads
sudo chown -R 1000:1000 /srv/backups  # Adjust user ID as needed
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Backup System
```bash
docker exec backup-service /app/scripts/backup_monitor.sh
```

## Manual Backup Commands

### Database Backup
```bash
docker exec backup-service /app/scripts/backup_db.sh
```

### Uploads Backup
```bash
docker exec backup-service /app/scripts/backup_uploads.sh
```

### Full Backup
```bash
docker exec backup-service /app/scripts/backup_full.sh
```

### Health Check
```bash
docker exec backup-service /app/scripts/backup_monitor.sh
```

## Restore Process

### From Full Backup
```bash
docker exec backup-service /app/scripts/restore_backup.sh crm_full_backup_2024-01-15_10-30-00.tar.gz
```

### From Individual Backups
```bash
# Restore database
docker exec -i cm-mysql mysql -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < backup_file.sql

# Restore uploads
tar -xzf uploads_backup.tar.gz -C /app/static/
```

## Monitoring and Troubleshooting

### Check Backup Logs
```bash
docker exec backup-service tail -f /var/log/cron.log
```

### Check Service Status
```bash
docker ps | grep backup-service
```

### Manual Cron Job Test
```bash
docker exec backup-service crontab -l
```

## Backup File Structure

```
/backups/
├── mysql/
│   ├── crm_database_2024-01-15_01-00-00.sql
│   └── crm_database_2024-01-16_01-00-00.sql
├── uploads/
│   ├── uploads_2024-01-15_02-00-00.tar.gz
│   └── uploads_2024-01-16_02-00-00.tar.gz
└── crm_full_backup_2024-01-14_03-00-00.tar.gz
```

## Security Considerations

1. **Backup Encryption**: Consider encrypting sensitive backups
2. **Access Control**: Restrict access to backup directories
3. **Off-site Storage**: Consider copying backups to external storage
4. **Testing**: Regularly test restore procedures

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check backup directory permissions
2. **Container Not Found**: Ensure MySQL container is running
3. **Disk Space**: Monitor available disk space
4. **Cron Not Running**: Check cron service status

### Debug Commands
```bash
# Check backup service logs
docker logs backup-service

# Test backup script manually
docker exec backup-service /app/scripts/backup_db.sh

# Check environment variables
docker exec backup-service env | grep DB_
```
