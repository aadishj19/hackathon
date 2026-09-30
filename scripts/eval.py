"""Accuracy check for "Ask your data": how often does the model's SQL give the right answer?

Each row in the cases file has a question and a known-correct SQL query. The script asks the
model, runs both queries and compares the results. It compares results, not SQL text, since
many different queries are correct. Extra columns and a different row order still count as a
pass, because the answer is the same.

Writing cases: the expected SQL should return only what the question asks for. For "which
segment has the most customers?" select just the segment, not the count as well, or a correct
answer without the count fails.

Run: uv run python scripts/eval.py [evals/ask_data_cases.csv]
Costs one or two LLM calls per case. Write cases that match the loaded data (DATA_DIR).
"""

import sys
import warnings

import pandas as pd

from hack import ask_data, data, llm
from hack.config import ROOT


def normalise(value) -> str:
    """Compare 5, 5.0 and 5.004 as equal, and ignore case and surrounding spaces in text."""
    if isinstance(value, bool) or value is None or pd.isna(value):
        return str(value)
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value).strip().lower()


def same_answer(expected: pd.DataFrame, actual: pd.DataFrame) -> bool:
    """Pass when the row counts match and every expected row's values appear in some model row."""
    if len(expected) != len(actual):
        return False
    actual_rows = [{normalise(v) for v in row} for row in actual.itertuples(index=False)]
    return all(
        any({normalise(v) for v in row} <= candidate for candidate in actual_rows)
        for row in expected.itertuples(index=False)
    )


def main() -> None:
    cases = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else ROOT / "evals" / "ask_data_cases.csv")
    if llm.provider() == "mock":
        sys.exit("The eval needs a real LLM provider. Add a key to .env.")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        con = data.connect()
    print(f"Running {len(cases)} cases on {llm.provider()} ({llm.model_name()})\n")

    passed = 0
    for i, case in enumerate(cases.itertuples(index=False), 1):
        expected = con.sql(case.expected_sql).df()
        try:
            result = ask_data.answer(con, case.question)
            ok, detail = same_answer(expected, result.df), result.sql
        except Exception as e:  # noqa: BLE001 - a crash counts as a failed case, not a stopped run
            ok, detail = False, f"{type(e).__name__}: {e}"
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {i}. {case.question}")
        if not ok:
            print(f"      model: {' '.join(detail.split())}")
            print(f"      expected: {expected.head(3).to_dict('records')}")

    print(f"\nAccuracy: {passed}/{len(cases)} ({passed / len(cases):.0%})")


if __name__ == "__main__":
    main()
