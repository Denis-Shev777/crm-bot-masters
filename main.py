"""
Beauty Master CRM Bot
Telegram bot for appointment booking and management.

Usage:
    python main.py
"""
import logging
import sys
import os
import asyncio

import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN
from bot.scheduler import setup_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


def main():
    """Main function to start the bot."""
    # Check token
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found! Please set it in .env file")
        sys.exit(1)

    # Initialize database
    logger.info("Initializing database...")
    from database import init_db, create_demo_data
    run_async(init_db())

    # Create demo data if needed
    logger.info("Creating demo data...")
    run_async(create_demo_data())

    # Initialize bot with state storage
    state_storage = StateMemoryStorage()
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", state_storage=state_storage)

    # Register handlers
    from bot.handlers import client, master
    client.register_handlers(bot)
    master.register_handlers(bot)

    # Setup scheduler for reminders
    setup_scheduler(bot)

    # Start polling
    logger.info("Bot starting...")
    try:
        bot.infinity_polling()
    finally:
        stop_scheduler()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
