"""
database/execute_sql.py

Runs a SQL query against SQL Server and returns the result as a
pandas DataFrame. Every query passes through validate_sql() first --
this file NEVER executes raw, unchecked SQL.
"""

import pandas as pd
from database.connection import get_connection
from utils.validator import validate_sql, UnsafeQueryError


def run_query(sql: str) -> pd.DataFrame:
    """
    Validates `sql`, then executes it and returns the results as a
    DataFrame. Raises UnsafeQueryError if validation fails (caller
    should catch this and show a friendly message instead of crashing).
    """
    safe_sql = validate_sql(sql)  # raises UnsafeQueryError if invalid

    conn = get_connection()
    try:
        df = pd.read_sql(safe_sql, conn)
    finally:
        conn.close()

    return df
