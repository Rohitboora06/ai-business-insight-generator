"""
utils/helpers.py

Small shared utility functions used across the app.
"""

import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Light cleaning applied to any uploaded CSV before it's written to
    SQL Server: strips whitespace from column names, drops fully
    empty rows/columns.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    return df
