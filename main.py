"""
Beauty Master CRM Bot
Telegram bot for appointment booking and management.

Usage:
    python main.py
"""
import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN
from database import init_db, create_demo_data
from bot.handlers import client, master
from bot.scheduler import setup_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    # Check token
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found! Please set it in .env file")
        sys.exit(1)

    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Create demo data if needed
    logger.info("Creating demo data...")
    await create_demo_data()

    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    dp.include_router(client.router)
    dp.include_router(master.router)

    # Setup scheduler for reminders
    setup_scheduler(bot)

    # Start polling
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        stop_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
