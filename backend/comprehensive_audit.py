import asyncio
import httpx
import sys
import os
import json
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import redis.asyncio as redis

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.config import get_settings

settings = get_settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Audit")

class AuditResult:
    def __init__(self):
        self.pass_count = 0
        self.fail_count = 0
        self.warn_count = 0
        self.details = []

    def log(self, status, component, message):
        symbol = {"PASS": "[OK]", "FAIL": "[ERROR]", "WARN": "[WARN]"}[status]
        print(f"{symbol} [{status}] {component}: {message}")
        self.details.append({"status": status, "component": component, "message": message})
        if status == "PASS": self.pass_count += 1
        elif status == "FAIL": self.fail_count += 1
        else: self.warn_count += 1

async def audit_database(result: AuditResult):
    print("\n--- Checking Database ---")
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            connect_args={"statement_cache_size": 0}
        )
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            result.log("PASS", "Database", "Connection successful")
            
            # Check for core tables
            core_tables = ["users", "hotels", "room_types", "bookings", "guests"]
            for table in core_tables:
                try:
                    await conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    result.log("PASS", "Database", f"Table '{table}' is healthy")
                except Exception as table_err:
                    result.log("FAIL", "Database", f"Table '{table}' check failed: {str(table_err)}")
        await engine.dispose()
    except Exception as e:
        result.log("FAIL", "Database", f"Connection failed: {str(e)}")

async def audit_redis(result: AuditResult):
    print("\n--- Checking Redis ---")
    try:
        r = redis.from_url("redis://localhost:6379", decode_responses=True)
        await r.ping()
        result.log("PASS", "Redis", "Connection successful")
        await r.close()
    except Exception as e:
        result.log("WARN", "Redis", f"Connection failed (Optional but recommended): {str(e)}")

async def audit_api_endpoints(result: AuditResult):
    print("\n--- Checking API Endpoints ---")
    base_url = "http://localhost:8001"
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Health Check
        try:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                result.log("PASS", "API", f"Health check OK ({resp.json().get('status')})")
            else:
                result.log("FAIL", "API", f"Health check failed with status {resp.status_code}")
        except Exception as e:
            result.log("FAIL", "API", f"Server unreachable on {base_url}: {str(e)}")

        # Docs
        try:
            resp = await client.get(f"{base_url}/docs")
            if resp.status_code == 200:
                result.log("PASS", "API", "Swagger Docs accessible")
            else:
                result.log("FAIL", "API", "Swagger Docs not loading")
        except Exception:
            pass

async def audit_ai_agent(result: AuditResult):
    print("\n--- Checking AI Agent (Ollama/OpenAI) ---")
    # Check Ollama if local
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                result.log("PASS", "AI", "Ollama is running locally")
            else:
                result.log("WARN", "AI", "Ollama found but returned error")
    except Exception:
        result.log("WARN", "AI", "Ollama not found on localhost:11434")

async def audit_supabase(result: AuditResult):
    print("\n--- Checking Supabase Integration ---")
    if not settings.SUPABASE_URL:
        result.log("WARN", "Supabase", "SUPABASE_URL is not set in .env")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.SUPABASE_URL}/rest/v1/", headers={"apikey": settings.SUPABASE_SERVICE_ROLE_KEY})
            if resp.status_code in [200, 401, 404]: # Even 401 means it's reachable
                result.log("PASS", "Supabase", "Supabase URL is reachable")
            else:
                result.log("FAIL", "Supabase", f"Supabase error status: {resp.status_code}")
    except Exception as e:
        result.log("FAIL", "Supabase", f"Connection failed: {str(e)}")

async def run_audit():
    print("========================================")
    print("   HOTELIER HUB COMPREHENSIVE AUDIT     ")
    print("========================================\n")
    
    result = AuditResult()
    
    # Run all audits
    await audit_database(result)
    await audit_redis(result)
    await audit_supabase(result)
    await audit_api_endpoints(result)
    await audit_ai_agent(result)
    
    print("\n" + "="*40)
    print(f"AUDIT SUMMARY:")
    print(f"TOTAL TESTS: {result.pass_count + result.fail_count + result.warn_count}")
    print(f"PASSED: {result.pass_count}")
    print(f"FAILED: {result.fail_count}")
    print(f"WARNINGS: {result.warn_count}")
    print("="*40)
    
    if result.fail_count > 0:
        print("\nCRITICAL: Kuch bade issues mile hain! Inhe thik karna zaroori hai.")
        sys.exit(1)
    else:
        print("\nSUCCESS: System stable lag raha hai.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_audit())
