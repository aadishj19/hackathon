# Idea bank (prepared before the event)

Use this at kickoff to match the KBC challenge to an idea that is already half thought through. Every idea plays to our mix: an AI step plus real numbers from the data. "Reuses" says which part of the repo gives a head start.

| Idea | User and painful moment | What the demo shows | Reuses |
|---|---|---|---|
| Ask your data for advisors | A branch or business advisor needs a number about a client or portfolio and has to wait days for a BI report | A plain-English question becomes a table and chart in seconds, with the SQL shown for trust | `ask_data`, the app's Ask tab, `scripts/eval.py` for accuracy |
| Explain my month | A customer sees a low balance and doesn't know why | Kate-style answer in plain language: the three biggest changes versus last month, plus one concrete tip | `data.connect()` on transactions, `llm.ask` with the numbers in the prompt |
| Cash-flow early warning for small businesses | A shop owner finds out too late that rent and VAT land in the same week | A 30-day projection chart with a warning and one suggested action (for example a short-term credit line) | Transactions data, the app's chart helper |
| Complaint and email triage | A service team drowns in messages and urgent ones wait | Each message classified by topic, urgency and sentiment with a draft reply; a dashboard of volumes per topic | `llm.ask_json` with a Pydantic schema; the BI view in the app or Power BI |
| Alert explainer for fraud or anti-money-laundering analysts | An analyst gets hundreds of flagged transactions and spends minutes on each | For one alert: why it was flagged, similar past cases, a suggested next step; the analyst decides | `ask_data` for the history, `llm.ask_json` for the summary |
| Data quality copilot | A data team gets a new source and doesn't know if it can be trusted | Upload a table and get the issues (missing values, odd codes, duplicates) explained in plain language, with a SQL check for each | `data.connect()`, `data.describe_for_llm()`, `llm.ask_json`; our BI and data provisioning experience |

## Works for any idea

- **Privacy by design:** mask names and account numbers before anything reaches the LLM, and show that masking in the demo.
- **Trust:** show where an answer comes from (the SQL, the rows used) and keep a person in charge of the final action.
- **A number for the pitch:** an accuracy from `scripts/eval.py`, and a time-saved estimate from the Numbers workstream.
- **Event tech partners** (Google Cloud, ElevenLabs, Cursor, Aikido): an ElevenLabs voice reading the answer aloud is a quick extra for customer-facing ideas.
