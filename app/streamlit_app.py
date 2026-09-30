"""Demo app. Run with: uv run streamlit run app/streamlit_app.py

Tabs: Explore (browse tables), Ask your data (text-to-SQL), Chat (LLM with the schema as
context; with an ElevenLabs key it also takes voice questions and reads answers aloud).
Replace or add tabs once the KBC challenge is known.
"""

import plotly.express as px
import streamlit as st

from hack import ask_data, data, llm, voice
from hack.config import data_dir, load_env

st.set_page_config(page_title="KBC Hackathon", layout="wide")
PREVIEW_ROWS = 1000


@st.cache_resource
def get_con():
    skipped: list[str] = []
    return data.connect(skipped=skipped), skipped


shared_con, skipped = get_con()
# A DuckDB connection isn't safe to share between threads, and Streamlit runs each browser
# tab on its own thread. A cursor is a per-tab handle onto the same in-memory data. When
# another tab reloads the data, the shared connection changes: rebuild this tab's cursor
# and drop everything based on the old data (the Ask answer, and the chat, which would
# otherwise be sent to the LLM along with the new data).
if st.session_state.get("con_source") is not shared_con:
    st.session_state["con_source"] = shared_con
    st.session_state["con"] = shared_con.cursor()
    for key in ("answer", "history", "speech"):
        st.session_state.pop(key, None)
con = st.session_state["con"]
tables = data.tables(con)

with st.sidebar:
    st.header("Setup")
    st.write(f"LLM: **{llm.provider()}** `{llm.model_name()}`")
    st.write(f"Data: `{data_dir().name}/` with {len(tables)} tables")
    st.write(f"Voice (ElevenLabs): **{'on' if voice.available() else 'off, no key'}**")
    for msg in skipped:
        st.warning(msg)
    if st.button("Reload data", help="Re-read .env and the data folder, e.g. after adding files"):
        load_env()
        llm.reset()
        voice.reset()
        get_con.clear()
        st.session_state.clear()
        st.rerun()
    if st.button("Export all tables for Power BI"):
        paths = data.export_for_powerbi(con)
        st.success(f"Wrote {len(paths)} CSV files to exports/")


def auto_chart(df):
    """Bar or line chart when the result is one label column plus one number column."""
    if len(df.columns) != 2 or len(df) < 2 or not df.iloc[:, 1].dtype.kind in "if":
        return
    x, y = df.columns
    is_time = df[x].dtype.kind == "M" or "date" in x.lower() or "month" in x.lower()
    fig = (px.line if is_time else px.bar)(df, x=x, y=y)
    st.plotly_chart(fig, width="stretch")


explore, ask, chat = st.tabs(["Explore", "Ask your data", "Chat"])

with explore:
    if not tables:
        st.info(f"No data files found in {data_dir()}. Drop CSV/Excel/Parquet files there.")
    else:
        t = st.selectbox("Table", tables)
        # Preview only: a full bank table can be millions of rows, too big to send to the browser
        rows = con.table(t).aggregate("count(*)").fetchone()[0]
        df = con.table(t).limit(PREVIEW_ROWS).df()
        shown = f", showing the first {PREVIEW_ROWS:,}" if rows > PREVIEW_ROWS else ""
        st.caption(f"{rows:,} rows, {len(df.columns)} columns{shown}")
        st.dataframe(df, width="stretch", height=400)
        with st.expander("Column summary (of the rows shown)"):
            # astype(str): describe() mixes numbers and labels, which the table widget rejects
            st.dataframe(df.describe(include="all").T.astype(str), width="stretch")

with ask:
    if llm.provider() == "mock":
        st.warning("Ask your data needs an LLM key in .env.")
    # A form only sends the question when "Ask" is pressed. A plain text box would re-send it
    # to the LLM on every click anywhere in the app, because Streamlit reruns the whole script.
    with st.form("ask_form"):
        question = st.text_input("Question", placeholder="Which segment spends most on travel?")
        submitted = st.form_submit_button("Ask")
    if submitted and question:
        st.session_state.pop("answer", None)
        with st.spinner("Thinking..."):
            try:
                st.session_state["answer"] = ask_data.answer(con, question)
            except Exception as e:  # noqa: BLE001 - show any failure on screen, never crash the demo
                st.error(f"{type(e).__name__}: {e}")
    if result := st.session_state.get("answer"):
        st.write(result.explanation)
        with st.expander("SQL"):
            st.code(result.sql, language="sql")
        auto_chart(result.df)
        if result.truncated:
            st.caption(f"Showing the first {ask_data.MAX_ROWS:,} rows of a larger result.")
        st.dataframe(result.df, width="stretch")


def chat_prompt() -> str | None:
    """Typed text, or a voice recording transcribed by ElevenLabs when a key is set."""
    submitted = st.chat_input(
        "Ask anything about the data or the challenge", accept_audio=voice.available()
    )
    if submitted is None or isinstance(submitted, str):
        return submitted
    if submitted.text:
        return submitted.text
    if submitted.audio:
        try:
            return voice.transcribe(submitted.audio.getvalue())
        except Exception as e:  # noqa: BLE001 - show any failure on screen, never crash the demo
            st.error(f"Transcription failed. {type(e).__name__}: {e}")
    return None


def read_aloud(text: str) -> None:
    speech = st.session_state.setdefault("speech", {})  # one paid call per answer, not per click
    try:
        if text not in speech:
            speech[text] = voice.speak(text)
        st.audio(speech[text], format="audio/mpeg", autoplay=True)
    except Exception as e:  # noqa: BLE001 - show any failure on screen, never crash the demo
        st.error(f"Speech failed. {type(e).__name__}: {e}")


with chat:
    history = st.session_state.setdefault("history", [])
    for msg in history:
        st.chat_message(msg["role"]).write(msg["content"])
    if prompt := chat_prompt():
        history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        system = "You help a team at a KBC hackathon. The available data:\n\n" + data.describe(con)
        with st.chat_message("assistant"), st.spinner("Thinking..."):
            try:
                reply = llm.chat(history, system=system)
            except Exception as e:  # noqa: BLE001 - show any failure on screen, never crash the demo
                history.pop()  # drop the unanswered question so a retry starts clean
                st.error(f"{type(e).__name__}: {e}")
                st.stop()
            st.write(reply)
        history.append({"role": "assistant", "content": reply})
    has_answer = bool(history) and history[-1]["role"] == "assistant"
    if voice.available() and has_answer and st.button("Read the last answer aloud"):
        read_aloud(history[-1]["content"])
