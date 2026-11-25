# db.py
# All database code is in this file: connecting, running queries and
# creating the tables the first time the app starts.

import os
import time

import psycopg2
import psycopg2.extras


def get_connection():
    # The connection string comes ONLY from the environment variable
    # DATABASE_URL, so the same code works in Docker and on Render.
    return psycopg2.connect(os.environ["DATABASE_URL"])


def run_query(sql, params=(), fetch="all"):
    """Run one SQL query.
    fetch="all"  -> return a list of rows (for SELECT)
    fetch="one"  -> return a single row or None (for SELECT)
    fetch="none" -> return nothing (for INSERT / UPDATE / DELETE)
    We always use %s placeholders, so user input never goes inside the SQL
    text itself (this prevents SQL injection).
    """
    conn = get_connection()
    try:
        # RealDictCursor gives rows as dictionaries: row["title"]
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = None
        if fetch == "all":
            result = cur.fetchall()
        elif fetch == "one":
            result = cur.fetchone()
        conn.commit()  # save the changes
        return result
    finally:
        conn.close()  # always close the connection


def init_db():
    """Create the tables from schema.sql if they do not exist yet."""
    # The database container may need a few seconds to start, so we retry.
    conn = None
    for attempt in range(1, 16):
        try:
            conn = get_connection()
            break
        except psycopg2.OperationalError:
            print(f"Database not ready (attempt {attempt}/15), waiting...")
            time.sleep(2)
    if conn is None:
        raise RuntimeError("Could not connect to the database")

    try:
        cur = conn.cursor()
        # to_regclass returns NULL if the table does not exist
        cur.execute("SELECT to_regclass('public.departments')")
        table_exists = cur.fetchone()[0] is not None

        if table_exists:
            print("Tables already exist: schema.sql skipped.")
        else:
            print("Tables not found: running schema.sql ...")
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, encoding="utf-8") as f:
                cur.execute(f.read())
            conn.commit()
    finally:
        conn.close()
