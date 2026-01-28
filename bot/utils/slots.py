"""Utility functions for time slot management."""
from datetime import datetime, timedelta
from typing import List
import pytz
from config import TIMEZONE
from database import get_schedule, get_blocked_slots, get_booked_slots


def parse_time(time_str: str) -> datetime:
    """Parse time string to datetime object."""
    return datetime.strptime(time_str, "%H:%M")


def time_to_str(dt: datetime) -> str:
    """Convert datetime to time string."""
    return dt.strftime("%H:%M")


async def get_available_slots(date_str: str, service_duration: int) -> List[str]:
    """
    Get available time slots for a specific date and service duration.

    Args:
        date_str: Date in YYYY-MM-DD format
        service_duration: Service duration in minutes

    Returns:
        List of available time slots like ["09:00", "10:30", ...]
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Get day of week (0 = Monday)
    day_of_week = target_date.weekday()

    # Get schedule for this day
    schedule = await get_schedule()
    day_schedule = next((s for s in schedule if s['day_of_week'] == day_of_week), None)

    if not day_schedule:
        return []  # Day off

    # Working hours
    work_start = parse_time(day_schedule['start_time'])
    work_end = parse_time(day_schedule['end_time'])

    # Get blocked slots for this date
    blocked = await get_blocked_slots(date_str)

    # Check if full day is blocked
    for block in blocked:
        if block.get('is_full_day'):
            return []

    # Get booked slots
    booked = await get_booked_slots(date_str)

    # Generate all possible slots (30 min intervals)
    slot_interval = 30
    slots = []

    current = work_start
    while current + timedelta(minutes=service_duration) <= work_end:
        time_str = time_to_str(current)
        slot_end = current + timedelta(minutes=service_duration)

        # Check if this slot conflicts with any booking
        is_available = True

        # Check blocked slots
        for block in blocked:
            if block.get('start_time') and block.get('end_time'):
                block_start = parse_time(block['start_time'])
                block_end = parse_time(block['end_time'])
                if not (slot_end <= block_start or current >= block_end):
                    is_available = False
                    break

        # Check booked appointments
        if is_available:
            for booking in booked:
                book_start = parse_time(booking['time'])
                book_end = book_start + timedelta(minutes=booking['duration'])
                # Check overlap
                if not (slot_end <= book_start or current >= book_end):
                    is_available = False
                    break

        # Check if slot is in the past (for today)
        if is_available and target_date.date() == now.date():
            slot_datetime = tz.localize(datetime.combine(target_date.date(), current.time()))
            if slot_datetime <= now:
                is_available = False

        if is_available:
            slots.append(time_str)

        current += timedelta(minutes=slot_interval)

    return slots


def format_date(date_str: str, lang: str = "ru") -> str:
    """Format date for display."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if lang == "ru":
        months = ["янв", "фев", "мар", "апр", "мая", "июн",
                  "июл", "авг", "сен", "окт", "ноя", "дек"]
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    else:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return f"{dt.day} {months[dt.month - 1]} ({weekdays[dt.weekday()]})"
