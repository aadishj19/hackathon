"""Generate a synthetic banking dataset with life moments planted in it, so the moments engine
has something real to find. Deterministic: re-running gives the same files.

Every customer lives a regular month from January to September 2026: income, rent, bills,
groceries, going out. Then about 30 customers get a planted change (a first salary, a move,
income that stops, ...) and a few get a decoy that looks like a change but is not one.

The correct answers go to evals/moments_truth.csv, not next to the data: every file in
DATA_DIR becomes a table, and the answers must not be visible to the app or the LLM. Customers
missing from the truth file have no moment.

    uv run python scripts/make_sample_data.py
"""

import random
from datetime import date, timedelta

import pandas as pd

from hack.config import ROOT

OUT = ROOT / "data" / "sample"
TRUTH = ROOT / "evals" / "moments_truth.csv"
rng = random.Random(42)

YEAR, MONTHS = 2026, range(1, 10)  # January to September 2026
CITIES = ["Leuven", "Brussels", "Antwerp", "Ghent", "Liège", "Mechelen", "Hasselt"]

# Per segment: (age range, income (category, low, high, day of the month it arrives), chance of
# paying rent and its range, spending compared with a young professional).
SEGMENTS = {
    "student":            ((18, 24), ("transfer", 900, 1300, 2),  (1.0, 350, 520),  0.6),
    "young professional": ((23, 35), ("salary", 2200, 3300, 25),  (0.9, 750, 1250), 1.0),
    "family":             ((30, 55), ("salary", 3200, 5500, 25),  (0.4, 900, 1600), 1.6),
    "senior":             ((65, 85), ("pension", 1400, 2600, 20), (0.2, 700, 1100), 0.9),
    "small business":     ((28, 65), ("salary", 1800, 4500, 26),  (0.5, 800, 1400), 1.2),
}  # fmt: skip

# Card spending per month for a young professional: (count low, count high, amount low, high).
SPENDING = {
    "groceries": (3, 6, 15, 110),
    "restaurants": (0, 3, 12, 70),
    "shopping": (0, 2, 15, 250),
    "travel": (0, 1, 60, 600),
}
NOT_CARD = ["app transfer", "online banking"]  # channels for the few purchases not paid by card

# (moment, eligible segments, how many, first and last month it can start, decision, note).
# The decision is what a good engine does: nudge with an offer, ask the customer first, hand
# over to a person, or do nothing.
PLANTS = [
    ("first_salary", ["student"], 5, (4, 8), "nudge",
     "first salary after studies; the customer file still says student"),
    ("moved", ["young professional", "family"], 5, (4, 8), "nudge",
     "rent up by a quarter or more, plus a furniture spend that month"),
    ("rent_stopped", ["young professional", "family", "small business"], 4, (4, 8), "ask",
     "rent stops and nothing replaces it: bought a home, moved in with someone, or behind on rent"),
    ("income_loss", ["young professional", "family", "small business"], 5, (4, 7), "hand_to_advisor",
     "income stops while spending goes on; no credit or sales offers"),
    ("big_travel", ["young professional", "family", "senior"], 5, (4, 9), "nudge",
     "a trip far above their usual travel spend"),
    ("late_salary", ["young professional", "family"], 3, (4, 8), "none",
     "decoy: one salary a month late, then two paid together"),
    ("rent_indexation", ["young professional", "family", "senior"], 2, (4, 9), "none",
     "decoy: yearly rent indexation of 2 to 4 percent, not a move"),
]  # fmt: skip


def new_customer(i: int) -> tuple[dict, dict]:
    """A customer row, plus their private life: the amounts and days of their regular month."""
    segment = rng.choice(list(SEGMENTS))
    ages, (category, lo, hi, day), (chance, rent_lo, rent_hi), spend = SEGMENTS[segment]
    customer = {
        "customer_id": f"C{i:04d}",
        "age": rng.randint(*ages),
        "segment": segment,
        "city": rng.choice(CITIES),
        "customer_since": date(2008, 1, 1) + timedelta(days=rng.randint(0, 6300)),
        "has_mobile_app": rng.random() < 0.8,
    }
    life = {
        "segment": segment,
        "income_category": category,
        "income": rng.uniform(lo, hi),
        "income_day": day + rng.randint(0, 2),
        "rent": rng.uniform(rent_lo, rent_hi) if rng.random() < chance else None,
        "rent_day": rng.randint(1, 5),
        "spend": spend * rng.uniform(0.8, 1.2),
        "utilities": rng.uniform(60, 200),
        "insurance": rng.uniform(20, 120),
        "event": None,
    }
    return customer, life


def plant(customers: list[dict], lives: dict[str, dict]) -> list[dict]:
    """Give some customers one life moment each, and return the correct answers."""
    truth, taken = [], set()
    for moment, segments, count, (first, last), decision, note in PLANTS:
        candidates = [
            c["customer_id"]
            for c in customers
            if c["segment"] in segments and c["customer_id"] not in taken
        ]
        rng.shuffle(candidates)
        for cid in candidates[:count]:
            taken.add(cid)
            life, month = lives[cid], rng.randint(first, last)
            life["event"] = (moment, month)
            if moment in ("moved", "rent_stopped", "rent_indexation") and life["rent"] is None:
                life["rent"] = rng.uniform(750, 1250)
            if moment == "first_salary":
                life["first_salary"] = rng.uniform(2100, 2800)
                next(c for c in customers if c["customer_id"] == cid)["age"] = rng.randint(21, 24)
            if moment == "moved":
                life["new_rent"] = life["rent"] * rng.uniform(1.25, 1.6)
            if moment == "rent_indexation":
                life["new_rent"] = life["rent"] * rng.uniform(1.02, 1.04)
            truth.append(
                {
                    "customer_id": cid,
                    "moment": moment,
                    "since": f"{YEAR}-{month:02d}",
                    "decision": decision,
                    "note": note,
                }
            )
    return sorted(truth, key=lambda r: r["customer_id"])


def one_month(cid: str, life: dict, month: int) -> list[dict]:
    """All transactions of one customer in one month, with the planted event applied."""
    rows = []
    moment, since = life["event"] or (None, 99)
    started = month >= since

    def add(day: int, amount: float, category: str, channel: str) -> None:
        rows.append(
            {
                "customer_id": cid,
                "date": date(YEAR, month, min(day, 28)),
                "amount_eur": round(amount, 2),
                "category": category,
                "channel": channel,
            }
        )

    # Income, positive. Small business income varies from month to month.
    income, category = life["income"], life["income_category"]
    if life["segment"] == "small business":
        income *= rng.uniform(0.65, 1.35)
    if moment == "first_salary" and started:
        income, category = life["first_salary"], "salary"
    paydays = [life["income_day"]]
    if (moment == "income_loss" and started) or (moment == "late_salary" and month == since):
        paydays = []
    if moment == "late_salary" and month == since + 1:
        paydays = [life["income_day"], life["income_day"] + 2]
    for day in paydays:
        add(day, income * rng.uniform(0.99, 1.01), category, "incoming transfer")

    # Rent and bills, negative, by direct debit.
    rent = life["rent"]
    if moment in ("moved", "rent_indexation") and started:
        rent = life["new_rent"]
    if moment == "rent_stopped" and started:
        rent = None
    if rent:
        add(life["rent_day"], -rent, "rent", "direct debit")
    utilities = life["utilities"] * rng.uniform(0.85, 1.15)
    add(rng.randint(8, 12), -utilities, "utilities", "direct debit")
    add(15, -life["insurance"], "insurance", "direct debit")

    # Everyday spending.
    for category, (n_lo, n_hi, lo, hi) in SPENDING.items():
        for _ in range(rng.randint(n_lo, n_hi)):
            channel = "card" if rng.random() < 0.85 else rng.choice(NOT_CARD)
            add(rng.randint(1, 28), -rng.uniform(lo, hi) * life["spend"], category, channel)
    if moment == "moved" and month == since:
        add(rng.randint(6, 20), -rng.uniform(800, 2500), "shopping", "card")
    if moment == "big_travel" and month == since:
        day = rng.randint(1, 20)
        add(day, -rng.uniform(600, 1400), "travel", "online banking")
        add(day + rng.randint(0, 5), -rng.uniform(900, 2200), "travel", "online banking")
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    customers, lives = [], {}
    for i in range(1, 301):
        customer, life = new_customer(i)
        customers.append(customer)
        lives[customer["customer_id"]] = life
    truth = plant(customers, lives)

    rows = [row for cid, life in lives.items() for m in MONTHS for row in one_month(cid, life, m)]
    transactions = pd.DataFrame(rows).sort_values(["date", "customer_id"], kind="stable")
    transactions.insert(0, "transaction_id", [f"T{n:05d}" for n in range(1, len(rows) + 1)])

    pd.DataFrame(customers).to_csv(OUT / "customers.csv", index=False)
    transactions.to_csv(OUT / "transactions.csv", index=False)
    pd.DataFrame(truth).to_csv(TRUTH, index=False)
    print(f"Wrote {len(customers)} customers and {len(transactions)} transactions to {OUT}")
    print(f"Wrote {len(truth)} planted moments to {TRUTH}")


if __name__ == "__main__":
    main()
