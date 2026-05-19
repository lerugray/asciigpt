# asciigpt — strategic fork, 2026-05-19

> Banked for a focused conversation. Three viable directions for what
> asciigpt should become; the choice hinges on tradeoffs Ray hasn't
> resolved yet. Surfaced live in a 2026-05-19 dogfood session; Ray
> asked to set aside for a deeper pass with more focus.

## What prompted the fork

Ran the v0 marquee invocation against the README's example prompts to
see real output, since asci-001 / asci-003 had just been swept to done
under the gsd-042 fleet-drift reconcile. Three runs of the same prompt
produced wildly inconsistent output; the LLM-prompt-to-2D-art path is
not reliable enough to share.

### Empirical findings — `python generate.py "steampunk airship over a burning city"`

| Run | Chars | What landed |
|-----|-------|-------------|
| 1 | ~643 | Balloon ellipse at top + four building columns below — recognizable, but the columns are byte-identical repeats |
| 2 | ~5000 | Balloon ellipse at top, then ~80 lines of `\|  \__/  \|` pattern repeating until token cap; composition lost |
| 3 | 285 | Just a balloon outline, truncated mid-draw; no city, no flames |

### Dragon + wolf prompts showed the same instability

- `"a dragon breathing fire over a castle"` — recognizable dragon head, then ~100 lines of `\    \` drifting diagonally off the right edge.
- `"lone wolf howling at the moon"` × 3 — three different attempts at composition, none obviously a wolf, but none degenerate.

### Image mode actually works

Tested `generate.py --image` against a hand-drawn airship silhouette
(ellipse + gondola + spike row). The deterministic path produced a
recognizable balloon + gondola + flames-as-spikes, dithered cleanly
via Floyd-Steinberg. The gradient presets, dithering, and Pillow
preprocessing are doing real work. **This path is shippable as-is.**

### Root cause

The current pipeline asks DeepSeek-chat to compose 2D spatial content
in a single LLM call. The system prompt is thoughtful — dimension
caps, subject-fidelity rules, anti-repetition rules, anti-drift rules,
palette guidance — and post-processing has a runaway-repetition guard
that cuts the tail after 6 byte-identical lines. The guard works for
identical lines but doesn't catch **drifting** patterns (each line
shifting by one space). Even with all the guardrails, the model is a
sequence generator trying to lay out 2D content; the failure modes
are the model's, not the prompt's.

DeepSeek isn't uniquely bad here — every LLM struggles with this. The
better-on-spatial-reasoning models (Claude, GPT-4) help on the margin
but don't solve the underlying problem.

## The fork

Three directions; the project can only really be one of them. Picking
is downstream of "what is asciigpt for in Ray's portfolio."

### (α) Pipeline reorientation — txt2img → ASCII via the existing image path

**Shape:** When a prompt comes in, generate an image with `gpt-image-1`
(mc already does this; ~$0.04/call), then run that image through the
existing image-mode pipeline — gradient + dither + the lot. Image-mode
in is unchanged. Pure prompt becomes prompt → image → ASCII.

**Pros:**
- Highest output-quality lift. The image-mode path produces shareable
  output today; pairing it with a real image generator skips the
  LLM-trying-to-draw-2D problem entirely.
- Both halves already exist in the codebase. This is a wiring change,
  not new infrastructure.
- Preserves the README's marquee invocation
  (`python generate.py "steampunk airship over a burning city"`).
- The hybrid `--prompt + --image` mode that pipeline.md already
  describes lands naturally as a special case (skip the image-gen
  step, use the supplied image).

**Cons:**
- $0.04 per generation. Not nothing — a casual user running 20
  prompts a day pays $24/month. Probably tolerable for Ray's own use,
  ambiguous for a shareable tool.
- Loses the "no other tool does this" pure-LLM purity. The marquee
  positioning shifts from "an LLM draws ASCII art directly" to
  "an AI pipeline produces ASCII art."
- Adds an OpenAI dependency on top of the existing DeepSeek one (or
  picks one to consolidate around).

**Implementation rough-out:**
- New `--image-gen` flag (or detect the absence of `--image`).
- New module that calls `gpt-image-1` with the user's prompt; the
  Tauri layer in mc already has this code working — port it.
- Pipe the returned image bytes into `load_and_preprocess` (no disk
  hop needed).
- Add an `--llm-text-only` escape hatch for the purist mode in case
  the LLM path turns out to be useful at some unforeseen point.

### (β) Narrow scope — ship image-mode-only

**Shape:** Cut prompt mode entirely. Position asciigpt as a polished
`jp2a` successor — gradient presets, Floyd-Steinberg dithering, edge
detection, Pillow preprocessing. No LLM.

**Pros:**
- Smallest scope, lowest risk. The thing that works becomes the
  product.
- Fastest path to "this is genuinely shippable and useful."
- No API costs, no API keys, no rate limits, no token failures.
  Runs entirely local.
- The MISSION.md "looks intentional — like vintage console box art"
  positioning still holds for image input. A photo of a dragon
  through Floyd-Steinberg + the `mechanical` gradient delivers on
  that promise.

**Cons:**
- Drops the marquee "prompt → art" claim entirely. The README needs
  a substantial rewrite.
- The differentiation against `jp2a` becomes "better preset library
  + better dithering + edge detection." Real, but not as
  immediately exciting.
- Closes off any portfolio narrative about "AI-assisted creative
  tools."

**Implementation rough-out:**
- Delete `generate_from_prompt`, the DeepSeek client, the system-prompt
  scaffolding, and the hybrid path.
- Rewrite README + MISSION.md to position around image-mode.
- Consider renaming the project — "asciigpt" carries the prompt-mode
  promise. Something like "asciidither" or "asciilab" would match
  the narrowed scope better.

### (γ) Fix prompt mode in place

**Shape:** Keep the current architecture, address the failure modes
incrementally — swap DeepSeek for Claude or GPT-4 (better spatial
reasoning); add a shifted-by-N repetition detector; maybe try a
two-pass approach (LLM produces a structural plan, then renders
constrained by it).

**Pros:**
- Preserves the original positioning ("an LLM draws ASCII art
  directly") if it pans out.
- Lowest commitment — can be tried before committing to (α) or (β).
- Two-pass is an interesting design space; the literature on
  LLM-as-spatial-reasoner is moving.

**Cons:**
- Highest risk that the underlying problem (LLMs can't reliably draw
  2D) doesn't yield to incremental fixes.
- Even when individual runs are good, the high run-to-run variance
  makes the tool feel broken — users would need to "roll the dice
  three times" for one good output.
- Claude / GPT-4 calls cost more than DeepSeek's, eating most of
  the "but it's just an LLM call" cost advantage.

**Implementation rough-out:**
- Add provider abstraction (Claude / OpenAI / DeepSeek as backends).
- Add a "shifted-repetition" detector to `clean_llm_output` (catch
  patterns like `\    \` / `\     \` / `\      \` etc.).
- Two-pass: prompt the LLM for a `STRUCTURE:` block (the composition
  outline), then prompt again for line-by-line rendering constrained
  by the structure.
- Build a small benchmark suite (10–20 representative prompts × N
  runs each) to measure consistency improvements quantitatively.

## My recommendation, banked for your call

**(α) Pipeline reorientation** — the txt2img → ASCII pivot. Reasons:

1. **It's the only one that produces output you'd actually share.**
   Image mode + a good image gives genuinely good ASCII; (β) limits
   inputs to "images you already have"; (γ) is a coin flip.
2. **Both halves already exist.** The image-mode pipeline is solid,
   and mc has a working `gpt-image-1` call you can lift.
3. **It preserves the README's UX.** Ray still types a prompt; ASCII
   art comes out. The mechanism behind the scenes is the operator's
   problem, not the user's.
4. **The cost is genuinely small per use** ($0.04/call) and entirely
   optional — the `--image` path stays free, and an
   `--llm-text-only` flag preserves the original path for anyone
   curious.

The main reason to NOT pick (α) is if Ray's portfolio narrative needs
asciigpt to be "pure LLM, no diffusion model in the loop." That's a
positioning call only Ray can make.

## Open questions worth sitting with before deciding

- **Portfolio role.** Is asciigpt meant to be (a) a polished
  shippable tool, (b) a vibecoder-portfolio piece that demonstrates
  range, (c) a hobby thing Ray enjoys? The right direction differs
  per role.
- **Cost tolerance.** $0.04/call is fine for personal use; for a
  publicly-released tool that hits Hacker News, the same call rate
  could run to real money. Does the tool BYOK (user supplies their
  own OpenAI key) or eat the cost?
- **Differentiation.** What's the one-line pitch — "an LLM that
  draws ASCII art" (current, (γ)), "the polished image-to-ASCII
  converter" ((β)), or "the AI pipeline that turns prompts into
  shareable ASCII art" ((α))?
- **Time budget.** (β) is shippable in a day; (α) is shippable in
  ~a session if mc's gpt-image-1 wiring ports cleanly; (γ) is a
  multi-session investigation with uncertain payoff.

## Files to read when picking this up

- This document (`directions-fork-2026-05-19.md`) — context + lean.
- `generate.py` — current implementation; the system prompt at
  `build_system_prompt` and the cleanup in `clean_llm_output` are
  the load-bearing parts of the current LLM path.
- `pipeline.md` — original design intent. Path A (prompt → ASCII)
  and Path B (image → ASCII) are described as separate flows; (α)
  composes them in series.
- `MISSION.md` — positioning. Rewriting this is downstream of the
  fork choice.
- `state/asciigpt/tasks.json` (in generalstaff-private) — asci-004
  tracks this fork as the next strategic decision.

## What's not in this document

- The actual code change for (α). Worth scoping in the focused
  session — needs a look at mc's `gpt-image-1` invocation to
  estimate the port effort.
- Benchmark methodology for (γ). If Ray picks (γ) as the
  exploration, a small benchmark harness (prompts × runs × quality
  rubric) is the first task.
- README/MISSION rewrites for (β) and (α). Both blocks are
  downstream of the fork — drafting them now would lock the
  positioning before Ray has picked.
