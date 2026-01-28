import aiosqlite
from datetime import datetime, date, time
from typing import Optional, List
from config import DATABASE_PATH


async def init_db():
    """Initialize database with all tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                name TEXT,
                phone TEXT,
                language TEXT DEFAULT 'ru',
                role TEXT DEFAULT 'client',
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_visits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Service categories
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Services table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                description_ru TEXT,
                description_en TEXT,
                duration INTEGER NOT NULL,
                price_egp REAL NOT NULL,
                price_usd REAL,
                photo_id TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Master schedule (working hours)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Blocked slots (days off, breaks)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                reason TEXT,
                is_full_day INTEGER DEFAULT 0
            )
        """)

        # Appointments table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'unpaid',
                payment_amount REAL,
                notes TEXT,
                reminder_24h_sent INTEGER DEFAULT 0,
                reminder_3h_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        # Reviews table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER UNIQUE,
                client_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments(id),
                FOREIGN KEY (client_id) REFERENCES users(id)
            )
        """)

        # Waitlist table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                service_id INTEGER,
                preferred_date TEXT,
                notified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES users(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        await db.commit()


# ============ USER OPERATIONS ============

async def get_user(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_user(telegram_id: int, username: str = None, name: str = None,
                      phone: str = None, language: str = 'ru', referral_code: str = None) -> int:
    import secrets
    user_referral = secrets.token_hex(4)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Find referrer if code provided
        referred_by = None
        if referral_code:
            cursor = await db.execute(
                "SELECT id FROM users WHERE referral_code = ?", (referral_code,)
            )
            row = await cursor.fetchone()
            if row:
                referred_by = row[0]

        cursor = await db.execute(
            """INSERT INTO users (telegram_id, username, name, phone, language, referral_code, referred_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (telegram_id, username, name, phone, language, user_referral, referred_by)
        )
        await db.commit()
        return cursor.lastrowid


async def update_user(telegram_id: int, **kwargs) -> None:
    if not kwargs:
        return

    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [telegram_id]

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE users SET {fields} WHERE telegram_id = ?", values
        )
        await db.commit()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


# ============ CATEGORY OPERATIONS ============

async def get_categories(active_only: bool = True) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM categories"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY sort_order"
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def create_category(name_ru: str, name_en: str, sort_order: int = 0) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO categories (name_ru, name_en, sort_order) VALUES (?, ?, ?)",
            (name_ru, name_en, sort_order)
        )
        await db.commit()
        return cursor.lastrowid


# ============ SERVICE OPERATIONS ============

async def get_services(category_id: int = None, active_only: bool = True) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM services WHERE 1=1"
        params = []

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)
        if active_only:
            query += " AND is_active = 1"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_service(service_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_service(category_id: int, name_ru: str, name_en: str,
                         duration: int, price_egp: float, price_usd: float = None,
                         description_ru: str = None, description_en: str = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO services (category_id, name_ru, name_en, description_ru,
               description_en, duration, price_egp, price_usd)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (category_id, name_ru, name_en, description_ru, description_en,
             duration, price_egp, price_usd)
        )
        await db.commit()
        return cursor.lastrowid


# ============ SCHEDULE OPERATIONS ============

async def get_schedule() -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM schedule WHERE is_active = 1 ORDER BY day_of_week"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def set_schedule(day_of_week: int, start_time: str, end_time: str) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Remove existing schedule for this day
        await db.execute("DELETE FROM schedule WHERE day_of_week = ?", (day_of_week,))

        cursor = await db.execute(
            "INSERT INTO schedule (day_of_week, start_time, end_time) VALUES (?, ?, ?)",
            (day_of_week, start_time, end_time)
        )
        await db.commit()
        return cursor.lastrowid


async def get_blocked_slots(date_str: str) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM blocked_slots WHERE date = ?", (date_str,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def block_slot(date_str: str, start_time: str = None, end_time: str = None,
                     reason: str = None, is_full_day: bool = False) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO blocked_slots (date, start_time, end_time, reason, is_full_day)
               VALUES (?, ?, ?, ?, ?)""",
            (date_str, start_time, end_time, reason, 1 if is_full_day else 0)
        )
        await db.commit()
        return cursor.lastrowid


# ============ APPOINTMENT OPERATIONS ============

async def get_appointments(client_id: int = None, date_str: str = None,
                           status: str = None, upcoming_only: bool = False) -> List[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT a.*, s.name_ru as service_name_ru, s.name_en as service_name_en,
                   s.duration, s.price_egp, u.name as client_name, u.phone as client_phone,
                   u.telegram_id as client_telegram_id, u.username as client_username
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.client_id = u.id
            WHERE 1=1
        """
        params = []

        if client_id:
            query += " AND a.client_id = ?"
            params.append(client_id)
        if date_str:
            query += " AND a.date = ?"
            params.append(date_str)
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if upcoming_only:
            today = datetime.now().strftime("%Y-%m-%d")
            query += " AND a.date >= ? AND a.status NOT IN ('cancelled', 'completed')"
            params.append(today)

        query += " ORDER BY a.date, a.time"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_appointment(appointment_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT a.*, s.name_ru as service_name_ru, s.name_en as service_name_en,
                   s.duration, s.price_egp, u.name as client_name, u.phone as client_phone,
                   u.telegram_id as client_telegram_id, u.username as client_username
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.client_id = u.id
            WHERE a.id = ?
        """, (appointment_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_appointment(client_id: int, service_id: int, date_str: str,
                             time_str: str, notes: str = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO appointments (client_id, service_id, date, time, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (client_id, service_id, date_str, time_str, notes)
        )
        await db.commit()
        return cursor.lastrowid


async def update_appointment(appointment_id: int, **kwargs) -> None:
    if not kwargs:
        return

    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [appointment_id]

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE appointments SET {fields} WHERE id = ?", values
        )
        await db.commit()


async def get_booked_slots(date_str: str) -> List[dict]:
    """Get all booked time slots for a given date."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT a.time, s.duration
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            WHERE a.date = ? AND a.status NOT IN ('cancelled')
        """, (date_str,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def count_active_appointments(client_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*) FROM appointments
            WHERE client_id = ? AND status NOT IN ('cancelled', 'completed')
            AND date >= date('now')
        """, (client_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0


# ============ REMINDERS ============

async def get_appointments_for_reminder(hours: int) -> List[dict]:
    """Get appointments that need reminders."""
    from datetime import datetime, timedelta
    import pytz
    from config import TIMEZONE

    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    target_time = now + timedelta(hours=hours)

    date_str = target_time.strftime("%Y-%m-%d")
    time_str = target_time.strftime("%H:%M")

    reminder_field = f"reminder_{hours}h_sent" if hours in [3, 24] else None

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get appointments around the target time
        cursor = await db.execute("""
            SELECT a.*, s.name_ru as service_name_ru, s.name_en as service_name_en,
                   u.telegram_id, u.language, u.name as client_name
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN users u ON a.client_id = u.id
            WHERE a.date = ? AND a.status NOT IN ('cancelled', 'completed')
            AND a.reminder_24h_sent = 0 AND ? = 24
            OR a.date = ? AND a.status NOT IN ('cancelled', 'completed')
            AND a.reminder_3h_sent = 0 AND ? = 3
        """, (date_str, hours, date_str, hours))

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def mark_reminder_sent(appointment_id: int, hours: int) -> None:
    field = f"reminder_{hours}h_sent"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE appointments SET {field} = 1 WHERE id = ?",
            (appointment_id,)
        )
        await db.commit()


# ============ REVIEWS ============

async def create_review(appointment_id: int, client_id: int, rating: int, text: str = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO reviews (appointment_id, client_id, rating, text) VALUES (?, ?, ?, ?)",
            (appointment_id, client_id, rating, text)
        )
        # Update user's total visits
        await db.execute(
            "UPDATE users SET total_visits = total_visits + 1 WHERE id = ?",
            (client_id,)
        )
        await db.commit()
        return cursor.lastrowid


async def get_average_rating() -> float:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT AVG(rating) FROM reviews")
        row = await cursor.fetchone()
        return round(row[0], 1) if row and row[0] else 0.0


# ============ STATISTICS ============

async def get_statistics(days: int = 30) -> dict:
    from datetime import datetime, timedelta

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Total appointments
        cursor = await db.execute(
            "SELECT COUNT(*) FROM appointments WHERE date >= ?", (start_date,)
        )
        total = (await cursor.fetchone())[0]

        # Completed
        cursor = await db.execute(
            "SELECT COUNT(*) FROM appointments WHERE date >= ? AND status = 'completed'",
            (start_date,)
        )
        completed = (await cursor.fetchone())[0]

        # Cancelled
        cursor = await db.execute(
            "SELECT COUNT(*) FROM appointments WHERE date >= ? AND status = 'cancelled'",
            (start_date,)
        )
        cancelled = (await cursor.fetchone())[0]

        # Revenue
        cursor = await db.execute("""
            SELECT SUM(s.price_egp) FROM appointments a
            JOIN services s ON a.service_id = s.id
            WHERE a.date >= ? AND a.status = 'completed'
        """, (start_date,))
        revenue = (await cursor.fetchone())[0] or 0

        # Popular services
        cursor = await db.execute("""
            SELECT s.name_ru, COUNT(*) as cnt FROM appointments a
            JOIN services s ON a.service_id = s.id
            WHERE a.date >= ?
            GROUP BY s.id ORDER BY cnt DESC LIMIT 5
        """, (start_date,))
        popular = await cursor.fetchall()

        return {
            "total_appointments": total,
            "completed": completed,
            "cancelled": cancelled,
            "revenue_egp": revenue,
            "popular_services": [(row[0], row[1]) for row in popular],
            "no_show_rate": round(cancelled / total * 100, 1) if total > 0 else 0
        }


# ============ DEMO DATA ============

async def create_demo_data():
    """Create demo categories and services for testing."""
    # Check if data exists
    categories = await get_categories()
    if categories:
        return

    # Create categories
    cat1 = await create_category("Маникюр", "Manicure", 1)
    cat2 = await create_category("Педикюр", "Pedicure", 2)
    cat3 = await create_category("Массаж", "Massage", 3)

    # Create services
    await create_service(cat1, "Классический маникюр", "Classic Manicure",
                         60, 300, 6, "Обработка кутикулы и покрытие лаком",
                         "Cuticle treatment and polish")
    await create_service(cat1, "Маникюр с гель-лаком", "Gel Manicure",
                         90, 500, 10, "Стойкое покрытие гель-лаком",
                         "Long-lasting gel polish")
    await create_service(cat1, "Наращивание ногтей", "Nail Extensions",
                         120, 800, 16, "Наращивание гелем или акрилом",
                         "Gel or acrylic extensions")

    await create_service(cat2, "Классический педикюр", "Classic Pedicure",
                         60, 400, 8, "Уход за стопами и ногтями",
                         "Foot and nail care")
    await create_service(cat2, "SPA-педикюр", "SPA Pedicure",
                         90, 600, 12, "Расслабляющий уход с маской",
                         "Relaxing treatment with mask")

    await create_service(cat3, "Расслабляющий массаж", "Relaxing Massage",
                         60, 500, 10, "Общий расслабляющий массаж",
                         "Full body relaxing massage")
    await create_service(cat3, "Массаж спины", "Back Massage",
                         30, 300, 6, "Массаж спины и шеи",
                         "Back and neck massage")

    # Create default schedule (Mon-Sat 9:00-18:00)
    for day in range(0, 6):  # 0=Monday, 5=Saturday
        await set_schedule(day, "09:00", "18:00")
