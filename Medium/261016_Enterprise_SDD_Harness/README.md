# Enterprise SDD Medium Article Package — v3

## Main content

- `ARTICLE_Medium_Paste_Ready.md` — complete article with Medium-friendly INSERT markers for six diagrams and the supplied book cover.
- `ARTICLE_Medium_with_Figures.md` — same article with relative links to all seven image assets for Markdown publishing and preview.
- `BOOK_UPDATE_Section_Only.md` — copy-ready v2.1 announcement block.

## Media

- `figures/Figure_01_*.png` to `figures/Figure_06_*.png` — six original landscape architecture/overview diagrams (unchanged from v2).
- `assets/NDSDD_Enterprise_Edition_Cover.jpg` — original user-supplied front cover, kept unchanged.
- `FIGURES_Captions_and_Alt_Text.md` — captions and accessibility descriptions for all seven media assets.

## Editorial provenance

v3 is based on the most recently user-edited article (including the revised **vendor lock-in** title and the added sections on harness dependency and portability). It is **not** based on the older v2 article narrative.

The only substantive new article addition is the short book notice in the final section, clarifying:

- The user's announcement of a **minor v2.1** update to *Non-Deterministic Spec-Driven Development: Enterprise Edition*.
- The focus on **readability**, with continued support for the Enterprise SDD framework.
- The distinction between a book editorial update and the **still-planned** November Copilot/Claude harness migration.

Product link: https://www.amazon.it/gp/product/B0GZZDFMYF

## Publishing workflow

1. Open `ARTICLE_Medium_Paste_Ready.md`.
2. Copy the article into the Medium editor.
3. At each image marker, insert its image from `figures/` or `assets/` and place the existing caption underneath.
4. Review title, links, copyright, image spacing, and alt text.
5. Use `ARTICLE_Medium_with_Figures.md` if Markdown-compatible image links are supported by the publishing workflow.

All six diagrams preserve their pre-existing numbering and the book cover remains separately identified, preventing broken Figure 1–6 references.

## Validation

- All image references, source file paths and placeholders are checked by the build script.
- The ZIP includes `MANIFEST.sha256` with hashes of the distributed files.
- No changes are made to `github.com/popoloni/enterprise-sdd`.

