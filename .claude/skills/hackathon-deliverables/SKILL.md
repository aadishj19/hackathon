---
name: hackathon-deliverables
description: Produce everything the jury receives - the one-page overview, the pitch (live, or a recorded video if that is the format), and a last check of the repo before handing in. Use from the 21:00 feature freeze onwards, or when the team asks about the one-pager, the pitch, a video or submitting.
---

# Deliverables: what the jury gets

Describe only what works. Before writing anything, open the app and click through the demo script, and read `docs/PLAYBOOK.md` for the one-sentence pitch. If nobody has confirmed the submission format and deadline yet, ask for them first.

## One-pager

Copy `docs/one-pager-template.md` to `docs/one-pager.md` and fill it in.
- Keep it to a single printed page (roughly 400 words).
- Open with the person who has the problem, not with the technology.
- Put the evidence in: the accuracy from `scripts/eval.py` with how many test cases it covers, and the time-saved or money estimate with its assumptions.
- If a PDF is needed, VS Code can print the Markdown preview to PDF.

## Pitch

Copy `docs/pitch-script-template.md` to `docs/pitch-script.md` and fill it in.
- The same script works live or as a video; plan it to run a little under the time limit.
- English is spoken at roughly 150 words a minute, so count words to check the length.
- Write down what is on screen for every part, so whoever records or presents knows what to show.

If a video is required:
- Capture the screen first, with no sound: Ubuntu has a built-in recorder (Ctrl+Shift+Alt+R) and Windows has Xbox Game Bar (Win+Alt+R).
- Then record the narration over it.
- Two separate passes are much faster than trying for one flawless take, and a headset keeps the venue noise out.

## Before handing in

Go through these with the team:
- [ ] `uv run python scripts/check.py` passes on the final commit, and that commit carries the `demo-ok` tag.
- [ ] The README's first lines say what the prototype does, for someone who wasn't there.
- [ ] `git ls-files` lists no `.env`, no challenge data (nothing in `data/` besides `data/sample/`) and no CSVs in `exports/`.
- [ ] If there is time: run an Aikido scan on the repo (see `docs/partners.md`).
- [ ] Restart the app and run the demo script once more from a clean start.
- [ ] The one-pager and the pitch or video are in the format the organisers asked for.
- [ ] Hand everything in with at least 20 minutes to spare.
