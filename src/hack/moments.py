"""Life-moments engine: notice a change in a customer's transactions, decide what to do, and
write the card. This file is the contract between the lanes; see
docs/plans/life-moments-engine.md and docs/plans/tasks.md.

    uv run python -m hack.moments      # prints usual payments, flagged customers, responses

PLACEHOLDER: `detect()` returns fixed rows for the four demo customers and `respond()` uses
template text, until the AI lane replaces them with SQL detectors and LLM wording. The word
lists, the rule table, `usual_month()` and `coming_up()` are real and can be built on.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

import duckdb
import pandas as pd

MOMENTS = ("first_salary", "moved", "rent_stopped", "income_missing", "income_loss", "big_travel")
DECISIONS = ("ask", "nudge", "protect_quietly", "none")

# The rule table: rules decide, the LLM only writes the wording.
RULES = {
    "first_salary": "ask",
    "moved": "ask",
    "rent_stopped": "ask",
    "income_missing": "protect_quietly",
    "income_loss": "protect_quietly",
    "big_travel": "nudge",
}
BUTTONS = {
    "first_salary": ["Finished studying, working now", "Still studying, this is a side job"],
    "moved": ["Yes, I moved", "No, same place"],
    "rent_stopped": ["Moved", "Payment problem"],
}
QUIET_ANSWERS = ("Prefer not to say", "That's not right")
QUIET_MONTHS = 3
REGULAR = ("salary", "pension", "transfer", "rent", "utilities", "insurance")
TODAY = date(2026, 9, 30)  # the demo's "today": the last day of the synthetic data


@dataclass
class Response:
    decision: str
    message: str = ""  # what the customer sees; empty for protect_quietly and none
    why: str = ""  # "why you see this": what we saw, never the cause we guessed
    benefit: str = ""  # "what's in it for you"
    buttons: list[str] = field(default_factory=list)
    staff_note: str = ""  # KBC side only, for protect_quietly
    quiet_until: date | None = None  # set after "Prefer not to say" or "That's not right"


def month_end(year: int, month: int) -> date:
    """Last day of a month, the only kind of `as_of` date the demo uses."""
    first_next = date(year + month // 12, month % 12 + 1, 1)
    return first_next - timedelta(days=1)


def usual_month(con: duckdb.DuckDBPyConnection, as_of: date) -> pd.DataFrame:
    """Each customer's regular payments over the three months up to `as_of`: category, usual
    day of the month, usual amount (income positive, costs negative) and when it was last seen.
    A payment counts as regular when it appeared in at least two of those months."""
    return con.execute(
        """
        SELECT customer_id, category,
               CAST(median(dayofmonth(date)) AS INTEGER) AS usual_day,
               round(median(amount_eur), 2) AS usual_amount,
               max(date) AS last_seen
        FROM transactions
        WHERE category IN (SELECT unnest(?))
          AND date <= ? AND date > CAST(? AS DATE) - INTERVAL 3 MONTH
        GROUP BY ALL
        HAVING count(DISTINCT month(date)) >= 2
        ORDER BY customer_id, usual_day
        """,
        [list(REGULAR), as_of, as_of],
    ).df()


def coming_up(con: duckdb.DuckDBPyConnection, customer_id: str, as_of: date) -> pd.DataFrame:
    """The Coming up panel: one customer's regular payments in the 30 days after `as_of`."""
    usual = usual_month(con, as_of)
    rows = []
    for r in usual[usual["customer_id"] == customer_id].itertuples():
        due = date(as_of.year, as_of.month, 1) + timedelta(days=31)
        due = date(due.year, due.month, min(r.usual_day, 28))
        if due <= as_of + timedelta(days=30):
            rows.append({"date": due, "category": r.category, "amount_eur": r.usual_amount})
    return pd.DataFrame(rows, columns=["date", "category", "amount_eur"]).sort_values("date")


# PLACEHOLDER rows: the four demo customers, as the real detectors should find them.
_DEMO = [
    ("C0001", "first_salary", 4, 12, "salary of about €2,260 since April; before that a transfer of about €750"),
    ("C0058", "rent_stopped", 4, 12, "rent of about €916 paid January to March; none since April"),
    ("C0009", "income_missing", 4, 4, "no salary in April; usually about €3,150 around the 25th"),
    ("C0134", "income_missing", 4, 4, "no salary in April; usually paid around the 25th"),
    ("C0134", "income_loss", 5, 12, "no salary since April, two months or more; costs continue"),
]  # fmt: skip


def detect(con: duckdb.DuckDBPyConnection, as_of: date) -> pd.DataFrame:
    """One row per flagged customer as of `as_of`: customer_id, moment, since, evidence.
    PLACEHOLDER: fixed demo rows; the AI lane replaces this with one SQL query per moment."""
    rows = [
        {"customer_id": cid, "moment": m, "since": f"{as_of.year}-{first:02d}", "evidence": ev}
        for cid, m, first, last, ev in _DEMO
        if first <= as_of.month <= last
    ]
    return pd.DataFrame(rows, columns=["customer_id", "moment", "since", "evidence"])


def respond(row: dict, answer: str | None = None, as_of: date = TODAY) -> Response:
    """What to do for one flagged row, given the customer's answer so far (if any).
    PLACEHOLDER text: the AI lane swaps the templates for llm.ask_json with these as fallback."""
    moment, evidence = row["moment"], row["evidence"]
    if answer in QUIET_ANSWERS:
        return Response("none", quiet_until=month_end(*_add_months(as_of, QUIET_MONTHS)))
    decision = RULES[moment]
    if decision == "protect_quietly":
        return Response(
            decision,
            why=f"We saw: {evidence}.",
            staff_note="Income interrupted: hold back all offers. Do not call. "
            "If the customer gets in touch, offer help with fixed costs.",
        )
    if answer:
        return Response("nudge", message=f"Thanks. Here is what helps after: {answer}.")
    return Response(
        decision,
        message=_TEMPLATES[moment],
        why=f"We saw: {evidence}.",
        benefit=_BENEFITS[moment],
        buttons=[*BUTTONS.get(moment, []), "Prefer not to say"] if decision == "ask" else [],
    )


_TEMPLATES = {
    "first_salary": "A first salary landed. Our records still say student. Has something changed?",
    "moved": "Your rent payment changed. Did you move?",
    "rent_stopped": "Your usual rent payment didn't go out this month. Has something changed?",
    "big_travel": "Big trip coming up? Check whether your card already covers cancellation "
    "before buying extra insurance.",
}
_BENEFITS = {
    "first_salary": "Tell us and you stop getting student offers.",
    "moved": "We can show what to arrange after a move, if you want.",
    "rent_stopped": "We only help with what you tell us; nothing changes otherwise.",
    "big_travel": "Avoid paying twice for the same cover.",
}


def _add_months(d: date, n: int) -> tuple[int, int]:
    m = d.month - 1 + n
    return d.year + m // 12, m % 12 + 1


if __name__ == "__main__":
    from hack import data

    con = data.connect()
    for month in (4, 5, 9):
        as_of = month_end(2026, month)
        print(f"\n=== as of {as_of} ===")
        for row in detect(con, as_of).to_dict("records"):
            r = respond(row, as_of=as_of)
            text = r.message or r.staff_note
            print(f"{row['customer_id']} {row['moment']:<15} {r.decision:<16} {text}")
    sept = month_end(2026, 9)
    quiet = respond({"moment": "rent_stopped", "evidence": ""}, "Prefer not to say", sept)
    print(f"\nC0058 answers 'Prefer not to say' in September: quiet until {quiet.quiet_until}")
    print("\nComing up for C0001 after September:\n", coming_up(con, "C0001", sept))
