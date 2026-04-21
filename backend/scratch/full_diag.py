import asyncio
from sqlmodel import select, text
from app.core.database import engine, get_session
from app.models.user import User
from app.models.hotel import Hotel

async def diagnostics():
    print("--- PROJECT DIAGNOSTICS ---")
    try:
        # 1. Connection check
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("1. Database Connection: OK")
            
            # 2. Schema check
            res = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
            tables = [r[0] for r in res]
            print(f"2. Public Tables: {tables}")
            
        # 3. Data count
        async for session in get_session():
            users_count = await session.execute(text("SELECT count(*) FROM users"))
            hotels_count = await session.execute(text("SELECT count(*) FROM hotels"))
            print(f"3. Record Counts: Users={users_count.scalar()}, Hotels={hotels_count.scalar()}")
            
            # 4. List recent users
            result = await session.execute(select(User).order_by(User.created_at.desc()).limit(5))
            recent_users = result.scalars().all()
            print("4. Recent Users:")
            for u in recent_users:
                print(f"   - {u.email} (ID: {u.id}, Hotel: {u.hotel_id})")
                
    except Exception as e:
        print(f"DIAGNOSTICS FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(diagnostics())
