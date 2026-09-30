---
name: streamlit
description: Use for any change to the Streamlit demo app (app/streamlit_app.py, app/pages/), including layout, widgets, charts, session state, caching, forms, reruns, styling or performance. Loads the official Streamlit reference docs that match the installed version.
---

# Streamlit (version-matched docs)

Streamlit ships its own reference docs for AI assistants inside the installed package, so they always match our version and avoid deprecated APIs. Find the entry point with:

```bash
uv run python -c "import os, streamlit; print(os.path.join(os.path.dirname(streamlit.__file__), '.agents', 'skills', 'developing-with-streamlit', 'SKILL.md'))"
```

Read that file first. It routes to topic files in the `references/` folder next to it; read only the ones relevant to the task.

Rules specific to this repo:

- Streamlit reruns the whole script on every click. Anything that calls the LLM must run only on an explicit action (a form submit or a button), with the result kept in `st.session_state`. See the "Ask your data" tab for the pattern.
- Use the per-session `con` cursor from the top of `app/streamlit_app.py`, not a new DuckDB connection.
- Never send a whole table to the browser; preview with `LIMIT`.
- After a change, run `uv run python scripts/check.py`. It renders every tab headless and fails if the app crashes.
