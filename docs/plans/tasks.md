# Tasks for tonight

What each lane builds, in which files, and by when. The why is in [life-moments-engine.md](life-moments-engine.md). Write your name next to your lane.

## Timeline

| Time | What |
|---|---|
| 20:25 | `src/hack/moments.py` pushed with the full contract and placeholder answers, so every lane can start |
| 20:25 to 21:15 | Build. Push small, every 20 to 30 minutes, `git pull --rebase` before every push |
| 21:15 | Everything joined up on `main`: the app page uses the real `detect()` and `respond()` |
| 21:30 | Feature freeze (moved from 21:00). Tag `demo-ok` |
| 21:30 to 22:15 | Aikido fixes, "after" screenshot, record the video |
| 22:15 to 22:30 | Submit on Builderbase |

This assumes the deadline is 23:00. The Pitch lane confirms it with the organisers first.

**Cut for tonight:** the freelancer showcase, senior fraud, the collision case, voice. The LLM wording only if there is time (template text is fine). The scale run and "been there" only if their lane is done early.

## Rules

- Only edit your own lane's files. Need something in another lane's file? Ask in the chat.
- `git pull --rebase` before every push. Stage files by name (`git add <file>`), never `git add .`.
- Before pushing code: `uv run ruff check .` and `uv run python scripts/check.py`.
- Your Claude or Cursor reads `AGENTS.md` automatically. Point it at this file and the plan.

## AI feature

Owner: ______

Files: `src/hack/moments.py`, the plant table in `scripts/make_sample_data.py`

1. Change the decisions in the generator's plant table: first salary and moved become `ask`, income loss becomes `protect_quietly`. Regenerate and check that only `evals/moments_truth.csv` changes.
2. `usual_month(con, as_of)`: each customer's regular payments with usual day and amount.
3. `detect(con, as_of)`: `first_salary`, `moved`, `rent_stopped`, `income_missing`, `income_loss`, `big_travel` as SQL, using only data up to `as_of`. The decoys (late salary, rent indexation) must not be flagged as September moments.
4. The rule table: moment to decision; "Prefer not to say" means quiet on that topic for three months; at most one card per customer per month.
5. `respond(row, answer=None)`: template text first. `llm.ask_json` with the template as fallback only if there is time.

Done by 21:15. Check: the command at the top of `moments.py` prints the flagged customers and one response per decision.

## App

Owner: ______

File: `app/pages/moments.py` (only that file)

1. Build on the placeholder rows in `moments.py` from 20:25. The real rows appear when the AI lane pushes.
2. A month selector from January to September.
3. Left: KBC's view, a table of flagged customers, how many were scanned, how long it took, messages sent and offers held back.
4. Right: the phone. The card with "why you see this" and "what's in it for you", the answer buttons including "Prefer not to say", answers remembered in `st.session_state`.
5. `protect_quietly`: the normal app with no card on the phone, and the staff note on KBC's side.
6. Under the card: the Coming up panel (next 30 days of regular payments) and the "Worried about money? Talk to someone" entry that every customer sees.
7. If the team agrees on GDPR opt-in: a "Life moments: on/off" toggle that makes the card disappear and marks the customer "opted out" in KBC's view.

Done by 21:15. Check: `uv run streamlit run app/streamlit_app.py`, open the Moments page, click through C0001, C0058, C0009 and C0134.

## Numbers

Owner: ______

Files: `evals/moments_cases.csv`, `scripts/eval_moments.py`

1. Test cases: all 29 customers from `evals/moments_truth.csv` plus about 10 quiet customers, including students with a negative month.
2. The baseline: every segment gets its standard offer every month.
3. The two numbers that matter most: sales offers while income had stopped (campaign: 21) and unwanted contacts (campaign: 1,656 from April to September).
4. Then: right next step, and asked before assuming (out of 14).
5. Only if done by 21:00: the scale run, timing `detect()` on about 30,000 extra fake customers with a separate random seed, written to `exports/` and never committed.

Done by 21:15. Check: `uv run python scripts/eval_moments.py` prints both sides of each measure.

## Pitch and security

Owner: ______

Files: `README.md`, `src/hack/ask_data.py` (the security fix only)

1. First: ask the organisers for the exact deadline and whether there is a live pitch. Ask the KBC mentors what KBC Mobile already offers.
2. Security fix in `ask_data.py`: turn off DuckDB's file access after the data is loaded. Test that a query using `read_csv` on a local file now fails, and that "Ask your data" still answers normal questions.
3. Make the repo public, connect it to Aikido, run the baseline AI Code Audit, take the "before" screenshot.
4. README: what it is, how to run it, what is unfinished, and the honest limitations from the plan.
5. Video script from the plan's demo table. Record from 21:30.

Done by 21:15 (the recording comes after the freeze).

## Claude (in Aadish's session)

1. 20:25: push `src/hack/moments.py` with the contract and placeholder answers.
2. Then help the AI lane with the detectors.
3. Only if the core works by about 20:50: "been there", as a separately seeded table of past home buyers plus one aggregation function.
