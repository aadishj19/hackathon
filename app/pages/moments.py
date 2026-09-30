"""Life moments: KBC's view on the left, the customer's phone on the right.

Everything on this page comes from src/hack/moments.py (detect, respond, coming_up), so it
shows the real engine as soon as the AI lane replaces the placeholders there. The phone is a
drawing: nothing is sent to anyone. Answers are remembered for this browser session only.
"""

import html
import time
from datetime import date, timedelta
from functools import partial
from urllib.parse import quote

import pandas as pd
import streamlit as st

from hack import data, moments

st.set_page_config(page_title="Life moments", layout="wide")
MONTHS = list(range(1, moments.TODAY.month + 1))
# One card per customer per month: when a customer has two moments, the safest one wins, so
# a customer under quiet protection never gets a card about something else.
PRIORITY = {"protect_quietly": 0, "ask": 1, "nudge": 2, "none": 3}
DECISION_COLOURS = {  # background and text colour per decision in KBC's view (from the theme)
    "ask": ("#E0F2FC", "#007AB1"),
    "nudge": ("#E6F4EA", "#3F7A0E"),
    "protect quietly": ("#FDF0E1", "#A55800"),
    "none": ("#F0F2F5", "#5B6B80"),
}
# Custom CSS only for what the theme can't do: the header band, the phone frame and the cards.
# The colours are the ones in .streamlit/config.toml. The "KBC" is plain text, not a logo.
STYLE = """
<style>
.lm-hero {background: linear-gradient(115deg, #0D2A50 0%, #0D2A50 45%, #007AB1 100%);
  color: #fff; border-radius: 18px; padding: 22px 28px; display: flex;
  justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;}
.lm-hero .brand {font-size: 1.75rem; font-weight: 700; line-height: 1.2;}
.lm-hero .brand b {color: #74C8ED;}
.lm-hero .sub {opacity: .85; margin-top: 4px;}
.lm-pill {border: 1px solid rgba(255,255,255,.4); background: rgba(255,255,255,.12);
  border-radius: 999px; padding: 5px 14px; font-size: .85rem; white-space: nowrap;}
.st-key-staffnote {background: #FFF8EE; border-left: 5px solid #DC7507; border-radius: 14px;
  padding: 14px 16px;}
/* The phone: a fixed-size dark frame modelled on KBC Mobile's dark mode. The screen in the
   middle scrolls, so the phone never changes size whatever the message says. */
.st-key-phone {background: #111418; border: 11px solid #050607; outline: 2px solid #2B3038;
  border-radius: 52px; padding: 8px 12px 10px; gap: 10px;
  box-shadow: 0 24px 50px rgba(13,42,80,.35);}
.st-key-screen {gap: 12px; scrollbar-width: none;}
.st-key-screen::-webkit-scrollbar {display: none;}
.lm-status {display: flex; justify-content: space-between; align-items: center;
  color: #fff; font-weight: 600; font-size: .95rem; padding: 4px 14px 0;}
.lm-island {background: #000; width: 110px; height: 30px; border-radius: 20px;}
.lm-signal {display: flex; gap: 6px; align-items: center; font-size: .8rem;}
.lm-battery {border: 1.5px solid #C9CED6; border-radius: 5px; padding: 0 4px; font-size: .7rem;}
.lm-top {display: flex; gap: 8px; align-items: center; margin-top: 12px;}
.lm-round {width: 40px; height: 40px; border-radius: 50%; background: #1E2228; flex: none;
  display: flex; align-items: center; justify-content: center; border: 1px solid #2B3038;}
.lm-search {flex: 1; height: 40px; border-radius: 20px; background: #1E2228;
  border: 1px solid #2B3038; display: flex; align-items: center; gap: 8px; padding: 0 12px;
  color: #C9CED6; font-size: .85rem;}
.lm-search .kate {margin-left: auto; color: #fff; font-weight: 700;}
.lm-dot {width: 14px; height: 14px; border-radius: 50%; display: inline-block; flex: none;
  background: radial-gradient(circle at 35% 35%, #BFE6FA, #3FA9F5 70%);}
.lm-accounts {display: flex; gap: 10px; overflow: hidden; margin-top: 4px;}
.lm-acc {flex: none; width: 138px; border-radius: 12px; overflow: hidden; background: #1E2228;}
.lm-acc .art {height: 52px; display: flex; align-items: center; justify-content: center;}
.lm-acc .blue {background: linear-gradient(135deg, #8FD3F7, #3FA9F5);}
.lm-acc .grey {background: #5B8DA8;}
.lm-acc .who {color: #C9CED6; font-size: .7rem; padding: 8px 10px 0; letter-spacing: .3px;}
.lm-acc .bal {color: #fff; font-weight: 700; font-size: 1rem; padding: 2px 10px 10px;}
.lm-pay {display: flex; gap: 10px; color: #E9EDF2; font-size: .85rem; padding: 5px 2px;}
.lm-pay .d {color: #9AA3AE; width: 38px; flex: none;}
.lm-pay .t {flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.lm-pay .a {white-space: nowrap;}
.lm-pay .a small {font-size: .7rem;}
.lm-pay .in {color: #7FD67F;}
.lm-link {color: #4FB3F0; font-size: .82rem; font-weight: 600;}
.lm-head {display: flex; justify-content: space-between; align-items: baseline;
  color: #fff; font-size: 1.1rem; margin-top: 6px;}
.lm-head .lm-link {font-size: .8rem;}
.lm-kate {display: flex; align-items: center; gap: 6px; color: #fff; font-weight: 600;
  font-size: .88rem;}
.st-key-card {background: #1E2228; border-radius: 14px; padding: 14px; gap: 8px;}
.lm-quiet {background: #1E2228; border-radius: 14px; padding: 16px; color: #9AA3AE;
  font-size: .88rem; display: flex; gap: 10px; align-items: center;}
.lm-list {background: #1E2228; border-radius: 14px; padding: 4px 12px;}
.lm-list .lm-pay {border-bottom: 1px solid #2B3038; padding: 8px 0;}
.lm-list .lm-pay:last-child {border-bottom: none;}
.lm-nav {display: flex; justify-content: space-between; background: #1E2228;
  border: 1px solid #2B3038; border-radius: 30px; padding: 5px;}
.lm-nav div {flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px;
  color: #E9EDF2; font-size: .66rem; padding: 6px 0; border-radius: 24px;}
.lm-nav .on {background: #2E343C;}
.lm-home {width: 120px; height: 4px; border-radius: 3px; background: #E9EDF2;
  margin: 2px auto 0;}
/* Streamlit's own widgets inside the phone, recoloured for the dark screen */
.st-key-phone [data-testid="stMarkdownContainer"] p {color: #E9EDF2;}
.st-key-phone [data-testid="stCaptionContainer"],
.st-key-phone [data-testid="stCaptionContainer"] p {color: #9AA3AE;}
.st-key-phone [data-testid="stExpander"] details {background: #262B33; border-color: #343A44;}
.st-key-phone [data-testid="stExpander"] summary,
.st-key-phone [data-testid="stExpander"] summary p,
.st-key-phone [data-testid="stExpander"] summary span {color: #E9EDF2;}
.st-key-phone [data-testid="stBaseButton-tertiary"],
.st-key-phone [data-testid="stBaseButton-tertiary"] p {color: #4FB3F0;}
.st-key-phone [data-testid="stBaseButton-primary"] {background: #1E8FD6;
  border-color: #1E8FD6;}
</style>
"""
# Simple line icons (24x24), drawn in the phone's text colour
_PATHS = {
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3'
    'M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "bell": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "wallet": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 13h2M3 9h15V6"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11M4 6h1M4 12h1M4 18h1"/>',
    "piggy": '<ellipse cx="12" cy="13" rx="7" ry="5"/><path d="M8 17v3M16 17v3M19 12h2M10 8h4"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
}


def icon(name: str, size: int = 20, colour: str = "#E9EDF2") -> str:
    """An <img> with the SVG inside it: st.html strips inline <svg> tags, but keeps images."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{colour}" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round">{_PATHS[name]}</svg>'
    )
    return f'<img width="{size}" height="{size}" src="data:image/svg+xml,{quote(svg)}">'


def eur(amount: float) -> str:
    """Belgian style, as in the app: -1 234,56 EUR with the cents smaller."""
    whole, cents = f"{abs(amount):,.2f}".split(".")
    sign = "+" if amount > 0 else "-"
    return f"{sign}{whole.replace(',', '&#8239;')}<small>,{cents} EUR</small>"


def payment_rows(items) -> str:
    return "".join(
        f'<div class="lm-pay"><span class="d">{d:%d/%m}</span>'
        f'<span class="t">{html.escape(what)}</span>'
        f'<span class="a{" in" if amount > 0 else ""}">{eur(amount)}</span></div>'
        for d, what, amount in items
    )


PHONE_TOP = f"""<div class="lm-status"><span>9:41</span><span class="lm-island"></span>
<span class="lm-signal">5G <span class="lm-battery">80</span></span></div>
<div class="lm-top"><span class="lm-round">{icon("gear")}</span>
<span class="lm-search">{icon("search", 18, "#C9CED6")} How can I help you?
<span class="kate"><span class="lm-dot"></span> Kate</span></span>
<span class="lm-round">{icon("bell")}</span></div>"""

PHONE_NAV = f"""<div class="lm-nav">
<div class="on">{icon("wallet")}Start</div><div>{icon("list")}My KBC</div>
<div>{icon("piggy")}Investments</div><div>{icon("layers")}Offer</div></div>
<div class="lm-home"></div>"""


@st.cache_resource
def get_con():
    return data.connect()


# Same pattern as the main app: one cursor per browser tab, since a DuckDB connection isn't
# safe to share between threads.
if st.session_state.get("moments_con_source") is not get_con():
    st.session_state["moments_con_source"] = get_con()
    st.session_state["moments_con"] = get_con().cursor()
con = st.session_state["moments_con"]
# (customer_id, moment) -> {"answer": the button pressed, "as_of": the month it was pressed}
answers = st.session_state.setdefault("moment_answers", {})


@st.cache_data(max_entries=24)
def scan(_con, as_of: date) -> tuple[pd.DataFrame, float, int]:
    """Run detect() on every customer once per month shown; returns rows, seconds, customers."""
    start = time.perf_counter()
    rows = moments.detect(_con, as_of)
    seconds = time.perf_counter() - start
    customers = _con.execute("SELECT count(*) FROM customers").fetchone()[0]
    return rows, seconds, customers


@st.cache_data(max_entries=1000)
def respond(row: tuple, answer: str | None, as_of: date, use_llm: bool = False) -> moments.Response:
    """Cached, so a click elsewhere on the page never asks the LLM for the same card twice.
    Template text by default: KBC's view only needs the decision, and asking the LLM for every
    flagged customer made the first load of a month take about a minute."""
    return moments.respond(dict(row), answer, as_of, use_llm=use_llm)


def response_for(row: dict, as_of: date) -> tuple[moments.Response, str | None]:
    """The customer's response this month, taking an earlier answer into account."""
    given = answers.get((row["customer_id"], row["moment"]))
    if given and given["as_of"] <= as_of:
        r = respond(tuple(row.items()), given["answer"], given["as_of"])
        if r.quiet_until is None or r.quiet_until >= as_of:
            return r, given["answer"]
    return respond(tuple(row.items()), None, as_of), None


def status(r: moments.Response, answer: str | None) -> str:
    if r.quiet_until:
        return f"No contact on this until {r.quiet_until + timedelta(days=1):%B %Y}"
    if r.decision == "protect_quietly":
        return "Offers held back, no card"
    if answer:
        return f"Answered: {answer}"
    return "Card shown" if r.decision in ("ask", "nudge") else "Nothing"


def remember(customer_id: str, moment: str, answer: str | None, as_of: date) -> None:
    if answer is None:
        answers.pop((customer_id, moment), None)
    else:
        answers[(customer_id, moment)] = {"answer": answer, "as_of": as_of}


def pick_customer(table_key: str, ids: list[str]) -> None:
    rows = st.session_state[table_key].selection.rows
    if rows and rows[0] < len(ids):
        st.session_state["phone_customer"] = ids[rows[0]]


st.html(STYLE)
st.html(
    """<div class="lm-hero"><div>
      <div class="brand"><b>KBC</b> &middot; Life moments</div>
      <div class="sub">Notice a change, ask before assuming, remember the answer,
      know when to stay quiet.</div></div>
      <span class="lm-pill">Demo &middot; synthetic data</span></div>"""
)
month = st.segmented_control(
    "Today is",
    MONTHS,
    default=moments.TODAY.month,
    required=True,
    format_func=lambda m: date(2026, m, 1).strftime("%b"),
    key="moment_month",
)
as_of = moments.month_end(moments.TODAY.year, month)
st.caption(f"The engine looks only at transactions up to {as_of:%d %B %Y}.")

rows, seconds, n_customers = scan(con, as_of)
flagged = []
for row in rows.to_dict("records"):
    r, answer = response_for(row, as_of)
    flagged.append({**row, "response": r, "answer": answer})
# One line per customer: the highest-priority moment of the month
flagged.sort(key=lambda f: (f["customer_id"], PRIORITY.get(f["response"].decision, 9)))
per_customer = {}
for f in flagged:
    per_customer.setdefault(f["customer_id"], f)
shown = list(per_customer.values())

kbc, phone = st.columns([1.6, 1], gap="large")

with kbc:
    st.subheader(":material/insights: KBC's view")
    cards = sum(
        f["response"].decision in ("ask", "nudge") and not f["response"].quiet_until for f in shown
    )
    held = sum(f["response"].decision == "protect_quietly" for f in shown)
    stats = [
        ("Scanned", f"{n_customers:,}", ":material/groups:"),
        ("Scan time", f"{seconds * 1000:,.0f} ms", ":material/bolt:"),
        ("Messages", cards, ":material/chat_bubble:"),
        ("Offers held", held, ":material/shield:"),
    ]
    for col, (label, value, symbol) in zip(st.columns(4), stats, strict=True):
        col.metric(label, value, icon=symbol, border=True)

    if not shown:
        st.info("No customer shows a life moment this month. Nobody gets a card.")
    else:
        table = pd.DataFrame(
            {
                "Customer": f["customer_id"],
                "Moment": f["moment"].replace("_", " ").capitalize(),
                "Since": f["since"],
                "Decision": f["response"].decision.replace("_", " "),
                "Status": status(f["response"], f["answer"]),
                "Evidence": f["evidence"],
            }
            for f in shown
        )

        def colour(decision: str) -> str:
            bg, fg = DECISION_COLOURS.get(decision, DECISION_COLOURS["none"])
            return f"background-color: {bg}; color: {fg}; font-weight: 600"

        table_key = f"moments_table_{month}"
        ids = [f["customer_id"] for f in shown]
        st.caption("Click a row to open that customer's phone.")
        st.dataframe(
            table.style.map(colour, subset=["Decision"]),
            hide_index=True,
            on_select=partial(pick_customer, table_key, ids),
            selection_mode="single-row",
            key=table_key,
            column_config={
                "Customer": st.column_config.TextColumn(width="small"),
                "Since": st.column_config.TextColumn(width="small"),
                "Decision": st.column_config.TextColumn(width="medium"),
                "Evidence": st.column_config.TextColumn(width="large"),
            },
        )

# The phone shows any customer: flagged ones first, then everyone else (who gets no card)
all_ids = [r[0] for r in con.execute("SELECT customer_id FROM customers ORDER BY 1").fetchall()]
flagged_ids = list(per_customer)
options = flagged_ids + [c for c in all_ids if c not in per_customer]
if st.session_state.get("phone_customer") not in options:
    st.session_state["phone_customer"] = options[0] if options else None
current = per_customer.get(st.session_state["phone_customer"])
# LLM wording only for the one card on the phone; the decision is the same either way
if current and not current["answer"]:
    card_row = tuple((k, current[k]) for k in ("customer_id", "moment", "since", "evidence"))
    current = {**current, "response": respond(card_row, None, as_of, use_llm=True)}

with kbc:
    if current and current["response"].staff_note:
        with st.container(key="staffnote"):
            st.markdown(f"**:material/lock: Staff note for {current['customer_id']}**")
            st.badge("Internal only, never shown to the customer", color="orange")
            st.write(current["response"].staff_note)
            st.caption(current["response"].why)

with phone:
    customer = st.selectbox(
        ":material/smartphone: Customer's phone",
        options,
        format_func=lambda c: (
            f"{c}  ·  {per_customer[c]['moment'].replace('_', ' ')}" if c in per_customer else c
        ),
        key="phone_customer",
    )
    with st.container(key="phone", width=390):
        st.html(PHONE_TOP)
        with st.container(height=470, border=False, key="screen"):
            recent = con.execute(
                """SELECT date, category, amount_eur FROM transactions
                WHERE customer_id = ? AND date <= ? ORDER BY date DESC, transaction_id DESC
                LIMIT 2""",
                [customer, as_of],
            ).fetchall()
            # No balances in our data, so the cards show them hidden, as the app's privacy
            # mode does, instead of a made-up number.
            st.html(
                f"""<div class="lm-accounts">
                <div class="lm-acc"><div class="art blue">{icon("wallet", 34, "#0D2A50")}</div>
                <div class="who">CURRENT ACCOUNT</div><div class="bal">&bull;&bull;&bull;&bull; EUR</div></div>
                <div class="lm-acc"><div class="art grey">{icon("piggy", 34, "#E9EDF2")}</div>
                <div class="who">SAVINGS</div><div class="bal">&bull;&bull;&bull;&bull; EUR</div></div>
                <div class="lm-acc"><div class="art grey"></div><div class="who">&nbsp;</div>
                <div class="bal">&nbsp;</div></div></div>
                {payment_rows((d, str(c).capitalize(), a) for d, c, a in recent)}
                <div class="lm-link">&#8963;&nbsp; Hide payments</div>
                <div class="lm-head"><span>For you</span>
                <span class="lm-link">All communications</span></div>"""
            )
            r = current["response"] if current else None
            if r and r.decision in ("ask", "nudge") and not r.quiet_until:
                with st.container(key="card"):
                    st.html(
                        f'<div class="lm-kate">{icon("mail", 22)}<span class="lm-dot"></span>'
                        "Kate wants you to know</div>"
                    )
                    st.markdown(r.message)
                    if current["answer"]:
                        st.caption(f"You answered: {current['answer']}")
                        st.button(
                            "Change my answer",
                            icon=":material/undo:",
                            type="tertiary",
                            on_click=remember,
                            args=(customer, current["moment"], None, as_of),
                        )
                    else:
                        buttons = list(r.buttons)
                        buttons += [b for b in moments.QUIET_ANSWERS if b not in buttons]
                        for b in buttons:
                            quiet = b in moments.QUIET_ANSWERS
                            st.button(
                                b,
                                key=f"answer_{customer}_{current['moment']}_{b}",
                                type="tertiary" if quiet else "primary",
                                width="stretch",
                                on_click=remember,
                                args=(customer, current["moment"], b, as_of),
                            )
                    if r.benefit:
                        st.caption(f"What's in it for you: {r.benefit}")
                    if r.why:
                        with st.expander("Why you see this", icon=":material/info:"):
                            st.write(r.why)
            elif r and r.quiet_until:
                st.html(
                    f"""<div class="lm-quiet">{icon("check", 22, "#9AA3AE")}
                    Thanks. We won't ask about this again before
                    {r.quiet_until + timedelta(days=1):%B %Y}.</div>"""
                )
                st.button(
                    "Undo",
                    icon=":material/undo:",
                    type="tertiary",
                    on_click=remember,
                    args=(customer, current["moment"], None, as_of),
                )
            else:
                # protect_quietly looks exactly like a customer with nothing to say: no card
                st.html(
                    f'<div class="lm-quiet">{icon("check", 22, "#9AA3AE")}'
                    "You're all caught up.</div>"
                )

            upcoming = moments.coming_up(con, customer, as_of)
            items = [
                (u.date, str(u.category).capitalize(), u.amount_eur) for u in upcoming.itertuples()
            ]
            st.html(
                '<div class="lm-head"><span>Coming up</span>'
                '<span class="lm-link">Next 30 days</span></div>'
                + (
                    f'<div class="lm-list">{payment_rows(items)}</div>'
                    if items
                    else '<div class="lm-quiet">No regular payments found.</div>'
                )
            )
            if st.button(
                "Worried about money? Talk to someone",
                icon=":material/support_agent:",
                type="tertiary",
            ):
                st.toast("An advisor will call you back. Nothing is shared with sales.")
        st.html(PHONE_NAV)
    st.caption("A drawing of the app: nothing is sent to anyone.")
