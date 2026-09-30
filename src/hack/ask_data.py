"""Ask a question in plain English, get SQL plus the result table (text-to-SQL).

Usage: `ask_data.answer(data.connect(), "Which segment spends most on travel?")` returns an
Answer with `.sql`, `.explanation` and `.df` (the result as a pandas DataFrame).
"""

from dataclasses import dataclass

import duckdb
import pandas as pd
from pydantic import BaseModel

from hack import llm
from hack.data import describe_for_llm

SYSTEM = """You write DuckDB SQL for a business analyst at a bank.
Rules:
- Use only the tables and columns in the schema below. Quote identifiers that need it.
- Return one read-only SELECT (or WITH ... SELECT) statement, no semicolon.
- Add LIMIT 200 unless the question asks for everything or the result is an aggregate.
- Prefer readable column aliases, since the result is shown to business users.

Schema:
{schema}"""


# Hard cap on result rows, whatever the model's SQL says. A "show every transaction" on a
# bank table could otherwise return millions of rows and freeze the app.
MAX_ROWS = 10_000


class SqlQuery(BaseModel):
    sql: str
    explanation: str


@dataclass
class Answer:
    question: str
    sql: str
    explanation: str
    df: pd.DataFrame
    truncated: bool = False  # True when the result had more than MAX_ROWS rows


def answer(con: duckdb.DuckDBPyConnection, question: str, retries: int = 1) -> Answer:
    system = SYSTEM.format(schema=describe_for_llm(con))
    prompt = question
    for attempt in range(retries + 1):
        try:
            q = llm.ask_json(prompt, SqlQuery, system=system)
        except llm.LLMError:
            if attempt == retries:
                raise
            continue  # an unreadable reply is usually a one-off, so ask again
        try:
            df = run_sql(con, q.sql, limit=MAX_ROWS + 1)  # one extra row reveals truncation
            return Answer(question, q.sql, q.explanation, df.head(MAX_ROWS), len(df) > MAX_ROWS)
        except (duckdb.Error, ValueError) as e:
            if attempt == retries:
                raise
            # Feed the error back once; the model usually fixes a wrong column name.
            prompt = f"{question}\n\nYour previous SQL:\n{q.sql}\nfailed with:\n{e}\nFix it."
    raise AssertionError("unreachable")


def run_sql(con: duckdb.DuckDBPyConnection, sql: str, limit: int | None = None) -> pd.DataFrame:
    """Run model-written SQL if DuckDB parses it as exactly one SELECT statement, returning
    at most `limit` rows (the query's own ORDER BY is kept).

    This blocks writes and multiple statements. Reading local files (read_csv and friends)
    is blocked separately: data.connect turns off DuckDB's file access after loading.
    """
    statements = con.extract_statements(sql)
    if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
        raise ValueError("Only a single SELECT statement is allowed.")
    result = con.sql(statements[0].query)
    return (result.limit(limit) if limit else result).df()
