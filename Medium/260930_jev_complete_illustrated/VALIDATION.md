# Validation — complete illustrated package

Prepared on 30 September 2026. This is an illustration and packaging update to the supplied essay; no new web/source audit was performed.

## Essay and figures

- Seven PNG figures are present under `figures/`, not merely linked to an external library.
- All seven are inserted at relevant sections in `essay.md`, with numbered captions and valid relative image paths.
- Each PNG was decoded and its integrity checked. Images are 2,700 pixels wide.
- The original manuscript body and code blocks are unchanged apart from the addition of image/caption blocks.
- All 20 original code/data assets checked against the earlier package are byte-identical.
- `essay.html` references the packaged PNGs. `essay-standalone.html` embeds all seven image files as data URIs; their decoded bytes match the PNGs exactly.
- Chromium rendered the standalone document at desktop (1,440 px) and mobile (390 px) viewport widths: seven images loaded in each, no external asset requests and no horizontal page overflow. Content was injected directly with Playwright because this container restricts file and local-URL navigation.
- Figure exports and representative article screenshots were visually inspected for layout and text overlap.

## Code checks rerun for this package

- Original response-contract tests: **16 passed**.
- Bridge, request-validation and protocol tests: **21 passed**.
- JavaScript simulation/freshness tests: **12 passed**.
- Total: **49 model-free automated tests passed**. Logs are included under `validation/`.
- Python parsing, JSON parsing, shell syntax and JavaScript syntax checks passed.

## Archive checks

The final ZIP is tested for CRC errors, extracted into a fresh directory, and its SHA-256 manifest and seven Markdown image references are checked against the extracted files.

## What was not tested

No model inference, model download, new browser-game benchmark, physical-Mac benchmark, calibration experiment or current-version compatibility test was performed during this packaging update. The illustrations are explanatory schematics, not measured model outputs. The runtime's prior browser-game tests used synthetic replies; those earlier observations are not new inference measurements.
