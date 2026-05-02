import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session as async_session_maker
from app.core.guest_agent import create_guest_agent_graph
from sqlalchemy import select
from app.models.hotel import Hotel
from app.models.integration import IntegrationSettings

async def test_live_agent():
    print("Testing ALL Hotels AI Settings...")
    async with async_session_maker() as session:
        # Get all hotels
        res = await session.execute(select(Hotel))
        hotels = res.scalars().all()
        
        for hotel in hotels:
            print("-" * 30)
            print(f"Hotel: {hotel.name} (Slug: {hotel.slug})")
            print(f"Provider: {hotel.ai_provider}")
            print(f"Model: {hotel.ai_model}")
            print(f"Has API Key: {bool(hotel.ai_api_key)}")
            
            # Get integration settings for detailed check
            int_res = await session.execute(select(IntegrationSettings).where(IntegrationSettings.hotel_id == hotel.id))
            integration = int_res.scalar_one_or_none()
            if integration:
                print(f"Integration Model: {integration.ai_model}")
                print(f"Integration Key: {bool(integration.ai_api_key)}")
            else:
                print("No integration settings found.")

if __name__ == "__main__":
    asyncio.run(test_live_agent())
