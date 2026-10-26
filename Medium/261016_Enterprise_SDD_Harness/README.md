# Enterprise SDD — Agent Harnesses / Medium Publication Package

**Release:** November 2026 article edition v2 · **Prepared:** 26 October 2026

This package contains the complete English-language Medium article, six consistent architecture diagrams, accessibility captions, research links, and publication guidance. It updates the prior four-figure package by adding OpenCode 2.0 and a three-paradigm introduction.

## How to publish

1. Open `ARTICLE_Medium_Paste_Ready.md` and paste the prose into the Medium editor. Medium will not resolve image paths from a local ZIP.
2. At each `[INSERT FIGURE XX HERE]` marker, upload the corresponding PNG from `figures/`.
3. Copy the caption immediately following the marker; apply the corresponding alt text from `FIGURES_Captions_and_Alt_Text.md`.
4. Alternatively, use `ARTICLE_Medium_with_Figures.md` in a Markdown editor/GitHub repository: its links refer to local `figures/` assets, all present in the ZIP.
5. Suggested cover/lead visual: `figures/Figure_01_Three_Shifts_in_Coding_Agents.png`. The remaining five figures should appear in their respective sections, not as a single composite image.

## Publication metadata

**Title:** Coding Agents Are Becoming Infrastructure: OpenCode 2.0, GitHub Copilot, Claude Code, and the Next Enterprise SDD

**Subtitle:** As November 2026 approaches, coding agents are changing in ways that go far beyond model benchmarks. Three different architectures show why the next generation of software engineering frameworks must separate execution from engineering authority.

**Suggested Medium topics/tags:** AI Agents · Software Engineering · GitHub Copilot · Claude Code · Developer Tools. If you prefer an OpenCode-focused tag, replace Developer Tools with OpenCode.

**Links:** https://github.com/popoloni/enterprise-sdd ; https://medium.com/towards-artificial-intelligence/opencode-2-0-turned-your-coding-agent-into-a-daemon-4663135862c4

## Included files

- `ARTICLE_Medium_with_Figures.md` — full article, including valid relative Markdown images.
- `ARTICLE_Medium_Paste_Ready.md` — identical article text, with explicit Medium image insertion markers.
- `figures/Figure_01_*.png` — overview comparison: OpenCode, Copilot, Claude.
- `figures/Figure_02_*.png` — OpenCode v2 shared service and execution boundary.
- `figures/Figure_03_*.png` — Microsoft Copilot Agent Host/AHP model.
- `figures/Figure_04_*.png` — Claude Code skills and subagents.
- `figures/Figure_05_*.png` — Enterprise SDD current architecture.
- `figures/Figure_06_*.png` — planned native-adapter architecture.
- `FIGURES_Captions_and_Alt_Text.md` — descriptive captions and accessibility text.
- `SOURCES_and_Fact_Check.md` — official documentation and factual cautions.
- `CHANGELOG.md`, `ASSETS.csv`, `MANIFEST.sha256` — revision tracking and asset verification.

## Scope statement

The article announces a planned November 2026 modernization of **GitHub Copilot and Claude Code integration**. OpenCode 2.0 is introduced to illustrate the broader industry shift toward service-based agent runtimes; there is no claim that Enterprise SDD already supports OpenCode 2.0 natively or that an OpenCode adapter is a committed November deliverable.

The four original figures have been retained, only renumbered to make room for the two new OpenCode-oriented images. The current/future Enterprise SDD pair continues to clearly distinguish *verified current* from *planned future*.

No changes have been pushed to the Enterprise SDD GitHub repository.
