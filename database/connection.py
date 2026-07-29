"""
database/connection.py

Handles the connection to SQL Server (running in Docker) using pyodbc.
Credentials are read from environment variables (see .env.example) so
nothing sensitive is hardcoded or committed to git.
"""

import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# --- Connection settings (from .env) ---
SQL_SERVER = os.getenv("SQL_SERVER", "localhost,1433")
SQL_DATABASE = os.getenv("SQL_DATABASE", "AIBusinessInsights")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_DRIVER = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")


def get_connection():
    """
    Opens and returns a new pyodbc connection to SQL Server.

    We open a fresh connection per use (rather than a single long-lived
    global connection) because Streamlit re-runs the script on every
    user interaction — a single shared connection can silently die
    or get reused across sessions in confusing ways.
    """
    conn_str = (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def test_connection():
    """Quick sanity check you can run standalone: python -m database.connection"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION;")
        row = cursor.fetchone()
        print("Connected successfully.")
        print(row[0])
        conn.close()
    except Exception as e:
        print("Connection failed:", e)


if __name__ == "__main__":
    test_connection()
