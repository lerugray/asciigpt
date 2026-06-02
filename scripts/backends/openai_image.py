#!/usr/bin/env python3
"""
asciigpt — reference OpenAI image-backend adapter (stdlib only).

Bridges any OpenAI image model into asciigpt's ``--backend command``: it takes
asciigpt's ``{prompt} {size} {output}`` arguments, calls the OpenAI Images API,
and writes a PNG to ``{output}``. No extra dependencies.

Wire it in:

    export OPENAI_API_KEY=sk-...
    export ASCIIGPT_IMAGE_COMMAND='python scripts/backends/openai_image.py {prompt} {size} {output}'
    asciigpt --prompt "a neon city at dusk" --backend command --preset high-contrast

Environment:
    OPENAI_API_KEY        required
    OPENAI_IMAGE_MODEL    optional (default: gpt-image-1)
    OPENAI_IMAGE_SIZE     optional (default: 1024x1024)

OpenAI renders only a few fixed sizes, so asciigpt's {size} (the procedural
canvas size) is ignored here in favour of OPENAI_IMAGE_SIZE — asciigpt
downsamples to the character grid afterwards regardless.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.openai.com/v1/images/generations"


def main(argv):
    # Wired as '... {prompt} {size} {output}', so argv = [prog, prompt, size, output].
    if len(argv) != 4:
        sys.stderr.write("usage: openai_image.py PROMPT SIZE OUTPUT\n")
        return 2
    prompt, _ignored_size, output = argv[1], argv[2], argv[3]

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.stderr.write(
            "OPENAI_API_KEY is not set. Export your key, then retry.\n"
        )
        return 1
    model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = os.environ.get("OPENAI_IMAGE_SIZE", "1024x1024")

    body = json.dumps(
        {"model": model, "prompt": prompt, "size": size, "n": 1}
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        sys.stderr.write(f"OpenAI API error {exc.code}: {detail}\n")
        return 1
    except urllib.error.URLError as exc:
        sys.stderr.write(f"Network error reaching OpenAI: {exc.reason}\n")
        return 1

    # gpt-image-1 returns inline base64; some models return a URL instead.
    try:
        item = payload["data"][0]
        if item.get("b64_json"):
            data = base64.b64decode(item["b64_json"])
        else:
            with urllib.request.urlopen(item["url"], timeout=120) as img:
                data = img.read()
    except (KeyError, IndexError, ValueError) as exc:
        sys.stderr.write(f"Unexpected OpenAI response shape: {exc}\n")
        return 1

    with open(output, "wb") as handle:
        handle.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
