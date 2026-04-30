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
    print("Testing Guest Agent with DB Settings...")
    async with async_session_maker() as session:
        # Get first hotel
        res = await session.execute(select(Hotel).limit(1))
        hotel = res.scalars().first()
        if not hotel:
            print("No hotel found.")
            return

        # Get integration settings
        int_res = await session.execute(select(IntegrationSettings).where(IntegrationSettings.hotel_id == hotel.id))
        integration = int_res.scalar_one_or_none()
        
        if not integration:
            print("No integration settings found for this hotel.")
            return
            
        print(f"Hotel: {hotel.name}")
        print(f"Provider: {integration.ai_provider}")
        print(f"Model: {integration.ai_model}")
        print(f"Has API Key: {bool(integration.ai_api_key)}")
        print(f"Base URL: {integration.ai_base_url}")

        try:
            agent = create_guest_agent_graph(
                session, 
                hotel.id, 
                integration.ai_provider,
                integration.ai_api_key,
                integration.ai_model,
                integration.ai_base_url
            )
            
            if not agent:
                print("Agent failed to initialize (returned None).")
                return
                
            print("Graph created successfully!")
            from langchain_core.messages import HumanMessage
            response = await agent.ainvoke({"messages": [HumanMessage(content="hello")]})
            print(f"Response received: {response['messages'][-1].content}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_agent())
