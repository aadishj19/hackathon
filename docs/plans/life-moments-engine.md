# Plan: the life-moments engine

Status: proposal for the team to agree on (30 September, updated around 19:45 with the customer-value review). Where this differs from the first tasks in `docs/PLAYBOOK.md`, this plan wins.

Why a customer would want this, the five-angle review behind it, and the Belgian facts with sources are in [customer-value.md](customer-value.md).

## The idea in one paragraph

KBC wants to understand what each customer needs and respond at the right moment, for 2.3 million customers, and explicitly not as "just another feature". Our answer: an engine that notices a possible life change in a customer's transactions (a first salary, a move, income that stops), **asks before assuming**, **remembers the answer**, and **knows when to stay quiet**. Its first job is to know when *not* to sell: when someone's income stops, the bank holds back every offer and says nothing, with help available if they reach for it.

## Pitch

> For KBC customers going through a life change, we built an engine that notices it, asks before assuming, remembers the answer, and knows when to stay quiet: on 300 synthetic customers it made \<0\> offers to people whose income had stopped, where a segment campaign made 21.

The engine's number comes from the Numbers lane; quote the real one, whatever it is. Two lines we always add: "It never changes credit decisions or prices", and "designed with GDPR and the AI Act in mind" (never "compliant").

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
| First salary | 5 | ask | A student's monthly transfer from home is replaced by a salary; the customer file still says "student" |
| Moved | 5 | ask | Rent goes up 25 to 60%, plus a large one-off purchase that month |
| Rent stopped | 4 | ask | Rent stops and nothing replaces it |
| Income loss | 5 | protect quietly | Income stops for two months or more while spending goes on |
| Big trip | 5 | nudge | A travel spend far above the customer's usual |
| Late salary (decoy) | 3 | none | One month without salary, then two salaries the month after |
| Rent indexation (decoy) | 2 | none | Rent goes up 2 to 4%, the yearly inflation increase, not a move |

**To do:** the answer file still says `nudge` for first salary and moved, and `hand_to_advisor` for income loss. Change the decisions in the generator's plant table and regenerate; the transactions stay identical, so the demo customers don't change.

Honest limits: the "large purchase" is a generic shopping transaction, not labelled furniture, and there are no account balances, so we can say "income stopped" but not "financial distress".

## The four decisions

| Decision | The customer sees | Used for |
|---|---|---|
| `ask` | A card that describes what we saw (never the cause we guessed) with answer buttons, always including "Prefer not to say" | First salary, moved, rent stopped |
| `nudge` | One useful tip, with "why you see this" and "what's in it for you" | Big trip ("check whether your card already covers cancellation") |
| `protect_quietly` | Nothing. All offers are held back, the advisor gets an internal note, and the "Worried about money?" entry that every customer sees stays available | Salary missing for one month, income loss |
| `none` | Nothing | Everyone else, including the decoys |

Rules for every card:

- **Describe what we saw, never the cause we guessed:** "Your usual rent payment didn't go out", not "you moved" or "you lost your job". The same signal can mean a divorce, a death or an illness.
- **Every card says "why you see this" and "what's in it for you".**
- **"Prefer not to say" and "That's not right" mean silence on that topic for three months**, and the card says so ("we won't ask again until January").
- **Belgian details come only after the customer answers**, and only the ones verified in [customer-value.md](customer-value.md).
- **Lock-screen notifications stay discreet** ("You have a message from KBC"), because phones get shared.

## What the jury sees: one demo page

Not a chatbot (a chatbot waits for the customer to ask; the brief is about KBC noticing first) and not a dashboard (KBC already has those). One Streamlit page with two sides:

```
┌──────────────────────────────────────────────────────────────────┐
│  Today is:  [Jan | Feb | ... | Sep]   ← moves in whole months     │
├───────────────────────────────┬──────────────────────────────────┤
│  KBC's view                   │  Customer's phone                 │
│  300 customers scanned, 0.4s  │  ┌──────────────────────┐         │
│  Messages sent: 7 of 300      │  │ A first salary landed│         │
│  Offers held back: 2          │  │ Our records still say│         │
│                               │  │ student. Something   │         │
│  C0001  first salary  ask     │  │ changed?             │         │
│  C0058  rent stopped  ask     │  │ [Working now]        │         │
│  C0134  income loss   quiet   │  │ [Still studying]     │         │
│  ...                          │  │ [Prefer not to say]  │         │
│                               │  │ Why you see this: ...│         │
│                               │  └──────────────────────┘         │
│                               │  For "protect quietly": the       │
│                               │  normal app, no promos, plus the  │
│                               │  staff note on KBC's side         │
└───────────────────────────────┴──────────────────────────────────┘
```

In real life the output would appear in channels KBC already has: a card in the KBC Mobile app or a message from Kate (their in-app assistant), a note on the advisor's screen, or an email.

The customer's answer is the core of the idea, not an extra. The engine remembers it: in the demo in the app session, in the vision in a per-customer "moment memory".

## Demo video (under 3 minutes)

| Time | Beat | What is on screen |
|---|---|---|
| 0:00 to 0:25 | The problem | C0001 started their first job in April; the bank still files them as a student and keeps sending student offers. C0134's salary stopped in April; the family segment campaign still sent them its usual sales offer in May. Both are being talked at; neither is being noticed |
| 0:25 to 0:50 | The scan | Move the month to September; every customer is scanned in under a second; most hear nothing this month |
| 0:50 to 1:20 | Ask before assuming | C0001: the first-salary card asks instead of congratulating. Click "Finished studying, working now": the student offers stop and a short first-job checklist appears (youth holidays) |
| 1:20 to 1:45 | The customer controls the bank | C0058, rent stopped: click "Prefer not to say". The card disappears and KBC's view shows "no contact on this until January" |
| 1:45 to 2:20 | Knowing when to stay quiet | Month April: C0009 (late salary) and C0134 (income loss) both get quiet protection; their phones show the normal app with no promos. Month May: C0009's salary arrived and they go back to normal; C0134 stays protected. "The kindest thing a bank can do here is say nothing and stop selling." |
| 2:20 to 2:50 | The numbers | Offers while income had stopped (engine against 21), unwanted contacts, asked before assuming; all on synthetic data, said out loud |

C0001, C0058, C0009 and C0134 all start in April according to `evals/moments_truth.csv`. If the data is ever regenerated with different settings, check them again.

## Architecture

### Tonight (what we build)

```
 data/sample/*.csv  ─ data.connect() ─►  DuckDB, in memory (a small SQL database inside the app)
        │
 ① DETECT   moments.detect(con, as_of)                      SQL, no AI
        │   one query per moment, run on ALL customers, only using data up to as_of
        ▼
 ② DECIDE   rule table: moment + the customer's earlier answer → decision     no AI
        │   (a "Prefer not to say" keeps that topic quiet for three months)
        ▼
 ③ PRIVACY  the prompt gets the moment, evidence numbers, segment and age band.
        │   No customer ID, no raw transactions.
        ▼
 ④ WRITE    llm.ask_json → Gemini: card text + "why you see this"   the only AI step
        │   fixed template text if there is no API key or the LLM fails;
        │   no text at all for protect_quietly
        ▼
 ⑤ SHOW     app/pages/moments.py (Streamlit)

 Evaluation, next to it: evals/moments_truth.csv → test cases → hack.cases
                         → engine against the illustrative segment campaign
```

Why AI only does step ④:

- **Scale:** SQL on every customer is cheap; the LLM runs only for the few who get a card.
- **Safety:** the LLM never chooses the decision, so it cannot turn "protect quietly" into a loan offer.
- **Security:** the LLM only sees numbers we computed and fixed button answers, never free text a user typed, so there is nothing to hijack with prompt injection (instructions hidden in text).

### At KBC scale (one slide in the pitch, not built)

```
 Core banking: transactions every day
        ▼
 DETECT   daily, on customers with new transactions AND on customers whose
          expected payments did not arrive (a missing salary creates no transaction)
        ▼
 MOMENT MEMORY   each customer's moments, answers, and quiet periods
        ▼
 DECIDE   policy rules: responsible lending, vulnerable customers,
          at most one message a week, customer consent
        ▼
 WRITE    LLM within wording approved by compliance, in the customer's language
        ▼
 CHANNELS  KBC Mobile card or Kate · advisor screen · email
        └──► answers flow back into MOMENT MEMORY
```

Cost grows with the number of moments, not the number of customers. The Numbers lane turns this into a scenario with its assumptions written out: customers × share with a moment per month × LLM calls per moment × price per call, plus how many advisor notes per month that means.

Vision line, from the blank-slate review: *"Help me need less from you, even when that earns you less."*

## The contract between lanes

`src/hack/moments.py` is the shared contract: the function names and data shapes the lanes agree to hand each other. It is written first with placeholder answers so the App and Numbers lanes can start straight away.

- **Word lists.** Moments: `first_salary`, `moved`, `rent_stopped`, `income_missing` (one month), `income_loss` (two months or more), `big_travel`. Decisions: `ask`, `nudge`, `protect_quietly`, `none`.
- **`detect(con, as_of)`** returns one row per flagged customer with `customer_id`, `moment`, `since` (like `2026-05`) and `evidence` (a short text of numbers). `as_of` is the last day of a month.
- **`respond(row, answer=None)`** returns `decision`, `message`, `why`, `benefit` ("what's in it for you"), `buttons` (the answer options, for `ask`), `staff_note` (for `protect_quietly`) and `quiet_until` (a date, after "Prefer not to say"). The decision comes from the rule table; the text from the LLM or a template; `message` is empty for `protect_quietly`.
- The truth file is scored as of 30 September, when every income loss has at least two missing months. `income_missing` is only visible at earlier months, which is what the April/May demo beat shows.

## Lanes and timeline

| Lane | Owns these files | First result | Joined up |
|---|---|---|---|
| AI feature | `src/hack/moments.py`, the plant table in `scripts/make_sample_data.py` | 19:45: answer file updated to the four decisions; one real detector (first salary) feeding one real card | 20:15: all detectors, the rule table with answers and quiet periods, LLM text with template fallback |
| App | `app/pages/moments.py` | 19:45: the page on placeholder rows, then the first real card | 20:15: month selector, answer buttons, quiet protection view, staff note, the "Worried about money?" entry |
| Numbers | `evals/moments_cases.csv`, `scripts/eval_moments.py` | 19:45: test cases (all 29 planted plus about 10 quiet customers, including students with a negative month) and the segment-campaign baseline | 20:30: the four measures below, cost scenario written |
| Pitch and security | `README.md`, `docs/`, `src/hack/ask_data.py` (security fix only) | 19:45: deadline and live-pitch answers from the organisers, README draft, video shot list | 20:30: file-access fix done, repo public, Aikido baseline scan run |

- 21:00: feature freeze, tag the working version as `demo-ok`.
- 21:00 to 22:15: small fixes for the Aikido findings, the "after" screenshot, record the video.
- 22:15 onwards: submit, well before the deadline.

Rules for four people on one `main` branch:

- Each lane edits only its own files; ask in the chat before touching someone else's.
- `git pull --rebase` before every push, and push small, every 20 to 30 minutes.

## How we prove it

We compare the engine with an **illustrative** segment campaign (each segment gets its standard offer every month). We call it illustrative because we have no evidence of what KBC actually does today. We do not show euro figures: we have no balances and no ground truth for money.

| Measure | Campaign | Engine |
|---|---|---|
| Sales offers while income had stopped | 21 | target 0 |
| Unwanted contacts (to the 276 who should hear nothing) | 1,656 from April to September | whatever `detect()` wrongly flags; quote the real number |
| Right next step (29 planted plus about 10 quiet) | right whenever the right answer was an offer | measured |
| Asked before assuming (the 14 `ask` cases) | 0 of 14 | measured, quoted as a count |

Said out loud in the video: "We planted these moments and wrote the detectors, so this shows the pipeline works; it doesn't predict real-world accuracy." The details and caveats per measure are in [customer-value.md](customer-value.md).

## Security

- **Fix before the Aikido scan:** the existing "Ask your data" tab runs SQL written by the LLM, and a SELECT can read any file on the machine through functions like `read_csv` (see the comment in `src/hack/ask_data.py`). Hiding the tab does not help, because Aikido reads the code. Candidate fix: switch off DuckDB's file access after the data is loaded. Test it before relying on it.
- **Known and stated:** the demo page lets anyone see any customer. That is fine for an internal demo on fake data, and the README says real use would sit behind KBC's login. If Aikido flags it anyway, we fix it then.
- **Built in:** no data rows and no customer IDs in prompts, decisions made by rules, LLM output checked against a fixed schema.

## Real versus faked

- **Real:** detection, decisions, the answer memory and quiet periods within a session, the card text, and every number on screen.
- **Faked:** the phone and the staff note are drawings, nothing is actually sent, there is no login, and the checklists are short hand-written lists.

## Deliberately left out

- The big trip stays in detection, but not in the video.
- No chatbot, no Power BI, no voice.
- No pushed card for income loss, and no automatic changes to the customer's money (such as pausing a savings plan) without asking.
- No unprompted insurance card after a move.
- Stretch goals, only if we are ahead at 20:30, in this order:
  1. **Senior fraud check:** an unusual large online transfer gets "That's unusual for you. Was that you?" [Yes, mine] [No, stop it] [Call me]. It covers seniors, who have no moment tonight, and would replace the big trip in the video. About 30 minutes, including a small generator addition.
  2. **Collision:** a customer who books a big trip and loses their income in the same period, where quiet protection blocks the travel tip.

## Questions for the team

1. Who owns which lane?
2. Is the contract right (the moment names, the four decisions, the fields `respond` returns)? Changing it now is free; changing it at 20:15 breaks two lanes.
3. Do we agree that rules decide and the LLM only writes the wording?
4. Do we agree to turn the first-salary and moved nudges into questions?
5. Is the senior fraud check in (as the first stretch goal) or out?
6. English or Dutch for the customer messages? English is easier for the jury to judge.
7. Is everyone fine with making the repo public at 20:30? (Git history was checked: no keys or data files were ever committed.)

## Review history

**First review** (GPT-6 Astra, through Codex): made the customer's answer the centre of the idea; moved to an "illustrative" baseline with measures fair to both sides; a missing salary gets caution first because a late salary and lost income look the same in month one; integration moved to 19:45; found the file-reading hole in "Ask your data" and the app breaking without an API key. Not taken: cutting the month selector, dropping the big trip from detection.

**Second review** (five angles: the customers, a sceptic, a Belgian fact-check, the jury, and GPT-6 Astra with only the brief; details in [customer-value.md](customer-value.md)): protection became the headline; income loss became quiet protection instead of an advisor handover (a customer who lost their job should not be reminded of it in the app); first salary and moved became questions; every card describes what was seen, never the guessed cause; "Prefer not to say" gives visible silence; no euro figures; Belgian details only when verified and only after the customer answers.
