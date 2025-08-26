# db.py
import sqlite3
import logging
import os
import io
import csv
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

logger = logging.getLogger(__name__)

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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

def fetch_applications(limit=10, offset=0):
    """Возвращает список заявок (list[dict]) упорядоченных по created_at DESC."""
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT id, position, phone, name, age, branch, schedule,
                   experience, driving_experience, selfemployed, salary_expect, created_at
            FROM applications
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def count_applications():
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) as cnt FROM applications")
        row = cur.fetchone()
        return row["cnt"] if row else 0


def get_application(app_id: int):
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def delete_application(app_id: int):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cur.rowcount  # 1 если удалено, 0 если нет


def export_applications_csv():
    """
    Возвращает bytes CSV всех заявок в кодировке utf-8.
    Заголовок соответствует полям таблицы.
    """
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT id, position, phone, name, age, branch, schedule,
                   experience, driving_experience, selfemployed, salary_expect, created_at
            FROM applications
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "position", "phone", "name", "age", "branch", "schedule",
        "experience", "driving_experience", "selfemployed", "salary_expect", "created_at"
    ])
    for r in rows:
        writer.writerow([r["id"], r["position"], r["phone"], r["name"], r["age"], r["branch"],
                         r["schedule"], r["experience"], r["driving_experience"], r["selfemployed"],
                         r["salary_expect"], r["created_at"]])
    return output.getvalue().encode("utf-8")
