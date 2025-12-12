# INFRASTRUCTURE LAYER - PostgreSQL Implementation

import psycopg2
from domain.interfaces import UserRepository


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository interface."""

    def __init__(self, host, port, database, user, password):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        self._init_table()

    def _init_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        """)
        self.conn.commit()

    def get_all(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email FROM users")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]

    def get_by_id(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return {"id": row[0], "name": row[1], "email": row[2]} if row else None

    def create(self, name: str, email: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
            (name, email)
        )
        user_id = cursor.fetchone()[0]
        self.conn.commit()
        return {"id": user_id, "name": name, "email": email}

    def delete(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        affected = cursor.rowcount
        self.conn.commit()
        return affected > 0
