---
name: hackathon-kickoff
description: Plan the build right after KBC presents its challenge. Turns briefing notes, slide photos or a challenge PDF into a scored shortlist of ideas, one chosen demo, what to fake versus build for real, and the first task in every workstream. Use at 18:00 when the brief arrives, or whenever the team needs to re-plan.
---

# Kickoff: from KBC's brief to a plan

Leuven venue, Wednesday 30 September 2026, building from 18:00 until 23:00. Four people who share the work (see `docs/PLAYBOOK.md`); nobody owns a fixed role. Aim to finish this in about 15 minutes. A rough plan now beats a perfect plan at 19:00.

## Pass 1: understand

Summarise the brief in two lines: who KBC wants to help, and with what. Then list what is still unknown. Of the unknowns, three matter most: how the jury scores, what has to be handed in (live pitch, video, one-pager, repo link), and the exact deadline. Ask the team to get those answered by the organisers if the brief doesn't say.

Also note which data KBC provides, and whether it may be sent to an external LLM. If it may not, say so up front: it changes the whole design (masking, synthetic data, or an LLM endpoint KBC provides).

## Pass 2: choose

Collect candidate ideas from the brief and from `docs/ideas.md`. Each idea is one user, one painful moment and one task that gets completed, not a feature list. Score each from 1 to 3 on:

| Criterion | Question |
|---|---|
| Fit | Does it answer what KBC asked, in their words? |
| Evidence | Can we show it on the data we actually have tonight, and measure that it helps? |
| Buildable | Can four people finish it by 21:00 with this repo? |
| Visible outcome | Will the jury see someone's task get done better within about ten seconds? |

Fit, Evidence and Buildable come first; novelty only breaks ties. Adding a chat box or a dashboard does not make an idea stronger. If no step genuinely needs AI, recommend the useful workflow anyway.

Present the top three in a table with their scores, then recommend one and say what would make you pick the runner-up instead.

## Pass 3: scope

For the chosen idea, write:

- **Demo script:** the exact clicks and inputs, at most six steps, as a presenter would perform them.
- **Real versus faked:** the AI step and any number on screen are real. Login, integrations with KBC systems and anything outside the demo script are faked or left out.
- **Three demo cases:** an ordinary one that works, an ambiguous one, and one where going ahead would be wrong, so the prototype must stop, ask for missing information or hand over to a person. Showing the third one well is worth more than any extra feature.
- **Baseline:** how the task is done today (by hand, or with a simple rule), run on the same cases with `hack.cases` so the pitch can compare time and mistakes, with the number of cases.
- **Head start from this repo:** which of these it uses: `data.connect()` (load any tables), `ask_data.answer()` (question to SQL), `llm.ask_json()` (classify or extract into a schema), `llm.chat()` (conversation), `hack.cases` (measure against a baseline), and the Streamlit app with its KBC colours.
- **Controls that change the outcome:** what the prototype refuses, blocks or asks for (missing evidence, data the user may not see, an unsafe action), and how personal data stays out of the prompt (`data.describe_for_llm()`). A badge or a role dropdown on its own proves nothing; showing the SQL is useful for trust, but it is not governance.

## Pass 4: start

- Write the one-sentence pitch into `docs/PLAYBOOK.md`.
- Give one concrete first task per workstream in the playbook (Data, AI feature, App, Numbers, Visuals, Pitch), each small enough to finish before the 19:30 check-in. Don't assign names; the team picks.
- Don't split the work by background (one person builds a chat, the other a dashboard, glued together at the end). Everyone works on the one workflow. The data person is a natural owner of the correct definitions, the expected answers in the test cases, and the exceptions that matter.
- If a partner tool fits naturally, mention it (Google Cloud for the LLM, an ElevenLabs voice, an Aikido scan before submitting). Skip it if it adds risk to the demo.
