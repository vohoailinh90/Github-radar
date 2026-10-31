# Reports

Hand-written learning reports about one or more repositories each, kept beside the pipeline's generated digests. They are not
produced by `radar.py`, they are not under `digests/` or `export/studio/`, and nothing here is handed to the studio.

Each report is a folder:

| File | What it is |
|---|---|
| `report.md` | The report in Vietnamese. Every claim carries a `[Sn]` label that resolves to a file of the studied repository at a pinned commit. |
| `slides.json` | The slide plan: title, section, sources, layout, tone, speaker notes. The deck is drawn from this and adds no idea of its own. |
| `<name>.pptx` | The deck, drawn on Moda from `slides.json` and exported as PPTX. |
| `deck.json` | The Moda canvas link, how many pages it has, the hash of the `slides.json` it was drawn from, and the studied commit. |

| Report | Studied repository | Commit |
|---|---|---|
| [genai-agents](genai-agents/report.md) | [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) | `1b45571` (2026-10-17) |
| [github-top3](github-top3/report.md) | build-your-own-x, awesome, public-apis | 2026-10-23 snapshot; [source pins](github-top3/sources.json) |
| [awesome-handbook](awesome-handbook/report.md) | [sindresorhus/awesome](https://github.com/sindresorhus/awesome) | `bc98e51`; 8 chapters / 16 lessons (2026-10-24) |
| [top30-claude-plugins](top30-claude-plugins/report.md) | the 30 repos of the "Top 30 Claude Code Plugins" image | READMEs read 2026-10-25; [source pins](top30-claude-plugins/sources.json); 55-page deck |
| [archify](archify/report.md) | [tt-a1i/archify](https://github.com/tt-a1i/archify) | `51a2917` (2026-10-25); 48-page deck |
| [graphify](graphify/report.md) | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | `0a8cd4e` (2026-10-27); 32-page deck; not yet reviewed by the VPS team |

Before starting or changing a report, claim its folder (`python3 scripts/claim.py claim docs/reports/<name>`, see [`docs/claims.md`](../claims.md)): several Claude or Codex sessions can work here at once, and the claim is what keeps two of them from building the same report, or two Moda canvases for it. `deck.json` holds the canvas link: edit that canvas, never create a second.

| [build-your-own-x](build-your-own-x/report.md) | [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) | `aa17439`; overview / 31 groups (2026-10-24) |

The format follows [vohoailinh90/Multiple-report](https://github.com/vohoailinh90/Multiple-report): a lesson, a slide plan and a Moda deck,
checked by a structure gate (sections in order, every `[Sn]` listed and used, slide layouts and text sizes).
