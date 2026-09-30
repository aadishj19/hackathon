# Plan: the life-moments engine

Status: proposal for the team to agree on (30 September, around 19:00). Where this differs from the first tasks in `docs/PLAYBOOK.md`, this plan wins, because it includes the changes from a second review (see the end).

## The idea in one paragraph

KBC wants to understand what each customer needs and respond at the right moment, for 2.3 million customers, and explicitly not as "just another feature". Our answer: an engine that notices a possible life change in a customer's transactions (a first salary, a move, income that stops), **asks before assuming**, **remembers the answer**, and picks one useful next step. Sometimes that step is holding back a sales offer and involving a human advisor instead.

## Pitch

> For KBC customers going through a life change, we built an engine that notices the change in their transactions, asks before assuming, remembers the answer, and picks one useful next step, including holding back a sales offer when income stops.

The measured result gets added once the Numbers lane has it (see "How we prove it").

## What the brief settled

- Scoring: originality 30%, technical ability ("does it work?") 30%, fit to the challenge 30%, security 10%.
- Security is scored by Aikido's AI code audit. It looks for business logic flaws, IDOR (reaching someone else's data by changing an ID), weak login and weak permission checks. We submit a screenshot before and after fixing its findings.
- Hand-in on Builderbase: a short description, a demo video under 3 minutes, a public GitHub repo with a README (what it is, how to run it, what is unfinished), and the Aikido screenshots.
- KBC gave no dataset, so we use synthetic (generated, fake) data. It is already built.

## The data (done)

- 300 fake customers and about 29,700 transactions from January to September 2026, made by `scripts/make_sample_data.py`.
- Every customer has a regular month: income, rent, bills, groceries, going out.
- 24 customers have a planted life moment and 5 have a decoy that looks like a change but is not one.
- The correct answers are in `evals/moments_truth.csv`, outside `data/`, so the app and the LLM never see them.

| Moment | Customers | Right decision | What it looks like in the data |
|---|---|---|---|
| First salary | 5 | nudge | A student's monthly transfer from home is replaced by a salary; the customer file still says "student" |
| Moved | 5 | nudge | Rent goes up 25 to 60%, plus a large one-off purchase that month |
| Rent stopped | 4 | ask | Rent stops and nothing replaces it |
| Income loss | 5 | hand to advisor | Income stops for two months or more while spending goes on |
| Big trip | 5 | nudge | A travel spend far above the customer's usual |
| Late salary (decoy) | 3 | none | One month without salary, then two salaries the month after |
| Rent indexation (decoy) | 2 | none | Rent goes up 2 to 4%, the yearly inflation increase, not a move |

Honest limits: the "large purchase" is a generic shopping transaction, not labelled furniture, and there are no account balances, so we can say "income stopped" but not "financial distress".

## What the jury sees: one demo page

Not a chatbot (a chatbot waits for the customer to ask; the brief is about KBC noticing first) and not a dashboard (KBC already has those). One Streamlit page with two sides:

```
┌──────────────────────────────────────────────────────────────────┐
│  Today is:  [Jan | Feb | ... | Sep]   ← moves in whole months     │
├───────────────────────────────┬──────────────────────────────────┤
│  KBC's view                   │  Customer's phone                 │
│  300 customers scanned, 0.4s  │  ┌──────────────────────┐         │
│                               │  │ We haven't seen your │         │
│  C0001  first salary  nudge   │  │ usual rent payment.  │         │
│  C0058  rent stopped  ask     │  │ Something changed?   │         │
│  C0134  income loss   advisor │  │ [Moved] [Delayed]    │         │
│  ...                          │  │ [Prefer not to say]  │         │
│                               │  │ Why you see this: ...│         │
│                               │  └──────────────────────┘         │
│                               │  or, for an advisor handover,     │
│                               │  the note the advisor receives    │
└───────────────────────────────┴──────────────────────────────────┘
```

In real life the output would appear in channels KBC already has: a card in the KBC Mobile app or a message from Kate (their in-app assistant), a note on the advisor's screen, or an email.

### The customer's answer changes what happens next

This is the core of the idea, not an extra. The "ask" cards have answer buttons, and the engine remembers the answer:

- Rent stopped: "Moved" leads to a relevant next step (update address, home insurance); "Payment delayed" leads to budgeting help and no offers; "Prefer not to say" means no offers and no further questions for a while.
- Income missing for one month: "Just a late payment" means nothing more happens; "I lost my job" hands over to an advisor; "Prefer not to say" means no offers.

In the demo the memory lives in the app session. In the vision it is a per-customer "moment memory".

## Demo video (under 3 minutes)

| Time | Beat | What is on screen |
|---|---|---|
| 0:00 to 0:20 | The problem | Segment campaigns treat everyone in a segment the same; customer C0001 started their first job and is still filed as a student |
| 0:20 to 0:50 | The scan | Move the month to September; every customer is scanned in under a second |
| 0:50 to 1:15 | Ordinary case | C0001, first salary: a nudge card with "why you see this" |
| 1:15 to 1:45 | Ambiguous case | C0058, rent stopped: the engine asks instead of pushing a mortgage; click an answer and the next step changes |
| 1:45 to 2:20 | Must-stop case | Move the month to April: C0009 (late salary) and C0134 (income loss) get the same cautious check-in. Move to May: C0009's salary arrived, C0134 still has none and goes to an advisor, with no offer |
| 2:20 to 2:50 | The numbers | Engine against an illustrative segment campaign on the same cases, plus the cost scenario at 2.3 million customers |

C0009 and C0134 both start in April according to `evals/moments_truth.csv`. If the data is ever regenerated with different settings, check the pair again.

## Architecture

### Tonight (what we build)

```
 data/sample/*.csv  ─ data.connect() ─►  DuckDB, in memory (a small SQL database inside the app)
        │
 ① DETECT   moments.detect(con, as_of)                      SQL, no AI
        │   one query per moment, run on ALL customers, only using data up to as_of
        ▼
 ② DECIDE   rule table: moment (+ the customer's answer) → decision        no AI
        ▼
 ③ PRIVACY  the prompt gets the moment, evidence numbers, segment and age band.
        │   No customer ID, no raw transactions.
        ▼
 ④ WRITE    llm.ask_json → Gemini: the message + "why you see this"   the only AI step
        │   fixed template text if there is no API key or the LLM fails
        ▼
 ⑤ SHOW     app/pages/moments.py (Streamlit)

 Evaluation, next to it: evals/moments_truth.csv → test cases → hack.cases
                         → engine against the illustrative segment campaign
```

Why AI only does step ④:

- **Scale:** SQL on every customer is cheap; the LLM runs only for the few who are flagged.
- **Safety:** the LLM never chooses the decision, so it cannot turn "hand to advisor" into a loan offer.
- **Security:** the LLM only sees numbers we computed and fixed button answers, never free text a user typed, so there is nothing to hijack with prompt injection (instructions hidden in text).

### At KBC scale (one slide in the pitch, not built)

```
 Core banking: transactions every day
        ▼
 DETECT   daily, on customers with new transactions AND on customers whose
          expected payments did not arrive (a missing salary creates no transaction)
        ▼
 MOMENT MEMORY   each customer's moments and their answers
        ▼
 DECIDE   policy rules: responsible lending, vulnerable customers,
          at most one message a week, customer consent
        ▼
 WRITE    LLM within wording approved by compliance, in the customer's language
        ▼
 CHANNELS  KBC Mobile card or Kate · advisor screen · email
        └──► answers flow back into MOMENT MEMORY
```

Cost grows with the number of moments, not the number of customers. The Numbers lane turns this into a scenario with its assumptions written out: customers × share with a moment per month × LLM calls per moment × price per call, plus how many advisor handovers per month that means.

## The contract between lanes

`src/hack/moments.py` is the shared contract: the function names and data shapes the lanes agree to hand each other. It is written first with placeholder answers so the App and Numbers lanes can start straight away.

- **Word lists.** Moments: `first_salary`, `moved`, `rent_stopped`, `income_missing` (one month), `income_loss` (two months or more), `big_travel`. Decisions: `nudge`, `ask`, `hand_to_advisor`, `none`.
- **`detect(con, as_of)`** returns one row per flagged customer with `customer_id`, `moment`, `since` (like `2026-05`) and `evidence` (a short text of numbers). `as_of` is the last day of a month.
- **`respond(row, answer=None)`** returns `decision`, `message` and `why`. The decision comes from the rule table, using the customer's answer if there is one. The text comes from the LLM, or from a template when there is no LLM.
- The truth file is scored as of 30 September, when every income loss has at least two missing months. `income_missing` is only visible at earlier months, which is what the April/May demo beat shows.

## Lanes and timeline

| Lane | Owns these files | First result | Joined up |
|---|---|---|---|
| AI feature | `src/hack/moments.py` | 19:45: one real detector (first salary) feeding one real card | 20:15: all detectors, the rule table, LLM text with template fallback |
| App | `app/pages/moments.py` | 19:45: the page on placeholder rows, then the first real card | 20:15: month selector, answer buttons, advisor note |
| Numbers | `evals/moments_cases.csv`, `scripts/eval_moments.py` | 19:45: test cases (all 29 planted plus about 10 quiet customers, including students with a negative month) and the segment-campaign baseline | 20:30: both runs compared, cost scenario written |
| Pitch and security | `README.md`, `docs/`, `src/hack/ask_data.py` (security fix only) | 19:45: deadline and live-pitch answers from the organisers, README draft, video shot list | 20:30: file-access fix done, repo public, Aikido baseline scan run |

- 21:00: feature freeze, tag the working version as `demo-ok`.
- 21:00 to 22:15: small fixes for the Aikido findings, the "after" screenshot, record the video.
- 22:15 onwards: submit, well before the deadline.

Rules for four people on one `main` branch:

- Each lane edits only its own files; ask in the chat before touching someone else's.
- `git pull --rebase` before every push, and push small, every 20 to 30 minutes.

## How we prove it

We compare the engine with an **illustrative** segment campaign (each segment gets its standard offer every month). We call it illustrative because we have no evidence of what KBC actually does today. Detecting moments is not something a campaign does, so we compare on things both can be judged on:

- **Appropriate next step:** the decision matches the answer file (quiet customers should get `none`).
- **Unwanted contacts:** a message sent to someone who should get `none`.
- **Sales offers while income has stopped:** the number that matters most.
- **Detection delay**, for the engine only: months between the change and the first reaction.

All results are on synthetic data, and the pitch says so.

## Security

- **Fix before the Aikido scan:** the existing "Ask your data" tab runs SQL written by the LLM, and a SELECT can read any file on the machine through functions like `read_csv` (see the comment in `src/hack/ask_data.py`). Hiding the tab does not help, because Aikido reads the code. Candidate fix: switch off DuckDB's file access after the data is loaded. Test it before relying on it.
- **Known and stated:** the demo page lets anyone see any customer. That is fine for an internal demo on fake data, and the README says real use would sit behind KBC's login. If Aikido flags it anyway, we fix it then.
- **Built in:** no data rows and no customer IDs in prompts, decisions made by rules, LLM output checked against a fixed schema.

## Real versus faked

- **Real:** detection, decisions, the answer memory within a session, the message text, and every number on screen.
- **Faked:** the phone and the advisor note are drawings, nothing is actually sent, there is no login, and the product offers are a short hand-written list.

## Deliberately left out

- The big trip moment stays in detection but not in the video.
- No chatbot, no Power BI, no voice.
- Stretch goal, only if we are ahead at 20:30: a "collision" customer who books a big trip and loses their income in the same period, where the income rule blocks the travel offer.

## Questions for the team

1. Who owns which lane?
2. Is the contract right (the moment names, the four decisions, the columns)? Changing it now is free; changing it at 20:15 breaks two lanes.
3. Do we agree that rules decide and the LLM only writes the wording?
4. Is the app a separate page (recommended, so nobody shares a file) or a tab in the main app?
5. English or Dutch for the customer messages? English is easier for the jury to judge.
6. Is everyone fine with making the repo public at 20:30? (Git history was checked: no keys or data files were ever committed.)

## What changed after the second review

We asked a second model (GPT-6 Astra, through Codex) to find the weak spots. What we took from it:

- The customer's answer, and the engine remembering it, moved from a stretch goal to the centre of the idea and the pitch.
- The comparison is now against an "illustrative" campaign and uses measures that are fair to both sides.
- A missing salary first gets a cautious question and only goes to an advisor after a second missing month, because in the first month a late salary and lost income look the same.
- Integration moved earlier, to 19:45, instead of waiting until 20:30.
- The file-reading hole in "Ask your data" and the app breaking without an API key were found and added to the plan.

What we did not take: cutting the month selector (it shows "the right moment" best) and dropping the big trip moment from detection (it costs one query).
