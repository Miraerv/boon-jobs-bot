import sqlite3
import logging
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

logger = logging.getLogger(__name__)

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка работы с БД: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            phone TEXT,
            name TEXT,
            age TEXT,
            branch TEXT,
            schedule TEXT,
            experience TEXT,
            driving_experience TEXT,
            selfemployed TEXT,
            salary_expect TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    logger.info("База данных инициализирована.")


def save_application(data: dict):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO applications (
            position, phone, name, age, branch, schedule,
            experience, driving_experience, selfemployed, salary_expect
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("position"),
            data.get("phone"),
            data.get("name"),
            data.get("age"),
            data.get("branch"),
            data.get("schedule"),
            data.get("experience"),
            data.get("driving_experience"),
            data.get("selfemployed"),
            data.get("salary_expect"),
        ))
    logger.info(f"Заявка сохранена: {data.get('name')} ({data.get('phone')})")
