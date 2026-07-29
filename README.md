# 📊 AI Business Insight Generator

An AI-powered assistant that lets you upload any CSV dataset, ask questions about it in plain English, and get back a **real, database-verified answer** plus an AI-written business insight.

## What it does

1. Upload a CSV file
2. The app creates a matching table in **SQL Server** and loads the data
3. Ask a question in plain English (e.g. *"What are the top 5 customers by total spend?"*)
4. **Groq** converts the question into a SQL query, using the actual table schema
5. The query is **validated** (read-only, single statement only) before it's allowed to run
6. The query is **executed against SQL Server** — the answer is always based on real data, not on the LLM's own guess
7. Groq writes a short, plain-language business insight based on the *actual* query results

## Why this design

A common shortcut in "AI + data" projects is to hand the LLM a sample of the data and let it answer directly from the prompt. That approach doesn't scale past small datasets and risks the model inventing numbers.

This project instead treats the LLM as a **query writer**, not a calculator:
- The LLM never sees or reports on data it hasn't been given — it only writes SQL
- SQL Server is the single source of truth for every number shown in the app
- A validation layer sits between "LLM generated some text" and "code executes it," blocking anything that isn't a safe, read-only `SELECT`

## Architecture

```
CSV upload
   │
   ▼
[database/upload_data.py] ── creates table + inserts rows ──▶ SQL Server (Docker)
   │
   ▼
User question (Streamlit)
   │
   ▼
[ai/generate_sql.py] ── Groq writes SQL using real schema
   │
   ▼
[utils/validator.py] ── blocks anything that isn't a safe SELECT
   │
   ▼
[database/execute_sql.py] ── runs the query against SQL Server
   │
   ▼
[ai/generate_insights.py] ── Groq summarizes the REAL results
   │
   ▼
Streamlit UI: question + generated SQL + result table + AI insight
```

## Tech stack

- **Python** — core application logic
- **Streamlit** — web UI
- **SQL Server (Docker)** — data storage and query execution
- **pyodbc** — Python ↔ SQL Server connection
- **Groq API (Llama 3.3)** — natural language → SQL, and results → insight
- **Pandas** — data handling between layers

## Project structure

```
ai_business_insights/
├── ai/
│   ├── llm_client.py         # Thin Groq API wrapper (auth + calls only)
│   ├── prompts.py            # The 2 prompt templates used in this app
│   ├── generate_sql.py       # Question -> SQL
│   └── generate_insights.py  # Query results -> business insight
├── database/
│   ├── connection.py         # SQL Server connection via pyodbc
│   ├── schema.py             # Infers table schema from any uploaded CSV
│   ├── upload_data.py        # Creates table + inserts uploaded rows
│   └── execute_sql.py        # Validates + runs a query, returns a DataFrame
├── utils/
│   ├── validator.py          # Safety layer: only allows read-only SELECT
│   └── helpers.py            # Small shared utilities
├── app.py                    # Streamlit entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Start SQL Server in Docker (adjust password as needed). On Apple Silicon Macs, Azure SQL Edge is used instead of full SQL Server, since it runs natively on ARM:
   ```bash
   docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourPassword123!" \
     -p 1433:1433 --name sqlserver -d mcr.microsoft.com/azure-sql-edge
   ```

2. Create the target database (e.g. using Azure Data Studio, or `sqlcmd`):
   ```sql
   CREATE DATABASE AIBusinessInsightDB;
   ```

3. Copy `.env.example` to `.env` and fill in your Groq API key and SQL Server credentials.

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Running it again later

After closing your terminal/VS Code, restart with:
```bash
source .venv/bin/activate
docker start sqlserver   # if not already running -- check with: docker ps
streamlit run app.py
```

## Safety notes

- All generated SQL passes through `utils/validator.py` before execution
- Only single, read-only `SELECT` statements are permitted
- Any query containing `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, or similar is rejected before it reaches the database
- API keys and database credentials are read from `.env`, which is git-ignored

## Possible extensions

- Multi-turn follow-up questions ("now break that down by region")
- Auto-generated charts from query results
- Downloadable PDF report of the insight
