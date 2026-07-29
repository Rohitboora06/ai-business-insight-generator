"""
database/schema.py

Since the user can upload ANY csv, we can't hardcode a table schema.
This module inspects the uploaded DataFrame and builds a matching
SQL Server table definition on the fly.
"""

import re
import pandas as pd


def clean_column_name(col: str) -> str:
    """
    SQL Server is picky about column names (spaces, special chars, etc).
    Convert 'Customer Name' -> 'Customer_Name', 'Age (yrs)' -> 'Age_yrs'
    """
    cleaned = re.sub(r"[^0-9a-zA-Z_]", "_", str(col).strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "col"
    if cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned


def infer_sql_type(series: pd.Series) -> str:
    """
    Maps a pandas column's dtype to a reasonable SQL Server column type.
    We keep this simple and slightly generous with sizes (e.g. NVARCHAR(255))
    rather than trying to be perfectly precise -- precision isn't the point
    of this project, getting a working, query-able table is.
    """
    if pd.api.types.is_bool_dtype(series):
        return "BIT"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "FLOAT"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"
    # Fallback: text. Size based on the longest value we actually see,
    # capped at NVARCHAR(MAX) if it's a long-text column.
    max_len = series.astype(str).str.len().max()
    if pd.isna(max_len):
        max_len = 255
    if max_len > 4000:
        return "NVARCHAR(MAX)"
    # Add some headroom above the observed max length
    size = min(max(int(max_len) * 2, 50), 4000)
    return f"NVARCHAR({size})"


def build_schema(df: pd.DataFrame, table_name: str) -> dict:
    """
    Returns a dict describing the table:
      {
        "table_name": "uploaded_data",
        "columns": [("Customer_Name", "NVARCHAR(200)"), ("Age", "BIGINT"), ...],
        "create_sql": "CREATE TABLE ... "
      }

    This dict is also what we hand to the LLM later, so it knows the
    real column names and types when generating SQL.
    """
    columns = []
    seen = set()
    for col in df.columns:
        clean = clean_column_name(col)
        # avoid duplicate column names after cleaning
        original_clean = clean
        i = 1
        while clean in seen:
            clean = f"{original_clean}_{i}"
            i += 1
        seen.add(clean)
        sql_type = infer_sql_type(df[col])
        columns.append((clean, sql_type))

    col_defs = ",\n    ".join(f"[{name}] {sql_type}" for name, sql_type in columns)
    create_sql = (
        f"IF OBJECT_ID('dbo.{table_name}', 'U') IS NOT NULL DROP TABLE dbo.{table_name};\n"
        f"CREATE TABLE dbo.{table_name} (\n    {col_defs}\n);"
    )

    return {
        "table_name": table_name,
        "columns": columns,
        "create_sql": create_sql,
    }


def schema_to_prompt_text(schema: dict) -> str:
    """
    Formats the schema as plain text to inject into the LLM prompt,
    e.g.:
        Table: uploaded_data
        Columns:
          - Customer_Name (NVARCHAR)
          - Age (BIGINT)
          - Purchase_Amount (FLOAT)
    """
    lines = [f"Table: {schema['table_name']}", "Columns:"]
    for name, sql_type in schema["columns"]:
        lines.append(f"  - {name} ({sql_type})")
    return "\n".join(lines)
