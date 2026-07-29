"""
database/upload_data.py

Takes an uploaded CSV (as a pandas DataFrame), creates a matching
table in SQL Server, and inserts all the rows.
"""

import pandas as pd
from database.connection import get_connection
from database.schema import build_schema, clean_column_name

TABLE_NAME = "uploaded_data"


def upload_dataframe(df: pd.DataFrame, table_name: str = TABLE_NAME) -> dict:
    """
    Creates (or replaces) a SQL Server table matching df's structure,
    then inserts every row.

    Returns the schema dict (from build_schema) so the caller can pass
    it straight to the AI layer for prompt context.
    """
    schema = build_schema(df, table_name)

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Create the table (drops any previous upload with the same name)
    cursor.execute(schema["create_sql"])
    conn.commit()

    # 2. Insert rows. fast_executemany speeds up bulk inserts a lot
    # for anything more than a handful of rows.
    cursor.fast_executemany = True

    clean_cols = [name for name, _ in schema["columns"]]
    placeholders = ", ".join("?" for _ in clean_cols)
    col_list = ", ".join(f"[{c}]" for c in clean_cols)
    insert_sql = f"INSERT INTO dbo.{table_name} ({col_list}) VALUES ({placeholders})"

    # Replace NaN with None so pyodbc inserts NULL instead of "nan"
    rows = df.where(pd.notnull(df), None).values.tolist()

    if rows:
        cursor.executemany(insert_sql, rows)
        conn.commit()

    conn.close()
    return schema
