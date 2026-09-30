# Life moments: a bank that notices, asks, and knows when to stay quiet

Tectonic Hackathon, KBC challenge, 30 September 2026.

KBC asked for a new way to understand, support and guide 2.3 million customers, not another feature. Our answer is an engine that reads each customer's transactions, notices when their life may be changing (a first salary, a move, rent that stops, income that stops), and then:

- **asks before assuming**: the card describes what the bank saw, never the cause it guessed ("Your usual rent payment didn't go out", not "you moved" or "you lost your job");
- **remembers the answer**: "Finished studying, working now" stops the student offers and shows a short first-job checklist; "Prefer not to say" keeps the bank quiet on that topic for three months, and the card says until when;
- **knows when to stay quiet**: when income stops, the customer gets no card and no reminder, every sales offer is held back, and the advisor gets an internal note. A "Worried about money? Talk to someone" entry is always there, for every customer, so it reveals nothing.

Every customer also gets **Coming up**: their own regular payments for the next 30 days, so the app is useful even in a month without a card.

It never changes credit decisions or prices, and it is designed with GDPR and the EU AI Act in mind.

## Run it

Needs [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh` on Mac or Linux).

```bash
git clone https://github.com/aadishj19/hackathon
cd hackathon
uv sync
uv run streamlit run app/streamlit_app.py
```

Open http://localhost:8501 and click **moments** in the sidebar. No API key is needed: without one the cards use fixed template text. To have an LLM write the card wording, copy `.env.example` to `.env` and fill in one provider (Gemini, Claude, OpenAI or Azure OpenAI).

A demo path:

1. **September**, customer **C0001**: a first salary landed while the bank still files them as a student. The card asks instead of congratulating. Click "Finished studying, working now".
2. **C0058**: rent stopped. Click "Prefer not to say": the card disappears and KBC's view shows "No contact on this until January 2027".
3. **April**, customer **C0134**: salary missing. The phone shows nothing; KBC's side shows the offers held back and the staff note. Switch to **May**: C0009, whose salary was only late, is back to normal; C0134 stays protected.

## How it works

```
transactions ─► usual month      each customer's regular payments (SQL)
             ─► detect           one SQL query per moment, on every customer, using only data up to "today"
             ─► decide           a fixed rule table + the customer's earlier answers
             ─► write            LLM writes the card text from numbers only; template if no key
             ─► show             KBC's view and the customer's phone (Streamlit)
```

Rules decide, the LLM only words the card. So the LLM can never turn "stay quiet" into a loan offer, and it never sees a customer ID, raw transactions or anything a user typed. The starter-kit "Ask your data" tab runs SQL written by an LLM, so the database's file access is switched off as soon as the data is loaded: that SQL cannot read or write files on the machine.

| Moment | What the data shows | Decision |
|---|---|---|
| First salary | a student's transfer from home is replaced by a salary | ask |
| Moved | rent up 25% or more, plus a large one-off purchase | ask |
| Rent stopped | rent stops and nothing replaces it | ask |
| Income missing (1 month) / income loss (2+ months) | salary stops while spending goes on | protect quietly |
| Big trip | travel spending far above the customer's usual | nudge (check your card's cancellation cover) |
| Late salary, yearly rent indexation | look like changes but are not | nothing |

## Results (synthetic data)

`uv run python scripts/eval_moments.py` compares the engine with an illustrative segment campaign, where every segment gets its standard offer every month, on 300 synthetic customers:

| Measure | Campaign | Engine |
|---|---|---|
| Sales offers after income stopped | 21 | 0 |
| Unwanted contacts to the 276 customers with nothing going on, April to September | 1,656 | 0 |
| Right next step (29 planted cases + 10 controls) | 5 of 39 | 39 of 39 |
| Asked before assuming (sensitive cases) | 0 of 14 | 14 of 14 |

We planted these moments and wrote the detectors, so this shows the pipeline works as designed; it does not predict accuracy on real KBC customers. Scanning all 300 customers takes well under a second.

## Honest limitations

- **All data is synthetic.** KBC gave no dataset; `scripts/make_sample_data.py` generates it, and the answers live in `evals/moments_truth.csv`, outside the data the app reads.
- **Money outside KBC is invisible.** A salary paid into another bank looks like no salary.
- **New customers have little history**, so their usual month is less certain.
- **Irregular incomes are harder.** For a freelancer, a month without income can be normal; the engine would wrongly go quiet on them.
- **No balances in the data**, so we show no euro savings and make no forecast.
- **The same signal can mean very different things** (a move, a divorce, a death), which is why the engine asks and never guesses the cause.

## Unfinished

- **No login.** The demo page lets anyone see any synthetic customer. Real use would sit behind KBC's authentication, with advisors seeing only their own customers.
- **The phone is a drawing.** Nothing is sent; answers are remembered only for the browser session, not in a per-customer "moment memory".
- **Not built tonight:** Payment watch (flag a regular bill that jumped or was charged twice, with a one-tap refund request), a consent-based "Call me back" handover to an advisor, a first-pension moment, and a balance forecast that shifts when a customer confirms a moment.

## Repo layout

| Path | What it is |
|---|---|
| `src/hack/moments.py` | The engine: `usual_month`, `coming_up`, `detect`, `respond`, the rule table |
| `app/pages/moments.py` | The demo page: KBC's view and the customer's phone |
| `scripts/eval_moments.py`, `evals/moments_cases.csv` | The evaluation above |
| `scripts/make_sample_data.py`, `data/sample/` | Synthetic customers and transactions with planted moments |
| `src/hack/llm.py` | The one place that talks to an LLM (Gemini, Claude, OpenAI or Azure OpenAI, picked in `.env`) |
| `src/hack/data.py` | Loads the CSV files into DuckDB, an in-memory SQL database |
| `app/streamlit_app.py`, `src/hack/ask_data.py`, `src/hack/voice.py` | Starter-kit tabs (explore tables, ask questions in English, chat) |
| `scripts/check.py` | Pre-push check: data loads, the app renders, the LLM answers |
| `docs/plans/` | The plan, the customer-value review and tonight's task list |
| `AGENTS.md` | Rules for the AI coding assistants we used (Claude Code, Cursor) |

## Team: git good

- Aadish Joshi - aadishj19@gmail.com
- Xiaofei Wang - annamsea2000@gmail.com
- Hung Thai Nguyen - nguyenhungthai0808@gmail.com
- Madhumitha Saravanan - madhumithasaravanann@gmail.com
