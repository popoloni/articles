# The Agent Wrote the Fix. Would You Ship It?

A Medium launch article by Enrico Papalini, on the release of *Engineering Software with Agentic AI* and the new reading order of the Non-Deterministic series.

## Editing and publishing

Edit the article, links, and image captions in `article.tex`. The companion `layout.tex` styles the PDF. `article.md` is the generated Markdown edition, and `article.pdf` is the print preview.

For a Medium draft, use the headline and subtitle from the Markdown edition. Place each JPG from `assets/` at its matching image reference. The description inside square brackets is the alt text, and the following paragraph is the visible caption. The five local image paths continue to work wherever the article and its `assets/` directory are kept together.

## Rebuild

On a system with Pandoc 3.x and a standard TeX Live installation, run `sh build.sh` from this directory. It produces both `article.md` and `article.pdf`. To regenerate just the Markdown, run:

    pandoc article.tex --from=latex --to=gfm --wrap=none --standalone --template=tools/medium.md.template --lua-filter=tools/medium.lua --output=article.md

## Illustration credits

Printed page numbers refer to the English 7 × 10 interiors.

| JPG | Source |
| --- | --- |
| `assets/esa.jpg` | Enrico Papalini, *Engineering Software with Agentic AI*, review edition 5.6.1, ch. 5, fig. 5.2, p. 65. Pen-and-crayon redrawing of the original timeline of two requests reading availability before either writes. |
| `assets/ndse.jpg` | Enrico Papalini, *Non-Deterministic Software Engineering*, Second Edition, English interior 13.7.3, ch. 7, fig. 7.3, p. 98. Original embedded illustration showing independent derivation of the candidate and the test oracle. |
| `assets/sdd.jpg` | Enrico Papalini, *Non-Deterministic Spec-Driven Development: Enterprise Edition*, Second Edition, v2.1 package, ch. 12, fig. 12.4, p. 205. Pen-and-crayon redrawing of the original artefact chain in the English hardcover. The checkout cross-check is on p. 204. |
| `assets/esa-overview.jpg` | Enrico Papalini, *Engineering Software with Agentic AI*, review edition 5.6.1, “How to use this book,” fig. F.1, printed p. viii. Hand-lettered adaptation of the overview of five parts, twelve chapters and two four-mission practice routes. The reading advice draws on the preface and pp. vii–ix. |
| `assets/reading-guide.jpg` | An original three-row comparison table created for this article, drawn in the same pen-and-crayon style. |

## Editable artwork

The workshop timeline, artefact chain, book overview and reading guide have editable SVGs in `artwork/`. Their pen outlines and lettering are separate from the four crayon textures in `artwork/media/`. The original illustration from *Non-Deterministic Software Engineering* is supplied as the published JPG.

To edit or export an SVG, install the bundled SketchHand typeface from `artwork/type/` and keep the `media/` folder alongside the SVGs. The lettering is based on EMS Tech, derived from Kimberly Geswein's Architects Daughter. The license is included with the font. The crayon shading was generated for this article using the blue panel in the original book illustration as its visual reference.

The PDF and Markdown use the ready-to-publish JPGs in `assets/`. Rebuild them with `sh build.sh` after changing the article or replacing a JPG.
