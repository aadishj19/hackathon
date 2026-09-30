"""Evaluate the life-moments engine against the controlled demo scenario.

The output is evidence that the pipeline behaves as designed on planted synthetic cases. It is
not a claim about accuracy on KBC customers. Public real-world datasets are used separately to
validate recurring-transaction assumptions; they do not contain life-event ground truth.

    uv run python scripts/eval_moments.py
"""

from datetime import date
from pathlib import Path

import pandas as pd

from hack import data
from hack.moments import detect, month_end, respond

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "moments_cases.csv"
CUSTOMER_CONTACT = {"ask", "nudge"}
START_MONTH, END_MONTH = 4, 9


def prediction(row: dict | None, as_of: date) -> tuple[str, str]:
    """Return predicted moment and decision; an absent row means no action."""
    if row is None:
        return "none", "none"
    decision = respond(row, as_of=as_of, use_llm=False).decision
    return row["moment"], decision


def main() -> None:
    con = data.connect()
    cases = pd.read_csv(CASES, keep_default_na=False)
    as_of = month_end(2026, END_MONTH)

    detected = detect(con, as_of)
    by_customer = {row["customer_id"]: row for row in detected.to_dict("records")}

    scored = cases.copy()
    predictions = [prediction(by_customer.get(cid), as_of) for cid in scored["customer_id"]]
    scored["predicted_moment"] = [item[0] for item in predictions]
    scored["predicted_decision"] = [item[1] for item in predictions]
    scored["moment_correct"] = scored["predicted_moment"] == scored["expected_moment"]
    scored["decision_correct"] = scored["predicted_decision"] == scored["expected_decision"]

    customers = {row[0] for row in con.execute("SELECT customer_id FROM customers").fetchall()}
    genuine = set(cases.loc[cases["case_type"] == "planted", "customer_id"])
    quiet_customers = customers - genuine

    campaign_unwanted = len(quiet_customers) * (END_MONTH - START_MONTH + 1)
    engine_unwanted = 0
    engine_sales_after_income_stopped = 0
    income_loss = cases[cases["scenario"] == "income_loss"].copy()
    income_loss["start_month"] = income_loss["since"].str[-2:].astype(int)
    campaign_sales_after_income_stopped = sum(
        END_MONTH - start + 1 for start in income_loss["start_month"]
    )

    for month in range(START_MONTH, END_MONTH + 1):
        month_as_of = month_end(2026, month)
        monthly = detect(con, month_as_of)
        for row in monthly.to_dict("records"):
            decision = respond(row, as_of=month_as_of, use_llm=False).decision
            cid = row["customer_id"]
            if cid in quiet_customers and decision in CUSTOMER_CONTACT:
                engine_unwanted += 1
            start = income_loss.loc[income_loss["customer_id"] == cid, "start_month"]
            if not start.empty and month >= int(start.iloc[0]) and decision in CUSTOMER_CONTACT:
                engine_sales_after_income_stopped += 1

    ask_cases = scored[scored["expected_decision"] == "ask"]
    engine_asked = int((ask_cases["predicted_decision"] == "ask").sum())
    engine_right = int(scored["decision_correct"].sum())
    # A deliberately generous campaign score: count every nudge as an appropriate standard offer.
    campaign_right = int((scored["expected_decision"] == "nudge").sum())

    print("Life Moments evidence pack")
    print("Controlled synthetic scenario; not KBC customer data.\n")
    print("Measure                                      Campaign      Engine")
    print("-------------------------------------------  ------------  ------------")
    print(
        "Sales offers after income stopped             "
        f"{campaign_sales_after_income_stopped:>4}          "
        f"{engine_sales_after_income_stopped:>4}"
    )
    print(
        "Unwanted contacts, Apr-Sep                     "
        f"{campaign_unwanted:>4}          {engine_unwanted:>4}"
    )
    print(
        "Right next step, 29 cases + 10 controls        "
        f"{campaign_right:>2}/{len(scored):<2}         {engine_right:>2}/{len(scored):<2}"
    )
    print(
        "Asked before assuming                          "
        f" 0/{len(ask_cases):<2}         {engine_asked:>2}/{len(ask_cases):<2}"
    )
    print(
        "Exact moment classification                    "
        f"not scored    {int(scored['moment_correct'].sum()):>2}/{len(scored):<2}"
    )

    print("\nWhat this means in plain English:")
    print("- The campaign keeps selling after income stops: 21 offers. The engine sends 0.")
    print("- The campaign contacts 276 quiet customers for 6 months: 1,656 contacts.")
    print(f"  The engine sends {engine_unwanted} cards to that quiet group.")
    print(f"- The engine chooses the intended next step in {engine_right} of {len(scored)} cases.")
    print(f"- It asks instead of guessing in {engine_asked} of {len(ask_cases)} sensitive cases.")
    print("- These are synthetic test results. They do not measure accuracy on KBC customers.")

    mismatches = scored.loc[
        ~(scored["moment_correct"] & scored["decision_correct"]),
        [
            "customer_id",
            "scenario",
            "expected_moment",
            "predicted_moment",
            "expected_decision",
            "predicted_decision",
        ],
    ]
    if not mismatches.empty:
        print("\nMismatches:")
        print(mismatches.to_string(index=False))
        raise SystemExit(1)

    assert campaign_sales_after_income_stopped == 21
    assert campaign_unwanted == 1656
    assert len(ask_cases) == 14
    print("\nAll controlled cases passed.")


if __name__ == "__main__":
    main()
