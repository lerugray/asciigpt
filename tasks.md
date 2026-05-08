# asciigpt — Task Backlog

> Priority: P0 = must-have for prototype, P1 = v1.0, P2 = post-v1 polish

## Phase 1: Foundation

| ID | Task | Pri | Status |
|----|------|-----|--------|
| F1 | Create MISSION.md | P0 | done |
| F2 | Create tasks.md | P0 | done |
| F3 | Create README.md with usage and examples | P1 | todo |
| F4 | Set up Python project structure (requirements.txt, .gitignore) | P0 | todo |

## Phase 2: Research

| ID | Task | Pri | Status |
|----|------|-----|--------|
| R1 | Analyze asciiart.eu/image-to-ascii — algorithm, char sets, tuning | P0 | todo |
| R2 | Analyze jp2a — baseline quality, flags, limitations | P0 | todo |
| R3 | Analyze libcaca/img2txt — approach, strengths | P1 | todo |
| R4 | Survey Nokse22/ascii-draw — UX patterns, glyph handling | P2 | todo |
| R5 | Document findings in research.md | P0 | todo |

## Phase 3: Pipeline Design

| ID | Task | Pri | Status |
|----|------|-----|--------|
| P1 | Define input types and their processing paths | P0 | todo |
| P2 | Design prompt-to-ascii LLM pipeline | P0 | todo |
| P3 | Design image-to-ascii conversion pipeline | P0 | todo |
| P4 | Define glyph density map for output quality | P0 | todo |
| P5 | Document the pipeline in pipeline.md | P0 | todo |

## Phase 4: Prototype Implementation

| ID | Task | Pri | Status |
|----|------|-----|--------|
| I1 | DeepSeek API client module | P0 | todo |
| I2 | Prompt-to-ascii generation (LLM in the loop) | P0 | todo |
| I3 | Image preprocessing (resize, grayscale, edge detection) | P0 | todo |
| I4 | Density-aware glyph mapping | P0 | todo |
| I5 | Image-to-ascii conversion pipeline | P0 | todo |
| I6 | CLI interface (argparse: --prompt, --image, --width, etc.) | P0 | todo |
| I7 | Output formatting (terminal, file, clipboard) | P1 | todo |
| I8 | Configuration system (API keys, defaults) | P1 | todo |

## Phase 5: Quality & Polish

| ID | Task | Pri | Status |
|----|------|-----|--------|
| Q1 | Test with diverse prompts (landscapes, portraits, objects) | P0 | todo |
| Q2 | Test with diverse images (photos, illustrations, logos) | P0 | todo |
| Q3 | Compare output quality against jp2a baseline | P1 | todo |
| Q4 | Tune LLM prompt for better glyph selection | P0 | todo |
| Q5 | Tune density map for better contrast and edges | P0 | todo |
| Q6 | Add examples/ directory with sample outputs | P1 | todo |
