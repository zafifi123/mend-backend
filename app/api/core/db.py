import psycopg2

DATABASE_URL = "postgresql://user:password@localhost:5432/mend_db"

def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()
