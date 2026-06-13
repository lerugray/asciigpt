# Fable direction memo — asciigpt (2026-06-12, final-night blitz)

State read: asciigpt is a healthy, finished-feeling v0.3.0. Python CLI, prompt→image→ASCII
architecture (locked at asci-004, direction α), 94 tests green, CI on 3.10/3.12/3.13, clean
tree, public on GitHub. Two real backends: ProceduralBackend (offline, deterministic, 9
keyword scenes + abstract fallback) and CommandBackend with an OpenAI adapter + recipes
(commit 7d139a1) for bring-your-own-AI. All GS-side strategic tasks done; asci-005 (PyPI
publish) is the only pending ledger item. Last code touch 2026-06-02; nothing is broken.

## The calls

1. **LOCK — PyPI publish is the next move, and it's one session.** Distribution is the only
   thing between "done" and "usable by strangers." Sequence: `python -m build` + `twine check`
   + verify the name `asciigpt` is free on PyPI (none of that needs credentials), then Ray
   pastes a scoped PyPI token and the upload fires the same session. The token is the single
   NAMED blocker; everything else is ready per pyproject.toml.

2. **LOCK — L1 ("live backend for arbitrary prompts") is satisfied by the BYO-AI recipe;
   demote it from P0.** The June 2 OpenAI adapter + CommandBackend already give live
   generation to anyone with a key. A native hosted ApiBackend would put API-cost ownership
   inside a free tool — wrong shape. Re-grade L1 to P2 in tasks.md when next edited.
   (Disagreement with the repo backlog recorded here; the scout brief had this right.)

3. **LOCK — wire `--backend openai` as a named shorthand that auto-routes when
   OPENAI_API_KEY is present.** One flag beats an env-template; small CLI change, big UX
   lift, fully testable. Do it in the same session as the PyPI prep so the published
   first-release UX includes it.

4. **LOCK — expand `_SCENES` before or alongside the PyPI ship.** Nine subjects is thin for
   users arriving via `pip install` with no key; unknown prompts falling to abstract blobs
   will underwhelm. Add 3-5 scenes (cat, spaceship, skyline) and make the fallback *say*
   which subjects it knows — behavior, not decoration. Pure Pillow, deterministic, tested.

5. **[RAY] Retrogaze integration (R1) — my lean: standalone-first, demote R1 to P2.** The
   README roadmap promises a "free companion to the SaaS" but zero wiring exists; PyPI is a
   distribution channel that doesn't depend on another project's schedule. Keep the roadmap
   line only if Ray still wants the tie-in; otherwise soften it. This is positioning — his
   axis.

6. **LOCK — AI-guided glyph selection (Q2, the original "GPT" premise) stays dormant, and
   when revived it gets a falsification gate first.** Before any build: cheap A/B of
   LLM-picked glyph ramps vs the current luminance ramp on ~5 images. If the eye can't tell,
   the feature doesn't exist. Empirical falsification before architecture.

## Risks to respect

- **PyPI name collision.** Verify `asciigpt` is unclaimed before building any publish
  narrative; if taken, the rename is a Ray call (naming = his axis).
- **README claim vs reality on retrogaze.** Until call 5 resolves, the roadmap line is a
  credibility gap for anyone who goes looking for the integration.
- **First-impression gap post-publish.** If PyPI ships before calls 3-4 land, the
  no-key first-click is nine scenes and abstract blobs. Ship them together.

## Fable-era note

The load-bearing decision of this project's life is asci-004: the marquee
"LLM-draws-characters" mode was unreliable and was *retired*, not patched — direction α
(prompt→image→ASCII through the solid deterministic converter) won. Do not relitigate that;
the full evidence trail is in `directions-fork-2026-05-19.md` and
`docs/handoffs/generative-revival-2026-06-02.md`. The register to preserve: this tool never
fakes AI. The ProceduralBackend is openly deterministic ("the seam's proof"), the AI path is
openly bring-your-own, and the README says which is which. That honesty is the project's
voice — a successor that blurs the offline/AI line to look more impressive is regressing it.
