#!/usr/bin/env python3
"""
Script to reset the database with the correct schema.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_database():
    """Drop all tables and recreate them with the correct schema."""
    try:
        from app.database import Base, engine
        from app.models import User, Role, Permission  # Import all models
        
        print("🗑️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
        
        print("🏗️  Creating tables with new schema...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def seed_database():
    """Seed the database with initial data."""
    try:
        from app.seeds.seed import seed_data
        print("🌱 Seeding database with initial data...")
        seed_data()
        print("✅ Database seeded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        return False

def main():
    """Main function."""
    print("🔄 Resetting FastAPI RBAC Database")
    print("=" * 40)
    
    # Reset database
    if not reset_database():
        return False
    
    # Seed data
    if not seed_database():
        print("⚠️  Database seeding failed, but tables were created.")
        return False
    
    print("\n🎉 Database reset completed successfully!")
    print("\n📋 Default users created:")
    print("  - Admin: username='admin', password='password123'")
    print("  - User: username='user', password='password123'")
    print("\n📋 Next steps:")
    print("1. Start the server: env\\Scripts\\python -m uvicorn app.main:app --reload")
    print("2. Open http://localhost:8000/docs")
    print("3. Test with: python test_rbac.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
