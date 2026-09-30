# Evaluation Data: What It Is and Why We Trust It

## Why synthetic data?

KBC did not provide customer data, and personal banking histories are private. We therefore built a controlled synthetic dataset: no row belongs to a real person, but the transaction structure follows patterns seen in public banking data.

We used these public sources as reference points:

- [PKDD'99 Financial](https://relational.fel.cvut.cz/dataset/Financial): real anonymised European accounts, transactions and standing orders.
- [MoneyData](https://data.mendeley.com/datasets/dnxtg6n4rv/1): more than 6,500 real anonymised retail-bank transactions across seven years.
- [Belgian Household Budget Survey](https://data.gov.be/en/datasets/67b8a34d4c6981a19f4cad0e779df597e8981c95): official Belgian household expenditure categories.

These sources informed the kinds of patterns and spending categories in the demo. The individual euro amounts are plausible fictional ranges, not estimates of KBC customers.

## What we generated

- 300 fictional customers and approximately 29,700 transactions.
- Nine months of recurring income, rent, utilities, insurance and everyday spending.
- 24 deliberately planted life-moment patterns.
- Five realistic decoys: late salaries and small rent indexation.
- Ten extra quiet controls: students with a negative-net month but no life event.

Because the cases are planted, we know the correct response in advance: ask, give a useful nudge, protect quietly, or do nothing.

## Measured results

| Controlled synthetic test | Segment campaign | Life Moments Engine |
|---|---:|---:|
| Sales offers after income stopped | 21 | **0** |
| Unwanted contacts, April–September | 1,656 | **0** |
| Right next step | 5/39 | **39/39** |
| Asked before assuming | 0/14 | **14/14** |

Run the evaluation with:

```bash
uv run python scripts/eval_moments.py
```

## How to interpret this

These results show that the prototype pipeline works on the situations we designed and that the rules handle the decoys correctly. They do **not** claim 100% accuracy on real KBC customers.

The honest description is:

> Public-data-informed, fully synthetic, controlled and reproducible.

The engine detects observable payment changes. It never treats a missing salary or changed rent as proof of job loss, moving, divorce or another personal event. It asks when confirmation is appropriate and stays quiet when contact could be harmful.

