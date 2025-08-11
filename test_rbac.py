#!/usr/bin/env python3
"""
Simple test script for the FastAPI RBAC system.
This script helps you test the authentication and get tokens for the API docs.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def test_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Server is running! Open http://localhost:8000/docs in your browser")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running with: uvicorn app.main:app --reload")
        return False

def test_auth_help():
    """Test the authentication help endpoint"""
    print_separator("Testing Authentication Help Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/auth/help")
        if response.status_code == 200:
            help_data = response.json()
            print("✅ Authentication help endpoint working!")
            print(f"📖 Message: {help_data['message']}")
            print("\n📋 Steps:")
            for step in help_data['steps']:
                print(f"   {step}")
            print("\n👥 Default Users:")
            for user_type, user_info in help_data['default_users'].items():
                print(f"   {user_type}: {user_info['username']} / {user_info['password']}")
            return True
        else:
            print(f"❌ Help endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing help endpoint: {e}")
        return False

def test_login(username, password):
    """Test user login and return token"""
    print_separator(f"Testing Login for {username}")
    
    try:
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful for {username}!")
            print(f"🔑 Access Token: {token_data['access_token']}")
            print(f"📝 Token Type: {token_data['token_type']}")
            print(f"\n💡 Copy this token and use it in the API docs:")
            print(f"   Bearer {token_data['access_token']}")
            return token_data['access_token']
        else:
            print(f"❌ Login failed for {username}: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_protected_endpoint(token, endpoint, description):
    """Test a protected endpoint with the given token"""
    print(f"\n🔒 Testing: {description}")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Success! Status: {response.status_code}")
            return True
        else:
            print(f"   ❌ Failed! Status: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 FastAPI RBAC System Test Script")
    print("This script will help you test the RBAC system and get tokens for the API docs.")
    
    # Test server health
    if not test_health():
        return
    
    # Test auth help
    if not test_auth_help():
        return
    
    print_separator("Testing Authentication")
    
    # Test admin login
    admin_token = test_login("admin", "password123")
    if not admin_token:
        print("❌ Admin login failed. Make sure you've run: python -m app.seeds.seed")
        return
    
    # Test user login
    user_token = test_login("user", "password123")
    if not user_token:
        print("❌ User login failed. Make sure you've run: python -m app.seeds.seed")
        return
    
    print_separator("Testing Protected Endpoints")
    
    # Test admin endpoints
    print("👑 Testing Admin Access:")
    test_protected_endpoint(admin_token, "/users", "List all users")
    test_protected_endpoint(admin_token, "/roles", "List all roles")
    test_protected_endpoint(admin_token, "/rbac/permission-hierarchy", "Get permission hierarchy")
    
    # Test user endpoints (should have limited access)
    print("\n👤 Testing User Access:")
    test_protected_endpoint(user_token, "/users", "List all users (should work)")
    test_protected_endpoint(user_token, "/roles", "List all roles (should fail)")
    test_protected_endpoint(user_token, "/rbac/current-user-info", "Get current user info")
    
    print_separator("Next Steps")
    print("🎯 Now you can:")
    print("1. Open http://localhost:8000/docs in your browser")
    print("2. Click the 'Authorize' button at the top")
    print("3. Enter one of these tokens:")
    print(f"   Admin: Bearer {admin_token}")
    print(f"   User:  Bearer {user_token}")
    print("4. Click 'Authorize' to enable authenticated endpoints")
    print("5. Test the protected endpoints in the API docs!")
    
    print("\n💡 Tips:")
    print("- Use admin token to test all endpoints")
    print("- Use user token to see permission restrictions")
    print("- Check the RBAC testing endpoints to understand the system")

if __name__ == "__main__":
    main()
