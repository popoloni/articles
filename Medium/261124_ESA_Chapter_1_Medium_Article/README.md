# Seven Green Tests. One Broken Fix.

A standalone English Medium article by Enrico Papalini explaining Chapter 1 of
*Engineering Software with Agentic AI: Reliable Change with Coding Agents*.

## Files

- **article.tex**: editable article, captions and links; the source of truth.
- **layout.tex**: PDF typography and page layout.
- **article.md**: generated Markdown with ordinary image links and alt text.
- **article.pdf**: rendered reading copy.
- **assets/boundaries.jpg**: Treasury rule diagram, 2400 × 1416 pixels.
- **assets/edod.jpg**: Expect–Delegate–Observe–Decide diagram, 2400 × 1560 pixels.
- **artwork/**: editable SVGs, crayon texture swatches and the handwriting font.
- **tools/**: Pandoc filter and Markdown template.
- **build.sh**: rebuilds the Markdown and PDF.

## Medium preparation

Use the title, subtitle and body from **article.md**. Insert the two JPGs where
the corresponding image links occur. Keep each caption under its image and use
the included alt text. The Markdown has no LaTeX commands or math dependencies.
The last section contains a linked invitation to buy the book.

## Rebuild

Install Pandoc 3.x and a TeX distribution with the packages named in
**layout.tex**. Run the following from this folder:

    sh build.sh

This runs Pandoc and two PDFLaTeX passes. The supplied JPGs are sufficient for
the article build; SVG rendering and the handwriting font are not required.

To edit the drawings, install **artwork/type/SketchHand.ttf**, open an SVG in
Inkscape, and retain its sibling **media** folder so the pastel texture references
resolve. The font's license is included in **artwork/type/OFL.txt**. The SVGs
preserve the exact text and diagram geometry.

## Source and editorial decisions

Primary source: *Engineering Software with Agentic AI*, English review edition
5.6.1, 23 November 2026, by Enrico Papalini.

- Chapter 1, “The first accountable change,” pp. 2–15: the negative-amount
  routing case, EDOD, baseline and independent checks, recorded repair,
  counterexamples, decision labels and remaining uncertainty.
- Figure 1.1, p. 3: source for the EDOD drawing.
- Figure 1.2, p. 5: source for the amount-boundary drawing.
- Preface and contents: scope of the twelve chapters, eight missions,
  appendices and companion repository.
- Appendix A, pp. 242–243: checked for consistency with the chapter's decisions.

The article identifies Treasury as a teaching case. The deliberately incomplete
seven-test repair is kept separate from the successful recorded agent repair.
The recorded development selection has twelve methods; its results are not
combined with the seven-case baseline. The EUR 5,000 equality behavior is an
existing promise to preserve. Queue selection does not authorize a payment.

The promotional ending describes the book's contents and includes the purchase
destination supplied for this project. It makes no price or availability claims.

Book: https://www.amazon.com/dp/B0HSPH86CG

Companion: https://github.com/popoloni/esa_ai
