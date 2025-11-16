import psycopg2
import os

class PostgresClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASS", "password"),
            database=os.getenv("PG_DB", "main")
        )
        self.conn.autocommit = True

    def execute(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def fetch_one(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()