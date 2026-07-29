"""
utils/validator.py

This is the safety layer between "the LLM generated some SQL text"
and "we actually run it against the database."

We NEVER trust generated SQL blindly. Rule: only a single, read-only
SELECT statement is allowed. Anything else is rejected before it
touches the database.
"""

import re

# Keywords that should never appear in a query we're about to run.
# This list is intentionally broad -- better to over-block and let a
# legit query be retried than to under-block and risk data loss.
BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "EXEC", "EXECUTE", "MERGE", "GRANT", "REVOKE", "CREATE",
    "sp_", "xp_", "--", "/*", "*/", ";",
]


class UnsafeQueryError(Exception):
    """Raised when generated SQL fails validation."""
    pass


def validate_sql(sql: str) -> str:
    """
    Validates that `sql` is a single, safe, read-only SELECT statement.
    Returns the cleaned SQL string if valid, otherwise raises
    UnsafeQueryError with a human-readable reason.
    """
    if not sql or not sql.strip():
        raise UnsafeQueryError("Generated SQL was empty.")

    cleaned = sql.strip()

    # Strip a trailing semicolon (single one is fine, just remove it --
    # this also naturally helps catch multi-statement injection below)
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    upper = cleaned.upper()

    # Must start with SELECT -- no exceptions.
    if not upper.startswith("SELECT"):
        raise UnsafeQueryError(
            "Only SELECT queries are allowed. Generated query did not start with SELECT."
        )

    # Block any dangerous keyword appearing anywhere in the query.
    for keyword in BLOCKED_KEYWORDS:
        # word-boundary check for word-like keywords, plain substring for symbols
        if re.match(r"^[A-Za-z_]+$", keyword):
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, upper):
                raise UnsafeQueryError(f"Blocked keyword detected in query: {keyword}")
        else:
            if keyword in cleaned:
                raise UnsafeQueryError(f"Blocked character/sequence detected in query: {keyword}")

    # Reject multiple statements (a semicolon followed by more content)
    if ";" in cleaned:
        raise UnsafeQueryError("Multiple SQL statements are not allowed.")

    return cleaned
