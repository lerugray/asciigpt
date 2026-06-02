# asciigpt — Task Backlog

> Priority: P0 = must-have, P1 = next, P2 = later polish.
> **Updated 2026-06-02:** re-aligned to the generative vision (prompt → image →
> ASCII). The old "prompt → LLM-draws-characters" backlog is gone — that path
> was retired. See `docs/handoffs/generative-revival-2026-06-02.md`.

## Done

| What | Notes |
|------|-------|
| Deterministic converter | presets, preprocessing, Sobel edges, dithering, text/ANSI/HTML, FIGlet |
| In-memory image input | `image_to_ascii` accepts a PIL image, not just a path |
| Generation seam | `asciigpt/generate.py`: pluggable `ImageBackend` + `prompt_to_ascii` |
| ProceduralBackend | offline, deterministic keyword scenes — the seam's proof |
| CommandBackend | live generation via any external command (`$ASCIIGPT_IMAGE_COMMAND`) |
| CLI generation | `--prompt` / `--backend` / `--gen-size`; v0.3.0; 94 tests green |

## Next

| ID | Task | Pri | Status |
|----|------|-----|--------|
| L1 | Live backend for arbitrary prompts: a hosted text-to-image API behind `--backend command` (or a native `ApiBackend`) | P0 | todo |
| R1 | retrogaze integration: expose generation as a free service alongside the SaaS (server absorbs backend cost) | P0 | todo |
| L2 | rasterize recipe: documented + smoke-tested `prompt → /render PNG → asciigpt` dev flow | P1 | todo |
| L3 | Packaging: `pyproject.toml` so `pip install .` gives a real `asciigpt` console script | P1 | todo |
| E1 | Example gallery: add a generated-from-prompt example (committed CLI output) | P1 | todo |
| Q1 | Prompt quality: per-subject default preset/preprocess; richer procedural scenes | P2 | todo |
| Q2 | AI-guided glyph selection (the original "GPT" quality layer) | P2 | todo |
| O1 | Optional ASCII → PNG output for monospace-unsafe sharing — deferred (Ray is fine without it) | P2 | todo |
