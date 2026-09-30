---
name: hackathon-kickoff
description: Plan the build right after KBC presents its challenge. Turns briefing notes, slide photos or a challenge PDF into a scored shortlist of ideas, one chosen demo, what to fake versus build for real, and the first task in every workstream. Use at 18:00 when the brief arrives, or whenever the team needs to re-plan.
---

# Kickoff: from KBC's brief to a plan

Leuven venue, Wednesday 30 September 2026, building from 18:00 until 23:00. Two people who share the work (see `docs/PLAYBOOK.md`); nobody owns a fixed role. Aim to finish this in about 15 minutes. A rough plan now beats a perfect plan at 19:00.

## Pass 1: understand

Summarise the brief in two lines: who KBC wants to help, and with what. Then list what is still unknown. Of the unknowns, three matter most: how the jury scores, what has to be handed in (live pitch, video, one-pager, repo link), and the exact deadline. Ask the team to get those answered by the organisers if the brief doesn't say.

Also note which data KBC provides, and whether it may be sent to an external LLM. If it may not, say so up front: it changes the whole design (masking, synthetic data, or an LLM endpoint KBC provides).

## Pass 2: choose

Collect candidate ideas from the brief and from `docs/ideas.md`, then score each one from 1 to 3 on:

| Criterion | Question |
|---|---|
| Fit | Does it answer what KBC asked, in their words? |
| Visible AI | Will the jury see the AI do something useful within about ten seconds? |
| Data | Can we show it on the data we actually have tonight? |
| Buildable | Can two people finish it by 21:00 with this repo? |

Present the top three in a table with their scores, then recommend one and say what would make you pick the runner-up instead.

## Pass 3: scope

For the chosen idea, write:

- **Demo script:** the exact clicks and inputs, at most six steps, as a presenter would perform them.
- **Real versus faked:** the AI step and any number on screen are real. Login, integrations with KBC systems and anything outside the demo script are faked or left out.
- **Head start from this repo:** which of these it uses: `data.connect()` (load any tables), `ask_data.answer()` (question to SQL), `llm.ask_json()` (classify or extract into a schema), `llm.chat()` (conversation), `scripts/eval.py` (accuracy), and the Streamlit app with its KBC colours.
- **Trust elements:** how personal data is kept out of the prompt, how the user sees where an answer came from, and where a person makes the final call. Bank juries look for all three.

## Pass 4: start

- Write the one-sentence pitch into `docs/PLAYBOOK.md`.
- Give one concrete first task per workstream in the playbook (Data, AI feature, App, Numbers, Visuals, Pitch), each small enough to finish before the 19:30 check-in. Don't assign names; the team picks.
- If a partner tool fits naturally, mention it (Google Cloud for the LLM, an ElevenLabs voice, an Aikido scan before submitting). Skip it if it adds risk to the demo.
