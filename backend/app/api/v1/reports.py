"""
Reports/Analytics Endpoints
Real-time dashboard statistics.
"""
from typing import List, Dict, Any
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Query, Depends
from sqlmodel import select, func, and_

from app.api.deps import CurrentUser, DbSession
from app.models.booking import Booking, BookingStatus
from app.models.room import RoomType

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: CurrentUser,
    session: DbSession,
    days: int = 30
):
    """
    Get consolidated dashboard stats for the last N days.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 1. Fetch relevant bookings
    query = select(Booking).where(
        Booking.hotel_id == current_user.hotel_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]),
        Booking.check_in >= start_date,
        Booking.check_in <= end_date
    )
    result = await session.execute(query)
    bookings = result.scalars().all()
    
    # 2. Total Revenue & Bookings
    total_revenue = sum(b.total_amount for b in bookings)
    total_bookings = len(bookings)
    
    # 3. Calculate Daily Stats for Charts
    # Initialize dictionary for last N days
    daily_stats = {}
    for i in range(days + 1):
        d = start_date + timedelta(days=i)
        daily_stats[d] = {"date": d.isoformat(), "revenue": 0, "occupancy": 0, "bookings": 0}
        
    # Get Total Inventory for Occupancy Calc
    # This is a simplification (assumes inventory constant)
    inventory_result = await session.execute(
        select(func.sum(RoomType.total_inventory)).where(RoomType.hotel_id == current_user.hotel_id)
    )
    total_inventory = inventory_result.scalar() or 0
    
    # Aggregate data
    for booking in bookings:
        # For revenue attribute to check-in date (simple attribution)
        if booking.check_in in daily_stats:
            daily_stats[booking.check_in]["revenue"] += booking.total_amount
            daily_stats[booking.check_in]["bookings"] += 1
            
            # For occupancy, we should ideally span the range, but for simple chart:
            # We count nights falling in this range? 
            # Let's simple it: Count check-ins as "occupancy" activity for valid chart (trend)
            # Or better: Check nights.
            
    # Accurate Occupancy Loop
    # Loop dates, count rooms occupied
    if total_inventory > 0:
        for d_key in daily_stats.keys():
            occupied = 0
            for b in bookings:
                if b.check_in <= d_key < b.check_out:
                    # Count rooms in this booking
                    # Each booking has 'rooms' list
                    occupied += len(b.rooms)
            
            daily_stats[d_key]["occupancy"] = min(100, int((occupied / total_inventory) * 100))

    # Convert to list sorted by date
    chart_data = sorted(daily_stats.values(), key=lambda x: x["date"])
    
    # Occupancy Rate (Average of period)
    avg_occupancy = sum(d["occupancy"] for d in chart_data) / len(chart_data) if chart_data else 0
    
    return {
        "summary": {
            "totalRevenue": total_revenue,
            "totalBookings": total_bookings,
            "occupancyRate": int(avg_occupancy),
            "netProfit": int(total_revenue * 0.7) # Simplified profit margin (Production tip: should include costs/expenses)
        },
        "revenueChart": chart_data,
        "occupancyChart": chart_data
    }

@router.get("/occupancy")
async def get_occupancy_report(
    current_user: CurrentUser,
    session: DbSession,
    start_date: date = Query(default=None),
    end_date: date = Query(default=None)
):
    """
    Get occupancy report for a date range.
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get total inventory
    inventory_result = await session.execute(
        select(func.sum(RoomType.total_inventory)).where(RoomType.hotel_id == current_user.hotel_id)
    )
    total_inventory = inventory_result.scalar() or 0
    
    if total_inventory == 0:
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_inventory": 0,
            "average_occupancy": 0,
            "daily_occupancy": []
        }
    
    # Get bookings in range
    query = select(Booking).where(
        Booking.hotel_id == current_user.hotel_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT]),
        Booking.check_out > start_date,
        Booking.check_in < end_date
    )
    result = await session.execute(query)
    bookings = result.scalars().all()
    
    # Calculate daily occupancy
    daily_occupancy = []
    current_date = start_date
    total_occupancy = 0
    days_count = 0
    
    while current_date <= end_date:
        occupied = 0
        for booking in bookings:
            if booking.check_in <= current_date < booking.check_out:
                occupied += len(booking.rooms) if hasattr(booking, 'rooms') else 1
        
        occupancy_rate = min(100, int((occupied / total_inventory) * 100))
        daily_occupancy.append({
            "date": current_date.isoformat(),
            "occupied_rooms": occupied,
            "available_rooms": total_inventory - occupied,
            "occupancy_rate": occupancy_rate
        })
        
        total_occupancy += occupancy_rate
        days_count += 1
        current_date += timedelta(days=1)
    
    average_occupancy = int(total_occupancy / days_count) if days_count > 0 else 0
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_inventory": total_inventory,
        "average_occupancy": average_occupancy,
        "daily_occupancy": daily_occupancy
    }

