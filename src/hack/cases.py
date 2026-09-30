"""Measure any feature on a fixed set of cases, and compare it with how the task is done today.

This is the evidence for the pitch: "correct on 17 of 20 cases, 4 seconds each, versus 12 of
20 and 3 minutes by hand". Works for any feature that takes text in and gives an answer out.

    from hack import cases
    test = cases.load("evals/triage_cases.csv")          # columns: input, expected[, note]
    results = cases.run(test, feature=triage)             # triage(text) -> answer
    results = cases.run(test, feature=triage, baseline=keyword_rule)
    print(cases.summary(results))
    results.to_csv("exports/triage_results.csv", index=False)

Pick cases on purpose, not only easy ones: ordinary cases, ambiguous ones, and cases where
the right outcome is to stop or ask a person. `note` is free text for why a case is there.
Each run of an LLM feature costs one call per case.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class Case:
    input: str
    expected: str
    note: str = ""


def load(path: Path | str) -> list[Case]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = {"input", "expected"} - set(df.columns)
    if missing:
        raise ValueError(f"{path} needs the columns input and expected; missing: {missing}")
    return [Case(r["input"], r["expected"], r.get("note", "")) for r in df.to_dict("records")]


def same_text(expected: str, actual: Any) -> bool:
    """Default check: equal after trimming and ignoring case; numbers equal to 2 decimals."""
    a, e = str(actual).strip().lower(), str(expected).strip().lower()
    try:
        return round(float(a), 2) == round(float(e), 2)
    except ValueError:
        return a == e


def run(
    cases: list[Case],
    feature: Callable[[str], Any],
    check: Callable[[str, Any], bool] = same_text,
    baseline: Callable[[str], Any] | None = None,
) -> pd.DataFrame:
    """Run `feature` (and optionally `baseline`) on every case. One row per case with the
    answer, whether it is correct, the seconds it took, and any error. A crash counts as
    wrong, so one bad case never stops the run."""
    rows = []
    for c in cases:
        row = {"input": c.input, "expected": c.expected, "note": c.note}
        row.update(_timed(feature, c, check, prefix=""))
        if baseline:
            row.update(_timed(baseline, c, check, prefix="baseline_"))
        rows.append(row)
    return pd.DataFrame(rows)


def summary(results: pd.DataFrame) -> str:
    """One line per approach, for example 'AI: 17/20 correct (85%), median 3.9 s per case'."""
    lines = [_line("AI", results, "")]
    if "baseline_ok" in results:
        lines.append(_line("Baseline", results, "baseline_"))
    wrong = results[~results["ok"]]
    for _, r in wrong.iterrows():
        got = r["error"] or r["actual"]
        lines.append(f"  wrong: {r['input'][:60]!r} expected {r['expected']!r}, got {got!r}")
    return "\n".join(lines)


def _timed(fn: Callable[[str], Any], case: Case, check, prefix: str) -> dict:
    start = time.perf_counter()
    try:
        actual, error = fn(case.input), ""
        ok = bool(check(case.expected, actual))
    except Exception as e:  # noqa: BLE001 - a crash is a wrong answer, not a stopped run
        actual, error, ok = None, f"{type(e).__name__}: {e}", False
    return {
        f"{prefix}actual": actual,
        f"{prefix}ok": ok,
        f"{prefix}seconds": round(time.perf_counter() - start, 2),
        f"{prefix}error": error,
    }


def _line(label: str, results: pd.DataFrame, prefix: str) -> str:
    n, correct = len(results), int(results[f"{prefix}ok"].sum())
    pct = f"{correct / n:.0%}" if n else "n/a"
    median = results[f"{prefix}seconds"].median() if n else 0
    return f"{label}: {correct}/{n} correct ({pct}), median {median:.1f} s per case"
