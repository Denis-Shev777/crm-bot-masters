import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "master123")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/bot.db")
TIMEZONE = os.getenv("TIMEZONE", "Africa/Cairo")

# Booking settings
MAX_ACTIVE_BOOKINGS = 3
BOOKING_DAYS_AHEAD = 14
REMINDER_HOURS = [24, 3]  # Hours before appointment to send reminders

# Loyalty settings
LOYALTY_VISITS_FOR_DISCOUNT = 5
LOYALTY_DISCOUNT_PERCENT = 10
REFERRAL_DISCOUNT_PERCENT = 10
