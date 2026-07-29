"""
app.py

AI Business Insight Generator -- Streamlit entry point.

Flow:
  1. User uploads a CSV
  2. We create a matching table in SQL Server and insert the rows
  3. User asks a question in plain English
  4. Groq converts the question into SQL, using the real schema
  5. We VALIDATE the SQL (read-only, single statement) before running it
  6. We EXECUTE it against SQL Server and get real results
  7. Groq writes a business-friendly summary of those real results
  8. We show: the question, the generated SQL, the result table, and the summary
"""

import streamlit as st
import pandas as pd

from database.upload_data import upload_dataframe
from database.execute_sql import run_query
from database.schema import schema_to_prompt_text
from ai.generate_sql import generate_sql, NoQueryPossibleError
from ai.generate_insights import generate_insight
from utils.validator import UnsafeQueryError

st.set_page_config(page_title="AI Business Insight Generator", page_icon="📊", layout="wide")

st.title("📊 AI Business Insight Generator")
st.caption(
    "Upload a CSV, ask a question in plain English, and get a real, "
    "SQL-backed answer with an AI-written business insight."
)

# --- Session state setup ---
if "schema" not in st.session_state:
    st.session_state.schema = None
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: question, sql, df, insight

# --- Step 1: Upload CSV ---
st.header("1. Upload your data")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    df_preview = pd.read_csv(uploaded_file)
    st.write(f"Preview ({len(df_preview)} rows, {len(df_preview.columns)} columns):")
    st.dataframe(df_preview.head(10), use_container_width=True)

    if st.button("Load into database"):
        with st.spinner("Creating table and uploading rows to SQL Server..."):
            try:
                schema = upload_dataframe(df_preview)
                st.session_state.schema = schema
                st.success(f"Loaded {len(df_preview)} rows into table `{schema['table_name']}`.")
            except Exception as e:
                st.error(f"Upload failed: {e}")

# --- Step 2: Ask a question ---
if st.session_state.schema:
    st.header("2. Ask a question about your data")

    with st.expander("View detected table schema"):
        st.code(schema_to_prompt_text(st.session_state.schema))

    question = st.text_input(
        "Ask in plain English, e.g. 'What are the top 5 customers by total spend?'"
    )

    if st.button("Get answer") and question.strip():
        schema_text = schema_to_prompt_text(st.session_state.schema)

        with st.spinner("Generating SQL query..."):
            try:
                sql = generate_sql(question, schema_text)
            except NoQueryPossibleError as e:
                st.warning(str(e))
                sql = None
            except Exception as e:
                st.error(f"Could not generate a query: {e}")
                sql = None

        if sql:
            with st.spinner("Running query against your data..."):
                try:
                    result_df = run_query(sql)
                except UnsafeQueryError as e:
                    st.error(f"Generated query was rejected for safety reasons: {e}")
                    result_df = None
                except Exception as e:
                    st.error(f"Query execution failed: {e}")
                    result_df = None

            if result_df is not None:
                with st.spinner("Writing business insight..."):
                    try:
                        insight = generate_insight(question, result_df)
                    except Exception as e:
                        insight = f"(Could not generate insight: {e})"

                st.session_state.history.insert(
                    0, {"question": question, "sql": sql, "df": result_df, "insight": insight}
                )

# --- Step 3: Show results (most recent first) ---
if st.session_state.history:
    st.header("3. Results")
    for i, entry in enumerate(st.session_state.history):
        with st.container(border=True):
            st.markdown(f"**Q: {entry['question']}**")

            with st.expander("Generated SQL"):
                st.code(entry["sql"], language="sql")

            st.dataframe(entry["df"], use_container_width=True)
            st.markdown("**AI Insight:**")
            st.markdown(entry["insight"])
