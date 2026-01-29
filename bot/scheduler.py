"""Appointment reminders scheduler."""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from telebot.async_telebot import AsyncTeleBot

from config import TIMEZONE, REMINDER_HOURS
from database import get_user, mark_reminder_sent
from locales import get_text
from bot.utils import format_date

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


async def send_reminders(bot: AsyncTeleBot):
    """Send appointment reminders."""
    import aiosqlite
    from config import DATABASE_PATH

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    # Check for 24h reminders
    for hours in REMINDER_HOURS:
        target_time = now + timedelta(hours=hours)
        target_date = target_time.strftime("%Y-%m-%d")
        target_hour = target_time.hour

        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Get appointments that need reminders
            reminder_field = f"reminder_{hours}h_sent"
            cursor = await db.execute(f"""
                SELECT a.*, s.name_ru as service_name_ru, s.name_en as service_name_en,
                       u.telegram_id, u.language, u.name as client_name
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                JOIN users u ON a.client_id = u.id
                WHERE a.date = ? AND a.status NOT IN ('cancelled', 'completed')
                AND a.{reminder_field} = 0
                AND CAST(substr(a.time, 1, 2) AS INTEGER) BETWEEN ? AND ?
            """, (target_date, target_hour - 1, target_hour + 1))

            appointments = await cursor.fetchall()

            for appt in appointments:
                appt = dict(appt)
                lang = appt['language'] or 'ru'
                service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')

                # Determine which reminder to send
                reminder_key = f"reminder_{hours}h"
                address = "Hurghada, Egypt"  # TODO: Make configurable

                text = get_text(reminder_key, lang,
                                service=service_name,
                                time=appt['time'],
                                date=format_date(appt['date'], lang),
                                address=address)

                try:
                    await bot.send_message(appt['telegram_id'], text)
                    await mark_reminder_sent(appt['id'], hours)
                    logger.info(f"Sent {hours}h reminder to {appt['telegram_id']}")
                except Exception as e:
                    logger.error(f"Failed to send reminder: {e}")


async def request_reviews(bot: AsyncTeleBot):
    """Request reviews for completed appointments."""
    import aiosqlite
    from config import DATABASE_PATH
    from bot.keyboards.client import review_rating_keyboard

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    check_time = now - timedelta(hours=2)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get completed appointments without reviews
        cursor = await db.execute("""
            SELECT a.*, u.telegram_id, u.language
            FROM appointments a
            JOIN users u ON a.client_id = u.id
            LEFT JOIN reviews r ON r.appointment_id = a.id
            WHERE a.status = 'completed'
            AND r.id IS NULL
            AND a.date = ?
        """, (check_time.strftime("%Y-%m-%d"),))

        appointments = await cursor.fetchall()

        for appt in appointments:
            appt = dict(appt)
            lang = appt['language'] or 'ru'

            try:
                from locales import get_text
                await bot.send_message(
                    appt['telegram_id'],
                    get_text("ask_review", lang),
                    reply_markup=review_rating_keyboard(appt['id'])
                )
                logger.info(f"Requested review from {appt['telegram_id']}")
            except Exception as e:
                logger.error(f"Failed to request review: {e}")


def setup_scheduler(bot: AsyncTeleBot):
    """Setup and start the scheduler."""
    # Send reminders every 30 minutes
    scheduler.add_job(
        send_reminders,
        IntervalTrigger(minutes=30),
        args=[bot],
        id="reminders",
        replace_existing=True
    )

    # Request reviews every hour
    scheduler.add_job(
        request_reviews,
        IntervalTrigger(hours=1),
        args=[bot],
        id="reviews",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
