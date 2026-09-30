# Event playbook

Five hours goes fast. The teams that do well pick one narrow problem, show it working on real data, and tell a clear story about who it helps and how much.

## Before 18:00

- [ ] Both laptops: `uv sync`, `uv run python scripts/check.py`, the app opens.
- [ ] One working LLM key in `.env`, tested. Bring a second provider's key as backup if possible.
- [ ] Partner tools set up per `docs/partners.md`: a Google Cloud or Gemini key, an ElevenLabs key, Cursor installed, Aikido connected to the repo.
- [ ] Power BI Desktop installed and opens a CSV from `exports/`.
- [ ] Phone hotspot ready in case the venue Wi-Fi is slow.
- [ ] Team size: the rules say 3 to 4 people. Confirm with the organisers that two is fine, or find a third on site.
- [ ] Check the participant emails for what must be handed in. Teams elsewhere expect a short recorded video and a one-page summary alongside the repo, but nothing official confirms that for Leuven, so be ready for a live pitch as well as a video.
- [ ] Screen recording tested on the presenting laptop (Ubuntu: Ctrl+Shift+Alt+R; Windows: Win+Alt+R).
- [ ] Skim `docs/ideas.md` so the kickoff starts from ideas already thought through.

## Questions to ask KBC in the first 30 minutes

- Who is the end user: a customer, an advisor in a branch, back office, compliance?
- What does success look like for them, and how is it measured today?
- What data can we use, and can it leave our laptops? (If not, the LLM call itself is a problem. Ask whether they provide an Azure OpenAI endpoint.)
- What are the judging criteria and exactly what do we submit (demo, slides, video, repo link)? What is the deadline?
- Is there an existing KBC product this should plug into, such as the Kate assistant in KBC Mobile?

## Timeline

| Time | Goal by the end of this block |
|---|---|
| 18:00 to 18:30 | Brief read together. One user and one problem picked. One-sentence pitch written below. |
| 18:30 to 19:00 | Real data loaded and understood. A first rough version of the AI feature runs, even on sample data. |
| 19:00 to 21:00 | The feature works on real data. The numbers for the pitch exist. |
| 21:00 | **Feature freeze.** From here, fix only what breaks the demo. Tag the working version (see Demo safety). |
| 21:00 to 22:15 | Demo path rehearsed, backup video recorded, one-pager and pitch script done. |
| 22:15 to 22:40 | Pitch rehearsed twice with a timer (or the video recorded), then submitted, well before 23:00. |

## Who does what

Roles aren't fixed. These are the workstreams; either of us can pick up any of them and swap when needed.

- **Data:** understand the tables and joins, clean them in the notebook, note data quality issues.
- **AI feature:** prompts, `src/hack/`, the logic that makes the demo useful.
- **App:** the Streamlit screens the judges will see.
- **Numbers:** the business case (volume, time saved, euros) and a set of 15 to 20 test cases with known correct answers, including ambiguous ones and ones where the right outcome is to stop. Run them with `hack.cases` against today's way of doing the task, to report accuracy and time for both. ("Ask your data" has its own version: `evals/ask_data_cases.csv` plus `scripts/eval.py`.)
- **Visuals:** charts in the app or a Power BI dashboard, only if the challenge calls for one.
- **Pitch:** slides, story, demo script, timekeeping.

How we split and swap:

- **Check in at 18:30, 19:30, 20:30 and 21:00.** Two minutes: what's done, what's stuck, who takes what next. Re-split whenever one side is blocked or the plan changes.
- **Say which files you're about to edit.** If the other person is in the same file, either pair on it or wait for their push.
- **Commit and push before handing over a task**, so the other person starts from the latest version.

## Our one-sentence pitch

> For **\<user\>** who struggles with **\<problem\>**, we built **\<solution\>**, which **\<measurable result\>**.

## Using the AI assistant during the event

Claude Code and Cursor load the skills in `.claude/skills/` automatically. Ask for them by name:

| When | Ask |
|---|---|
| 18:00, brief in hand | "Run hackathon-kickoff on this brief: ..." (paste text, attach slide photos or the PDF) |
| Any app change | The streamlit skill loads by itself; no need to ask. |
| 21:00 freeze | "Run hackathon-deliverables." It drafts the one-pager and pitch from what is built, then walks the hand-in checks. |

## Pitch

Structure, timings and shot list are in `docs/pitch-script-template.md`; the one-page overview is `docs/one-pager-template.md`. We don't know the judging criteria yet, so ask KBC at kickoff what they will score. Our working guess, to check against their answer: they care about a measured improvement for one real user, personal data staying protected, and a person staying in control of consequential decisions.

## Demo safety

- Streamlit keeps state while it runs. Click "Reload data" in the sidebar before presenting to start clean.
- Tag every version where the demo works end to end, and always at the 21:00 freeze. If `main` breaks right before the pitch, demo from the tag:
  ```bash
  git tag -f demo-ok && git push -f origin demo-ok   # -f only moves the tag, never main
  git checkout demo-ok                               # demo from the last good state
  git checkout main                                  # back to normal afterwards
  ```
- Keep the backup video on the laptop desktop.
- If the LLM is slow on stage, set `ANTHROPIC_EFFORT=low` in `.env` and click "Reload data".
- Solutions may be used by KBC and SD Worx (per the event rules), so don't build on anything you can't share.
