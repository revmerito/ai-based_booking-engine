import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session as async_session_maker
from app.core.guest_agent import create_guest_agent_graph
from sqlalchemy import select
from app.models.hotel import Hotel

async def test_agent_creation():
    print("Testing Guest Agent Graph Creation...")
    async with async_session_maker() as session:
        res = await session.execute(select(Hotel).limit(1))
        hotel = res.scalars().first()
        if not hotel:
            print("No hotel found.")
            return

        try:
            graph = create_guest_agent_graph(session, hotel.id)
            print("Graph created successfully!")
            
            print("Testing invocation with 'hello'...")
            from langchain_core.messages import HumanMessage
            response = await graph.ainvoke({"messages": [HumanMessage(content="hello")]})
            print(f"Response received: {response['messages'][-1].content}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_creation())
