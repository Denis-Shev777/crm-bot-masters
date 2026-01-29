from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime, timedelta
from locales import get_text


def master_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Master panel main menu."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=get_text("btn_today", lang)),
        KeyboardButton(text=get_text("btn_calendar", lang))
    )
    builder.row(
        KeyboardButton(text=get_text("btn_settings", lang)),
        KeyboardButton(text=get_text("btn_block_slot", lang))
    )
    builder.row(
        KeyboardButton(text=get_text("btn_stats", lang)),
        KeyboardButton(text=get_text("btn_broadcast", lang))
    )
    builder.row(
        KeyboardButton(text=get_text("back", lang))
    )
    return builder.as_markup(resize_keyboard=True)


def appointment_actions_keyboard(appointment_id: int, lang: str, client_telegram_id: int = None) -> InlineKeyboardMarkup:
    """Actions for appointment management."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("btn_confirm_booking", lang),
            callback_data=f"m_confirm:{appointment_id}"
        ),
        InlineKeyboardButton(
            text=get_text("btn_reject_booking", lang),
            callback_data=f"m_reject:{appointment_id}"
        )
    )
    if client_telegram_id:
        builder.row(InlineKeyboardButton(
            text=get_text("btn_contact_client", lang),
            url=f"tg://user?id={client_telegram_id}"
        ))
    builder.row(InlineKeyboardButton(
        text="✔️ Выполнено / Done",
        callback_data=f"m_complete:{appointment_id}"
    ))
    return builder.as_markup()


def master_calendar_keyboard(lang: str, days: int = 7) -> InlineKeyboardMarkup:
    """Master calendar for viewing appointments."""
    builder = InlineKeyboardBuilder()
    today = datetime.now()

    row = []
    for i in range(days):
        day = today + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_display = day.strftime("%d.%m")
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][day.weekday()]
        if lang == "en":
            weekday = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][day.weekday()]

        row.append(InlineKeyboardButton(
            text=f"{day_display} ({weekday})",
            callback_data=f"m_day:{day_str}"
        ))

        if len(row) == 3:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    # Navigation
    builder.row(
        InlineKeyboardButton(text="« Prev week", callback_data="m_cal:prev"),
        InlineKeyboardButton(text="Next week »", callback_data="m_cal:next")
    )
    return builder.as_markup()


def schedule_settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Schedule settings keyboard."""
    days = ["Пн/Mo", "Вт/Tu", "Ср/We", "Чт/Th", "Пт/Fr", "Сб/Sa", "Вс/Su"]
    builder = InlineKeyboardBuilder()

    for i, day in enumerate(days):
        builder.row(InlineKeyboardButton(
            text=day,
            callback_data=f"m_sched:{i}"
        ))

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="m_back:main"
    ))
    return builder.as_markup()


def block_slot_calendar_keyboard(lang: str, days: int = 14) -> InlineKeyboardMarkup:
    """Calendar for blocking slots."""
    builder = InlineKeyboardBuilder()
    today = datetime.now()

    row = []
    for i in range(days):
        day = today + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_display = day.strftime("%d.%m")

        row.append(InlineKeyboardButton(
            text=day_display,
            callback_data=f"m_block_day:{day_str}"
        ))

        if len(row) == 4:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="m_back:main"
    ))
    return builder.as_markup()


def block_type_keyboard(date_str: str, lang: str) -> InlineKeyboardMarkup:
    """Block full day or specific time."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🚫 Весь день / Full day",
        callback_data=f"m_block_full:{date_str}"
    ))
    builder.row(InlineKeyboardButton(
        text="🕐 Выбрать время / Select time",
        callback_data=f"m_block_time:{date_str}"
    ))
    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="m_back:block"
    ))
    return builder.as_markup()


def stats_period_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Statistics period selection."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="7 дней / days", callback_data="m_stats:7"),
        InlineKeyboardButton(text="30 дней / days", callback_data="m_stats:30")
    )
    builder.row(
        InlineKeyboardButton(text="90 дней / days", callback_data="m_stats:90"),
        InlineKeyboardButton(text="Всё / All", callback_data="m_stats:365")
    )
    return builder.as_markup()


def block_time_slots_keyboard(date_str: str, lang: str) -> InlineKeyboardMarkup:
    """Time slots for blocking specific hours."""
    builder = InlineKeyboardBuilder()

    # Generate time slots from 09:00 to 18:00
    times = []
    for hour in range(9, 18):
        times.append(f"{hour:02d}:00")
        times.append(f"{hour:02d}:30")

    row = []
    for time_slot in times:
        row.append(InlineKeyboardButton(
            text=time_slot,
            callback_data=f"m_block_slot|{date_str}|{time_slot}"
        ))
        if len(row) == 4:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data=f"m_block_day:{date_str}"
    ))
    return builder.as_markup()
