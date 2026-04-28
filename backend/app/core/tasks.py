"""
Background Tasks Module
FastAPI BackgroundTasks ke liye heavy processing tasks.
"""
from app.core.database import async_session
from app.models.timeline import BookingTimeline
import logging

logger = logging.getLogger(__name__)

async def log_timeline_task(booking_id: str, event_type: str, old_value: str, new_value: str, message: str, changed_by: str):
    """
    Booking Timeline events ko background mein log karta hai.
    Main API response ko block nahi hone deta.
    """
    logger.info(f"Background Task: Logging timeline for booking {booking_id}")
    try:
        async with async_session() as session:
            timeline = BookingTimeline(
                booking_id=booking_id,
                event_type=event_type,
                old_value=old_value,
                new_value=new_value,
                message=message,
                changed_by=changed_by
            )
            session.add(timeline)
            await session.commit()
            logger.info(f"Background Task: Timeline logged successfully for {booking_id}")
    except Exception as e:
        logger.error(f"Background Task Error: Failed to log timeline: {e}")


async def send_email_placeholder(email: str, subject: str, body: str):
    """
    Email bhejne ka placeholder.
    In production, yahan Resend/SendGrid ka API call aayega.
    """
    logger.info(f"Background Task: Sending email to {email} - Subject: {subject}")
    # Simulating email delay
    import asyncio
    await asyncio.sleep(1) 
    logger.info(f"Background Task: Email sent successfully to {email}")
