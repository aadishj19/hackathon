"""Load every table file in a folder into one DuckDB database, queryable by SQL and pandas.

    from hack import data
    con = data.connect()                        # loads DATA_DIR from .env
    df = con.sql("SELECT * FROM transactions").df()

CSV, Parquet, JSON and Excel are supported. Each Excel sheet becomes its own table named
<file>_<sheet>. Table names are the file name in snake_case.
"""

import re
import warnings
from pathlib import Path

import duckdb
import pandas as pd

from hack.config import data_dir

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
    # Nothing needs files after loading, so no reading or writing them from here on. This can't
    # be switched back on for this connection.
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
