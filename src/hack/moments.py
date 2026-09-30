"""Life-moments engine: notice a change in a customer's transactions, decide what to do, and
write the card. This file is the contract between the lanes; see
docs/plans/life-moments-engine.md and docs/plans/tasks.md.

    uv run python -m hack.moments      # prints usual payments, flagged customers, responses

`detect()` is one SQL query per moment over all customers. `respond()` decides with the rule
table and has the LLM write the card text, falling back to fixed templates without an API key
or when the LLM fails.
"""

import warnings
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import cache

import duckdb
import pandas as pd
from pydantic import BaseModel

from hack import data, llm

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


# Every detector starts from one row per customer per month up to `as_of`, with zeros for a
# month without a payment: a missing salary creates no transaction, so it has to be filled in.
# The whole history is used, not only the last few months, so a change stays visible after it
# happened (a move in May is still a move in September).
_MONTHLY = """
WITH tx AS (
    SELECT customer_id, CAST(date_trunc('month', date) AS DATE) AS month, date, category,
           amount_eur
    FROM transactions
    WHERE date <= $as_of
),
monthly AS (
    SELECT c.customer_id, m.month,
           coalesce(sum(t.amount_eur) FILTER (t.category IN ('salary', 'pension', 'transfer')), 0)
               AS income,
           count(t.amount_eur) FILTER (t.category = 'salary') AS salaries,
           count(t.amount_eur) FILTER (t.category = 'transfer') AS transfers,
           coalesce(-sum(t.amount_eur) FILTER (t.category = 'rent'), 0) AS rent,
           coalesce(-sum(t.amount_eur) FILTER (t.category = 'travel'), 0) AS travel,
           coalesce(-min(t.amount_eur) FILTER (t.category = 'shopping'), 0) AS biggest_purchase,
           coalesce(-sum(t.amount_eur)
               FILTER (t.category IN ('groceries', 'restaurants', 'shopping', 'travel')), 0)
               AS spending
    FROM (SELECT DISTINCT customer_id FROM tx) c
    CROSS JOIN (SELECT DISTINCT month FROM tx) m
    LEFT JOIN tx t ON t.customer_id = c.customer_id AND t.month = m.month
    GROUP BY ALL
),
this_month AS (SELECT CAST(date_trunc('month', CAST($as_of AS DATE)) AS DATE) AS month)
"""

# One query per moment. Each returns customer_id, moment, since (a DATE, the month the change
# started) and evidence (a short text of numbers, no names). Thresholds were checked on the
# synthetic data: see docs/plans/handoff-ai-lane.md.
_DETECTORS = {
    # A student's monthly transfer from home is replaced by a salary.
    "first_salary": """
        , first_pay AS (
            SELECT customer_id, min(month) AS since FROM monthly WHERE salaries > 0 GROUP BY 1
        )
        SELECT f.customer_id, 'first_salary' AS moment, f.since,
               format('salary of about €{:,} since {}; before that a transfer of about €{:,}',
                      CAST(round(avg(m.income) FILTER (m.month >= f.since AND m.salaries > 0)) AS INT),
                      strftime(f.since, '%B'),
                      CAST(round(avg(m.income) FILTER (m.month < f.since AND m.transfers > 0)) AS INT))
                   AS evidence
        FROM first_pay f JOIN monthly m USING (customer_id)
        GROUP BY f.customer_id, f.since
        HAVING count(*) FILTER (m.month < f.since AND m.transfers > 0 AND m.salaries = 0) > 0
    """,
    # Rent jumps by more than 15% from one month to the next. Normal rent never changes; the
    # yearly indexation is 2 to 4%.
    "moved": """
        , steps AS (
            SELECT *, lag(rent) OVER (PARTITION BY customer_id ORDER BY month) AS before
            FROM monthly
        )
        SELECT customer_id, 'moved' AS moment, month AS since,
               format('rent went from about €{:,} to €{:,} in {}', CAST(round(before) AS INT),
                      CAST(round(rent) AS INT), strftime(month, '%B'))
               || CASE WHEN biggest_purchase >= 800
                       THEN format(', plus a one-off purchase of about €{:,} that month',
                                   CAST(round(biggest_purchase) AS INT))
                       ELSE '' END AS evidence
        FROM steps
        WHERE before > 0 AND rent > 1.15 * before
        QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY month) = 1
    """,
    # Rent paid in at least two months, then none this month.
    "rent_stopped": """
        , paid AS (
            SELECT customer_id, count(*) FILTER (rent > 0) AS months_paid,
                   min(month) FILTER (rent > 0) AS first_paid,
                   max(month) FILTER (rent > 0) AS last_paid,
                   median(rent) FILTER (rent > 0) AS usual
            FROM monthly GROUP BY 1
        )
        SELECT customer_id, 'rent_stopped' AS moment,
               CAST(last_paid + INTERVAL 1 MONTH AS DATE) AS since,
               format('rent of about €{:,} paid {} to {}; none since {}',
                      CAST(round(usual) AS INT), strftime(first_paid, '%B'),
                      strftime(last_paid, '%B'), strftime(last_paid + INTERVAL 1 MONTH, '%B'))
                   AS evidence
        FROM paid, this_month
        WHERE months_paid >= 2 AND last_paid < this_month.month
    """,
    # No income this month after income before. One month missing is income_missing (a late
    # salary looks the same), two months or more is income_loss. A low month does not count:
    # small business income varies by 35% either way.
    "income": """
        , usual AS (
            SELECT customer_id, mode(category) AS category, median(amount_eur) AS amount,
                   CAST(median(dayofmonth(date)) AS INT) AS day
            FROM tx WHERE category IN ('salary', 'pension', 'transfer') GROUP BY 1
        ),
        gap AS (
            SELECT m.customer_id, max(m.month) FILTER (m.income > 0) AS last_paid,
                   sum(m.spending) FILTER (m.month = this_month.month) AS spending_now
            FROM monthly m, this_month GROUP BY 1
        )
        SELECT g.customer_id,
               CASE WHEN date_diff('month', g.last_paid, this_month.month) = 1
                    THEN 'income_missing' ELSE 'income_loss' END AS moment,
               CAST(g.last_paid + INTERVAL 1 MONTH AS DATE) AS since,
               CASE WHEN date_diff('month', g.last_paid, this_month.month) = 1
                    THEN format('no {} in {}; usually about €{:,} around day {}', u.category,
                                strftime(this_month.month, '%B'), CAST(round(u.amount) AS INT), u.day)
                    ELSE format('no {} since {} ({} months); usually about €{:,} around day {}; '
                                'everyday spending continues (about €{:,} in {})', u.category,
                                strftime(g.last_paid + INTERVAL 1 MONTH, '%B'),
                                date_diff('month', g.last_paid, this_month.month),
                                CAST(round(u.amount) AS INT), u.day,
                                CAST(round(g.spending_now) AS INT), strftime(this_month.month, '%B'))
               END AS evidence
        FROM gap g JOIN usual u USING (customer_id), this_month
        WHERE g.last_paid < this_month.month
    """,
    # One month of travel far above anything the customer usually spends. The most recent trip
    # counts, so a May trip is still visible in September.
    "big_travel": """
        SELECT customer_id, 'big_travel' AS moment, month AS since,
               format('travel spending of about €{:,} in {}; usually about €{:,} a month',
                      CAST(round(travel) AS INT), strftime(month, '%B'), CAST(round(usual) AS INT))
                   AS evidence
        FROM (SELECT *, median(travel) OVER (PARTITION BY customer_id) AS usual FROM monthly)
        WHERE travel >= 1500
        QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY month DESC) = 1
    """,
}

# When a customer matches more than one moment, the first in this list wins: protection comes
# before any question or tip, so nobody whose income stopped gets a travel nudge.
_PRIORITY = ["income_loss", "income_missing", "rent_stopped", "moved", "first_salary", "big_travel"]


def detect(con: duckdb.DuckDBPyConnection, as_of: date) -> pd.DataFrame:
    """One row per flagged customer as of `as_of`: customer_id, moment, since, evidence.
    `as_of` is the last day of a month; only transactions up to that day are used."""
    found = pd.concat(
        [con.execute(_MONTHLY + sql, {"as_of": as_of}).df() for sql in _DETECTORS.values()]
    )
    found["since"] = pd.to_datetime(found["since"]).dt.strftime("%Y-%m")
    found["rank"] = found["moment"].map(_PRIORITY.index)
    found = found.sort_values(["customer_id", "rank"]).drop_duplicates("customer_id")
    columns = ["customer_id", "moment", "since", "evidence"]
    return found[columns].reset_index(drop=True)


def respond(
    row: dict, answer: str | None = None, as_of: date = TODAY, use_llm: bool = True
) -> Response:
    """What to do for one flagged row, given the customer's answer so far (if any).
    The decision always comes from the rules and the answer; the LLM only writes the words on a
    card that has not been answered yet. `use_llm=False` gives the template text straight away,
    for when you only need the decision (for example to count messages for every customer)."""
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
        return Response(
            "nudge",
            message=FOLLOW_UPS.get((moment, answer), "Thanks, noted. Nothing changes."),
            staff_note=_PAYMENT_PROBLEM_NOTE if answer == "Payment problem" else "",
        )
    buttons = [*BUTTONS.get(moment, []), "Prefer not to say"] if decision == "ask" else []
    text = CardText(
        message=_TEMPLATES[moment], why=f"We saw: {evidence}.", benefit=_BENEFITS[moment]
    )
    if use_llm and llm.provider() != "mock":
        try:
            text = _card_text(moment, evidence, *_profile(row.get("customer_id")), tuple(buttons))
        except Exception as e:  # noqa: BLE001 - any LLM failure falls back to the template text
            warnings.warn(f"Card text from the LLM failed, using the template: {e}", stacklevel=2)
    return Response(
        decision, message=text.message, why=text.why, benefit=text.benefit, buttons=buttons
    )


class CardText(BaseModel):
    """The only thing the LLM writes: the words on one card."""

    message: str
    why: str
    benefit: str


_CARD_RULES = """You write the text of one short card in the KBC Mobile banking app (KBC is a
Belgian bank). The bank noticed a change in the customer's own payments. Write in plain English.

Rules:
- Describe only what was seen in the payments. Never guess the cause: write "your usual rent
  payment didn't go out", never "you moved" or "you lost your job".
- No product offers, no sales, no congratulations, no exclamation marks, no euro amounts.
- message: one or two short sentences. If there are answer buttons, end with a question the
  buttons answer.
- why: one sentence starting "We saw", saying which payments changed and since when.
- benefit: one short sentence on what the customer gains from answering or acting.
Keep the meaning of the example card; you may only make the wording fit this customer better."""


@cache
def _card_text(
    moment: str, evidence: str, segment: str, age_band: str, buttons: tuple[str, ...]
) -> CardText:
    """LLM wording for one card, cached on every input, so a Streamlit rerun costs nothing.
    Only the moment, computed numbers, segment and age band go in: no ID, name or payment rows.
    A failure raises and is not cached, so the next call tries again."""
    prompt = (
        f"Change noticed: {moment.replace('_', ' ')}\n"
        f"What the payments show: {evidence}\n"
        f"Customer: {segment}, age {age_band}\n"
        f"Answer buttons: {', '.join(buttons) or 'none'}\n"
        f"Example card: {_TEMPLATES[moment]} Benefit: {_BENEFITS[moment]}"
    )
    text = llm.ask_json(prompt, CardText, system=_CARD_RULES)
    if not text.message.strip() or len(text.message) > 300:
        raise llm.LLMError(f"unusable card text: {text.message!r}")
    return text


@cache
def _customers() -> dict[str, tuple[str, str]]:
    """Segment and age band per customer, read once. `respond()` gets only the detect() row."""
    rows = data.connect().execute("SELECT customer_id, segment, age FROM customers").fetchall()
    return {
        cid: (segment, f"{age // 10 * 10} to {age // 10 * 10 + 9}") for cid, segment, age in rows
    }


def _profile(customer_id: str | None) -> tuple[str, str]:
    return _customers().get(customer_id, ("customer", "unknown"))


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


# What the customer sees after answering a card (Markdown). Belgian details come only after an
# answer, and only the ones checked against sources in docs/plans/customer-value.md.
_MOVING_CHECKLIST = (
    "Thanks. A short moving checklist:\n\n"
    "- **Address:** declare your new address to your municipality within 8 working days; "
    "a late declaration can be fined.\n"
    "- **Fire insurance:** on a written Flemish lease, tenants must have fire and water "
    "damage insurance.\n"
    "- **Rent deposit:** at most 3 months' rent in Flanders (2 in Brussels and Wallonia), on a "
    "blocked account. You can open a free rent deposit account in KBC Mobile."
)
FOLLOW_UPS = {
    ("first_salary", "Finished studying, working now"): (
        "Thanks, we've updated your profile, so no more student offers. For a first job:\n\n"
        "- **Youth holidays:** under 25 and graduated this year? After a month of work you can "
        "top up to 4 weeks' holiday next year, paid at 65% by the RVA (form C103).\n"
        "- **Paid holidays:** in your first year you have few or none, because they are built "
        "on last year's work.\n"
        "- **Child benefit:** the Flemish Groeipakket stops once you work full time, so let "
        "your parents know."
    ),
    ("first_salary", "Still studying, this is a side job"): (
        "Thanks, noted. Nothing changes: you keep everything that comes with being a student."
    ),
    ("moved", "Yes, I moved"): _MOVING_CHECKLIST,
    ("moved", "No, same place"): "Thanks, noted. Nothing changes.",
    ("rent_stopped", "Moved"): (
        "Thanks. Two things after moving out:\n\n"
        "- **Address:** declare your new address to your municipality within 8 working days; "
        "a late declaration can be fined.\n"
        "- **Old rent deposit:** it is released only with the written agreement of you and "
        "your landlord, or a judge's decision."
    ),
    ("rent_stopped", "Payment problem"): (
        "Thanks for telling us. We won't show you any offers. What can help:\n\n"
        "- **Overview:** the income and spending overview in KBC Mobile shows where your "
        "money goes each month.\n"
        "- **Subscriptions:** the subscriptions overview lists what you pay regularly, so you "
        "can stop what you don't need.\n"
        '- **Talk to someone:** tap "Worried about money?" and an advisor calls you back. '
        "Nothing is shared with sales."
    ),
}
_PAYMENT_PROBLEM_NOTE = (
    "Customer reported a payment problem: hold back all offers. Do not call unless they ask."
)


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
            r = respond(row, as_of=as_of, use_llm=False)
            text = r.message or r.staff_note
            print(f"{row['customer_id']} {row['moment']:<15} {r.decision:<16} {text}")
    sept = month_end(2026, 9)
    first_salary = detect(con, sept).query("customer_id == 'C0001'").to_dict("records")[0]
    print(
        f"\nC0001's card with LLM wording ({llm.provider()}):\n", respond(first_salary, as_of=sept)
    )
    quiet = respond({"moment": "rent_stopped", "evidence": ""}, "Prefer not to say", sept)
    print(f"\nC0058 answers 'Prefer not to say' in September: quiet until {quiet.quiet_until}")
    print("\nComing up for C0001 after September:\n", coming_up(con, "C0001", sept))
