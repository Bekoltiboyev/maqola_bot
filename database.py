import aiosqlite
from datetime import datetime

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_blocked INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_current INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    journal_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_ext TEXT NOT NULL,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    admin_comment TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(journal_id) REFERENCES journals(id)
);

CREATE TABLE IF NOT EXISTS admin_files (
    key TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_journal ON submissions(journal_id);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

        # Migratsiya: eski bazada 'submissions' jadvalida status/admin_comment ustunlari bo'lmasligi mumkin
        for ddl in (
            "ALTER TABLE submissions ADD COLUMN status TEXT DEFAULT 'pending'",
            "ALTER TABLE submissions ADD COLUMN admin_comment TEXT",
        ):
            try:
                await db.execute(ddl)
                await db.commit()
            except Exception:
                pass  # ustun allaqachon mavjud

        cur = await db.execute("SELECT COUNT(*) FROM journals")
        row = await cur.fetchone()
        if row[0] == 0:
            await db.execute("INSERT INTO journals (number, is_current) VALUES (1, 1)")
            await db.commit()


# ---------------- USERS ----------------

async def get_user_by_tg(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        return await cur.fetchone()


async def register_user(tg_id: int, full_name: str, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (tg_id, full_name, phone) VALUES (?, ?, ?)",
            (tg_id, full_name, phone),
        )
        await db.commit()


async def get_all_user_tg_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT tg_id FROM users WHERE is_blocked = 0")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        return row[0]


# ---------------- JOURNALS ----------------

async def get_current_journal():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM journals WHERE is_current = 1 ORDER BY id DESC LIMIT 1"
        )
        return await cur.fetchone()


async def count_journals():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM journals")
        row = await cur.fetchone()
        return row[0]


async def create_new_journal():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE journals SET is_current = 0")
        cur = await db.execute("SELECT COALESCE(MAX(number), 0) FROM journals")
        row = await cur.fetchone()
        new_number = row[0] + 1
        await db.execute(
            "INSERT INTO journals (number, is_current) VALUES (?, 1)", (new_number,)
        )
        await db.commit()
        return new_number


# ---------------- SUBMISSIONS ----------------

async def has_submitted(user_id: int, journal_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM submissions WHERE user_id = ? AND journal_id = ?",
            (user_id, journal_id),
        )
        row = await cur.fetchone()
        return row[0] > 0


async def add_submission(user_id: int, journal_id: int, file_name: str, file_path: str, file_ext: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO submissions (user_id, journal_id, file_name, file_path, file_ext) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, journal_id, file_name, file_path, file_ext),
        )
        await db.commit()
        return cur.lastrowid


async def get_user_submissions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT s.*, j.number AS journal_number
            FROM submissions s
            JOIN journals j ON s.journal_id = j.id
            WHERE s.user_id = ?
            ORDER BY s.submitted_at DESC
            """,
            (user_id,),
        )
        return await cur.fetchall()


async def count_submissions():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM submissions")
        row = await cur.fetchone()
        return row[0]


async def get_pending_submissions():
    """Hali ko'rib chiqilmagan (status='pending') barcha maqolalarni qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT s.*, u.tg_id AS user_tg_id, u.full_name AS user_full_name,
                   u.phone AS user_phone, j.number AS journal_number
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN journals j ON s.journal_id = j.id
            WHERE s.status = 'pending' OR s.status IS NULL
            ORDER BY s.id
            """
        )
        return await cur.fetchall()
    """Maqolani foydalanuvchi va jurnal ma'lumotlari bilan birga qaytaradi (admin ko'rib chiqishi uchun)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT s.*, u.tg_id AS user_tg_id, u.full_name AS user_full_name, j.number AS journal_number
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN journals j ON s.journal_id = j.id
            WHERE s.id = ?
            """,
            (submission_id,),
        )
        return await cur.fetchone()


async def set_submission_status(submission_id: int, status: str, admin_comment: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE submissions SET status = ?, admin_comment = ? WHERE id = ?",
            (status, admin_comment, submission_id),
        )
        await db.commit()


# ---------------- ADMIN FILES (Axborot xati / Maqola namunasi) ----------------

async def set_admin_file(key: str, file_id: str, file_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO admin_files (key, file_id, file_name, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                file_id = excluded.file_id,
                file_name = excluded.file_name,
                updated_at = excluded.updated_at
            """,
            (key, file_id, file_name, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_admin_file(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM admin_files WHERE key = ?", (key,))
        return await cur.fetchone()


# ---------------- MAJBURIY KANALLAR (istalgancha) ----------------

async def add_channel(chat_id: str, url: str, title: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO channels (chat_id, url, title) VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                url = excluded.url,
                title = excluded.title
            """,
            (chat_id, url, title),
        )
        await db.commit()


async def remove_channel(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()


async def get_all_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM channels ORDER BY id")
        return await cur.fetchall()


async def get_channel(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        return await cur.fetchone()


async def update_channel_title(channel_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE channels SET title = ? WHERE id = ?", (title, channel_id))
        await db.commit()