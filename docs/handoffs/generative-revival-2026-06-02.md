# asciigpt — generative revival (handoff, 2026-06-02)

> Supersedes the "deterministic converter only, no generation" framing of the
> 2026-05-28 brief. That pivot was a **tactical retreat** — the prompt→LLM path
> was unreliable, so the team fell back to building a solid converter — not a
> change of destination. The north star is, and was, an image-gpt-style ASCII
> **generator**, with the deterministic converter retained as the engine.

## Decisions (operator, 2026-06-02)

1. **Headline capability = prompt → ASCII.** A text-to-image step makes a base
   picture; the existing converter turns it into ASCII (`prompt → image →
   ASCII`). *Not* an LLM typing characters; *not* a bespoke image model. The
   output is ASCII, never a raster image.
2. **Shape = library-first.** The `asciigpt` package is the core; the CLI and a
   future retrogaze service are thin front-ends. The image generator is a
   pluggable backend behind one interface (`ImageBackend`).
3. **Backend cost.** A live text-to-image backend may be a paid API; the
   retrogaze service absorbs that cost server-side. (This updates MISSION's old
   "no paid external services" rule.) For local development, use Ray's
   Anthropic subscription via the `rasterize` plugin.
4. **Output stays ASCII** — no raster image output is required (Ray, explicit).
   An ASCII→PNG share format is a deferred maybe (tasks.md O1).

## What shipped this session (v0.3.0)

- `image_to_ascii` accepts an in-memory PIL image, not just a path (the one
  refactor generation needed).
- `asciigpt/generate.py`: the `ImageBackend` seam + `prompt_to_ascii()`.
  - **ProceduralBackend** (default): offline, deterministic keyword scenes
    (sphere/sun/moon/star/house/tree/mountain/heart/face) + a deterministic
    abstract fallback. It is the seam's *proof*, not a general artist.
  - **CommandBackend**: live generation via any external command — a
    `{prompt} {output} {size}` shell template from `$ASCIIGPT_IMAGE_COMMAND`
    (or `command=`), with clear errors on missing command / failure / timeout /
    no-output.
- CLI: `--prompt`, `--backend {procedural,command}`, `--gen-size`.
- 20 new tests (94 total, green). Verified end-to-end: `prompt → external
  Pillow renderer → PNG → asciigpt` produced a clean graded sunset with sun and
  mountain silhouettes.

## How rasterize fits

[`rasterize`](https://github.com/suxrobgm/rasterize) is a Claude Code **plugin**
(`/render`), agent-driven: Claude picks an engine (Pillow / Cairo / Matplotlib /
Plotly / Playwright), writes a render script, runs it in a managed venv, and
emits a PNG. It is **not** a standalone CLI, so it is not a direct library
dependency. Two ways it feeds asciigpt:

1. **Agent workflow (dev):** in a Claude Code session with rasterize loaded,
   `/render <prompt>` writes a PNG, then `asciigpt <png>` converts it — on Ray's
   Anthropic sub.
2. **CommandBackend (config):** point `$ASCIIGPT_IMAGE_COMMAND` at any
   render-to-file step (a rasterize wrapper, or a hosted text-to-image API CLI
   for the retrogaze service).

To install rasterize for the dev workflow:
`git clone https://github.com/suxrobgm/rasterize && claude --plugin-dir ./rasterize`
then `python scripts/setup.py` inside it (pdm venv + engines).

## Next (see tasks.md)

- **L1** — a live backend for arbitrary prompts (hosted text-to-image API).
- **R1** — retrogaze integration (free companion to the SaaS).
- **L3** — packaging (`pyproject.toml` → a real `asciigpt` console script).
- **Q2** — AI-guided glyph selection (the original quality-layer idea).
