"""
Database seeding script for CRM system.
This script populates the database with realistic sample data for all models.

Usage:
    python -m app.seeds.seed
    
Or from the backend directory:
    python -c "from app.seeds.seed import main; main()"
"""

import sys
import os
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, engine
from app.models import Base, User, Role, Permission, Bank, Customer, TokenBlacklist
from app.models.associations import role_permissions
from app.seeds.factories import DataFactory

class DatabaseSeeder:
    """Main seeder class that coordinates the seeding process."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.created_objects: Dict[str, List[Any]] = {
            'permissions': [],
            'roles': [],
            'users': [],
            'banks': [],
            'customers': []
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"❌ Error occurred: {exc_val}")
            self.db.rollback()
        self.db.close()
    
    def clear_existing_data(self, confirm: bool = False):
        """Clear existing data from all tables (use with caution)."""
        if not confirm:
            response = input("⚠️  This will delete ALL existing data. Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled.")
                return False
        
        try:
            print("🗑️  Clearing existing data...")
            
            # Delete in reverse dependency order
            self.db.query(Customer).delete()
            self.db.query(Bank).delete()
            self.db.query(User).delete()
            self.db.execute(role_permissions.delete())
            self.db.query(Permission).delete()
            self.db.query(Role).delete()
            self.db.query(TokenBlacklist).delete()
            
            self.db.commit()
            print("✅ Existing data cleared successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            self.db.rollback()
            return False
    
    def seed_permissions(self):
        """Seed permission data."""
        print("🔑 Seeding permissions...")
        
        permissions_data = DataFactory.generate_permissions()
        
        for perm_data in permissions_data:
            try:
                # Check if permission already exists
                existing = self.db.query(Permission).filter(Permission.name == perm_data["name"]).first()
                if existing:
                    print(f"   ⚠️  Permission '{perm_data['name']}' already exists, skipping")
                    self.created_objects['permissions'].append(existing)
                    continue
                
                permission = Permission(
                    name=perm_data["name"],
                    description=perm_data["description"]
                )
                self.db.add(permission)
                self.created_objects['permissions'].append(permission)
                
            except IntegrityError as e:
                print(f"   ❌ Error creating permission '{perm_data['name']}': {e}")
                self.db.rollback()
                continue
        
        self.db.commit()
        print(f"   ✅ Created {len(self.created_objects['permissions'])} permissions")
    
    def seed_roles(self):
        """Seed role data with hierarchy."""
        print("👥 Seeding roles...")
        
        roles_data = DataFactory.generate_roles()
        permission_map = {p.name: p for p in self.created_objects['permissions']}
        
        # Create roles first (without parent relationships)
        for role_data in roles_data:
            try:
                # Check if role already exists
                existing = self.db.query(Role).filter(Role.name == role_data["name"]).first()
                if existing:
                    print(f"   ⚠️  Role '{role_data['name']}' already exists, skipping")
                    self.created_objects['roles'].append(existing)
                    continue
                
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    level=role_data["level"]
                )
                self.db.add(role)
                self.created_objects['roles'].append(role)
                
            except IntegrityError as e:
                print(f"   ❌ Error creating role '{role_data['name']}': {e}")
                self.db.rollback()
                continue
        
        self.db.commit()
        
        # Now set up hierarchy relationships
        role_map = {r.name: r for r in self.created_objects['roles']}
        
        for role_data in roles_data:
            role = role_map.get(role_data["name"])
            if not role:
                continue
            
            # Set parent relationship
            if role_data["name"] == "manager":
                role.parent_id = role_map["admin"].id
            elif role_data["name"] == "user":
                role.parent_id = role_map["manager"].id
            elif role_data["name"] == "viewer":
                role.parent_id = role_map["user"].id
            
            # Assign permissions
            for perm_name in role_data["permissions"]:
                permission = permission_map.get(perm_name)
                if permission and permission not in role.permissions:
                    role.permissions.append(permission)
        
        self.db.commit()
        print(f"   ✅ Created {len(self.created_objects['roles'])} roles with hierarchy")
    
    def seed_users(self):
        """Seed user data."""
        print("👤 Seeding users...")
        
        users_data = DataFactory.generate_users(20)
        role_map = {r.name: r for r in self.created_objects['roles']}
        
        for user_data in users_data:
            try:
                # Check if user already exists
                existing = self.db.query(User).filter(User.user_name == user_data["user_name"]).first()
                if existing:
                    print(f"   ⚠️  User '{user_data['user_name']}' already exists, skipping")
                    self.created_objects['users'].append(existing)
                    continue
                
                role = role_map.get(user_data["role_name"])
                if not role:
                    print(f"   ❌ Role '{user_data['role_name']}' not found for user '{user_data['user_name']}'")
                    continue
                
                user = User(
                    user_name=user_data["user_name"],
                    password_hash=user_data["password_hash"],
                    role_id=role.id,
                    status=user_data["status"]
                )
                self.db.add(user)
                self.created_objects['users'].append(user)
                
            except IntegrityError as e:
                print(f"   ❌ Error creating user '{user_data['user_name']}': {e}")
                self.db.rollback()
                continue
        
        self.db.commit()
        print(f"   ✅ Created {len(self.created_objects['users'])} users")
    
    def seed_banks(self):
        """Seed bank data."""
        print("🏦 Seeding banks...")
        
        banks_data = DataFactory.generate_banks(15)
        user_map = {u.user_name: u for u in self.created_objects['users']}
        
        for bank_data in banks_data:
            try:
                # Check if bank already exists
                existing = self.db.query(Bank).filter(Bank.bank_name == bank_data["bank_name"]).first()
                if existing:
                    print(f"   ⚠️  Bank '{bank_data['bank_name']}' already exists, skipping")
                    self.created_objects['banks'].append(existing)
                    continue
                
                creator = user_map.get(bank_data["created_by_user_name"])
                
                bank = Bank(
                    bank_name=bank_data["bank_name"],
                    logo=bank_data["logo"],
                    description=bank_data["description"],
                    created_by_user_id=creator.id if creator else None
                )
                self.db.add(bank)
                self.created_objects['banks'].append(bank)
                
            except IntegrityError as e:
                print(f"   ❌ Error creating bank '{bank_data['bank_name']}': {e}")
                self.db.rollback()
                continue
        
        self.db.commit()
        print(f"   ✅ Created {len(self.created_objects['banks'])} banks")

    def seed_customers(self):
        """Seed customer data."""
        print("👥 Seeding customers...")

        bank_names = [b.bank_name for b in self.created_objects['banks']]
        user_names = [u.user_name for u in self.created_objects['users']]
        customers_data = DataFactory.generate_customers(50, bank_names, user_names)

        bank_map = {b.bank_name: b for b in self.created_objects['banks']}
        user_map = {u.user_name: u for u in self.created_objects['users']}

        for customer_data in customers_data:
            try:
                # Check if customer already exists
                existing = self.db.query(Customer).filter(Customer.customer_id == customer_data["customer_id"]).first()
                if existing:
                    print(f"   ⚠️  Customer '{customer_data['customer_id']}' already exists, skipping")
                    self.created_objects['customers'].append(existing)
                    continue

                bank = bank_map.get(customer_data["bank_name"])
                creator = user_map.get(customer_data["created_by_user_name"])

                if not bank:
                    print(f"   ❌ Bank '{customer_data['bank_name']}' not found for customer '{customer_data['customer_id']}'")
                    continue

                if not creator:
                    print(f"   ❌ User '{customer_data['created_by_user_name']}' not found for customer '{customer_data['customer_id']}'")
                    continue

                customer = Customer(
                    customer_id=customer_data["customer_id"],
                    type=customer_data["type"],
                    currency=customer_data["currency"],
                    credit=customer_data["credit"],
                    amount=customer_data["amount"],
                    bank_id=bank.bank_id,
                    note=customer_data["note"],
                    create_by_user=creator.id
                )
                self.db.add(customer)
                self.created_objects['customers'].append(customer)

            except IntegrityError as e:
                print(f"   ❌ Error creating customer '{customer_data['customer_id']}': {e}")
                self.db.rollback()
                continue

        self.db.commit()
        print(f"   ✅ Created {len(self.created_objects['customers'])} customers")

    def run_full_seed(self, clear_data: bool = False):
        """Run the complete seeding process."""
        print("🌱 Starting database seeding process...")
        print("=" * 50)

        try:
            # Clear existing data if requested
            if clear_data:
                if not self.clear_existing_data():
                    return False

            # Create tables if they don't exist
            print("📋 Creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("   ✅ Database tables ready")

            # Seed data in dependency order
            self.seed_permissions()
            self.seed_roles()
            self.seed_users()
            self.seed_banks()
            self.seed_customers()

            # Print summary
            print("\n" + "=" * 50)
            print("🎉 Seeding completed successfully!")
            print("\n📊 Summary:")
            print(f"   • Permissions: {len(self.created_objects['permissions'])}")
            print(f"   • Roles: {len(self.created_objects['roles'])}")
            print(f"   • Users: {len(self.created_objects['users'])}")
            print(f"   • Banks: {len(self.created_objects['banks'])}")
            print(f"   • Customers: {len(self.created_objects['customers'])}")

            print("\n🔑 Default Login Credentials:")
            print("   • Admin: username='admin', password='password123'")
            print("   • Manager: username='manager', password='password123'")
            print("   • User: username='user', password='password123'")

            print("\n📚 Next Steps:")
            print("   1. Start your FastAPI server: uvicorn app.main:app --reload")
            print("   2. Visit http://localhost:8000/docs for API documentation")
            print("   3. Login with the default credentials above")
            print("   4. Explore the seeded data through the API endpoints")

            return True

        except Exception as e:
            print(f"\n❌ Seeding failed: {e}")
            self.db.rollback()
            return False


def main():
    """Main entry point for the seeding script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed the CRM database with sample data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    print("🚀 CRM Database Seeder")
    print("=" * 50)

    with DatabaseSeeder() as seeder:
        success = seeder.run_full_seed(clear_data=args.clear)

        if success:
            print("\n✅ Database seeding completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Database seeding failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
