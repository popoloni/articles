# The Economics of AI Loops - Hand-Drawn Edition

This is the complete reproducible source package for the article.

## Figure integration

`src/article.tex` actively includes the ten new architect-style hand-drawn PNG figures from `figures/`.
The former TikZ-derived/rendered PDF include line is retained as a LaTeX comment immediately above each active PNG include.

The earlier package did not contain the underlying inline TikZ environments, only their rendered PDF outputs. Therefore the commented reference is the former PDF include rather than unavailable TikZ source code.

## Build

From the package root:

```bash
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=output src/article.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=output src/article.tex
```

The compiled article is provided at `output/article.pdf`.

## Contents

- `src/article.tex` - updated LaTeX article
- `src/generated_values.tex` - generated numerical macros
- `src/ai_economics_model.py` - reproducible Python model
- `figures/` - ten hand-drawn PNG figures
- `data/` - frozen assumptions and price snapshot
- `output/` - compiled PDF and calculated result tables
- `MATH_MODEL.md` - mathematical model documentation
