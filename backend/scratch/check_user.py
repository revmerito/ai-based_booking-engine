import asyncio
from sqlmodel import select
from app.core.database import get_session
from app.models.user import User

async def check_user(email):
    async for session in get_session():
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            print(f"User found: ID={user.id}, Email={user.email}, HotelID={user.hotel_id}")
        else:
            print(f"User NOT found: {email}")

if __name__ == "__main__":
    asyncio.run(check_user("raju@gmail.com"))
