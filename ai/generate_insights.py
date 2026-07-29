"""
ai/generate_insights.py

Takes the ACTUAL results returned from SQL Server (never the LLM's
own claimed answer) and asks Groq to summarize them in plain
business language. This is what makes the app trustworthy -- the
numbers in the insight always trace back to a real, executed query.
"""

import pandas as pd
from ai.llm_client import ask_llm
from ai.prompts import build_insight_prompt

MAX_ROWS_FOR_PROMPT = 50  # keep prompt size reasonable for large result sets


def _results_to_text(df: pd.DataFrame) -> str:
    if df.empty:
        return "(no rows returned)"
    display_df = df.head(MAX_ROWS_FOR_PROMPT)
    text = display_df.to_string(index=False)
    if len(df) > MAX_ROWS_FOR_PROMPT:
        text += f"\n... ({len(df) - MAX_ROWS_FOR_PROMPT} more rows not shown)"
    return text


def generate_insight(question: str, results_df: pd.DataFrame) -> str:
    """
    Returns a plain-text business insight based on the real query
    results for `question`.
    """
    results_text = _results_to_text(results_df)
    prompt = build_insight_prompt(question, results_text)
    return ask_llm(prompt, temperature=0.4)
