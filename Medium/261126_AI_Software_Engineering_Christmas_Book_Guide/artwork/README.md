# Reading-map artwork

`reading-map.svg` is an editable vector diagram with live text. The original handwriting font is not redistributed. Editing in a vector editor may require a compatible locally installed font.

To rebuild both the SVG and the 2600 × 1700 JPEG:

```sh
python3 draw_reading_map.py --render
```

Requires Python, Pillow, Inkscape, and a fontconfig-based render environment. The original font used for the supplied JPGs is not included; install a compatible font locally if you wish to reproduce the exact hand-lettered appearance. Run without `--render` to regenerate only the SVG.

The arrows mark possible starting points from the reader’s question. They do not imply prerequisites or make the separately published Packt volume part of the numbered trilogy.

## Seven book-coverage maps

The coverage figures share the typography, colours and rendering primitives in `coverage_canvas.py`. Each is supplied as an editable SVG and a 2800 x 1800 JPG. Their topic groups are editorial summaries, not chapter-by-chapter sequences.

Rebuild the seven figures with:

```sh
python3 draw_coverage_foundations.py
python3 draw_coverage_practice_loops.py
python3 draw_coverage_originals.py
```

All commands run from this `artwork/` directory and use the same Python, Pillow, Inkscape and fontconfig dependencies as the overall map. The JPGs are written to the sibling `assets/` directory. To regenerate the maps, use an independently installed compatible handwriting font. The shipped JPGs preserve the original text appearance.

| File stem | Book |
| --- | --- |
| `coverage-ndse2` | Non-Deterministic Software Engineering, Second Edition |
| `coverage-ndsdd2` | Non-Deterministic Spec-Driven Development: Enterprise Edition, Second Edition |
| `coverage-agentic-ai` | Engineering Software with Agentic AI |
| `coverage-loop-engineering` | Loop Engineering for AI Agents, separate Packt volume |
| `coverage-ndse-original` | Non-Deterministic Software Engineering, original edition |
| `coverage-ndsdd-original` | Non-Deterministic Spec-Driven Development, original edition |
| `coverage-autonomous-agents` | Non-Deterministic Autonomous Coding Agents |
