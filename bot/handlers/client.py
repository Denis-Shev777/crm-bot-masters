"""Client handlers for the bot."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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

router = Router()


class Registration(StatesGroup):
    """Registration states."""
    language = State()
    name = State()
    phone = State()


class BookingState(StatesGroup):
    """Booking flow states."""
    service_id = State()
    category_id = State()


# ============ START & REGISTRATION ============

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    user = await get_user(message.from_user.id)

    # Check for referral code in deep link
    referral_code = None
    if message.text and len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        await state.update_data(referral_code=referral_code)

    if user:
        # Existing user - show main menu
        await message.answer(
            get_text("main_menu", user['language']),
            reply_markup=main_menu_keyboard(user['language'])
        )
    else:
        # New user - start registration
        await message.answer(
            get_text("welcome", "ru"),
            reply_markup=language_keyboard()
        )
        await state.set_state(Registration.language)


@router.callback_query(F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    """Process language selection."""
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await callback.message.edit_text(get_text("ask_name", lang))
    await state.set_state(Registration.name)
    await callback.answer()


@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    """Process name input."""
    data = await state.get_data()
    lang = data.get('language', 'ru')
    await state.update_data(name=message.text)
    await message.answer(
        get_text("ask_phone", lang),
        reply_markup=phone_keyboard(lang)
    )
    await state.set_state(Registration.phone)


@router.message(Registration.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Process phone from contact."""
    data = await state.get_data()
    lang = data.get('language', 'ru')
    name = data.get('name')
    phone = message.contact.phone_number
    referral_code = data.get('referral_code')

    await create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=name,
        phone=phone,
        language=lang,
        referral_code=referral_code
    )

    await state.clear()
    await message.answer(
        get_text("registration_complete", lang, name=name),
        reply_markup=main_menu_keyboard(lang)
    )


@router.message(Registration.phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Process phone from text."""
    data = await state.get_data()
    lang = data.get('language', 'ru')
    name = data.get('name')
    phone = message.text
    referral_code = data.get('referral_code')

    await create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        name=name,
        phone=phone,
        language=lang,
        referral_code=referral_code
    )

    await state.clear()
    await message.answer(
        get_text("registration_complete", lang, name=name),
        reply_markup=main_menu_keyboard(lang)
    )


# ============ MAIN MENU ============

@router.message(F.text.in_(["📅 Записаться", "📅 Book Now"]))
async def show_categories(message: Message):
    """Show service categories."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start first")
        return

    lang = user['language']
    categories = await get_categories()

    await message.answer(
        get_text("choose_category", lang),
        reply_markup=categories_keyboard(categories, lang)
    )


@router.message(F.text.in_(["💰 Услуги и цены", "💰 Services & Prices"]))
async def show_services_catalog(message: Message):
    """Show all services."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start first")
        return

    lang = user['language']
    categories = await get_categories()

    await message.answer(
        get_text("choose_category", lang),
        reply_markup=categories_keyboard(categories, lang)
    )


@router.message(F.text.in_(["📖 Мои записи", "📖 My Bookings"]))
async def show_my_bookings(message: Message):
    """Show user's bookings."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start first")
        return

    lang = user['language']
    appointments = await get_appointments(client_id=user['id'], upcoming_only=True)

    if not appointments:
        await message.answer(get_text("no_bookings", lang))
        return

    await message.answer(
        get_text("your_bookings", lang),
        reply_markup=my_bookings_keyboard(appointments, lang)
    )


@router.message(F.text.in_(["📞 Контакты", "📞 Contacts"]))
async def show_contacts(message: Message):
    """Show contact information."""
    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    # TODO: Make these configurable
    address = "Hurghada, Egypt"
    phone = "+20 XXX XXX XXXX"
    schedule = "Mon-Sat: 09:00 - 18:00"

    await message.answer(
        get_text("contacts_info", lang, address=address, phone=phone, schedule=schedule)
    )


@router.message(F.text.in_(["🌐 Язык", "🌐 Language"]))
async def change_language(message: Message):
    """Change language."""
    await message.answer(
        get_text("welcome", "ru"),
        reply_markup=language_keyboard()
    )


@router.callback_query(F.data.startswith("lang:"))
async def process_language_change(callback: CallbackQuery):
    """Process language change for existing user."""
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    lang = callback.data.split(":")[1]
    await update_user(callback.from_user.id, language=lang)

    await callback.message.edit_text(get_text("main_menu", lang))
    await callback.message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_keyboard(lang)
    )
    await callback.answer()


@router.message(F.text.in_(["👥 Пригласить друга", "👥 Invite Friend"]))
async def show_referral(message: Message):
    """Show referral link."""
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start first")
        return

    lang = user['language']
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user['referral_code']}"

    await message.answer(
        get_text("referral_info", lang, link=link, discount=REFERRAL_DISCOUNT_PERCENT)
    )


# ============ CATEGORIES & SERVICES ============

@router.callback_query(F.data.startswith("cat:"))
async def show_category_services(callback: CallbackQuery, state: FSMContext):
    """Show services in category."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)

    services = await get_services(category_id=category_id)

    await callback.message.edit_text(
        get_text("choose_service", lang),
        reply_markup=services_keyboard(services, lang, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("srv:"))
async def show_service_detail(callback: CallbackQuery, state: FSMContext):
    """Show service details."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)

    if not service:
        await callback.answer("Service not found")
        return

    await state.update_data(service_id=service_id)

    name = get_service_name(service, lang)
    desc = service.get(f'description_{lang}') or service.get('description_ru') or ""
    price_usd = service.get('price_usd') or int(service['price_egp'] / 50)

    text = get_text("service_info", lang,
                    name=name,
                    description=desc,
                    duration=service['duration'],
                    price_egp=int(service['price_egp']),
                    price_usd=price_usd)

    await callback.message.edit_text(
        text,
        reply_markup=service_detail_keyboard(service_id, lang)
    )
    await callback.answer()


# ============ BOOKING FLOW ============

@router.callback_query(F.data.startswith("book:"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Start booking process - show calendar."""
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Please /start first")
        return

    lang = user['language']
    service_id = int(callback.data.split(":")[1])

    # Check booking limit
    active_count = await count_active_appointments(user['id'])
    if active_count >= MAX_ACTIVE_BOOKINGS:
        await callback.answer(
            get_text("booking_limit", lang, count=active_count, max=MAX_ACTIVE_BOOKINGS),
            show_alert=True
        )
        return

    await state.update_data(service_id=service_id)

    await callback.message.edit_text(
        get_text("choose_date", lang),
        reply_markup=calendar_keyboard(lang, BOOKING_DAYS_AHEAD, service_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    """Process date selection - show available times."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    parts = callback.data.split(":")
    date_str = parts[1]
    service_id = int(parts[2])

    service = await get_service(service_id)
    if not service:
        await callback.answer("Service not found")
        return

    # Get available slots
    slots = await get_available_slots(date_str, service['duration'])

    await state.update_data(date=date_str, service_id=service_id)

    if not slots:
        await callback.answer(get_text("no_slots", lang), show_alert=True)
        return

    await callback.message.edit_text(
        f"{get_text('choose_time', lang)}\n📅 {format_date(date_str, lang)}",
        reply_markup=time_slots_keyboard(slots, date_str, service_id, lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time:"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Process time selection - show confirmation."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    parts = callback.data.split(":")
    date_str = parts[1]
    time_str = parts[2]
    service_id = int(parts[3])

    service = await get_service(service_id)
    if not service:
        await callback.answer("Service not found")
        return

    service_name = get_service_name(service, lang)

    await state.update_data(time=time_str)

    text = get_text("booking_confirm", lang,
                    service=service_name,
                    date=format_date(date_str, lang),
                    time=time_str,
                    price=int(service['price_egp']))

    await callback.message.edit_text(
        text,
        reply_markup=booking_confirm_keyboard(service_id, date_str, time_str, lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_book:"))
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Confirm and create booking."""
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Please /start first")
        return

    lang = user['language']
    parts = callback.data.split(":")
    service_id = int(parts[1])
    date_str = parts[2]
    time_str = parts[3]

    service = await get_service(service_id)
    if not service:
        await callback.answer("Service not found")
        return

    # Create appointment
    appointment_id = await create_appointment(
        client_id=user['id'],
        service_id=service_id,
        date_str=date_str,
        time_str=time_str
    )

    service_name = get_service_name(service, lang)

    # Notify client
    await callback.message.edit_text(
        get_text("booking_created", lang,
                 service=service_name,
                 date=format_date(date_str, lang),
                 time=time_str)
    )

    # Notify master (admin)
    from bot.handlers.master import notify_master_new_booking
    await notify_master_new_booking(callback.bot, appointment_id)

    await state.clear()
    await callback.answer()


# ============ MY BOOKINGS MANAGEMENT ============

@router.callback_query(F.data.startswith("appt:"))
async def show_appointment_detail(callback: CallbackQuery):
    """Show appointment details."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    appointment_id = int(callback.data.split(":")[1])
    appt = await get_appointment(appointment_id)

    if not appt:
        await callback.answer("Appointment not found")
        return

    service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')
    status = get_status_text(appt['status'], lang)

    text = get_text("booking_item", lang,
                    service=service_name,
                    date=format_date(appt['date'], lang),
                    time=appt['time'],
                    status=status)

    can_cancel = appt['status'] not in ['cancelled', 'completed']

    await callback.message.edit_text(
        text,
        reply_markup=appointment_detail_keyboard(appointment_id, lang, can_cancel)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_appt:"))
async def request_cancel_appointment(callback: CallbackQuery):
    """Request appointment cancellation."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    appointment_id = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        get_text("confirm_cancel", lang),
        reply_markup=cancel_confirm_keyboard(appointment_id, lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_cancel:"))
async def confirm_cancel_appointment(callback: CallbackQuery):
    """Confirm appointment cancellation."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    appointment_id = int(callback.data.split(":")[1])

    await update_appointment(appointment_id, status='cancelled')

    await callback.message.edit_text(get_text("booking_cancelled", lang))
    await callback.answer()


# ============ BACK NAVIGATION ============

@router.callback_query(F.data.startswith("back:"))
async def handle_back(callback: CallbackQuery, state: FSMContext):
    """Handle back navigation."""
    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    target = callback.data.split(":")[1]
    data = await state.get_data()

    if target == "main":
        await callback.message.delete()
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=main_menu_keyboard(lang)
        )
    elif target == "categories":
        categories = await get_categories()
        await callback.message.edit_text(
            get_text("choose_category", lang),
            reply_markup=categories_keyboard(categories, lang)
        )
    elif target == "services":
        category_id = data.get('category_id')
        if category_id:
            services = await get_services(category_id=category_id)
            await callback.message.edit_text(
                get_text("choose_service", lang),
                reply_markup=services_keyboard(services, lang, category_id)
            )
    elif target == "service_detail":
        service_id = data.get('service_id')
        if service_id:
            service = await get_service(service_id)
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

                await callback.message.edit_text(
                    text,
                    reply_markup=service_detail_keyboard(service_id, lang)
                )
    elif target == "my_bookings":
        appointments = await get_appointments(client_id=user['id'], upcoming_only=True)
        if appointments:
            await callback.message.edit_text(
                get_text("your_bookings", lang),
                reply_markup=my_bookings_keyboard(appointments, lang)
            )
        else:
            await callback.message.edit_text(get_text("no_bookings", lang))

    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle no-operation callbacks."""
    await callback.answer()
