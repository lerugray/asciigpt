# Generate with your own AI

asciigpt's offline **procedural** backend works for everyone with zero setup,
but it only knows a handful of subjects. For *real* art from *any* prompt, point
`--backend command` at an image generator you already have access to. asciigpt
runs the command and converts whatever PNG it writes — so **any** generator
works.

The command is a template with three placeholders — `{prompt}` `{output}`
`{size}` — and it must write an image to `{output}`. asciigpt shell-quotes
`{prompt}` and `{output}` for you, and reports a clear error if the command
fails, writes nothing, or times out.

## OpenAI (gpt-image-1 / DALL·E)

A ready-made stdlib adapter ships in
[`scripts/backends/openai_image.py`](../scripts/backends/openai_image.py):

```bash
export OPENAI_API_KEY=sk-...
export ASCIIGPT_IMAGE_COMMAND='python scripts/backends/openai_image.py {prompt} {size} {output}'

asciigpt --prompt "a neon city at dusk" --backend command --preset high-contrast
```

Optional: `OPENAI_IMAGE_MODEL` (default `gpt-image-1`) and `OPENAI_IMAGE_SIZE`
(default `1024x1024`). asciigpt downsamples to the character grid, so a big
source size is fine.

## Claude (via the rasterize plugin)

If you use Claude Code, the [`rasterize`](https://github.com/suxrobgm/rasterize)
plugin renders a prompt to a PNG with Pillow / Cairo / Matplotlib / Playwright:

1. `git clone https://github.com/suxrobgm/rasterize && claude --plugin-dir ./rasterize`,
   then `python scripts/setup.py` inside it.
2. In Claude Code: `/render a neon city at dusk` → save the PNG.
3. `asciigpt that.png --preset high-contrast`

rasterize is agent-driven (not a CLI), so it's a two-step flow rather than a
`--backend command` template — but it's the easiest path if your sub is Claude.

## Any other generator

Anything that writes an image from a prompt works — a local Stable Diffusion
script, a different API, your own tool:

```bash
export ASCIIGPT_IMAGE_COMMAND='my-generator --prompt {prompt} --out {output}'
asciigpt --prompt "a lighthouse in a storm" --backend command
```

Write an adapter on the model of `scripts/backends/openai_image.py` for any API:
take `{prompt} {size} {output}`, produce a PNG at `{output}`, exit non-zero with
a message on failure.
