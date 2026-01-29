"""Client handlers for the bot."""
import asyncio
import telebot
from telebot.types import Message, CallbackQuery
from telebot.handler_backends import State, StatesGroup

from database import (
    get_user, create_user, update_user,
    get_categories, get_services, get_service,
    get_appointments, get_appointment, create_appointment,
    update_appointment, count_active_appointments, get_user_by_id
)
from locales import get_text, get_service_name, get_category_name, get_status_text
from bot.keyboards.client import (
    language_keyboard, phone_keyboard, main_menu_keyboard,
    categories_keyboard, services_keyboard, service_detail_keyboard,
    calendar_keyboard, time_slots_keyboard, booking_confirm_keyboard,
    my_bookings_keyboard, appointment_detail_keyboard, cancel_confirm_keyboard
)
from bot.utils import get_available_slots, format_date
from config import MAX_ACTIVE_BOOKINGS, BOOKING_DAYS_AHEAD, ADMIN_IDS, REFERRAL_DISCOUNT_PERCENT


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


class Registration(StatesGroup):
    """Registration states."""
    language = State()
    name = State()
    phone = State()


class BookingState(StatesGroup):
    """Booking flow states."""
    service_id = State()
    category_id = State()


# Store for user data during registration/booking
user_data = {}


def get_user_data(user_id: int) -> dict:
    """Get user data from storage."""
    if user_id not in user_data:
        user_data[user_id] = {}
    return user_data[user_id]


def clear_user_data(user_id: int):
    """Clear user data from storage."""
    if user_id in user_data:
        del user_data[user_id]


def register_handlers(bot: telebot.TeleBot):
    """Register all client handlers."""

    # ============ START & REGISTRATION ============

    @bot.message_handler(commands=['start'])
    def cmd_start(message: Message):
        """Handle /start command."""
        user = run_async(get_user(message.from_user.id))

        # Check for referral code in deep link
        referral_code = None
        if message.text and len(message.text.split()) > 1:
            referral_code = message.text.split()[1]
            data = get_user_data(message.from_user.id)
            data['referral_code'] = referral_code

        if user:
            # Existing user - show main menu
            bot.send_message(
                message.chat.id,
                get_text("main_menu", user['language']),
                reply_markup=main_menu_keyboard(user['language'])
            )
        else:
            # New user - start registration
            bot.send_message(
                message.chat.id,
                get_text("welcome", "ru"),
                reply_markup=language_keyboard()
            )
            bot.set_state(message.from_user.id, Registration.language, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("lang:"), state=Registration.language)
    def process_language(callback: CallbackQuery):
        """Process language selection during registration."""
        lang = callback.data.split(":")[1]
        data = get_user_data(callback.from_user.id)
        data['language'] = lang
        bot.edit_message_text(
            get_text("ask_name", lang),
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.set_state(callback.from_user.id, Registration.name, callback.message.chat.id)
        bot.answer_callback_query(callback.id)

    @bot.message_handler(state=Registration.name)
    def process_name(message: Message):
        """Process name input."""
        data = get_user_data(message.from_user.id)
        lang = data.get('language', 'ru')
        data['name'] = message.text
        bot.send_message(
            message.chat.id,
            get_text("ask_phone", lang),
            reply_markup=phone_keyboard(lang)
        )
        bot.set_state(message.from_user.id, Registration.phone, message.chat.id)

    @bot.message_handler(content_types=['contact'], state=Registration.phone)
    def process_phone_contact(message: Message):
        """Process phone from contact."""
        data = get_user_data(message.from_user.id)
        lang = data.get('language', 'ru')
        name = data.get('name')
        phone = message.contact.phone_number
        referral_code = data.get('referral_code')

        run_async(create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=name,
            phone=phone,
            language=lang,
            referral_code=referral_code
        ))

        clear_user_data(message.from_user.id)
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(
            message.chat.id,
            get_text("registration_complete", lang, name=name),
            reply_markup=main_menu_keyboard(lang)
        )

    @bot.message_handler(state=Registration.phone)
    def process_phone_text(message: Message):
        """Process phone from text."""
        data = get_user_data(message.from_user.id)
        lang = data.get('language', 'ru')
        name = data.get('name')
        phone = message.text
        referral_code = data.get('referral_code')

        run_async(create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=name,
            phone=phone,
            language=lang,
            referral_code=referral_code
        ))

        clear_user_data(message.from_user.id)
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(
            message.chat.id,
            get_text("registration_complete", lang, name=name),
            reply_markup=main_menu_keyboard(lang)
        )

    # ============ MAIN MENU ============

    @bot.message_handler(func=lambda m: m.text in ["📅 Записаться", "📅 Book Now"])
    def show_categories(message: Message):
        """Show service categories."""
        user = run_async(get_user(message.from_user.id))
        if not user:
            bot.send_message(message.chat.id, "Please /start first")
            return

        lang = user['language']
        categories = run_async(get_categories())

        bot.send_message(
            message.chat.id,
            get_text("choose_category", lang),
            reply_markup=categories_keyboard(categories, lang)
        )

    @bot.message_handler(func=lambda m: m.text in ["💰 Услуги и цены", "💰 Services & Prices"])
    def show_services_catalog(message: Message):
        """Show all services."""
        user = run_async(get_user(message.from_user.id))
        if not user:
            bot.send_message(message.chat.id, "Please /start first")
            return

        lang = user['language']
        categories = run_async(get_categories())

        bot.send_message(
            message.chat.id,
            get_text("choose_category", lang),
            reply_markup=categories_keyboard(categories, lang)
        )

    @bot.message_handler(func=lambda m: m.text in ["📖 Мои записи", "📖 My Bookings"])
    def show_my_bookings(message: Message):
        """Show user's bookings."""
        user = run_async(get_user(message.from_user.id))
        if not user:
            bot.send_message(message.chat.id, "Please /start first")
            return

        lang = user['language']
        appointments = run_async(get_appointments(client_id=user['id'], upcoming_only=True))

        if not appointments:
            bot.send_message(message.chat.id, get_text("no_bookings", lang))
            return

        bot.send_message(
            message.chat.id,
            get_text("your_bookings", lang),
            reply_markup=my_bookings_keyboard(appointments, lang)
        )

    @bot.message_handler(func=lambda m: m.text in ["📞 Контакты", "📞 Contacts"])
    def show_contacts(message: Message):
        """Show contact information."""
        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        address = "Hurghada, Egypt"
        phone = "+20 XXX XXX XXXX"
        schedule = "Mon-Sat: 09:00 - 18:00"

        bot.send_message(
            message.chat.id,
            get_text("contacts_info", lang, address=address, phone=phone, schedule=schedule)
        )

    @bot.message_handler(func=lambda m: m.text in ["🌐 Язык", "🌐 Language"])
    def change_language(message: Message):
        """Change language."""
        bot.send_message(
            message.chat.id,
            get_text("welcome", "ru"),
            reply_markup=language_keyboard()
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("lang:"))
    def process_language_change(callback: CallbackQuery):
        """Process language change for existing user."""
        user = run_async(get_user(callback.from_user.id))
        if not user:
            bot.answer_callback_query(callback.id)
            return

        lang = callback.data.split(":")[1]
        run_async(update_user(callback.from_user.id, language=lang))

        bot.edit_message_text(
            get_text("main_menu", lang),
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.send_message(
            callback.message.chat.id,
            get_text("main_menu", lang),
            reply_markup=main_menu_keyboard(lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.message_handler(func=lambda m: m.text in ["👥 Пригласить друга", "👥 Invite Friend"])
    def show_referral(message: Message):
        """Show referral link."""
        user = run_async(get_user(message.from_user.id))
        if not user:
            bot.send_message(message.chat.id, "Please /start first")
            return

        lang = user['language']
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user['referral_code']}"

        bot.send_message(
            message.chat.id,
            get_text("referral_info", lang, link=link, discount=REFERRAL_DISCOUNT_PERCENT)
        )

    # ============ CATEGORIES & SERVICES ============

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
    def show_category_services(callback: CallbackQuery):
        """Show services in category."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        category_id = int(callback.data.split(":")[1])
        data = get_user_data(callback.from_user.id)
        data['category_id'] = category_id

        services = run_async(get_services(category_id=category_id))

        bot.edit_message_text(
            get_text("choose_service", lang),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=services_keyboard(services, lang, category_id)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("srv:"))
    def show_service_detail(callback: CallbackQuery):
        """Show service details."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        service_id = int(callback.data.split(":")[1])
        service = run_async(get_service(service_id))

        if not service:
            bot.answer_callback_query(callback.id, "Service not found")
            return

        data = get_user_data(callback.from_user.id)
        data['service_id'] = service_id

        name = get_service_name(service, lang)
        desc = service.get(f'description_{lang}') or service.get('description_ru') or ""
        price_usd = service.get('price_usd') or int(service['price_egp'] / 50)

        text = get_text("service_info", lang,
                        name=name,
                        description=desc,
                        duration=service['duration'],
                        price_egp=int(service['price_egp']),
                        price_usd=price_usd)

        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=service_detail_keyboard(service_id, lang)
        )
        bot.answer_callback_query(callback.id)

    # ============ BOOKING FLOW ============

    @bot.callback_query_handler(func=lambda c: c.data.startswith("book:"))
    def start_booking(callback: CallbackQuery):
        """Start booking process - show calendar."""
        user = run_async(get_user(callback.from_user.id))
        if not user:
            bot.answer_callback_query(callback.id, "Please /start first")
            return

        lang = user['language']
        service_id = int(callback.data.split(":")[1])

        # Check booking limit
        active_count = run_async(count_active_appointments(user['id']))
        if active_count >= MAX_ACTIVE_BOOKINGS:
            bot.answer_callback_query(
                callback.id,
                get_text("booking_limit", lang, count=active_count, max=MAX_ACTIVE_BOOKINGS),
                show_alert=True
            )
            return

        data = get_user_data(callback.from_user.id)
        data['service_id'] = service_id

        bot.edit_message_text(
            get_text("choose_date", lang),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=calendar_keyboard(lang, BOOKING_DAYS_AHEAD, service_id)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("date:"))
    def select_date(callback: CallbackQuery):
        """Process date selection - show available times."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        parts = callback.data.split(":")
        date_str = parts[1]
        service_id = int(parts[2])

        service = run_async(get_service(service_id))
        if not service:
            bot.answer_callback_query(callback.id, "Service not found")
            return

        # Get available slots
        slots = run_async(get_available_slots(date_str, service['duration']))

        data = get_user_data(callback.from_user.id)
        data['date'] = date_str
        data['service_id'] = service_id

        if not slots:
            bot.answer_callback_query(
                callback.id,
                get_text("no_slots", lang),
                show_alert=True
            )
            return

        bot.edit_message_text(
            f"{get_text('choose_time', lang)}\n📅 {format_date(date_str, lang)}",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=time_slots_keyboard(slots, date_str, service_id, lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("time|"))
    def select_time(callback: CallbackQuery):
        """Process time selection - show confirmation."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        parts = callback.data.split("|")
        date_str = parts[1]
        time_str = parts[2]
        service_id = int(parts[3])

        service = run_async(get_service(service_id))
        if not service:
            bot.answer_callback_query(callback.id, "Service not found")
            return

        service_name = get_service_name(service, lang)

        data = get_user_data(callback.from_user.id)
        data['time'] = time_str

        text = get_text("booking_confirm", lang,
                        service=service_name,
                        date=format_date(date_str, lang),
                        time=time_str,
                        price=int(service['price_egp']))

        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=booking_confirm_keyboard(service_id, date_str, time_str, lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_book|"))
    def confirm_booking(callback: CallbackQuery):
        """Confirm and create booking."""
        user = run_async(get_user(callback.from_user.id))
        if not user:
            bot.answer_callback_query(callback.id, "Please /start first")
            return

        lang = user['language']
        parts = callback.data.split("|")
        service_id = int(parts[1])
        date_str = parts[2]
        time_str = parts[3]

        service = run_async(get_service(service_id))
        if not service:
            bot.answer_callback_query(callback.id, "Service not found")
            return

        # Create appointment
        appointment_id = run_async(create_appointment(
            client_id=user['id'],
            service_id=service_id,
            date_str=date_str,
            time_str=time_str
        ))

        service_name = get_service_name(service, lang)

        # Notify client
        bot.edit_message_text(
            get_text("booking_created", lang,
                     service=service_name,
                     date=format_date(date_str, lang),
                     time=time_str),
            callback.message.chat.id,
            callback.message.message_id
        )

        # Notify master (admin)
        from bot.handlers.master import notify_master_new_booking
        notify_master_new_booking(bot, appointment_id)

        clear_user_data(callback.from_user.id)
        bot.answer_callback_query(callback.id)

    # ============ MY BOOKINGS MANAGEMENT ============

    @bot.callback_query_handler(func=lambda c: c.data.startswith("appt:"))
    def show_appointment_detail(callback: CallbackQuery):
        """Show appointment details."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        appointment_id = int(callback.data.split(":")[1])
        appt = run_async(get_appointment(appointment_id))

        if not appt:
            bot.answer_callback_query(callback.id, "Appointment not found")
            return

        service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')
        status = get_status_text(appt['status'], lang)

        text = get_text("booking_item", lang,
                        service=service_name,
                        date=format_date(appt['date'], lang),
                        time=appt['time'],
                        status=status)

        can_cancel = appt['status'] not in ['cancelled', 'completed']

        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=appointment_detail_keyboard(appointment_id, lang, can_cancel)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_appt:"))
    def request_cancel_appointment(callback: CallbackQuery):
        """Request appointment cancellation."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        appointment_id = int(callback.data.split(":")[1])

        bot.edit_message_text(
            get_text("confirm_cancel", lang),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=cancel_confirm_keyboard(appointment_id, lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_cancel:"))
    def confirm_cancel_appointment(callback: CallbackQuery):
        """Confirm appointment cancellation."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        appointment_id = int(callback.data.split(":")[1])

        run_async(update_appointment(appointment_id, status='cancelled'))

        bot.edit_message_text(
            get_text("booking_cancelled", lang),
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.answer_callback_query(callback.id)

    # ============ BACK NAVIGATION ============

    @bot.callback_query_handler(func=lambda c: c.data.startswith("back:"))
    def handle_back(callback: CallbackQuery):
        """Handle back navigation."""
        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        target = callback.data.split(":")[1]
        data = get_user_data(callback.from_user.id)

        if target == "main":
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(
                callback.message.chat.id,
                get_text("main_menu", lang),
                reply_markup=main_menu_keyboard(lang)
            )
        elif target == "categories":
            categories = run_async(get_categories())
            bot.edit_message_text(
                get_text("choose_category", lang),
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=categories_keyboard(categories, lang)
            )
        elif target == "services":
            category_id = data.get('category_id')
            if category_id:
                services = run_async(get_services(category_id=category_id))
                bot.edit_message_text(
                    get_text("choose_service", lang),
                    callback.message.chat.id,
                    callback.message.message_id,
                    reply_markup=services_keyboard(services, lang, category_id)
                )
        elif target == "service_detail":
            service_id = data.get('service_id')
            if service_id:
                service = run_async(get_service(service_id))
                if service:
                    name = get_service_name(service, lang)
                    desc = service.get(f'description_{lang}') or service.get('description_ru') or ""
                    price_usd = service.get('price_usd') or int(service['price_egp'] / 50)

                    text = get_text("service_info", lang,
                                    name=name,
                                    description=desc,
                                    duration=service['duration'],
                                    price_egp=int(service['price_egp']),
                                    price_usd=price_usd)

                    bot.edit_message_text(
                        text,
                        callback.message.chat.id,
                        callback.message.message_id,
                        reply_markup=service_detail_keyboard(service_id, lang)
                    )
        elif target == "my_bookings":
            appointments = run_async(get_appointments(client_id=user['id'], upcoming_only=True))
            if appointments:
                bot.edit_message_text(
                    get_text("your_bookings", lang),
                    callback.message.chat.id,
                    callback.message.message_id,
                    reply_markup=my_bookings_keyboard(appointments, lang)
                )
            else:
                bot.edit_message_text(
                    get_text("no_bookings", lang),
                    callback.message.chat.id,
                    callback.message.message_id
                )

        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data == "noop")
    def noop_callback(callback: CallbackQuery):
        """Handle no-operation callbacks."""
        bot.answer_callback_query(callback.id)
