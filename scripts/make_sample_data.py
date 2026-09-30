"""Generate a small synthetic banking dataset so the app has something to show before the
real challenge data arrives. Deterministic: re-running gives the same files.

    uv run python scripts/make_sample_data.py
"""

import random
from datetime import date, timedelta

import pandas as pd

from hack.config import ROOT

OUT = ROOT / "data" / "sample"
rng = random.Random(42)

SEGMENTS = ["student", "young professional", "family", "senior", "small business"]
CITIES = ["Leuven", "Brussels", "Antwerp", "Ghent", "Liège", "Mechelen", "Hasselt"]
CATEGORIES = {
    "groceries": (8, 120),
    "restaurants": (12, 90),
    "travel": (40, 900),
    "utilities": (30, 250),
    "shopping": (10, 400),
    "salary": (-4500, -1800),
    "rent": (650, 1600),
    "insurance": (20, 180),
}
CHANNELS = ["card", "app transfer", "direct debit", "online banking"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    customers = [
        {
            "customer_id": f"C{i:04d}",
            "age": rng.randint(18, 85),
            "segment": rng.choice(SEGMENTS),
            "city": rng.choice(CITIES),
            "customer_since": date(2008, 1, 1) + timedelta(days=rng.randint(0, 6300)),
            "has_mobile_app": rng.random() < 0.8,
        }
        for i in range(1, 301)
    ]
    transactions = []
    start = date(2026, 1, 1)
    for n in range(1, 6001):
        cat = rng.choice(list(CATEGORIES))
        lo, hi = CATEGORIES[cat]
        transactions.append(
            {
                "transaction_id": f"T{n:05d}",
                "customer_id": rng.choice(customers)["customer_id"],
                "date": start + timedelta(days=rng.randint(0, 272)),
                "amount_eur": round(-rng.uniform(lo, hi), 2),
                "category": cat,
                "channel": "direct debit" if cat in ("rent", "utilities") else rng.choice(CHANNELS),
            }
        )
    pd.DataFrame(customers).to_csv(OUT / "customers.csv", index=False)
    pd.DataFrame(transactions).sort_values("date").to_csv(OUT / "transactions.csv", index=False)
    print(f"Wrote {len(customers)} customers and {len(transactions)} transactions to {OUT}")


if __name__ == "__main__":
    main()
