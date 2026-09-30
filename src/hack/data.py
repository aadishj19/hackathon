"""Load every table file in a folder into one DuckDB database, queryable by SQL and pandas.

    from hack import data
    con = data.connect()                        # loads DATA_DIR from .env
    df = con.sql("SELECT * FROM transactions").df()
    data.export_for_powerbi(con)                # writes exports/<table>.csv

CSV, Parquet, JSON and Excel are supported. Each Excel sheet becomes its own table named
<file>_<sheet>. Table names are the file name in snake_case.
"""

import re
import warnings
from pathlib import Path

import duckdb
import pandas as pd

from hack.config import EXPORTS_DIR, data_dir, env

_READERS = {".csv": "read_csv_auto", ".parquet": "read_parquet", ".json": "read_json_auto"}


def connect(
    folder: Path | str | None = None, skipped: list[str] | None = None
) -> duckdb.DuckDBPyConnection:
    """Files that fail to load are skipped with a warning and appended to `skipped`."""
    folder = Path(folder) if folder else data_dir()
    con = duckdb.connect()
    for path in sorted(folder.rglob("*")):
        # "~$" files are the lock files Excel creates next to an open workbook
        if path.name.startswith(("~$", ".")) or not path.is_file():
            continue
        try:
            _load(con, path)
        except Exception as e:  # noqa: BLE001 - one bad file must not stop the others loading
            msg = f"Skipped {path.relative_to(folder)}: {e}"
            warnings.warn(msg, stacklevel=2)
            if skipped is not None:
                skipped.append(msg)
    # Model-written SQL runs on this connection, so no reading or writing files from here on.
    # This can't be switched back on, which is why export_for_powerbi writes through pandas.
    con.execute("SET enable_external_access = false")
    return con


def _load(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix in _READERS:
        source = str(path).replace("'", "''")
        name = _q(_unique(con, table_name(path.stem)))
        try:
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM {_READERS[suffix]}('{source}')")
        except duckdb.InvalidInputException:
            if suffix != ".csv":
                raise
            # Older Belgian exports are often Latin-1 (Windows) rather than UTF-8
            con.execute(
                f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{source}', encoding='latin-1')"
            )
    elif suffix in (".xlsx", ".xls"):
        for sheet, df in pd.read_excel(path, sheet_name=None).items():
            if df.empty and len(df.columns) == 0:
                continue
            name = _q(_unique(con, table_name(f"{path.stem}_{sheet}")))
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM df")


def table_name(raw: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", raw).strip("_").lower()
    return f"t_{name}" if name[:1].isdigit() else name or "table"


def _unique(con: duckdb.DuckDBPyConnection, name: str) -> str:
    """Add _2, _3, ... when two files map to the same table name."""
    taken, candidate, n = set(tables(con)), name, 1
    while candidate in taken:
        n += 1
        candidate = f"{name}_{n}"
    return candidate


def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [row[0] for row in con.execute("SHOW TABLES").fetchall()]


DETAIL_LEVELS = ("schema", "labels", "samples")
# A text column counts as labels (safe to list) only if it has few distinct values AND each
# value repeats often. A 12-row table of customer names has few values, but none repeat.
_MAX_LABELS = 15
_MIN_REPEATS = 10
# Never list values of columns whose name suggests personal or account data
_PERSONAL = re.compile(
    r"name|mail|phone|iban|bic|account|address|street|postcode|zip|birth|passport|ssn|nationa",
    re.IGNORECASE,
)


def describe_for_llm(con: duckdb.DuckDBPyConnection) -> str:
    """The schema text sent to the LLM, at the level set by LLM_DATA_DETAIL in .env.

    Default "labels": no data rows ever leave the laptop, only table and column names, types,
    row counts, and the values of low-variety text columns (such as category = travel). Use
    "schema" if KBC allows nothing else to be shared, "samples" only for synthetic data.
    """
    detail = env("LLM_DATA_DETAIL", "labels").lower()
    if detail not in DETAIL_LEVELS:
        raise ValueError(f"LLM_DATA_DETAIL must be one of {', '.join(DETAIL_LEVELS)}.")
    return describe(con, detail)


def describe(con: duckdb.DuckDBPyConnection, detail: str = "samples") -> str:
    """Plain-text schema of every table. `detail` is "schema" (names, types, row counts),
    "labels" (plus the values of low-variety text columns) or "samples" (plus 3 rows).
    The default shows sample rows, for people reading it in the notebook."""
    parts = []
    for t in tables(con):
        count = con.execute(f"SELECT COUNT(*) FROM {_q(t)}").fetchone()[0]
        lines = [f"Table {t} ({count} rows)"]
        for name, col_type, *_ in con.execute(f"DESCRIBE {_q(t)}").fetchall():
            line = f"  - {name} ({col_type})"
            if detail != "schema" and col_type == "VARCHAR" and not _PERSONAL.search(name):
                values = _labels(con, t, name, count)
                if values:
                    line += f", values: {', '.join(values)}"
            lines.append(line)
        if detail == "samples":
            sample = con.execute(f"SELECT * FROM {_q(t)} LIMIT 3").df()
            lines.append(f"  sample:\n{sample.to_string(index=False, max_colwidth=40)}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _labels(con: duckdb.DuckDBPyConnection, table: str, column: str, rows: int) -> list[str]:
    """The distinct values of a text column if they look like categories: few of them, each
    repeated on average at least _MIN_REPEATS times. Otherwise nothing."""
    values = con.execute(
        f"SELECT DISTINCT {_q(column)} FROM {_q(table)} WHERE {_q(column)} IS NOT NULL "
        f"ORDER BY 1 LIMIT {_MAX_LABELS + 1}"
    ).fetchall()
    if not values or len(values) > _MAX_LABELS or rows < _MIN_REPEATS * len(values):
        return []
    return [str(v[0])[:40] for v in values]


def export_for_powerbi(
    con: duckdb.DuckDBPyConnection, names: list[str] | None = None, out: Path = EXPORTS_DIR
) -> list[Path]:
    """Write tables as CSV for Power BI (Get data > Text/CSV, or Folder for all at once).

    A full export (no `names`) first deletes the CSVs already in `out`, so a Power BI folder
    import never mixes in tables from an earlier dataset, such as the sample data.
    """
    out.mkdir(parents=True, exist_ok=True)
    if names is None:
        for old in out.glob("*.csv"):
            old.unlink()
    written = []
    for t in names or tables(con):
        path = out / f"{t}.csv"
        # DuckDB's own file access is off (see connect), so pandas writes the file.
        # utf-8-sig adds a byte-order mark, so Power BI and Excel read accents (é, è) correctly.
        con.table(t).df().to_csv(path, index=False, encoding="utf-8-sig")
        written.append(path)
    return written
