# Notes for AI coding assistants

Claude Code, Cursor and Codex all read this file automatically, so it is the single place for these rules.

Five-hour hackathon project (Tectonic Hackathon, KBC track, 30 Sep 2026). The goal is a working demo, not production code. Prefer the smallest change that makes the demo better.

## Layout

- `src/hack/llm.py`: the only place that talks to an LLM. Use `llm.ask`, `llm.ask_json(prompt, PydanticModel)` or `llm.chat`; never call a provider SDK directly from feature code. The provider is picked in `.env`.
- `src/hack/data.py`: loads every file in `DATA_DIR` into an in-memory DuckDB (`data.connect()`), `data.describe()` for a schema summary people read, `data.describe_for_llm()` for anything sent to an LLM (it follows `LLM_DATA_DETAIL` and by default contains no data rows), `data.export_for_powerbi()`.
- `src/hack/ask_data.py`: text-to-SQL over the loaded tables.
- `src/hack/voice.py`: ElevenLabs speech (`voice.speak`, `voice.transcribe`); check `voice.available()` first, since the key is optional.
- `docs/partners.md`: event partner tools (Google Cloud, ElevenLabs, Cursor, Aikido) and how each is wired in.
- `app/streamlit_app.py`: the demo. New features go in as a new tab or a new file under `app/pages/`.
- `src/hack/cases.py`: measure any feature on a CSV of test cases (input, expected, note) against a baseline, with accuracy and seconds per case. Costs LLM calls; run it only when asked.
- `scripts/check.py`: pre-push check (data loads, every app tab renders, LLM reachable).
- `scripts/eval.py` with `evals/ask_data_cases.csv`: accuracy of "Ask your data" against questions with known-correct SQL. Costs LLM calls; run it only when asked.
- `.claude/skills/`: skills that Claude Code and Cursor load automatically. `streamlit` (version-matched Streamlit docs), `hackathon-deliverables` (one-pager, pitch script, submission checklist).
- `docs/`: the event playbook, the plans in `docs/plans/`, and templates for the one-pager and pitch script.
- `.streamlit/config.toml`: app settings, including a KBC-coloured theme. Colours come from KBC's public website, not an official brand guideline; don't add KBC's logo without their permission.

## Rules

- Keep mock mode working: with no API key the app must still start and show data.
- Never commit challenge data, exports or secrets. Under `data/` only `data/sample/` and `data/README.md` are tracked; under `exports/` only `exports/README.md`; `.env` never. Challenge data may be confidential.
- Never put data rows in an LLM prompt. Build prompts about the data with `data.describe_for_llm()`, not `data.describe()` or raw query results, unless the team has confirmed the data may be shared.
- Before saying something works, run `uv run python scripts/check.py` and `uv run ruff check .`, and start the app with `uv run streamlit run app/streamlit_app.py`.
- Add dependencies with `uv add <package>`, never pip.
- Before Streamlit work, follow `.claude/skills/streamlit/SKILL.md`. It loads the docs that match our installed Streamlit version, so it avoids deprecated APIs.

## Working style

- Plan big features before coding. If a change is more than about 30 minutes of work, touches more than two files, or changes the demo flow, first write a short plan in the chat and wait for a yes. The plan covers: what the user will see, which files change, what is faked versus real, how we'll check it works (a command or a click path), and what is deliberately left out. Keep it under 15 lines. Small fixes and changes after the 21:00 freeze skip this.
- Read the relevant code and data before changing anything. No speculative edits to "see if it fixes it".
- When a bug shows up in one place, check the other places that use the same pattern.
- Explain unfamiliar terms in one plain sentence. Not everyone on the team is a software engineer.
- After every change, list the changed files and give one command that shows the change working, with the expected result.
- After the 21:00 feature freeze, make only the smallest fix that keeps the demo working.

## Git

- Four people push to `main`. `main` must always run, because it is what we demo.
- Don't commit or push unless the user asks. Before a commit, the checks above must pass.
- One change per commit, titled with a conventional prefix (`feat:`, `fix:`, `docs:`, `chore:`) and a plain-English description.
- Never force-push and never rewrite history on `main`.
- Stage specific files (`git add <file>`), never `git add .`, so data or `.env` can't slip in.
