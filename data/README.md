# data/

- `sample/` is synthetic banking data (300 customers, about 29,700 transactions from January to September 2026) from `scripts/make_sample_data.py`. Each customer has a regular monthly life, and 29 customers have a planted life moment or a decoy. The correct answers are in `evals/moments_truth.csv`, kept outside `data/` so the app and the LLM never see them. KBC gave no dataset, so this is what we build and demo on.
- Put the KBC challenge files in `data/raw/` and set `DATA_DIR=data/raw` in `.env`. Everything in `data/` except `sample/` is gitignored, because challenge data may be confidential. Share it with each other over USB or chat, not through GitHub.

Supported formats: CSV, Parquet, JSON and Excel (each sheet becomes its own table).
