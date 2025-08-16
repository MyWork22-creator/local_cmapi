# CRM Database Seeding System

This directory contains comprehensive seeding functionality for the CRM system database. The seeding system creates realistic sample data for all models with proper relationships and dependencies.

## 📋 What Gets Seeded

### 1. Permissions (44 permissions)
- **User Management**: create, read, update, delete, list, status
- **Role Management**: create, read, update, delete, list, assign
- **Permission Management**: create, read, update, delete, list, assign
- **Bank Management**: create, read, update, delete, list
- **Customer Management**: create, read, update, delete, list, export
- **Hierarchy Management**: read, manage, validate
- **System Administration**: admin, audit, backup, maintenance
- **Dashboard & Reporting**: view, generate, export, analytics

### 2. Roles (4 roles with hierarchy)
- **Admin** (Level 0): Full system access with all permissions
- **Manager** (Level 1): Limited administrative access, child of Admin
- **User** (Level 2): Basic access, child of Manager
- **Viewer** (Level 3): Read-only access, child of User

### 3. Users (20 users)
- **Default Users**: admin, manager, user (all with password: `password123`)
- **Random Users**: 17 additional users with diverse roles and statuses
- **Statuses**: active (80%), inactive (15%), suspended (5%)

### 4. Banks (15 banks)
- **Real Banks**: JPMorgan Chase, Bank of America, Wells Fargo, etc.
- **Realistic Data**: Proper names, descriptions, and logo URLs
- **Creator Relationships**: Linked to admin/manager users

### 5. Customers (50 customers)
- **Customer Types**: individual, business, corporate, premium, vip
- **Currencies**: USD (50%), EUR (20%), GBP (15%), CAD (8%), AUD (5%), JPY (2%)
- **Realistic Amounts**: Type-based credit and amount distributions
- **Bank Relationships**: Distributed across all banks
- **Creator Relationships**: Linked to various users

## 🚀 Quick Start

### Method 1: Command Line (Recommended)

```bash
# Navigate to the backend directory
cd backend

# Run the seeder
python -m app.seeds.seed

# Or with options
python -m app.seeds.seed --clear  # Clear existing data first
```

### Method 2: Programmatic Usage

```python
from app.seeds.seed import DatabaseSeeder

# Basic seeding
with DatabaseSeeder() as seeder:
    seeder.run_full_seed()

# Clear existing data and reseed
with DatabaseSeeder() as seeder:
    seeder.run_full_seed(clear_data=True)
```

### Method 3: Individual Components

```python
from app.seeds.seed import DatabaseSeeder

with DatabaseSeeder() as seeder:
    seeder.seed_permissions()
    seeder.seed_roles()
    seeder.seed_users()
    seeder.seed_banks()
    seeder.seed_customers()
```

## 🔧 Command Line Options

```bash
python -m app.seeds.seed [OPTIONS]

Options:
  --clear     Clear existing data before seeding
  --force     Skip confirmation prompts
  --help      Show help message
```

## 📊 Default Login Credentials

After seeding, you can login with these default accounts:

| Username | Password    | Role    | Permissions |
|----------|-------------|---------|-------------|
| admin    | password123 | admin   | All permissions |
| manager  | password123 | manager | Limited admin access |
| user     | password123 | user    | Basic access |

## 🏗️ Architecture

### Files Structure

```
app/seeds/
├── __init__.py          # Package initialization
├── factories.py         # Data generation factories
├── seed.py             # Main seeding logic
└── README.md           # This documentation
```

### Key Components

1. **DataFactory** (`factories.py`): Generates realistic sample data using Faker
2. **DatabaseSeeder** (`seed.py`): Coordinates the seeding process with proper dependency management
3. **Dependency Management**: Ensures data is created in the correct order (permissions → roles → users → banks → customers)

## 🔄 Seeding Process Flow

1. **Permissions**: Create all system permissions
2. **Roles**: Create role hierarchy with permission assignments
3. **Users**: Create users with role assignments and password hashing
4. **Banks**: Create banks with creator relationships
5. **Customers**: Create customers with bank and creator relationships

## ⚠️ Important Notes

### Data Safety
- The `--clear` option will **DELETE ALL EXISTING DATA**
- Always backup your database before using `--clear` in production
- The seeder checks for existing records and skips duplicates by default

### Dependencies
- Requires all models to be properly imported and registered
- Uses the same database connection as the main application
- Respects all model constraints and validations

### Performance
- Seeding 50 customers + 15 banks + 20 users typically takes 5-10 seconds
- Uses batch operations where possible
- Includes progress indicators and error handling

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the backend directory
   cd backend
   python -m app.seeds.seed
   ```

2. **Database Connection Issues**
   ```bash
   # Check your .env file has correct database settings
   # Ensure database server is running
   ```

3. **Permission Errors**
   ```bash
   # Ensure database user has CREATE/INSERT permissions
   ```

4. **Existing Data Conflicts**
   ```bash
   # Use --clear to remove existing data
   python -m app.seeds.seed --clear
   ```

### Error Messages

- **"Permission already exists"**: Normal behavior, seeder skips existing records
- **"Role not found"**: Check that roles were created successfully
- **"Database connection failed"**: Verify database settings in .env

## 🔍 Verification

After seeding, verify the data was created correctly:

```bash
# Check record counts
curl -X GET "http://localhost:8000/api/v1/users" -H "Authorization: Bearer YOUR_TOKEN"
curl -X GET "http://localhost:8000/api/v1/banks" -H "Authorization: Bearer YOUR_TOKEN"
curl -X GET "http://localhost:8000/api/v1/customers" -H "Authorization: Bearer YOUR_TOKEN"

# Test login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'
```

## 🎯 Next Steps

1. **Start the FastAPI server**: `uvicorn app.main:app --reload`
2. **Visit API docs**: http://localhost:8000/docs
3. **Login with default credentials**
4. **Explore the seeded data through API endpoints**
5. **Customize the seed data** by modifying `factories.py`

## 🔧 Customization

To customize the seed data:

1. **Modify quantities**: Edit the numbers in `seed.py` (e.g., `generate_users(20)`)
2. **Add new data types**: Extend `DataFactory` in `factories.py`
3. **Change default users**: Modify the default users in `generate_users()`
4. **Add new permissions**: Update `generate_permissions()` in `factories.py`
