#!/usr/bin/env python3
"""
Script to create database tables and seed initial data.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_tables():
    """Create all database tables."""
    try:
        from app.database import Base, engine
        from app.models import User, Role, Permission  # Import all models
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def seed_database():
    """Seed the database with initial data."""
    try:
        from app.seeds.seed import seed_data
        print("Seeding database with initial data...")
        seed_data()
        print("✅ Database seeded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Setting up FastAPI RBAC Database")
    print("=" * 40)
    
    # Create tables
    if not create_tables():
        return False
    
    # Seed data
    if not seed_database():
        print("⚠️  Database seeding failed, but tables were created.")
        print("You can try running: python -m app.seeds.seed")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the server: env\\Scripts\\python -m uvicorn app.main:app --reload")
    print("2. Open http://localhost:8000/docs")
    print("3. Test with: python test_rbac.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
