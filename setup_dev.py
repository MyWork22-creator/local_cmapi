#!/usr/bin/env python3
"""
Development setup script for FastAPI RBAC project.
This script helps set up the development environment quickly.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_virtual_environment():
    """Set up virtual environment if it doesn't exist."""
    if Path("env").exists():
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv env", "Creating virtual environment")

def install_dependencies():
    """Install project dependencies."""
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = "env\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "env/bin/pip"
    
    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")

def setup_database():
    """Set up the database with initial data."""
    # Determine the correct python path based on OS
    if os.name == 'nt':  # Windows
        python_path = "env\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "env/bin/python"
    
    success = run_command(f"{python_path} -m app.seeds.seed", "Setting up database with initial data")
    if success:
        print("📊 Database seeded with default users:")
        print("   - Admin: username='admin', password='password123'")
        print("   - User: username='user', password='password123'")
    return success

def main():
    """Main setup function."""
    print("🚀 FastAPI RBAC Development Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup failed, but you can try running it manually:")
        print("   python -m app.seeds.seed")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   env\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source env/bin/activate")
    
    print("2. Start the development server:")
    print("   uvicorn app.main:app --reload")
    print("3. Open http://localhost:8000/docs in your browser")
    print("4. Test the API with: python test_rbac.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
