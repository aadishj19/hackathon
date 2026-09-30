# Pitch script: demo video

Under 3 minutes, at about 150 spoken words a minute. The spoken text is about 400 words (2:40), which leaves roughly 20 seconds of slack for clicks and pauses. Every number and every screen below was checked on the app and in `scripts/eval_moments.py` on 30 September.

App: `uv run streamlit run app/streamlit_app.py`, which opens the Life moments page at http://localhost:8501.

## Before pressing record

- Restart the app, then open a fresh browser tab, so no earlier answers are remembered.
- Warm the card cache: in September, open C0001 and C0058 on the phone once, then reload the tab. The recording then never waits on the LLM.
- Browser zoom so the KBC view and the phone both fit on screen.
- Capture the screen first with no sound (Ubuntu: Ctrl+Shift+Alt+R), then record the narration over it. Two passes are much faster than one perfect take.
- Have a terminal ready with `uv run python scripts/eval_moments.py` already run, for scene 7.

## Scenes

**1. The problem (0:00 to 0:20)**
> Meet two KBC customers. In April, C0001 got their first salary, but the bank still files them as a student. That same month, C0134's salary stopped. A segment campaign keeps talking at both of them: student offers for one, the usual family sales offer for the other. Neither of them is being noticed.

On screen: the Moments page with "Today is" on **Apr**. Point at C0001 and C0134 in KBC's view.

**2. What we built (0:20 to 0:30)**
> We built an engine that notices a life change in a customer's own payments, asks before assuming, remembers the answer, and knows when to stay quiet.

On screen: the blue header band.

**3. The scan (0:30 to 0:55)**
> End of September. The engine scans all 300 customers in under a tenth of a second, with plain SQL, no AI. Nineteen get a card this month. Everyone else just sees Coming up: their own regular payments. A bank that only speaks when it matters.

On screen: click **Sep**. The metrics row (Scanned 300, scan time in milliseconds, Messages 19, Offers held 5). Scroll the phone down to Coming up.

**4. Ask before assuming (0:55 to 1:25)**
> C0001's salary replaced the transfer from home. We don't congratulate them on a job we guessed. We ask. And "why you see this" shows exactly which payments changed. They tap "Finished studying, working now". The student offers stop, and they get a short first-job checklist, like youth holidays paid by the RVA.

On screen: pick **C0001** on the phone. Open "Why you see this". Click **Finished studying, working now**; the checklist appears.

**5. The customer controls the bank (1:25 to 1:45)**
> C0058's rent stopped. That could be a new home, a breakup, or money trouble. We don't guess. They choose "Prefer not to say", and the bank goes silent on this topic until January. KBC's view shows it too.

On screen: pick **C0058**. Click **Prefer not to say**; the phone shows "We won't ask about this again before January 2027", and the Status column in KBC's view says "No contact on this until January 2027".

**6. Knowing when to stay quiet (1:45 to 2:20)**
> Back to April. C0009 and C0134 both missed a salary. In month one, a late salary and a lost job look the same. So both get quiet protection: no card, no offers, and a note for the advisor. In May, C0009's salary arrives twice, and they're back to normal. C0134 stays protected, with help one tap away. The kindest thing a bank can do here is say nothing, and stop selling.

On screen: click **Apr**. Pick **C0009**: the phone says "You're all caught up", and the orange staff note appears in KBC's view. Pick **C0134**: the same. Click **May**: C0009 is gone from the table, and C0134 is still "protect quietly".

**7. The numbers (2:20 to 2:45)**
> We compared the engine with a simple segment campaign on 300 synthetic customers, April to September. The campaign made 21 sales offers to people whose income had stopped. The engine: none. It contacted quiet customers 1,656 times. The engine: zero. And the engine asked before assuming in all 14 sensitive cases. We planted these moments ourselves, so this shows the pipeline works, not real-world accuracy.

On screen: the terminal output of `scripts/eval_moments.py` (the table with Campaign and Engine columns).

**8. Why KBC can trust it (2:45 to 2:55)**
> Rules decide, and the AI only writes the words. No customer ID or transaction ever goes into a prompt. It never changes credit decisions or prices, and it was designed with GDPR and the AI Act in mind.

On screen: back to the app, the phone on C0001's card.
