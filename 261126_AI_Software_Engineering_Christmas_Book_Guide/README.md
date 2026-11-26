# AI Software Engineering — The Christmas Book Guide

## Publication package

An English article by Enrico Papalini introducing the Non-Deterministic series to readers who do not already know its books. It follows the question-led approach of the public four-volume reading guide and includes Amazon buying links.

The article preserves the current trilogy order, explains the separately published Packt companion, and identifies the original three books as optional branches. The cancellation example is an editorial illustration, not a reported book experiment or production case.

## Files

- `article.tex`: canonical editable article, captions and links.
- `layout.tex`: PDF typography and layout.
- `article.md`: generated Markdown for editing or adapting to Medium.
- `article.pdf`: rendered reading copy.
- `assets/reading-map.jpg`: overall reading map, 2600 x 1700 pixels.
- `assets/coverage-*.jpg`: seven detailed book-coverage illustrations, each 2800 x 1800 pixels.
- `assets/banners/01_*.jpg` through `07_*.jpg`: seven English square introductory cards (2160 x 2160), each placed before its book’s detailed illustration.
- `assets/covers/cover-*.jpg`: seven authentic English front covers, with native dimensions and provenance in `assets/covers/SOURCES.md`.
- `artwork/*.svg`: editable vector versions of all eight figures.
- `artwork/draw_reading_map.py`: overall-map generator.
- `artwork/draw_coverage_foundations.py`: the two current foundation/specification maps.
- `artwork/draw_coverage_practice_loops.py`: the practical-agent and Packt runtime maps.
- `artwork/draw_coverage_originals.py`: maps for the original three series volumes.
- `artwork/coverage_canvas.py`: shared pen-and-crayon rendering primitives.
- `tools/`: Markdown conversion template and caption/alt-text filter.
- `SOURCES.md`: source and purchase-link verification notes.
- `CHANGELOG.md`: revision record.

The eight original editorial illustrations use pen lettering and blue/orange crayon strokes on white paper. The seven English square banners add navy framing and a compact chapter-orientation map. Seven English square topic banners now open each book section, followed by the seven original detailed maps. The overall map is retained, for fifteen images appearing in the article; the seven separate official English covers remain available as source assets. Every image has an accessible description in the Markdown, and each square banner links to the corresponding Amazon edition. The current trilogy and the separately published Packt companion remain distinct; the original series volumes retain positions four through six.

The banners are didactic section openers, introducing one key question and the broad scope of the book. The detailed coverage pictures remain editorial summaries of each book's topics. They do not replace the contents pages or imply that the depicted topic groups are the books' chapter sequence. Source links appear in their captions.

## Rebuild the article

Dependencies: Pandoc 3.x and a complete LaTeX installation with pdfLaTeX and the packages named in `layout.tex` (including Charter, Latin Modern, graphicx, caption, float, fancyhdr, titlesec and hyperref).

From this directory:

```sh
sh build.sh
```

The build regenerates the Markdown from LaTeX, then compiles the PDF twice. All figures are already rendered and do not need rebuilding for text-only edits.

For the figures’ optional regeneration requirements and commands, see `artwork/README.md`.

## Use on Medium

Copy the article text from `article.md` or your preferred Markdown editor. Upload the fifteen JPGs actually referenced in the article: the overall reading map, seven square English introductory banners in `assets/banners/`, and seven detailed maps in `assets/`. Follow the order in Markdown and retain the paired captions. Each banner already contains its book cover; do not insert the separate miniature cover a second time. The seven original standalone covers remain as supplementary source assets only. Confirm image links, captions and Amazon links after importing to Medium. Markdown conversion does not publish the article or upload its images to Medium automatically.

The separately downloadable Markdown uses the same `assets/` paths. Extract the JPG archive alongside it, preserving the `assets/` directory, to resolve those images locally.

Use the editable LaTeX source for subsequent revisions, then rebuild both outputs so that the versions remain aligned.

English banner + detailed-map educational revision prepared 26 November 2026.

**Font distribution:** this package intentionally does not include any font files. The exported JPG diagrams retain their original typography. Editable SVGs and authoring scripts are provided for further adaptation, but regenerating identical lettering may require a compatible font installed independently.
