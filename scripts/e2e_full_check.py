import requests
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Load environment variables
load_dotenv()
load_dotenv("backend/.env")

def print_status(component, status, message=""):
    color = "\033[92m" if status == "PASS" else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{status}{reset}] {component}: {message}")

async def test_db():
    url = os.getenv("DATABASE_URL")
    if not url:
        print_status("Database", "FAIL", "DATABASE_URL not found")
        return False
    try:
        engine = create_async_engine(url, connect_args={"statement_cache_size": 0})
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print_status("Database", "PASS", "Connection successful (Supabase Postgres)")
        return True
    except Exception as e:
        print_status("Database", "FAIL", str(e))
        return False

def test_backend_health():
    url = "http://localhost:8001/health"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print_status("Backend Health", "PASS", f"Status 200, version: {r.json().get('version')}")
            return True
        else:
            print_status("Backend Health", "FAIL", f"Status {r.status_code}")
            return False
    except Exception:
        print_status("Backend Health", "SKIP", "Local server not running on :8001")
        return None

def test_supabase_storage():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        print_status("Storage", "FAIL", "Supabase credentials missing")
        return False
    
    bucket = "hotel-assets"
    test_file = "e2e_test_delete_me.txt"
    upload_url = f"{url}/storage/v1/object/{bucket}/{test_file}"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    
    try:
        r = requests.post(upload_url, headers=headers, data="test", timeout=5)
        if r.status_code == 200:
            print_status("Storage", "PASS", "Upload successful")
            # Cleanup
            requests.delete(upload_url, headers=headers)
            return True
        else:
            msg = r.json().get("message", r.text)
            print_status("Storage", "FAIL", f"Upload failed ({r.status_code}): {msg}")
            return False
    except Exception as e:
        print_status("Storage", "FAIL", str(e))
        return False

def test_auth_flow():
    # This tests the actual API endpoints
    base_url = "http://localhost:8001/api/v1"
    test_user = {
        "email": f"test_e2e_{os.urandom(2).hex()}@example.com",
        "password": "Password123!",
        "name": "E2E Test User",
        "hotel_name": "Test Hotel"
    }
    
    try:
        # 1. Signup
        r = requests.post(f"{base_url}/auth/register", json=test_user, timeout=10)
        if r.status_code not in [200, 201]:
             print_status("Auth Flow", "FAIL", f"Signup failed: {r.text}")
             return False
        
        # 2. Login
        login_data = {"email": test_user["email"], "password": test_user["password"]}
        r = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
        if r.status_code == 200:
            print_status("Auth Flow", "PASS", "Signup and Login successful")
            return True
        else:
            print_status("Auth Flow", "FAIL", f"Login failed: {r.text}")
            return False
    except Exception:
        print_status("Auth Flow", "SKIP", "Backend not reachable for Auth test")
        return None

async def main():
    print("=== End-to-End System Integrity Check ===\n")
    
    db_ok = await test_db()
    storage_ok = test_supabase_storage()
    backend_ok = test_backend_health()
    
    if backend_ok:
        auth_ok = test_auth_flow()
    else:
        print_status("Auth Flow", "SKIP", "Backend must be running for this test")

    print("\n=== Summary ===")
    if db_ok and storage_ok:
        print("Infrastructure: READY")
    else:
        print("Infrastructure: ISSUES DETECTED")

if __name__ == "__main__":
    asyncio.run(main())
