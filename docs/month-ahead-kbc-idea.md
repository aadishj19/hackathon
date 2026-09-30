~# Month Ahead: KBC Case Proposal (Draft for Review)

Tectonic Hackathon, KBC challenge

## 1. The idea in one line

On the 1st of each month, every customer gets a forecast of where their balance will end up, what could go wrong, and one-tap actions to fix it. Life moments shift the forecast months in advance, so the bank warns about next month's problem before it happens, not only this month's.

## 2. Why this fits the KBC brief

The brief asks for a scalable personalization approach that helps KBC understand, support and guide customers, not just another feature.

| Brief question | How Month Ahead answers it |
|---|---|
| What signals help us understand what customers need? | Transactions, recurring payments, annual bills, declared life moments |
| How can customers be recognized by situation, behavior and intent? | Each customer's own income and spending pattern, plus their current life moment |
| How can experiences adapt automatically? | Every customer sees a different forecast, different warnings and different actions |
| How can it work across products and channels? | Covers accounts, savings, loans and insurance bills; same forecast can feed app, advisor view and voice |
| How can it create impact for millions at once? | Lightweight statistical computation per customer, no LLM call per customer |

Judging weights: originality 30%, technical ability 30%, fit 30%, security 10% (Aikido audit).

## 3. How it feels for the customer

- **Start of month:** "You'll likely end October with about €420 (between €150 and €700). Rent, your loan and 4 subscriptions are already counted."
- **Mid-month update:** "You've spent more on groceries and eating out than usual. Your forecast dropped to €90, with a 30% chance of going negative before your salary arrives. Move €200 from savings?"
- **Looking ahead:** "Your car insurance (€640) is due in December. Setting aside €160 per month from now keeps December normal."
- **Life moment:** "You told us you're moving in November. Moving costs, a deposit and double rent for one month will lower your November balance by about €2,400. Here's a plan to prepare."

We show a **range, not a single number**. It is more honest and it makes "chance of going negative" meaningful.

(All amounts above are illustrative examples, not real figures.)

## 4. The three layers

### 4.1 Known money (recurring detection)

Detect salary, rent, loans, direct debits and subscriptions from transaction history, based on regularity in counterparty, amount and interval. Include **annual and irregular known costs**, because these cause most surprises: car insurance, yearly subscriptions, property tax, school costs in September, holidays.

### 4.2 Uncertain money (variable spending)

Model the rest (groceries, eating out, shopping) from the customer's own history, with seasonality and day-of-month patterns.

Proposed method: resample historical daily spending for the remaining days of the month many times (bootstrap / Monte Carlo) and read off the 10th, 50th and 90th percentiles of the end-of-month balance. Cheap, explainable, and gives the probability of going negative directly.

### 4.3 Life moments (the forward shift)

A life moment changes the cash profile over several months. Each gets a cost template that adjusts future forecasts.

| Life moment | Detected or entered | Effect on forecast |
|---|---|---|
| Moving house | Declared, or rent payment changes | One-off costs, deposit, possible double rent |
| New job / salary change | Salary amount or employer changes | New income baseline |
| Baby / new child | Declared only | Rising monthly costs, one-off purchases |
| Buying a car | Declared, or loan application | Down payment, insurance, fuel |
| Back to school | Calendar + children in household | September spike |
| Holiday | Declared, or travel bookings | One-off spike |
| Starting studies / leaving home | Declared, or new rent | New fixed costs |

**Design rule: sensitive moments are declared, never inferred.** Guessing a pregnancy or a divorce from transactions feels invasive and creates legal risk. We only detect neutral changes (new salary, new rent) and ask the customer to confirm: "It looks like your rent changed. Did you move?"

## 5. Actions (where time is saved)

Every warning comes with a ready action:

- Move money from savings, or back to savings when there is a surplus
- Set up a monthly set-aside for an upcoming annual bill or life moment
- Reschedule a transfer until after payday
- Review subscriptions that push the forecast down
- For bigger gaps, suggest an advisor conversation or a suitable product, with a clear explanation and no pushy selling

## 6. Refinements

- **Accuracy tracking:** compare forecast with actual balance every month. In the demo, backtest on synthetic history and report error and interval coverage (e.g. share of months where the actual balance fell inside the 80% range).
- **Customer corrections:** "This payment isn't recurring" or "My salary changes next month" updates the forecast immediately.
- **Alert discipline:** only warn when the probability of a problem is meaningful, and cap the number of alerts.
- **Explainability:** every forecast can be opened to see its parts: known income, known costs, expected spending, life moment adjustments.

## 7. Scalability

- Per customer: simple arithmetic and a small simulation, no LLM call
- Nightly batch, plus updates when new transactions arrive
- LLM (optional) only for phrasing messages; templates also work
- Demo: run on a large synthetic population, report measured throughput, extrapolate carefully to 2.3M customers. Only claim what we actually measure.

## 8. Security (10% of score, Aikido audit)

Aikido checks IDOR, authentication, authorization and business logic flaws. Relevant for us:

- Every API call checks that the customer can only access their own forecast and transactions (no ID guessing)
- Actions like "move money" must be protected against double submission and manipulation of amounts
- No secrets or API keys in the repo (also a hackathon rule)
- Build these in from the start, then run the Aikido baseline scan, fix, rescan, and screenshot before/after

## 9. Honest limitations (say these in the pitch)

- **Money outside KBC is invisible.** If salary or spending goes through another bank, the forecast will be off. Account aggregation could help later; we don't claim it.
- **Cold start:** new customers with little history get wider ranges, falling back on patterns from similar customers.
- **Irregular income** (students, freelancers) gives wide ranges. That is honest, but we should say it.
- **Life moment costs:** we don't invent real figures. Label them illustrative, or source them (e.g. Statbel household budget data, to be checked before quoting).
- **Existing KBC features:** we don't know what KBC's app already offers. Ask the KBC mentors early and focus the pitch on what is new.

## 10. Hackathon scope

### Must work end to end

1. Synthetic data generator: 3 to 5 personas, 12+ months of transactions, annual bills and at least one life moment
2. Recurring detection + bootstrap forecast with ranges
3. One declared life moment (moving) that shifts future months
4. Start-of-month screen and one mid-month warning with a one-tap action
5. Backtest numbers and a scale run

### Nice to have

- Voice summary with ElevenLabs ("Your month ahead" as a 20-second audio briefing)
- Advisor view of the same forecast
- Subscription review screen

## 11. Demo storyline (under 3 minutes)

1. Persona on 1 October: forecast range and what's in it
2. Fast-forward to mid-month: spending runs high, warning appears, one tap fixes it
3. Customer declares "moving in November": November forecast drops, set-aside plan appears
4. Proof it works: backtest accuracy and large-scale run
5. Aikido before/after screenshot

## 12. Submission checklist

- [ ] Short project description on Builderbase
- [ ] Demo video under 3 minutes
- [ ] Public GitHub repo with README (what it is, how to run it, what's unfinished)
- [ ] Aikido screenshots before and after
- [ ] Only synthetic data, no confidential data or keys in the repo

## 13. Open questions for the team

- Who owns what: data generator + forecast engine, backend/API + security, frontend + demo video?
- Which stack do we use?
- Is the voice briefing worth the time, or do we skip it?
- Anything in this plan you disagree with or want to cut?
