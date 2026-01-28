from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from datetime import datetime, timedelta
from locales import get_text, get_service_name, get_category_name


def language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")
    )
    return builder.as_markup()


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Phone sharing keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(
        text=get_text("btn_send_phone", lang),
        request_contact=True
    ))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Main menu keyboard for clients."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=get_text("btn_book", lang)),
        KeyboardButton(text=get_text("btn_my_bookings", lang))
    )
    builder.row(
        KeyboardButton(text=get_text("btn_services", lang)),
        KeyboardButton(text=get_text("btn_contacts", lang))
    )
    builder.row(
        KeyboardButton(text=get_text("btn_language", lang)),
        KeyboardButton(text=get_text("btn_referral", lang))
    )
    return builder.as_markup(resize_keyboard=True)


def categories_keyboard(categories: list, lang: str) -> InlineKeyboardMarkup:
    """Categories list keyboard."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        name = get_category_name(cat, lang)
        builder.row(InlineKeyboardButton(
            text=name,
            callback_data=f"cat:{cat['id']}"
        ))
    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:main"
    ))
    return builder.as_markup()


def services_keyboard(services: list, lang: str, category_id: int) -> InlineKeyboardMarkup:
    """Services list keyboard."""
    builder = InlineKeyboardBuilder()
    for service in services:
        name = get_service_name(service, lang)
        price = int(service['price_egp'])
        duration = service['duration']
        builder.row(InlineKeyboardButton(
            text=f"{name} - {price} EGP ({duration} мин)",
            callback_data=f"srv:{service['id']}"
        ))
    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:categories"
    ))
    return builder.as_markup()


def service_detail_keyboard(service_id: int, lang: str) -> InlineKeyboardMarkup:
    """Service detail keyboard with book button."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=get_text("btn_book_service", lang),
        callback_data=f"book:{service_id}"
    ))
    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:services"
    ))
    return builder.as_markup()


def calendar_keyboard(lang: str, days_ahead: int = 14, selected_service_id: int = None) -> InlineKeyboardMarkup:
    """Calendar keyboard for date selection."""
    builder = InlineKeyboardBuilder()
    today = datetime.now()

    # Create buttons for each day
    row = []
    for i in range(days_ahead):
        day = today + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_display = day.strftime("%d.%m")
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][day.weekday()]
        if lang == "en":
            weekday = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][day.weekday()]

        row.append(InlineKeyboardButton(
            text=f"{day_display} ({weekday})",
            callback_data=f"date:{day_str}:{selected_service_id}"
        ))

        if len(row) == 3:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:service_detail"
    ))
    return builder.as_markup()


def time_slots_keyboard(slots: list, date_str: str, service_id: int, lang: str) -> InlineKeyboardMarkup:
    """Time slots keyboard."""
    builder = InlineKeyboardBuilder()

    if not slots:
        builder.row(InlineKeyboardButton(
            text=get_text("no_slots", lang),
            callback_data="noop"
        ))
    else:
        row = []
        for slot in slots:
            row.append(InlineKeyboardButton(
                text=slot,
                callback_data=f"time:{date_str}:{slot}:{service_id}"
            ))
            if len(row) == 4:
                builder.row(*row)
                row = []
        if row:
            builder.row(*row)

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data=f"book:{service_id}"
    ))
    return builder.as_markup()


def booking_confirm_keyboard(service_id: int, date_str: str, time_str: str, lang: str) -> InlineKeyboardMarkup:
    """Booking confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"✅ {get_text('confirm', lang)}",
            callback_data=f"confirm_book:{service_id}:{date_str}:{time_str}"
        ),
        InlineKeyboardButton(
            text=f"❌ {get_text('cancel', lang)}",
            callback_data="back:main"
        )
    )
    return builder.as_markup()


def my_bookings_keyboard(appointments: list, lang: str) -> InlineKeyboardMarkup:
    """My bookings list keyboard."""
    builder = InlineKeyboardBuilder()

    for appt in appointments:
        service_name = appt.get(f'service_name_{lang}') or appt.get('service_name_ru')
        date = appt['date']
        time = appt['time']
        builder.row(InlineKeyboardButton(
            text=f"📋 {service_name} - {date} {time}",
            callback_data=f"appt:{appt['id']}"
        ))

    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:main"
    ))
    return builder.as_markup()


def appointment_detail_keyboard(appointment_id: int, lang: str, can_cancel: bool = True) -> InlineKeyboardMarkup:
    """Appointment detail keyboard."""
    builder = InlineKeyboardBuilder()
    if can_cancel:
        builder.row(InlineKeyboardButton(
            text=get_text("btn_cancel_booking", lang),
            callback_data=f"cancel_appt:{appointment_id}"
        ))
    builder.row(InlineKeyboardButton(
        text=get_text("back", lang),
        callback_data="back:my_bookings"
    ))
    return builder.as_markup()


def cancel_confirm_keyboard(appointment_id: int, lang: str) -> InlineKeyboardMarkup:
    """Cancel confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("yes", lang),
            callback_data=f"confirm_cancel:{appointment_id}"
        ),
        InlineKeyboardButton(
            text=get_text("no", lang),
            callback_data=f"appt:{appointment_id}"
        )
    )
    return builder.as_markup()


def review_rating_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    """Star rating keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(*[
        InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate:{appointment_id}:{i}")
        for i in range(1, 6)
    ])
    return builder.as_markup()


def skip_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Skip button keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=get_text("btn_skip", lang),
        callback_data="skip_review"
    ))
    return builder.as_markup()
