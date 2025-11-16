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

    def fetch_table_columns(self, table_name):
        """Fetch column names and types for a table"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
                (table_name,)
            )
            return {row[0]: row[1] for row in cur.fetchall()}

    def list_tables(self):
        """List all tables in public schema"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            return [r[0] for r in cur.fetchall()]

    def ensure_base_schema(self):
        """Run base schema file to create users table and extensions"""
        cur = self.conn.cursor()
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'base_schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    cur.execute(f.read())
                self.conn.commit()
        except Exception as e:
            print(f"Warning: Could not load base schema: {e}")
        finally:
            cur.close()