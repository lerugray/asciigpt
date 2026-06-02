# asciigpt — next steps for the orchestrator (session note, 2026-06-02)

Picks up after the generative-revival session. The project is **public, shipped,
and green** — the two items below are optional polish, not fixes. Nothing here is
blocking; the tool works today.

## Status snapshot
- Public: https://github.com/lerugray/asciigpt
- Released: **v0.3.0** (early-preview pre-release)
- 94 tests green; CI passing on Python 3.10 / 3.12 / 3.13
- `prompt → image → ASCII` seam in place: offline `ProceduralBackend` +
  `CommandBackend` (bring-your-own-AI). Full context in
  [`generative-revival-2026-06-02.md`](generative-revival-2026-06-02.md).

## Follow-up 1 — Publish to PyPI  (tasks.md: P1)
**Why:** today it's `git clone … && pip install .`; PyPI makes it
`pip install asciigpt` — the biggest friction-drop for the public / r/aigamedev
share.
**Already done:** `pyproject.toml` is complete (metadata, deps, console script,
dynamic version, classifiers); a build should just work.
**Steps (needs Ray's PyPI account + API token):**
1. `pip install build twine`
2. `python -m build`  → wheel + sdist in `dist/`
3. (optional) TestPyPI dry-run first: `twine upload -r testpypi dist/*`
4. `twine upload dist/*`  (needs `~/.pypirc` or a `PYPI_API_TOKEN`)
5. Verify in a clean venv: `pip install asciigpt` → `asciigpt --version`
**Agent boundary:** PyPI credentials are Ray's — an agent can build + dry-run on
TestPyPI; the human does the real upload (or provides a scoped token).

## Follow-up 2 — Stronger first-click demo  (tasks.md: Q1, plus L1)
**Why:** the default offline backend only knows ~9 subjects; an unknown prompt
("a spaceship") becomes an abstract blob. A fresh clone without an AI backend can
underwhelm. Two independent ways to improve — pick either or both:

- **(a) Richer procedural scenes** — add subjects to the `_SCENES` table in
  [`asciigpt/generate.py`](../../asciigpt/generate.py) (cat, robot, spaceship,
  city skyline, mountain range, fish, …). Pure Pillow primitives, deterministic,
  no new deps: add a `_draw_*` / `_scene_*` helper and a `_SCENES` row each, plus
  a keyword test in `tests/test_generate.py`. Cheap, safe, immediately improves
  the no-setup experience.
- **(b) A more turnkey live backend** — make real generation closer to one step:
  e.g. register the OpenAI adapter as a named backend (`--backend openai`)
  instead of the env-template, or auto-route when `OPENAI_API_KEY` is present.
  Keeps bring-your-own-AI, fewer moving parts. (tasks.md L1.)

## Parked / already decided (don't re-litigate)
- ASCII→PNG output: deferred (Ray is fine without it) — tasks.md O1.
- AI-guided glyph selection: later quality layer — tasks.md Q2.
- License = MIT; commits go straight to `master` (Ray's flow).
