# Event partners and how we can use them

Partner list from https://www.tectonicconf.eu/hackathon (checked 30 September 2026). Local press says participants get tools and credits from the tech partners, but no amounts or claim steps are published. **Ask at the venue desk at 18:00 how to claim them.**

## Tech partners (worth using)

| Partner | What it is | Ready in this repo | Do before 18:00 |
|---|---|---|---|
| **Google Cloud** | Cloud platform with Gemini models, and Claude through Vertex AI | `LLM_PROVIDER=vertex` (Claude on Google Cloud) and `LLM_PROVIDER=gemini` in `src/hack/llm.py`, same `ask` / `ask_json` / `chat` functions | Either get a Gemini key at https://aistudio.google.com/apikey (free tier, no card), or pick a Google Cloud project, run `gcloud auth application-default login`, and set `GOOGLE_CLOUD_PROJECT`. New Google Cloud accounts get a free trial credit (card required). Then run `uv run python scripts/check.py`. |
| **ElevenLabs** | Speech: text to voice, and voice to text | `src/hack/voice.py`. In the Chat tab: a microphone in the chat box, and a "Read the last answer aloud" button. Hidden without a key. | Create an account at https://elevenlabs.io (free plan with monthly credits), copy the API key into `ELEVENLABS_API_KEY`, and try both in the app. Check that the free plan allows API use. |
| **Cursor** | AI code editor | `AGENTS.md` and the skills in `.claude/skills/` are read by Cursor. `.cursorignore` keeps `.env` and challenge data away from its AI. `.vscode/` settings work in Cursor too. | Install Cursor and sign in (free Hobby plan) on whichever laptop will use it, then open the repo once so it indexes. |
| **Aikido** | Security scanning: leaked secrets, vulnerable dependencies, risky code | Listed in the hand-in checklist of the `hackathon-deliverables` skill. | Sign in at https://app.aikido.dev with GitHub (free plan, no card), give it read access to this repo, and let the first scan run (about a minute). Then a re-scan before handing in is one click. |

Why it matters: using a partner's tool where it genuinely helps may count with the jury, and a working key set up in the afternoon avoids a sign-up flow at 20:00. Never let a partner tool put the demo at risk; mock mode and the Anthropic provider stay as fallbacks.

## Other partners (nothing to build)

| Partner | Role | Relevance for us |
|---|---|---|
| KBC | Our challenge track | Everything. |
| SD Worx | The other track (HR and payroll) | None. |
| Spott | Prize partner (the €10,000 prize). A Leuven start-up building recruitment software | None for the build. |
| Wonderful | Event partner. Builds AI agents for customer service in regulated industries such as banking | None to build with, but they may be in the room: a KBC idea about customer service would speak their language. |
| Entourage Ventures | Event partner, a Ghent venture capital fund and studio | None for the build. |
| In The Pocket, NextGen Belgium | Organisers. In The Pocket is a Ghent digital product studio | Good product thinking and a clean demo matter to them as organisers. |
