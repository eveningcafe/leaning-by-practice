# DATA LAYER - Database Access

import sqlite3

DATABASE = "/app/db/users.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_all() -> list:
    conn = sqlite3.connect(DATABASE)
    rows = conn.execute("SELECT id, name, email FROM users").fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]


def get_by_id(user_id: int):
    conn = sqlite3.connect(DATABASE)
    row = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return {"id": row[0], "name": row[1], "email": row[2]} if row else None


def create(name: str, email: str) -> dict:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": user_id, "name": name, "email": email}


def delete(user_id: int) -> bool:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0
