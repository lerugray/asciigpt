# asciigpt — build-out goal + brief (2026-05-28)

> Prep doc for an autonomous `/goal` session. Read this top to bottom
> before setting the goal. The headline: **the design vision is well
> documented, but it is forked — there are three mutually-exclusive
> directions and Ray has not picked one.** An autonomous `/goal` needs
> a single concrete target, so the goal below assumes a direction
> (α). If that assumption is wrong, fix the goal first (see
> "Direction gate" at the end).

---

## 1. The design vision (grounded in the actual docs)

asciigpt is **an AI-assisted, CLI-first, runs-local ASCII-art
generator written in Python.** Source of truth: `MISSION.md`, `README.md`,
`pipeline.md`, `research.md`, and the GS-side brief at
`generalstaff-private/docs/internal/asciigpt-brief.md`.

What it is meant to BE and DO at maturity (`MISSION.md` "Success"):

> Ray types `python generate.py "steampunk airship over a burning city"`
> and gets terminal-ready ASCII art he'd actually want to share.

Two input paths (`pipeline.md`):

- **Prompt → ASCII** (the marquee feature) — describe art in natural
  language, get ASCII out.
- **Image → ASCII** (deterministic converter) — Pillow preprocessing
  (resize / grayscale / edge detect / brightness / contrast / gamma) +
  named **gradient presets** + **Floyd–Steinberg dithering**. Everything
  jp2a/libcaca do, "plus some."
- **Hybrid** — image as a style/anatomy reference for a prompt.

Differentiator (`research.md` §Summary): no existing tool (jp2a,
libcaca, asciiart.eu, Nokse22/ascii-draw, asciicam) does **prompt → art
through an AI pipeline**. The whole landscape is pixel-luminance→glyph.
"The 'gpt' in the name is the point."

End vision for *this* push: polish it enough to ship as a **free bonus
on retrogaze** (Ray's NES-era pixel-art SaaS). That makes the retro /
pixel register load-bearing — see reference projects.

Non-goals (`MISSION.md`): not a drawing app, not a web converter/SaaS,
not (yet) integrated into retrogaze, not "just another jp2a wrapper."

Constraints: Ray is a non-programmer — **code must stay readable and
heavily commented** (the current `generate.py` is one ~960-line file
with 12 labelled sections; preserve that legibility). Budget: DeepSeek
API (≈free) or BYOK; **no paid external services baked in as
mandatory.**

---

## 2. CRITICAL — the design vision is FORKED (read before goaling)

A 2026-05-19 dogfood (documented in `directions-fork-2026-05-19.md`,
tracked as GS task `asci-004`, status **deferred / priority 1 /
interactive-only**) found:

- **Image mode works and is shippable as-is.** Real ASCII out, clean
  dithering, presets doing real work.
- **Prompt mode (the marquee feature) is unreliable.** Three runs of
  the same prompt gave: (1) a recognizable balloon+city, (2) ~80 lines
  of degenerate repetition, (3) a 285-char truncated outline. Root
  cause: an LLM is a sequence generator being asked to lay out 2D
  spatial content — the failure is the model's, not the prompt's, and
  no provider swap fully fixes it.

Ray banked **three mutually-exclusive directions** and explicitly
deferred the call as *his* domain (portfolio role / cost tolerance /
positioning):

- **(α) Pipeline reorientation** — prompt → *generate an image*
  (`gpt-image-1`) → run it through the existing image pipeline. Both
  halves already exist in-repo; it's a wiring change. Preserves the
  marquee `python generate.py "..."` UX. ~$0.04/call. **This is the
  doc's recommended lean AND the best fit for the "free bonus on
  retrogaze" goal** (retrogaze is literally a prompt→image→retro-art
  pipeline — same shape).
- **(β) Narrow to image-mode only** — ship a polished jp2a successor,
  no LLM. Smallest scope, zero API cost. Would mean dropping the
  marquee claim and probably renaming the project.
- **(γ) Fix prompt mode in place** — provider swap + shifted-repetition
  detector + maybe two-pass. Highest risk; the doc calls it "a coin
  flip."

**Why this matters for `/goal`:** a Haiku evaluator checks the end-state
each turn. If the goal says "build out the design vision" without
resolving the fork, the session will either (a) thrash between
directions, or (b) silently pick one and possibly the wrong one. The
goal below picks **α** because it's the documented lean and the
retrogaze-bonus framing favors it. **If Ray prefers β or γ, swap the
goal per the Direction gate at the bottom before pasting.**

---

## 3. Reference projects (found — where they live, what to borrow)

**Borrow the txt2img wiring from these (for direction α):**

- **mission-companion** (`/Users/rayweiss/Desktop/Dev Work/mission-companion/`)
  — has a working `gpt-image-1` call. Rust:
  `src-tauri/src/lib.rs` ~line 752 (`/v1/images/generations`, model
  `gpt-image-1`, `size 1024x1024`, reads `data[0].b64_json`). JS mirror:
  `src/app.js`. This is the "mc's gpt-image-1 wiring" the fork doc says
  to port.
- **mission-PMA** (`/Users/rayweiss/Desktop/Dev Work/mission-PMA/scripts/probe-panel-openai.py`)
  — **the cleanest reference for asciigpt because it's already Python.**
  `requests.post` to `https://api.openai.com/v1/images/generations`,
  payload `{model: "gpt-image-1", size: "1024x1024", quality: ...}`,
  decodes `data[0].b64_json` via `base64.b64decode`. Lift this pattern
  almost verbatim into a new asciigpt module, then feed the returned
  bytes straight into `load_and_preprocess` (BytesIO, no disk hop).

**Borrow the aesthetic / register from:**

- **retrogaze** (`/Users/rayweiss/Desktop/Dev Work/retrogaze/`) — NES-era
  pixel-art generation, prompt→image→constraint-enforced retro art.
  asciigpt ships as a free bonus here, so match the retro register:
  prompt-driven, retro/pixel output (the `blocky` █▓▒░ gradient is the
  ASCII analogue of NES tiles), "built by a game designer, not venture
  capital" voice. retrogaze proves the prompt→image→retro-art shape
  works end-to-end — α is the same architecture in ASCII.

**Borrow conventions / quality bar from (already inventoried in
`research.md`):** jp2a (CLI flag conventions `--width`/`--invert`/
`--background`, HTML output, directional edge glyphs, the quality bar to
beat), libcaca/img2txt (output-format list, dithering algorithms, gamma),
asciiart.eu (named gradient presets — already adopted), Nokse22/ascii-draw
(pyfiglet/FIGlet for title cards). asciicam is a boundary marker (out of
scope), not a parts donor.

---

## 4. Current state → vision gap

**Built and working** (`generate.py`, ~960 lines, 12 sections):
- `.env` loading, DeepSeek client, prompt-engineering system prompt.
- Prompt → ASCII path (`generate_from_prompt` + `clean_llm_output` with
  a runaway-repetition guard) — **works but output is unreliable.**
- Image → ASCII path (`load_and_preprocess`, `map_luminance_to_glyph`,
  `apply_floyd_steinberg`, `generate_from_image`) — **solid, shippable.**
- 7 gradient presets, full argparse CLI (positional prompt, `--image`,
  `--width`, `--gradient`, `--dither`, `--style`, `--brightness`,
  `--contrast`, `--gamma`, `--edges`, `--invert`, `--temperature`,
  `--list-gradients`), terminal+file output.

**Gaps to close for a "polished, shippable" tool:**
1. **The fork is unresolved** (see §2) — the #1 blocker.
2. **Marquee output is unreliable** — α fixes this by routing prompt →
   image → image-pipeline.
3. **No tests at all** — `find` for `test_*.py` returns nothing. A
   shippable tool needs at least smoke + unit coverage on the
   deterministic image path (presets, glyph mapping, dithering) and on
   CLI arg parsing.
4. **No `examples/` directory** — README references sample outputs;
   none exist. (`tasks.md` Q6.)
5. **README v0.2+ list is unbuilt**: HTML output, `--clipboard`, batch
   mode, FIGlet/pyfiglet title cards, ANSI color. Pick the subset that
   serves the retrogaze-bonus goal; don't gold-plate.
6. **No `pyproject.toml` / `python -m asciigpt` entry point** — it's a
   loose `generate.py`. A shippable bonus tool benefits from a real
   module + console-script entry (decide: keep single-file legibility
   vs. package it — Ray's "readable code" constraint favors keeping the
   single annotated file and just adding a thin `__main__.py` shim).

---

## 5. Concrete build list (for direction α)

In rough dependency order:

1. **Wire prompt → image → ASCII.** New `generate_from_prompt_via_image`
   (or an `--image-gen`/auto path): call `gpt-image-1` (port the
   mission-PMA Python pattern), pipe bytes via `BytesIO` into
   `load_and_preprocess`, run the existing image pipeline. Default the
   bare `python generate.py "prompt"` invocation to this path.
2. **Keep an escape hatch.** `--llm-text-only` preserves the original
   direct-LLM path (the fork doc explicitly wants this).
3. **BYOK + cost honesty.** Read `OPENAI_API_KEY` from env/.env (extend
   `.env.example`); if missing, fail with a clear message pointing at
   where to get a key. Don't bake in a shared key.
4. **Retro register defaults.** Make the retrogaze-bonus framing real —
   e.g. default or feature the `blocky`/pixel gradient for the
   prompt→image path; ensure output reads as retro box-art.
5. **Tests.** `tests/` with: gradient-preset integrity, luminance→glyph
   mapping, Floyd–Steinberg on a tiny synthetic grid, CLI arg parsing,
   and a mocked-API smoke test for the prompt path (mock the HTTP call;
   don't spend real money in CI).
6. **`examples/`** with a few committed sample outputs (image-mode at
   least — deterministic, reproducible).
7. **README usage section** updated to reflect the α pipeline and the
   new flags; keep it honest about cost (BYOK, ~$0.04/prompt).
8. **Entry point** — thin `python -m asciigpt` shim or keep
   `python generate.py`; document whichever ships.

Skip for this push unless they fall out cheaply: HTML output, clipboard,
batch, ANSI color, FIGlet (these are the README "v0.2+" wishlist — nice,
not load-bearing for a polished retrogaze bonus).

---

## 6. The `/goal` string (paste this — assumes direction α)

```
/goal asciigpt is built out to ship as a polished free bonus on retrogaze, via direction α (prompt → gpt-image-1 → existing image pipeline). Done when ALL hold: (1) `python generate.py "a steampunk airship over a burning city"` runs end-to-end and prints retro ASCII art by routing the prompt through image generation then the existing image pipeline (no raw-LLM-draws-2D path as the default); (2) a `--llm-text-only` flag preserves the original direct-LLM path; (3) OPENAI_API_KEY is read from env/.env with a clear error if missing, and .env.example documents it; (4) image mode (`python generate.py --image <file>`) still works unchanged; (5) a `tests/` suite exists covering gradient presets, luminance→glyph mapping, Floyd–Steinberg dithering, and CLI arg parsing, the API path is tested with the network call mocked, and `python -m pytest` passes; (6) an `examples/` directory holds at least two committed sample outputs; (7) README has an accurate usage section for the new pipeline, names the BYOK requirement and ~$0.04/prompt cost, and `generate.py` stays a readable, well-commented single file. Each item must be verifiable by reading files / running tests, not by inspection of intent.
```

---

## 7. Direction gate — DO THIS FIRST if α is not the call

The goal above commits to **α**. Before pasting it, confirm α is what
Ray wants. If he prefers:

- **β (image-mode only):** rewrite the goal to "prompt mode removed,
  README+MISSION repositioned around image mode, tests + examples for
  the deterministic path, optional rename." Drop items 1–3.
- **γ (fix prompt mode in place):** rewrite the goal around a benchmark
  harness (N prompts × M runs × a pass rubric) + a shifted-repetition
  detector + provider abstraction, with a measurable consistency
  threshold as the done-condition. Note this is the riskiest and may
  not converge — a `/goal` on γ could legitimately fail to complete.

If Ray hasn't picked, the cleanest move is a 30-second decision before
the session, **not** an autonomous goal that guesses. This is a
purpose/positioning call — Ray's axis, not the engineer session's.

---

*Reference files:* `MISSION.md`, `README.md`, `pipeline.md`,
`research.md`, `directions-fork-2026-05-19.md`, `generate.py`;
GS-side `state/asciigpt/{MISSION.md,tasks.json}` (asci-004) and
`docs/internal/asciigpt-brief.md`.
