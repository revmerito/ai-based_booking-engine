import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session as async_session_maker
from app.models.lead import Lead
from app.core.external_sync import sync_to_google_sheet
from sqlalchemy import select

async def test_leads_and_sync():
    print("Starting Leads and Google Sheets Sync Test...")
    
    # 1. Test Sync Function (Mock Webhook)
    # We use a dummy URL to see if it triggers without error
    print("Testing sync to Google Sheets (Mock)...")
    await sync_to_google_sheet("https://httpbin.org/post", {"test": "data", "guest": "John Doe"})
    print("Sync utility executed successfully.")

    # 2. Test DB Saving
    async with async_session_maker() as session:
        print("Testing Lead DB Save...")
        # Get a sample hotel ID
        from app.models.hotel import Hotel
        res = await session.execute(select(Hotel).limit(1))
        hotel = res.scalars().first()
        
        if not hotel:
            print("No hotel found in DB to test with.")
            return

        new_lead = Lead(
            hotel_id=hotel.id,
            guest_name="Test Guest",
            guest_phone="9876543210",
            guest_email="test@example.com",
            room_type_preference="Deluxe Room",
            ai_conversation_summary="Test lead from script"
        )
        session.add(new_lead)
        await session.commit()
        print(f"Lead saved to DB with ID: {new_lead.id}")

        # Verify query
        res = await session.execute(select(Lead).where(Lead.guest_name == "Test Guest"))
        saved_lead = res.scalars().first()
        if saved_lead:
            print(f"Verification successful: Found Lead '{saved_lead.guest_name}'")
        else:
            print("Verification failed: Lead not found in DB.")

if __name__ == "__main__":
    asyncio.run(test_leads_and_sync())
