"""Master (admin) panel handlers."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import pytz

from database import (
    get_user, update_user, get_appointments, get_appointment,
    update_appointment, block_slot, get_statistics, get_schedule, set_schedule
)
from locales import get_text, get_status_text
from bot.keyboards.master import (
    master_menu_keyboard, appointment_actions_keyboard,
    master_calendar_keyboard, schedule_settings_keyboard,
    block_slot_calendar_keyboard, block_type_keyboard, stats_period_keyboard,
    block_time_slots_keyboard
)
from bot.keyboards.client import main_menu_keyboard
from bot.utils import format_date
from config import ADMIN_IDS, MASTER_PASSWORD, TIMEZONE

router = Router()


class MasterAuth(StatesGroup):
    """Master authentication states."""
    password = State()


class ScheduleSettings(StatesGroup):
    """Schedule settings states."""
    day = State()
    start_time = State()
    end_time = State()


class BlockSlot(StatesGroup):
    """Block slot states."""
    date = State()
    start_time = State()
    end_time = State()


def is_master(user_id: int) -> bool:
    """Check if user is master/admin."""
    return user_id in ADMIN_IDS


# ============ MASTER LOGIN ============

@router.message(Command("master"))
async def cmd_master(message: Message, state: FSMContext):
    """Master panel access."""
    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    if is_master(message.from_user.id):
        # Already authorized
        await message.answer(
            get_text("master_menu", lang),
            reply_markup=master_menu_keyboard(lang)
        )
    else:
        # Request password
        await message.answer("Enter master password:")
        await state.set_state(MasterAuth.password)


@router.message(MasterAuth.password)
async def process_master_password(message: Message, state: FSMContext):
    """Process master password."""
    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    if message.text == MASTER_PASSWORD:
        # Add to admin list temporarily (in real app - save to DB)
        ADMIN_IDS.append(message.from_user.id)
        await state.clear()
        await message.answer(
            get_text("master_menu", lang),
            reply_markup=master_menu_keyboard(lang)
        )
    else:
        await message.answer("Wrong password. Try again or /start")
        await state.clear()


# ============ TODAY'S APPOINTMENTS ============

@router.message(F.text.in_(["📋 Записи на сегодня", "📋 Today's Bookings"]))
async def show_today_appointments(message: Message):
    """Show today's appointments."""
    if not is_master(message.from_user.id):
        await message.answer(get_text("master_only", "ru"))
        return

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).strftime("%Y-%m-%d")

    appointments = await get_appointments(date_str=today)

    if not appointments:
        await message.answer(get_text("no_appointments_today", lang))
        return

    # Format appointments list
    items = []
    for appt in appointments:
        status = get_status_text(appt['status'], lang)
        item = get_text("appointment_item", lang,
                        time=appt['time'],
                        client=appt['client_name'] or "Unknown",
                        service=appt.get(f'service_name_{lang}') or appt.get('service_name_ru'),
                        phone=appt['client_phone'] or "-",
                        status=status)
        items.append(item)

    text = get_text("today_appointments", lang,
                    date=format_date(today, lang),
                    list="\n\n".join(items))

    await message.answer(text)

    # Show action buttons for each appointment
    for appt in appointments:
        if appt['status'] == 'pending':
            await message.answer(
                f"🔔 {appt['client_name']} - {appt['time']}",
                reply_markup=appointment_actions_keyboard(
                    appt['id'], lang, appt['client_telegram_id']
                )
            )


# ============ CALENDAR VIEW ============

@router.message(F.text.in_(["📅 Календарь записей", "📅 Calendar"]))
async def show_master_calendar(message: Message):
    """Show master calendar."""
    if not is_master(message.from_user.id):
        await message.answer(get_text("master_only", "ru"))
        return

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    await message.answer(
        "Выберите день / Select day:",
        reply_markup=master_calendar_keyboard(lang)
    )


@router.callback_query(F.data.startswith("m_day:"))
async def show_day_appointments(callback: CallbackQuery):
    """Show appointments for specific day."""
    if not is_master(callback.from_user.id):
        await callback.answer(get_text("master_only", "ru"))
        return

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    date_str = callback.data.split(":")[1]
    appointments = await get_appointments(date_str=date_str)

    if not appointments:
        await callback.answer(f"No appointments on {date_str}", show_alert=True)
        return

    items = []
    for appt in appointments:
        status = get_status_text(appt['status'], lang)
        item = f"🕐 {appt['time']} - {appt['client_name']}\n   📋 {appt.get(f'service_name_{lang}') or appt.get('service_name_ru')}\n   {status}"
        items.append(item)

    text = f"📅 {format_date(date_str, lang)}\n\n" + "\n\n".join(items)

    await callback.message.edit_text(
        text,
        reply_markup=master_calendar_keyboard(lang)
    )
    await callback.answer()


# ============ APPOINTMENT ACTIONS ============

@router.callback_query(F.data.startswith("m_confirm:"))
async def confirm_appointment(callback: CallbackQuery):
    """Confirm appointment."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    appointment_id = int(callback.data.split(":")[1])
    await update_appointment(appointment_id, status='confirmed')

    # Get appointment details to notify client
    appt = await get_appointment(appointment_id)
    if appt:
        client_lang = 'ru'  # TODO: get from user
        user = await get_user(appt['client_telegram_id'])
        if user:
            client_lang = user['language']

        service_name = appt.get(f'service_name_{client_lang}') or appt.get('service_name_ru')

        try:
            await callback.bot.send_message(
                appt['client_telegram_id'],
                get_text("booking_confirmed_client", client_lang,
                         service=service_name,
                         date=format_date(appt['date'], client_lang),
                         time=appt['time'])
            )
        except Exception:
            pass

    await callback.answer("✅ Confirmed!")
    await callback.message.edit_text("✅ Appointment confirmed")


@router.callback_query(F.data.startswith("m_reject:"))
async def reject_appointment(callback: CallbackQuery):
    """Reject appointment."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    appointment_id = int(callback.data.split(":")[1])
    await update_appointment(appointment_id, status='cancelled')

    # Notify client
    appt = await get_appointment(appointment_id)
    if appt:
        client_lang = 'ru'
        user = await get_user(appt['client_telegram_id'])
        if user:
            client_lang = user['language']

        try:
            await callback.bot.send_message(
                appt['client_telegram_id'],
                get_text("booking_rejected_client", client_lang)
            )
        except Exception:
            pass

    await callback.answer("❌ Rejected")
    await callback.message.edit_text("❌ Appointment rejected")


@router.callback_query(F.data.startswith("m_complete:"))
async def complete_appointment(callback: CallbackQuery):
    """Mark appointment as completed."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    appointment_id = int(callback.data.split(":")[1])
    await update_appointment(appointment_id, status='completed')

    await callback.answer("✔️ Completed!")
    await callback.message.edit_text("✔️ Appointment marked as completed")


# ============ SCHEDULE SETTINGS ============

@router.message(F.text.in_(["⚙️ Настройки расписания", "⚙️ Schedule Settings"]))
async def show_schedule_settings(message: Message):
    """Show schedule settings."""
    if not is_master(message.from_user.id):
        await message.answer(get_text("master_only", "ru"))
        return

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    schedule = await get_schedule()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    text = "📅 Текущее расписание / Current schedule:\n\n"
    for day in schedule:
        text += f"{days[day['day_of_week']]}: {day['start_time']} - {day['end_time']}\n"

    text += "\nВыберите день для изменения / Select day to edit:"

    await message.answer(text, reply_markup=schedule_settings_keyboard(lang))


@router.callback_query(F.data.startswith("m_sched:"))
async def edit_schedule_day(callback: CallbackQuery, state: FSMContext):
    """Edit schedule for specific day."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    day = int(callback.data.split(":")[1])
    await state.update_data(schedule_day=day)

    days = ["Понедельник/Monday", "Вторник/Tuesday", "Среда/Wednesday",
            "Четверг/Thursday", "Пятница/Friday", "Суббота/Saturday", "Воскресенье/Sunday"]

    await callback.message.edit_text(
        f"📅 {days[day]}\n\nВведите время начала работы (HH:MM), например 09:00\nEnter start time (HH:MM), e.g. 09:00:"
    )
    await state.set_state(ScheduleSettings.start_time)
    await callback.answer()


@router.message(ScheduleSettings.start_time)
async def process_schedule_start(message: Message, state: FSMContext):
    """Process schedule start time."""
    if not is_master(message.from_user.id):
        return

    await state.update_data(start_time=message.text)
    await message.answer(
        "Введите время окончания работы (HH:MM), например 18:00\nEnter end time (HH:MM), e.g. 18:00:"
    )
    await state.set_state(ScheduleSettings.end_time)


@router.message(ScheduleSettings.end_time)
async def process_schedule_end(message: Message, state: FSMContext):
    """Process schedule end time and save."""
    if not is_master(message.from_user.id):
        return

    data = await state.get_data()
    day = data['schedule_day']
    start = data['start_time']
    end = message.text

    await set_schedule(day, start, end)

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    await state.clear()
    await message.answer(
        f"✅ Расписание обновлено / Schedule updated!\n{start} - {end}",
        reply_markup=master_menu_keyboard(lang)
    )


# ============ BLOCK SLOT ============

@router.message(F.text.in_(["🚫 Закрыть слот", "🚫 Block Slot"]))
async def show_block_calendar(message: Message):
    """Show calendar for blocking slots."""
    if not is_master(message.from_user.id):
        await message.answer(get_text("master_only", "ru"))
        return

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    await message.answer(
        "Выберите дату для блокировки / Select date to block:",
        reply_markup=block_slot_calendar_keyboard(lang)
    )


@router.callback_query(F.data.startswith("m_block_day:"))
async def select_block_day(callback: CallbackQuery, state: FSMContext):
    """Select day to block."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    date_str = callback.data.split(":")[1]
    await state.update_data(block_date=date_str)

    await callback.message.edit_text(
        f"📅 {format_date(date_str, lang)}\n\nВыберите тип блокировки / Select block type:",
        reply_markup=block_type_keyboard(date_str, lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("m_block_full:"))
async def block_full_day(callback: CallbackQuery, state: FSMContext):
    """Block full day."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    date_str = callback.data.split(":")[1]
    await block_slot(date_str, is_full_day=True, reason="Day off")

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    await state.clear()
    await callback.message.edit_text(f"🚫 День {date_str} заблокирован / Day blocked")
    await callback.answer("✅ Blocked!")


@router.callback_query(F.data.startswith("m_block_time:"))
async def show_block_time_slots(callback: CallbackQuery):
    """Show time slots for blocking."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    date_str = callback.data.split(":")[1]

    await callback.message.edit_text(
        f"📅 {format_date(date_str, lang)}\n\nВыберите время для блокировки / Select time to block:",
        reply_markup=block_time_slots_keyboard(date_str, lang)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("m_block_slot|"))
async def block_specific_slot(callback: CallbackQuery, state: FSMContext):
    """Block specific time slot."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split("|")
    date_str = parts[1]
    time_str = parts[2]

    await block_slot(date_str, start_time=time_str, end_time=time_str, reason="Blocked slot")

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    await callback.message.edit_text(
        f"🚫 Слот {time_str} на {format_date(date_str, lang)} заблокирован / Slot blocked"
    )
    await callback.answer("✅ Blocked!")


# ============ STATISTICS ============

@router.message(F.text.in_(["📊 Статистика", "📊 Statistics"]))
async def show_stats_menu(message: Message):
    """Show statistics period selection."""
    if not is_master(message.from_user.id):
        await message.answer(get_text("master_only", "ru"))
        return

    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    await message.answer(
        "Выберите период / Select period:",
        reply_markup=stats_period_keyboard(lang)
    )


@router.callback_query(F.data.startswith("m_stats:"))
async def show_statistics(callback: CallbackQuery):
    """Show statistics for period."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    days = int(callback.data.split(":")[1])
    stats = await get_statistics(days)

    popular = "\n".join([f"  • {name}: {count}" for name, count in stats['popular_services']])

    text = get_text("stats_report", lang,
                    days=days,
                    total=stats['total_appointments'],
                    completed=stats['completed'],
                    cancelled=stats['cancelled'],
                    revenue=int(stats['revenue_egp']),
                    no_show=stats['no_show_rate'],
                    popular=popular or "—")

    await callback.message.edit_text(text)
    await callback.answer()


# ============ BACK TO CLIENT MENU ============

@router.message(F.text.in_(["« Назад", "« Back"]))
async def back_to_main(message: Message):
    """Return to client main menu."""
    user = await get_user(message.from_user.id)
    lang = user['language'] if user else 'ru'

    await message.answer(
        get_text("main_menu", lang),
        reply_markup=main_menu_keyboard(lang)
    )


@router.callback_query(F.data.startswith("m_back:"))
async def master_back(callback: CallbackQuery):
    """Handle master panel back navigation."""
    if not is_master(callback.from_user.id):
        await callback.answer()
        return

    user = await get_user(callback.from_user.id)
    lang = user['language'] if user else 'ru'

    target = callback.data.split(":")[1]

    if target == "main":
        await callback.message.edit_text(get_text("master_menu", lang))
    elif target == "block":
        await callback.message.edit_text(
            "Выберите дату для блокировки / Select date to block:",
            reply_markup=block_slot_calendar_keyboard(lang)
        )

    await callback.answer()


# ============ NOTIFICATION HELPER ============

async def notify_master_new_booking(bot: Bot, appointment_id: int):
    """Send notification to master about new booking."""
    appt = await get_appointment(appointment_id)
    if not appt:
        return

    for admin_id in ADMIN_IDS:
        try:
            admin_user = await get_user(admin_id)
            lang = admin_user['language'] if admin_user else 'ru'

            service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')

            text = get_text("new_booking_notification", lang,
                            client=appt['client_name'] or "Unknown",
                            username=appt['client_username'] or "-",
                            service=service_name,
                            date=format_date(appt['date'], lang),
                            time=appt['time'],
                            phone=appt['client_phone'] or "-")

            await bot.send_message(
                admin_id,
                text,
                reply_markup=appointment_actions_keyboard(
                    appointment_id, lang, appt['client_telegram_id']
                )
            )
        except Exception:
            pass
