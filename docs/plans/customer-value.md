# Customer value: what the engine gives the customer

Companion to [life-moments-engine.md](life-moments-engine.md). The plan says what we build; this page says why a customer would be glad it exists, and what we learned when we attacked that question from five angles (30 September, around 19:30).

## The test every card must pass

> Would the customer be glad they got this, even if they bought nothing?

If not, we don't send it. In order of priority, a card should:

1. **Protect:** stop something bad happening (a fee, being uninsured, a sales pitch at a bad moment, a scam).
2. **Save hassle:** prepare an admin task for them.
3. **Save money:** including telling them what they *don't* need to buy.
4. **Only then offer a product**, and only when it clearly fits.

The value for KBC is trust, not conversion: a customer who was helped comes back at the next moment. We say that plainly in the pitch instead of hiding it.

## How we looked at it

Five reviewers worked separately, without seeing each other's answers:

| Angle | Who | Question |
|---|---|---|
| The customers | Claude agent | What does each segment actually want, and what annoys them? |
| The sceptic | Claude agent | Where is this creepy or harmful? What earns trust? |
| Belgian reality | Claude agent with web search | Which Belgian details are true, with sources? |
| The jury | Claude agent | How do we measure customer value honestly, and stand out? |
| Blank slate | GPT-6 Astra (via Codex), given only KBC's brief | What is the ideal experience, from the customer's side? |

## What they agreed on

1. **Protection is the headline, not detection.** The engine's first job is to know when *not* to sell. Every other team will show an offer; our strongest moment is an offer that doesn't appear.
2. **The customer controls the bank, visibly.** "That's not right" and "Prefer not to say" make the bank go quiet, with the date on screen ("we won't ask again until January").
3. **Describe what we saw, never the cause we guessed.** "Your usual rent payment didn't go out", never "you moved" or "you lost your job".
4. **No euro figures.** We have no balances and no ground truth for money. Invented savings would cost us credibility.

## Moments that must not produce a message

A customer who lost their job should not open the app and be reminded of it. The same holds for any moment that may be painful. The sceptic's list of what our signals can really mean:

- **Divorce or separation:** rent goes up, a large purchase, one income gone. Looks like "moved" or "income loss".
- **A death in the family:** a partner's salary stops while spending goes on.
- **Illness or maternity leave:** income drops and comes from a different sender (the health insurer instead of the employer). Looks like job loss.
- **A shared phone or joint account:** a partner reads a card about a missing salary or a trip.

So income loss gets **quiet protection**:

- All sales offers are held back. The customer simply stops seeing promos.
- No card, no reminder, no call from the bank.
- Help is there if they reach for it: a "Worried about money? Talk to someone" entry that **every customer sees, all the time**. If it only appeared for flagged customers, its appearance would itself say "we know".
- The advisor gets an internal note ("income interrupted: no offers; if they get in touch, offer help with fixed costs"). The advisor does not call; an unexpected call can feel like debt collection.
- Nothing is done to their money without asking (no automatic pausing of a savings plan).

Notifications stay discreet on the lock screen ("You have a message from KBC"), so a shared phone reveals nothing.

## Per moment: what the customer gets

| Moment | Decision | What the customer sees | What's in it for them |
|---|---|---|---|
| First salary | ask | "A first salary landed. Our records still say student. Has something changed?" [Finished studying, working now] [Still studying, this is a side job] [Prefer not to say] | After "working now": no more student offers, and a short "first job" checklist. A part-time student is not wrongly treated as graduated |
| Rent changed (moved?) | ask | "Your rent payment changed. Did you move?" [Yes, I moved] [No, same place] [Prefer not to say] | After "yes": the moving checklist below. A landlord's price rise or a new flatmate gets no insurance pitch |
| Rent stopped | ask | "Your usual rent payment didn't go out this month. Has something changed?" [Moved] [Payment problem] [Prefer not to say] | "Moved" leads to the checklist; "Payment problem" leads to budgeting help and no offers |
| Salary missing, 1 month | protect quietly | Nothing | Offers held back; harmless if the salary is just late |
| Income loss, 2+ months | protect quietly | Nothing, apart from the help entry every customer sees | No sales pitch in a hard moment; help when they choose |
| Big trip | nudge | "Big trip coming up? Check whether your card already covers cancellation before buying extra insurance." | Avoids paying twice for the same cover |
| Late salary, rent indexation (decoys) | none | Nothing | No false alarm |

"Prefer not to say" and "That's not right" mean silence on that topic for three months, and the card says so.

## Belgian details we can use (checked against sources)

Only shown **after the customer has answered**, never as the opening line. Everything else stays phrased as "check whether ...".

| Moment | Detail | Source |
|---|---|---|
| Moved | Declare your new address to the municipality within 8 working days; a late declaration can be fined | [brugge.be](https://www.brugge.be/burgerzaken/adres/adreswijziging) |
| Moved | Fire and water damage insurance is mandatory for tenants on written Flemish leases since 1 January 2019 | [schuermans-law.be](https://www.schuermans-law.be/nl/nieuws/vanaf-1-januari-2019-de-huurder-vlaanderen-verplicht-een-verzekering-tegen-het-risico-brand) |
| Moved | A rent deposit is at most 3 months' rent in Flanders (2 in Brussels and Wallonia), held on a blocked account, released only with both parties' written agreement or a judge's decision | [kbc.be](https://www.kbc.be/particulieren/nl/sparen/spaarrekeningen/huurwaarborg-hoeveel-maanden.html) |
| Moved | KBC offers a free rent deposit account (huurwaarborgrekening), opened in KBC Mobile | [kbc.be](https://www.kbc.be/particulieren/nl/sparen/spaarrekeningen/huurwaarborg.html) |
| First job | Youth holidays (jeugdvakantie): under 25 and graduated this year, worked at least a month, then next year you can top up to 4 weeks' holiday, paid at 65% by the RVA (the national employment office) with form C103 | [rva.be](https://www.rva.be/burgers/verlof/hebt-u-recht-op-de-jeugdvakantie) |
| First job | In your first year of work you have few or no paid holidays, because holiday rights are built on last year's work | [securex.be](https://www.securex.be/nl/lex4you/werkgever/nieuws/vier-weken-vakantie-dankzij-de-europese-vakantie) |
| First job | The Flemish child benefit (Groeipakket) stops once you work full time (over 80 hours a month); relevant for the parents | [myfamily.be](https://www.myfamily.be/nl-be/jobstudent/werken-als-student) |
| Big trip | KBC Gold and Platinum credit cards include trip-cancellation insurance (up to €6,000 and €10,000) when the trip is paid with a KBC payment method | [kbc.be](https://www.kbc.be/particulieren/nl/betalen/annulatieverzekering-kredietkaart.html) |
| Job loss (help page only) | Register with VDAB within 8 days after your notice period ends, then take the C4 from your employer to a union or the HVW (the public benefits office) | [vdab.be](https://www.vdab.be/orienteren/ontslag/stappenplan), [rva.be](https://www.rva.be/burgers/volledige-werkloosheid/hoe-moet-u-de-uitkeringen-aanvragen/hoe-moet-u-een-aanvraag-indienen-na-een-tewerkstelling) |
| Existing KBC features | KBC Mobile has an income and spending overview, a subscriptions overview and automatic saving orders; Kate is the free assistant in the app | [kbc.be](https://www.kbc.be/particulieren/nl/product/betalen/zelf-bankieren/met-je-smartphone/nieuw-in-mobile.html) |

Not found on kbc.be: a payment-holiday or budget-coaching product. We don't claim one.

For later, verified but not used tonight: the legal retirement age is 66 since 1 February 2025, and self-employed social contributions are due on the last day of each quarter, with quarterly VAT due on the 25th of the following month.

## Honest ways to measure it

Both sides are scored on the same synthetic customers, as of 30 September. The baseline is an **illustrative** segment campaign: every segment gets its standard offer every month.

| Measure | Campaign | Engine | Say out loud |
|---|---|---|---|
| Sales offers while income had stopped | 21 (C0134 ×6, C0027 ×5, C0251 ×4, C0091 ×3, C0152 ×3) | target 0 | "The campaign has no income check because we defined it that way. The engine's number is the point, not the gap." |
| Unwanted contacts (to the 276 customers who should hear nothing) | 276 a month, 1,656 from April to September | whatever `detect()` wrongly flags | Quote the real number even if it is not zero. An honest 40 beats a suspicious 0 |
| Right next step (29 planted plus about 10 quiet customers) | counted as right whenever the right answer was an offer | measured | "We planted these moments and wrote the detectors. This shows the pipeline works, not real-world accuracy." |
| Asked before assuming (the 14 `ask` cases) | 0 of 14 | measured | Quote the count, not a percentage; the sample is small |

What we can show in the demo: the customer's answer changes the next step; "Prefer not to say" gives silence for months; every card says why; most customers hear nothing in a given month. What we only claim, labelled as vision: retention, trust, 2.3 million customers, compliance-approved wording.

## Rules we keep in the pitch

- "It never changes credit decisions or prices." (Creditworthiness scoring is high-risk under the EU AI Act; we stay out of it.)
- "Designed with GDPR and the AI Act in mind", never "compliant".
- Inferred moments are profiling under GDPR, which is why the engine asks, lets the customer correct it, and stays quiet on request.

## Ideas we kept for later

- **Senior fraud check (stretch goal):** "€2,400 left your account by online transfer. That's unusual for you. Was that you?" [Yes, mine] [No, stop it] [Call me]. Pure protection, and it covers seniors, who have no moment tonight. It needs a small generator addition and one detector, about 30 minutes. It would replace the big trip in the video.
- **Vision slide, from Astra's blank-slate answer:** "Help me need less from you, even when that earns you less." Checking a lease before signing it, and rehearsing a family's budget before parental leave, are scenes for the vision, not for tonight.
- **New baby** (a new child benefit payment arriving): too sensitive to nudge on; at most an ask, and not tonight.
- **Moments the customer tells us, never guessed** (from the Month Ahead proposal): a baby on the way, buying a car, children going back to school, a planned move. Declared by the customer, they can shift what the bank prepares for the months ahead.
- **Small business owners:** income already varies month to month, so a single bad month is noise. A two-month gap gets the same quiet protection, with answer options that fit ("unpaid invoices", "I can't work right now") if we ever add an ask.

## What we did not take

- A pushed card for income loss, including the practical job-loss steps. Those live on the help page the customer opens themselves.
- The unprompted home insurance card after a move. The sceptic rated it the creepiest card, because it links an inference from payments to a different product.
