"""Multilingual texts for the bot."""

TEXTS = {
    "ru": {
        # Common
        "welcome": "Добро пожаловать! Выберите язык / Welcome! Choose language:",
        "main_menu": "Главное меню",
        "back": "« Назад",
        "cancel": "Отмена",
        "confirm": "Подтвердить",
        "yes": "Да",
        "no": "Нет",

        # Main menu buttons
        "btn_book": "📅 Записаться",
        "btn_my_bookings": "📖 Мои записи",
        "btn_services": "💰 Услуги и цены",
        "btn_contacts": "📞 Контакты",
        "btn_language": "🌐 Язык",
        "btn_referral": "👥 Пригласить друга",

        # Registration
        "ask_name": "Как вас зовут?",
        "ask_phone": "Отправьте номер телефона для связи:",
        "btn_send_phone": "📱 Отправить номер",
        "registration_complete": "Отлично, {name}! Регистрация завершена.",

        # Services
        "choose_category": "Выберите категорию:",
        "choose_service": "Выберите услугу:",
        "service_info": "💅 {name}\n\n{description}\n\n⏱ Длительность: {duration} мин\n💵 Цена: {price_egp} EGP (~${price_usd})",
        "btn_book_service": "📅 Записаться на эту услугу",

        # Booking
        "choose_date": "Выберите дату:",
        "choose_time": "Выберите время:",
        "no_slots": "К сожалению, на эту дату нет свободных слотов.",
        "booking_confirm": "Подтвердите запись:\n\n📋 Услуга: {service}\n📅 Дата: {date}\n🕐 Время: {time}\n💵 Стоимость: {price} EGP",
        "booking_created": "✅ Запись создана!\n\n📋 {service}\n📅 {date} в {time}\n\nМы отправим напоминание за день до визита.",
        "booking_limit": "У вас уже {count} активных записей. Максимум - {max}.",

        # My bookings
        "no_bookings": "У вас пока нет активных записей.",
        "your_bookings": "Ваши записи:",
        "booking_item": "📋 {service}\n📅 {date} в {time}\nСтатус: {status}",
        "btn_cancel_booking": "❌ Отменить запись",
        "booking_cancelled": "Запись отменена.",
        "confirm_cancel": "Вы уверены, что хотите отменить запись?",

        # Statuses
        "status_pending": "⏳ Ожидает подтверждения",
        "status_confirmed": "✅ Подтверждена",
        "status_paid": "💳 Оплачена",
        "status_completed": "✔️ Завершена",
        "status_cancelled": "❌ Отменена",

        # Reminders
        "reminder_24h": "🔔 Напоминание!\n\nЗавтра в {time} у вас запись:\n📋 {service}\n\nАдрес: {address}\n\nДо встречи!",
        "reminder_3h": "🔔 Через 3 часа ваша запись!\n\n📋 {service}\n🕐 {time}\n\nАдрес: {address}",

        # Referral
        "referral_info": "👥 Пригласите друзей и получите скидку!\n\nВаша реферальная ссылка:\n{link}\n\nЗа каждого приглашённого друга вы оба получите {discount}% скидку на следующий визит!",

        # Contacts
        "contacts_info": "📍 Адрес: {address}\n📞 Телефон: {phone}\n\n🕐 Режим работы:\n{schedule}",

        # Master panel
        "master_menu": "👩‍💼 Панель мастера",
        "btn_today": "📋 Записи на сегодня",
        "btn_calendar": "📅 Календарь записей",
        "btn_settings": "⚙️ Настройки расписания",
        "btn_block_slot": "🚫 Закрыть слот",
        "btn_stats": "📊 Статистика",
        "btn_broadcast": "📢 Рассылка",

        "no_appointments_today": "На сегодня записей нет.",
        "today_appointments": "📋 Записи на сегодня ({date}):\n\n{list}",
        "appointment_item": "🕐 {time} - {client}\n   📋 {service}\n   📞 {phone}\n   Статус: {status}",

        # Notifications
        "new_booking_notification": "🔔 Новая запись!\n\n👤 Клиент: {client} (@{username})\n📋 Услуга: {service}\n📅 Дата: {date} в {time}\n📞 Телефон: {phone}\n\nСтатус: Ожидает подтверждения",
        "btn_confirm_booking": "✅ Подтвердить",
        "btn_reject_booking": "❌ Отклонить",
        "btn_contact_client": "📞 Связаться",

        "booking_confirmed_client": "✅ Ваша запись подтверждена!\n\n📋 {service}\n📅 {date} в {time}\n\nЖдём вас!",
        "booking_rejected_client": "❌ К сожалению, ваша запись была отклонена.\n\nВы можете выбрать другое время.",

        # Stats
        "stats_report": "📊 Статистика за {days} дней:\n\n📋 Всего записей: {total}\n✅ Выполнено: {completed}\n❌ Отменено: {cancelled}\n💵 Доход: {revenue} EGP\n📉 % отмен: {no_show}%\n\n🔝 Популярные услуги:\n{popular}",

        # Reviews
        "ask_review": "Как вам процедура? Оцените от 1 до 5 ⭐",
        "ask_review_text": "Спасибо! Хотите оставить комментарий?",
        "btn_skip": "Пропустить",
        "review_thanks": "Спасибо за отзыв! 🙏",

        # Errors
        "error_occurred": "Произошла ошибка. Попробуйте позже.",
        "master_only": "Эта функция доступна только мастеру.",
    },

    "en": {
        # Common
        "welcome": "Welcome! Choose language:",
        "main_menu": "Main menu",
        "back": "« Back",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "yes": "Yes",
        "no": "No",

        # Main menu buttons
        "btn_book": "📅 Book Now",
        "btn_my_bookings": "📖 My Bookings",
        "btn_services": "💰 Services & Prices",
        "btn_contacts": "📞 Contacts",
        "btn_language": "🌐 Language",
        "btn_referral": "👥 Invite Friend",

        # Registration
        "ask_name": "What's your name?",
        "ask_phone": "Please share your phone number:",
        "btn_send_phone": "📱 Share Phone",
        "registration_complete": "Great, {name}! Registration complete.",

        # Services
        "choose_category": "Choose a category:",
        "choose_service": "Choose a service:",
        "service_info": "💅 {name}\n\n{description}\n\n⏱ Duration: {duration} min\n💵 Price: {price_egp} EGP (~${price_usd})",
        "btn_book_service": "📅 Book This Service",

        # Booking
        "choose_date": "Choose a date:",
        "choose_time": "Choose time:",
        "no_slots": "Sorry, no available slots on this date.",
        "booking_confirm": "Confirm your booking:\n\n📋 Service: {service}\n📅 Date: {date}\n🕐 Time: {time}\n💵 Price: {price} EGP",
        "booking_created": "✅ Booking confirmed!\n\n📋 {service}\n📅 {date} at {time}\n\nWe'll send you a reminder before your visit.",
        "booking_limit": "You have {count} active bookings. Maximum is {max}.",

        # My bookings
        "no_bookings": "You have no active bookings.",
        "your_bookings": "Your bookings:",
        "booking_item": "📋 {service}\n📅 {date} at {time}\nStatus: {status}",
        "btn_cancel_booking": "❌ Cancel Booking",
        "booking_cancelled": "Booking cancelled.",
        "confirm_cancel": "Are you sure you want to cancel this booking?",

        # Statuses
        "status_pending": "⏳ Pending confirmation",
        "status_confirmed": "✅ Confirmed",
        "status_paid": "💳 Paid",
        "status_completed": "✔️ Completed",
        "status_cancelled": "❌ Cancelled",

        # Reminders
        "reminder_24h": "🔔 Reminder!\n\nTomorrow at {time} you have:\n📋 {service}\n\nAddress: {address}\n\nSee you!",
        "reminder_3h": "🔔 Your appointment in 3 hours!\n\n📋 {service}\n🕐 {time}\n\nAddress: {address}",

        # Referral
        "referral_info": "👥 Invite friends and get a discount!\n\nYour referral link:\n{link}\n\nFor each friend you invite, you both get {discount}% off your next visit!",

        # Contacts
        "contacts_info": "📍 Address: {address}\n📞 Phone: {phone}\n\n🕐 Working hours:\n{schedule}",

        # Master panel
        "master_menu": "👩‍💼 Master Panel",
        "btn_today": "📋 Today's Bookings",
        "btn_calendar": "📅 Calendar",
        "btn_settings": "⚙️ Schedule Settings",
        "btn_block_slot": "🚫 Block Slot",
        "btn_stats": "📊 Statistics",
        "btn_broadcast": "📢 Broadcast",

        "no_appointments_today": "No appointments for today.",
        "today_appointments": "📋 Today's appointments ({date}):\n\n{list}",
        "appointment_item": "🕐 {time} - {client}\n   📋 {service}\n   📞 {phone}\n   Status: {status}",

        # Notifications
        "new_booking_notification": "🔔 New booking!\n\n👤 Client: {client} (@{username})\n📋 Service: {service}\n📅 Date: {date} at {time}\n📞 Phone: {phone}\n\nStatus: Pending confirmation",
        "btn_confirm_booking": "✅ Confirm",
        "btn_reject_booking": "❌ Reject",
        "btn_contact_client": "📞 Contact",

        "booking_confirmed_client": "✅ Your booking is confirmed!\n\n📋 {service}\n📅 {date} at {time}\n\nSee you there!",
        "booking_rejected_client": "❌ Unfortunately, your booking was declined.\n\nPlease choose another time.",

        # Stats
        "stats_report": "📊 Statistics for {days} days:\n\n📋 Total bookings: {total}\n✅ Completed: {completed}\n❌ Cancelled: {cancelled}\n💵 Revenue: {revenue} EGP\n📉 Cancellation rate: {no_show}%\n\n🔝 Popular services:\n{popular}",

        # Reviews
        "ask_review": "How was your experience? Rate from 1 to 5 ⭐",
        "ask_review_text": "Thank you! Would you like to leave a comment?",
        "btn_skip": "Skip",
        "review_thanks": "Thank you for your feedback! 🙏",

        # Errors
        "error_occurred": "An error occurred. Please try again later.",
        "master_only": "This feature is only available for the master.",
    }
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Get localized text by key."""
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def get_service_name(service: dict, lang: str) -> str:
    """Get localized service name."""
    return service.get(f"name_{lang}") or service.get("name_ru")


def get_category_name(category: dict, lang: str) -> str:
    """Get localized category name."""
    return category.get(f"name_{lang}") or category.get("name_ru")


def get_status_text(status: str, lang: str) -> str:
    """Get localized status text."""
    status_map = {
        "pending": "status_pending",
        "confirmed": "status_confirmed",
        "paid": "status_paid",
        "completed": "status_completed",
        "cancelled": "status_cancelled"
    }
    return get_text(status_map.get(status, status), lang)
