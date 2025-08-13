"""Migration script to add role hierarchy support to existing database."""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir.parent))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models.role import Role
from app.services.role_hierarchy_service import RoleHierarchyService


def migrate_role_hierarchy():
    """Add hierarchy columns to existing roles table and set default values."""
    
    print("🔄 Starting role hierarchy migration...")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'roles' 
            AND column_name IN ('parent_id', 'level')
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        if 'parent_id' in existing_columns and 'level' in existing_columns:
            print("✅ Hierarchy columns already exist. Checking data consistency...")
        else:
            print("📝 Adding hierarchy columns to roles table...")
            
            # Add parent_id column if it doesn't exist
            if 'parent_id' not in existing_columns:
                db.execute(text("""
                    ALTER TABLE roles 
                    ADD COLUMN parent_id INTEGER REFERENCES roles(id) ON DELETE SET NULL
                """))
                print("   ✅ Added parent_id column")
            
            # Add level column if it doesn't exist
            if 'level' not in existing_columns:
                db.execute(text("""
                    ALTER TABLE roles 
                    ADD COLUMN level INTEGER NOT NULL DEFAULT 0
                """))
                print("   ✅ Added level column")
            
            # Create indexes
            try:
                db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_role_parent_level 
                    ON roles(parent_id, level)
                """))
                db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_role_hierarchy 
                    ON roles(level, parent_id)
                """))
                print("   ✅ Created hierarchy indexes")
            except Exception as e:
                print(f"   ⚠️  Index creation warning: {e}")
            
            db.commit()
        
        # Set default levels for existing roles
        print("🔧 Setting default hierarchy levels...")
        roles = db.query(Role).all()
        
        for role in roles:
            if role.level is None:
                role.level = 0
        
        db.commit()
        print(f"   ✅ Updated {len(roles)} roles with default level 0")
        
        # Validate hierarchy integrity
        print("🔍 Validating hierarchy integrity...")
        issues = RoleHierarchyService.validate_hierarchy_integrity(db)
        
        if issues:
            print(f"   ⚠️  Found {len(issues)} hierarchy issues:")
            for issue in issues:
                print(f"      - {issue['type']}: {issue['description']}")
            
            # Fix level issues automatically
            level_issues = [i for i in issues if i['type'] == 'incorrect_level']
            if level_issues:
                print("   🔧 Fixing level issues...")
                fixed_count = RoleHierarchyService.fix_hierarchy_levels(db)
                print(f"      ✅ Fixed {fixed_count} role levels")
        else:
            print("   ✅ Hierarchy integrity validated successfully")
        
        # Display hierarchy summary
        print("\n📊 Role Hierarchy Summary:")
        tree = RoleHierarchyService.get_role_hierarchy_tree(db)
        
        def print_tree(nodes, indent=0):
            for node in nodes:
                prefix = "  " * indent + ("├─ " if indent > 0 else "")
                print(f"{prefix}{node['name']} (Level {node['level']}) - {len(node['all_permissions'])} permissions")
                if node['children']:
                    print_tree(node['children'], indent + 1)
        
        if tree:
            print_tree(tree)
        else:
            print("   No roles found")
        
        print(f"\n✅ Role hierarchy migration completed successfully!")
        print(f"   Total roles: {len(roles)}")
        print(f"   Root roles: {len(tree)}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_sample_hierarchy():
    """Create a sample role hierarchy for demonstration."""
    
    print("\n🎯 Creating sample role hierarchy...")
    
    db = SessionLocal()
    
    try:
        # Check if sample roles already exist
        existing_roles = {role.name: role for role in db.query(Role).all()}
        
        # Create sample hierarchy: admin -> manager -> user
        if 'admin' not in existing_roles:
            admin_role = Role(name='admin', description='System administrator', level=0)
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("   ✅ Created admin role")
        else:
            admin_role = existing_roles['admin']
            print("   ℹ️  Admin role already exists")
        
        if 'manager' not in existing_roles:
            manager_role = Role(
                name='manager', 
                description='Department manager', 
                parent_id=admin_role.id,
                level=1
            )
            db.add(manager_role)
            db.commit()
            db.refresh(manager_role)
            print("   ✅ Created manager role (child of admin)")
        else:
            manager_role = existing_roles['manager']
            if not manager_role.parent_id:
                manager_role.parent_id = admin_role.id
                manager_role.level = 1
                db.commit()
                print("   ✅ Updated manager role hierarchy")
        
        if 'user' not in existing_roles:
            user_role = Role(
                name='user', 
                description='Regular user', 
                parent_id=manager_role.id,
                level=2
            )
            db.add(user_role)
            db.commit()
            db.refresh(user_role)
            print("   ✅ Created user role (child of manager)")
        else:
            user_role = existing_roles['user']
            if not user_role.parent_id:
                user_role.parent_id = manager_role.id
                user_role.level = 2
                db.commit()
                print("   ✅ Updated user role hierarchy")
        
        print("✅ Sample hierarchy created: admin -> manager -> user")
        
    except Exception as e:
        print(f"❌ Sample hierarchy creation failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Role Hierarchy Migration Tool")
    print("=" * 50)
    
    # Run migration
    migrate_role_hierarchy()
    
    # Ask if user wants to create sample hierarchy
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_hierarchy()
    else:
        print("\n💡 Tip: Run with --sample to create a sample role hierarchy")
    
    print("\n🎉 Migration completed!")
    print("\n📚 Next steps:")
    print("   1. Restart your FastAPI application")
    print("   2. Use /api/v1/hierarchy/tree to view the role hierarchy")
    print("   3. Use /api/v1/hierarchy/{role_id} to see role details")
    print("   4. Create roles with parent_id to build your hierarchy")
