# data/

- `sample/` is synthetic banking data (300 customers, 6,000 transactions) from `scripts/make_sample_data.py`. It is committed so the app works before the real data arrives.
- Put the KBC challenge files in `data/raw/` and set `DATA_DIR=data/raw` in `.env`. Everything in `data/` except `sample/` is gitignored, because challenge data may be confidential. Share it with each other over USB or chat, not through GitHub.

Supported formats: CSV, Parquet, JSON and Excel (each sheet becomes its own table).
