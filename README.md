# KBC track, Tectonic Hackathon Leuven

Team repo for the [Tectonic Hackathon](https://www.tectonicconf.eu/hackathon) preselection round, Leuven, Wednesday 30 September 2026, 18:00 to 23:00. The best 16 teams per track go to the final in Ghent on 20 October.

The KBC challenge brief is revealed at the start, so this repo is a problem-agnostic launchpad: load whatever data KBC gives us, put an LLM on top, and demo it. See [docs/PLAYBOOK.md](docs/PLAYBOOK.md) for the plan during the event.

## Setup (do this before 18:00)

1. Install [uv](https://docs.astral.sh/uv/) (it manages Python and the packages for us).
   - Linux or Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Clone and install:
   ```bash
   git clone https://github.com/aadishj19/hackathon
   cd hackathon
   uv sync
   ```
3. Copy `.env.example` to `.env` and fill in one LLM provider. With no key the app runs in mock mode, which is enough to work on data.
4. Check everything works:
   ```bash
   uv run python scripts/check.py
   uv run streamlit run app/streamlit_app.py
   ```
   The app opens at http://localhost:8501 with three tabs: Explore, Ask your data, Chat.

## What is where

| Path | What it does |
|---|---|
| `src/hack/llm.py` | One function set (`ask`, `ask_json`, `chat`) for Claude (Anthropic or Google Cloud), Gemini, OpenAI or Azure OpenAI. Switch provider in `.env`. |
| `src/hack/data.py` | Loads every CSV, Excel, Parquet or JSON file in `DATA_DIR` as a SQL table (DuckDB, an in-process SQL engine). Exports tables as CSV for Power BI. |
| `src/hack/ask_data.py` | "Ask your data": turns an English question into SQL, runs it, returns a table. |
| `src/hack/voice.py` | ElevenLabs voice: transcribe a spoken question, read an answer aloud. Optional. |
| `app/streamlit_app.py` | The demo app. Settings in `.streamlit/config.toml`: a KBC-coloured theme, reachable only from your own laptop, no usage statistics sent. |
| `scripts/check.py` | Run before every push: data loads, every app tab renders, the LLM answers. |
| `scripts/eval.py` | Accuracy of "Ask your data": runs the questions in `evals/ask_data_cases.csv` and compares against known-correct SQL. Uses LLM calls. |
| `notebooks/explore.ipynb` | Starter notebook for exploring and cleaning data in pandas or SQL. |
| `AGENTS.md`, `.claude/skills/` | Rules and skills for AI assistants (Claude Code, Cursor, Codex): Streamlit docs, kickoff plan, submission deliverables. |
| `docs/` | Event playbook, idea bank, partner tools (`docs/partners.md`), one-pager and pitch script templates. |
| `.vscode/` | Recommended extensions and format-on-save for VS Code and Cursor. |
| `data/sample/` | Synthetic bank data so everything works before the real data arrives. |
| `data/raw/` | Where the KBC data goes. Gitignored. |
| `exports/` | CSV output for Power BI. Gitignored. |

## Using the real data

1. Put the challenge files in `data/raw/`.
2. Set `DATA_DIR=data/raw` in `.env`.
3. Click "Reload data" in the app sidebar. It re-reads `.env` too, so no restart is needed.
4. Replace the sample questions in `evals/ask_data_cases.csv` with questions about the real data, then run `uv run python scripts/eval.py` for an accuracy number for the pitch.

## Power BI

In the app sidebar, click "Export all tables for Power BI", or call `data.export_for_powerbi(con)` from the notebook. In Power BI Desktop, use Get data > Folder and pick `exports/`. After a re-export, press Refresh.

## Git during the event

Two people, one `main` branch. Before editing a file, say so, so we don't both change it at once. Commit and push small and often (every 20 to 30 minutes), because small merges rarely conflict.

```bash
git pull --rebase          # get the other person's work first
git add <files you changed>
git commit -m "feat: short description"
git push
```

If `git pull --rebase` reports a conflict:

```bash
# Open each file git lists and find the blocks marked
#   <<<<<<<  (their version)  =======  (your version)  >>>>>>>
# Keep the lines you want, delete the three marker lines, save. Then:
git add <that file>
git rebase --continue

# If it gets confusing, this undoes the whole pull and puts you back where you were:
git rebase --abort
```

Trying something risky, like replacing the whole UI? Do it on a branch (`git switch -c try-new-ui`) and merge only if it works.
