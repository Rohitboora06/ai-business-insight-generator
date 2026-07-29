"""
ai/prompts.py

All prompt templates live here, separate from the API-calling logic.
This makes them easy to read and iterate on without touching
llm_client.py or the generate_*.py files.

There are exactly two prompts in this project:
  1. SQL_GENERATION_PROMPT  -- turns a natural language question into SQL
  2. INSIGHT_GENERATION_PROMPT -- turns query results into a business summary
"""

SQL_GENERATION_PROMPT = """You are a SQL expert. Convert the user's question into a single, valid Microsoft SQL Server SELECT query.

{schema}

Rules:
- Output ONLY the raw SQL query. No explanations, no markdown, no code fences, no comments.
- Use only SELECT statements. Never modify data.
- Use only the exact table and column names given above.
- Use TOP instead of LIMIT (this is SQL Server syntax).
- If the question cannot be answered with the given columns, output exactly: NO_QUERY_POSSIBLE

User question: "{question}"

SQL query:"""


INSIGHT_GENERATION_PROMPT = """You are a business analyst. Based on the user's question and the query results below, write a short, clear business insight.

User question: "{question}"

Query results (as a table):
{results}

Write your response as:
1. A one-sentence direct answer to the question.
2. 2-3 bullet points of relevant observations from the data.
3. One brief, actionable recommendation if appropriate.

Keep it concise and business-friendly -- avoid technical jargon about the data itself (no mention of SQL, tables, or column names)."""


def build_sql_prompt(question: str, schema_text: str) -> str:
    return SQL_GENERATION_PROMPT.format(schema=schema_text, question=question)


def build_insight_prompt(question: str, results_text: str) -> str:
    return INSIGHT_GENERATION_PROMPT.format(question=question, results=results_text)
