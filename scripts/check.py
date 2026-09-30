"""Pre-push check: does the data load, does the app render, does the engine run, is the LLM
reachable?

Run: uv run python scripts/check.py
Exits with an error if the app crashes, so a broken page never reaches main.
The "missing ScriptRunContext" warning printed first is harmless (Streamlit's own test mode).
"""

import sys
import warnings

from streamlit.testing.v1 import AppTest

from hack import data, llm, moments
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

    # Renders the app headless, the same way a browser would load it
    app = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=120).run()
    if app.exception:
        print("App: FAILED to render")
        for e in app.exception:
            print(f"  {e.value}")
        sys.exit(1)
    print(f"App: renders, metrics {[(m.label, m.value) for m in app.metric]}")

    found = moments.detect(con, moments.TODAY)
    print(f"Engine: {len(found)} customers flagged as of {moments.TODAY}")
    print(f"LLM provider: {llm.provider()} ({llm.model_name()})")
    print(f"LLM says: {llm.ask('Reply with exactly: OK')!r}")


if __name__ == "__main__":
    main()
