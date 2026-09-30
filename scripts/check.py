"""Pre-push check: does the data load, does every app tab render, is the LLM reachable?

Run: uv run python scripts/check.py
Exits with an error if the app crashes, so a broken page never reaches main.
The "missing ScriptRunContext" warning printed first is harmless (Streamlit's own test mode).
"""

import sys
import warnings

from streamlit.testing.v1 import AppTest

from hack import ask_data, data, llm, voice
from hack.config import ROOT, data_dir


def main() -> None:
    skipped: list[str] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        con = data.connect(skipped=skipped)
    names = data.tables(con)
    print(f"Data folder: {data_dir()} -> {len(names)} tables: {', '.join(names) or 'none'}")
    for msg in skipped:
        print(f"  {msg}")

    # Renders the app headless, the same way a browser would load it. No LLM calls happen
    # here because nothing is typed into the app.
    app = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=60).run()
    if app.exception:
        print("App: FAILED to render")
        for e in app.exception:
            print(f"  {e.value}")
        sys.exit(1)
    print(f"App: renders, tabs {[t.label for t in app.tabs]}")

    print(f"Voice (ElevenLabs): {'key set' if voice.available() else 'off, no ELEVENLABS_API_KEY'}")
    print(f"LLM provider: {llm.provider()} ({llm.model_name()})")
    print(f"LLM says: {llm.ask('Reply with exactly: OK')!r}")
    if llm.provider() == "mock" or not names:
        print("Skipping the ask-your-data test (needs an LLM key and at least one table).")
        return
    result = ask_data.answer(con, f"How many rows does {names[0]} have?")
    print(f"Text-to-SQL: {result.sql}\n{result.df.to_string(index=False)}")


if __name__ == "__main__":
    main()
