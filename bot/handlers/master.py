"""Master (admin) panel handlers."""
import asyncio
import telebot
from telebot.types import Message, CallbackQuery
from telebot.handler_backends import State, StatesGroup
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


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


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


# Store for master data
master_data = {}


def get_master_data(user_id: int) -> dict:
    """Get master data from storage."""
    if user_id not in master_data:
        master_data[user_id] = {}
    return master_data[user_id]


def clear_master_data(user_id: int):
    """Clear master data from storage."""
    if user_id in master_data:
        del master_data[user_id]


def is_master(user_id: int) -> bool:
    """Check if user is master/admin."""
    return user_id in ADMIN_IDS


def register_handlers(bot: telebot.TeleBot):
    """Register all master handlers."""

    # ============ MASTER LOGIN ============

    @bot.message_handler(commands=['master'])
    def cmd_master(message: Message):
        """Master panel access."""
        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        if is_master(message.from_user.id):
            # Already authorized
            bot.send_message(
                message.chat.id,
                get_text("master_menu", lang),
                reply_markup=master_menu_keyboard(lang)
            )
        else:
            # Request password
            bot.send_message(message.chat.id, "Enter master password:")
            bot.set_state(message.from_user.id, MasterAuth.password, message.chat.id)

    @bot.message_handler(state=MasterAuth.password)
    def process_master_password(message: Message):
        """Process master password."""
        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        if message.text == MASTER_PASSWORD:
            # Add to admin list temporarily
            ADMIN_IDS.append(message.from_user.id)
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(
                message.chat.id,
                get_text("master_menu", lang),
                reply_markup=master_menu_keyboard(lang)
            )
        else:
            bot.send_message(message.chat.id, "Wrong password. Try again or /start")
            bot.delete_state(message.from_user.id, message.chat.id)

    # ============ TODAY'S APPOINTMENTS ============

    @bot.message_handler(func=lambda m: m.text in ["📋 Записи на сегодня", "📋 Today's Bookings"])
    def show_today_appointments(message: Message):
        """Show today's appointments."""
        if not is_master(message.from_user.id):
            bot.send_message(message.chat.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        tz = pytz.timezone(TIMEZONE)
        today = datetime.now(tz).strftime("%Y-%m-%d")

        appointments = run_async(get_appointments(date_str=today))

        if not appointments:
            bot.send_message(message.chat.id, get_text("no_appointments_today", lang))
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

        bot.send_message(message.chat.id, text)

        # Show action buttons for each appointment
        for appt in appointments:
            if appt['status'] == 'pending':
                bot.send_message(
                    message.chat.id,
                    f"🔔 {appt['client_name']} - {appt['time']}",
                    reply_markup=appointment_actions_keyboard(
                        appt['id'], lang, appt['client_telegram_id']
                    )
                )

    # ============ CALENDAR VIEW ============

    @bot.message_handler(func=lambda m: m.text in ["📅 Календарь записей", "📅 Calendar"])
    def show_master_calendar(message: Message):
        """Show master calendar."""
        if not is_master(message.from_user.id):
            bot.send_message(message.chat.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        bot.send_message(
            message.chat.id,
            "Выберите день / Select day:",
            reply_markup=master_calendar_keyboard(lang)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_day:"))
    def show_day_appointments(callback: CallbackQuery):
        """Show appointments for specific day."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        date_str = callback.data.split(":")[1]
        appointments = run_async(get_appointments(date_str=date_str))

        if not appointments:
            bot.answer_callback_query(callback.id, f"No appointments on {date_str}", show_alert=True)
            return

        items = []
        for appt in appointments:
            status = get_status_text(appt['status'], lang)
            item = f"🕐 {appt['time']} - {appt['client_name']}\n   📋 {appt.get(f'service_name_{lang}') or appt.get('service_name_ru')}\n   {status}"
            items.append(item)

        text = f"📅 {format_date(date_str, lang)}\n\n" + "\n\n".join(items)

        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=master_calendar_keyboard(lang)
        )
        bot.answer_callback_query(callback.id)

    # ============ APPOINTMENT ACTIONS ============

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_confirm:"))
    def confirm_appointment(callback: CallbackQuery):
        """Confirm appointment."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        appointment_id = int(callback.data.split(":")[1])
        run_async(update_appointment(appointment_id, status='confirmed'))

        # Get appointment details to notify client
        appt = run_async(get_appointment(appointment_id))
        if appt:
            client_lang = 'ru'
            user = run_async(get_user(appt['client_telegram_id']))
            if user:
                client_lang = user['language']

            service_name = appt.get(f'service_name_{client_lang}') or appt.get('service_name_ru')

            try:
                bot.send_message(
                    appt['client_telegram_id'],
                    get_text("booking_confirmed_client", client_lang,
                             service=service_name,
                             date=format_date(appt['date'], client_lang),
                             time=appt['time'])
                )
            except Exception:
                pass

        bot.answer_callback_query(callback.id, "✅ Confirmed!")
        bot.edit_message_text(
            "✅ Appointment confirmed",
            callback.message.chat.id,
            callback.message.message_id
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_reject:"))
    def reject_appointment(callback: CallbackQuery):
        """Reject appointment."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        appointment_id = int(callback.data.split(":")[1])
        run_async(update_appointment(appointment_id, status='cancelled'))

        # Notify client
        appt = run_async(get_appointment(appointment_id))
        if appt:
            client_lang = 'ru'
            user = run_async(get_user(appt['client_telegram_id']))
            if user:
                client_lang = user['language']

            try:
                bot.send_message(
                    appt['client_telegram_id'],
                    get_text("booking_rejected_client", client_lang)
                )
            except Exception:
                pass

        bot.answer_callback_query(callback.id, "❌ Rejected")
        bot.edit_message_text(
            "❌ Appointment rejected",
            callback.message.chat.id,
            callback.message.message_id
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_complete:"))
    def complete_appointment(callback: CallbackQuery):
        """Mark appointment as completed."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        appointment_id = int(callback.data.split(":")[1])
        run_async(update_appointment(appointment_id, status='completed'))

        bot.answer_callback_query(callback.id, "✔️ Completed!")
        bot.edit_message_text(
            "✔️ Appointment marked as completed",
            callback.message.chat.id,
            callback.message.message_id
        )

    # ============ SCHEDULE SETTINGS ============

    @bot.message_handler(func=lambda m: m.text in ["⚙️ Настройки расписания", "⚙️ Schedule Settings"])
    def show_schedule_settings(message: Message):
        """Show schedule settings."""
        if not is_master(message.from_user.id):
            bot.send_message(message.chat.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        schedule = run_async(get_schedule())
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        text = "📅 Текущее расписание / Current schedule:\n\n"
        for day in schedule:
            text += f"{days[day['day_of_week']]}: {day['start_time']} - {day['end_time']}\n"

        text += "\nВыберите день для изменения / Select day to edit:"

        bot.send_message(message.chat.id, text, reply_markup=schedule_settings_keyboard(lang))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_sched:"))
    def edit_schedule_day(callback: CallbackQuery):
        """Edit schedule for specific day."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        day = int(callback.data.split(":")[1])
        data = get_master_data(callback.from_user.id)
        data['schedule_day'] = day

        days = ["Понедельник/Monday", "Вторник/Tuesday", "Среда/Wednesday",
                "Четверг/Thursday", "Пятница/Friday", "Суббота/Saturday", "Воскресенье/Sunday"]

        bot.edit_message_text(
            f"📅 {days[day]}\n\nВведите время начала работы (HH:MM), например 09:00\nEnter start time (HH:MM), e.g. 09:00:",
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.set_state(callback.from_user.id, ScheduleSettings.start_time, callback.message.chat.id)
        bot.answer_callback_query(callback.id)

    @bot.message_handler(state=ScheduleSettings.start_time)
    def process_schedule_start(message: Message):
        """Process schedule start time."""
        if not is_master(message.from_user.id):
            return

        data = get_master_data(message.from_user.id)
        data['start_time'] = message.text
        bot.send_message(
            message.chat.id,
            "Введите время окончания работы (HH:MM), например 18:00\nEnter end time (HH:MM), e.g. 18:00:"
        )
        bot.set_state(message.from_user.id, ScheduleSettings.end_time, message.chat.id)

    @bot.message_handler(state=ScheduleSettings.end_time)
    def process_schedule_end(message: Message):
        """Process schedule end time and save."""
        if not is_master(message.from_user.id):
            return

        data = get_master_data(message.from_user.id)
        day = data['schedule_day']
        start = data['start_time']
        end = message.text

        run_async(set_schedule(day, start, end))

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        clear_master_data(message.from_user.id)
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(
            message.chat.id,
            f"✅ Расписание обновлено / Schedule updated!\n{start} - {end}",
            reply_markup=master_menu_keyboard(lang)
        )

    # ============ BLOCK SLOT ============

    @bot.message_handler(func=lambda m: m.text in ["🚫 Закрыть слот", "🚫 Block Slot"])
    def show_block_calendar(message: Message):
        """Show calendar for blocking slots."""
        if not is_master(message.from_user.id):
            bot.send_message(message.chat.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        bot.send_message(
            message.chat.id,
            "Выберите дату для блокировки / Select date to block:",
            reply_markup=block_slot_calendar_keyboard(lang)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_block_day:"))
    def select_block_day(callback: CallbackQuery):
        """Select day to block."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        date_str = callback.data.split(":")[1]
        data = get_master_data(callback.from_user.id)
        data['block_date'] = date_str

        bot.edit_message_text(
            f"📅 {format_date(date_str, lang)}\n\nВыберите тип блокировки / Select block type:",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=block_type_keyboard(date_str, lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_block_full:"))
    def block_full_day(callback: CallbackQuery):
        """Block full day."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        date_str = callback.data.split(":")[1]
        run_async(block_slot(date_str, is_full_day=True, reason="Day off"))

        clear_master_data(callback.from_user.id)
        bot.edit_message_text(
            f"🚫 День {date_str} заблокирован / Day blocked",
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.answer_callback_query(callback.id, "✅ Blocked!")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_block_time:"))
    def show_block_time_slots(callback: CallbackQuery):
        """Show time slots for blocking."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        date_str = callback.data.split(":")[1]

        bot.edit_message_text(
            f"📅 {format_date(date_str, lang)}\n\nВыберите время для блокировки / Select time to block:",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=block_time_slots_keyboard(date_str, lang)
        )
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_block_slot|"))
    def block_specific_slot(callback: CallbackQuery):
        """Block specific time slot."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        parts = callback.data.split("|")
        date_str = parts[1]
        time_str = parts[2]

        run_async(block_slot(date_str, start_time=time_str, end_time=time_str, reason="Blocked slot"))

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        bot.edit_message_text(
            f"🚫 Слот {time_str} на {format_date(date_str, lang)} заблокирован / Slot blocked",
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.answer_callback_query(callback.id, "✅ Blocked!")

    # ============ STATISTICS ============

    @bot.message_handler(func=lambda m: m.text in ["📊 Статистика", "📊 Statistics"])
    def show_stats_menu(message: Message):
        """Show statistics period selection."""
        if not is_master(message.from_user.id):
            bot.send_message(message.chat.id, get_text("master_only", "ru"))
            return

        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        bot.send_message(
            message.chat.id,
            "Выберите период / Select period:",
            reply_markup=stats_period_keyboard(lang)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_stats:"))
    def show_statistics(callback: CallbackQuery):
        """Show statistics for period."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        days = int(callback.data.split(":")[1])
        stats = run_async(get_statistics(days))

        popular = "\n".join([f"  • {name}: {count}" for name, count in stats['popular_services']])

        text = get_text("stats_report", lang,
                        days=days,
                        total=stats['total_appointments'],
                        completed=stats['completed'],
                        cancelled=stats['cancelled'],
                        revenue=int(stats['revenue_egp']),
                        no_show=stats['no_show_rate'],
                        popular=popular or "—")

        bot.edit_message_text(
            text,
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.answer_callback_query(callback.id)

    # ============ BACK TO CLIENT MENU ============

    @bot.message_handler(func=lambda m: m.text in ["« Назад", "« Back"])
    def back_to_main(message: Message):
        """Return to client main menu."""
        user = run_async(get_user(message.from_user.id))
        lang = user['language'] if user else 'ru'

        bot.send_message(
            message.chat.id,
            get_text("main_menu", lang),
            reply_markup=main_menu_keyboard(lang)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("m_back:"))
    def master_back(callback: CallbackQuery):
        """Handle master panel back navigation."""
        if not is_master(callback.from_user.id):
            bot.answer_callback_query(callback.id)
            return

        user = run_async(get_user(callback.from_user.id))
        lang = user['language'] if user else 'ru'

        target = callback.data.split(":")[1]

        if target == "main":
            bot.edit_message_text(
                get_text("master_menu", lang),
                callback.message.chat.id,
                callback.message.message_id
            )
        elif target == "block":
            bot.edit_message_text(
                "Выберите дату для блокировки / Select date to block:",
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=block_slot_calendar_keyboard(lang)
            )

        bot.answer_callback_query(callback.id)


# ============ NOTIFICATION HELPER ============

def notify_master_new_booking(bot: telebot.TeleBot, appointment_id: int):
    """Send notification to master about new booking."""
    appt = run_async(get_appointment(appointment_id))
    if not appt:
        return

    for admin_id in ADMIN_IDS:
        try:
            admin_user = run_async(get_user(admin_id))
            lang = admin_user['language'] if admin_user else 'ru'

            service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')

            text = get_text("new_booking_notification", lang,
                            client=appt['client_name'] or "Unknown",
                            username=appt['client_username'] or "-",
                            service=service_name,
                            date=format_date(appt['date'], lang),
                            time=appt['time'],
                            phone=appt['client_phone'] or "-")

            bot.send_message(
                admin_id,
                text,
                reply_markup=appointment_actions_keyboard(
                    appointment_id, lang, appt['client_telegram_id']
                )
            )
        except Exception:
            pass
