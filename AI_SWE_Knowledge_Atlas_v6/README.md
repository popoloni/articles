# AI & Software Engineering — Knowledge Atlas
## Single-file explorer · audited v6 · 11 October 2026

Open **AI_SWE_Knowledge_Atlas_v6.html** in a current desktop browser. The application, styles, original graph attributes and display data are embedded in that one file. No server, installation, login, API key, external font, library or CDN is required for exploration. Opening a source's external article link requires an internet connection. This package does not modify the book or the original graph.

## Starting view

The page always starts with **W001–W193**, the original 193-document Polimi collection, arranged by the nine Polimi thematic streams. O and P sources and structural/audit nodes start hidden. The 64 remaining direct W-to-W relationships are visible; the 637 dense inferred-similarity links start hidden. This is a visibility choice, not deletion of relationships.

The embedded graph contains **881 nodes, 5,860 directed keyed edges and 218 relationship types**. Its 366 source records consist of W193, O50 and P123; another 515 records describe topics, chapters, sections, teaching, claims, provenance and audit matters.

## Sources, groups and filters

Use **Scope** to toggle the W, O and P collections independently. O identifies Addy Osmani; P identifies The Pragmatic Engineer / Gergely Orosz and contributors. Neither prefix is an evidence-quality score.

The top **Group by** control switches between Polimi streams, book chapters, source collection and an ungrouped view. Check or uncheck groups to choose a subset. A theme filter matches primary OR secondary membership. A multi-topic source appears only once, in its first eligible selected group; sidebar counts can overlap while graph counts do not. A grouping rectangle is a visual aid, not an invented graph node.

For book chapters, choose between **Editorial mapping (including proposals)** and **Actual v6 chapter citations**. The latter is derived exclusively from the graph's `CITED_IN_CHAPTER_BUNDLE_V6` edges. Bibliography inclusion and a proposed chapter placement do not become chapter citations. Unassigned sources have a separate group instead of being silently dropped. The same one-position-per-source rule applies to chapter layout.

Additional switches limit the view to the 223 printed W/O/P source identifiers or hide the 15 retitled Pulse-derived P excerpts (the strict P view has 108 articles). Search accepts stable IDs, titles, authors and source descriptions. The Results tab offers a searchable, keyboard-focusable alternative to selecting small canvas labels.

Expand **Context nodes** to add any of eight structural categories. **Group hubs** adds the actual theme/chapter hub records for the active grouping and exposes their original relationships. All context + all collections + all relationship types displays the entire graph.

## Every relationship is independently controllable

The **Relationships** tab contains a checkbox for each of the **218 original relation types**, grouped into nine collapsible UI families. A family switch changes all its types; use All, None, Readable or name search for faster selection. Counts show what is visible and what exists in the full payload.

An edge appears only when its type is enabled and both endpoints are in the current view. Turning classification edges off does not erase the source's membership metadata. Some classes connect documents to context records, so enable the corresponding context category to see them. No thematic similarity, chapter membership or other synthetic relationship is added merely to make the picture denser.

Click an edge for its direction, original relation type, keyed identity and available provenance. Parallel original relationships are retained. Some links necessarily share visual space in a dense view; the node inspector's connection list gives an unambiguous alternative to clicking canvas lines. Dashed styling distinguishes inferred/editorial/proposed kinds where identifiable; the original relation type remains authoritative.

## Dragging, zoom and layout

- Drag a node to move it. It is pinned by default so later layout passes preserve your placement; double-click it to toggle its pin.
- Drag blank canvas to pan. Scroll or pinch to zoom; Fit and +/− controls are also available.
- Use **Auto-layout** to re-arrange visible, unpinned nodes. **Release all pins** first when you want the layout to move everything.
- Select IDs only, IDs plus titles, or hidden labels in Display & layout. Group boundaries, arrows, edge opacity and isolated-node visibility are configurable.
- Select a source and focus one or two hops of its currently enabled relationships. Hidden-neighbor entries can be explicitly revealed; this clears restrictive filters as reported by the interface.

The layout uses group-aware placement, force relaxation, rectangular collision separation and a final clearance pass. It runs in an embedded local worker, with a main-thread fallback. The tested unpinned W193, full-source366 and full881 layouts have zero intersecting node boxes. This does not promise a crossing-free drawing or automatic resolution of overlaps between intentionally pinned nodes. Larger views need zooming; ID-plus-title labels and the inspector are usually easier to read on a filtered subset.

## Details, export and saved views

Click a source for its title, attribution, annotation, evidence limitations, source link, thematic memberships and separate actual/proposed chapter information. Original graph attributes remain available in the inspector. Click a connection to inspect its own original metadata.

**Export** saves the current view as JSON, the visible subgraph as JSON, the complete original graph as JSON, or the current graph drawing as vector SVG. A saved view includes filters, positions, pins and the camera. Load it through the same menu. The saved view must carry the exact original graph fingerprint; an incompatible file is rejected without changing the view. Reopening the HTML restores the W193 startup instead of silently restoring a previous session.

Keyboard shortcuts: **/** search, **F** fit, **L** layout, **P** toggle the selected node's pin, **Esc** close a dialog or details. Use the visible clear-focus control to leave a neighborhood view. Shortcuts do not interfere with typing into a text field.

## Provenance and editorial boundaries

The graph is the audited W193/O50/P123 v6 file supplied with the 231-page book. Every original node attribute, edge endpoint, edge key, edge attribute and graph-level attribute is preserved in the payload and full JSON export. UI group families, display labels and source summaries are explicitly additional presentation data.

Current chapter labels and printed-source flags were read from the matching v6 LaTeX source package and `graph/CURRENT_SOURCE_CATALOGUE_V6.json`. Historical labels and audit states remain unchanged in raw graph attributes. Restricted P-source content, unresolved source discrepancies, original study replication and the real production pilot remain open. This browser does not establish independent validation of the cited claims.

Original graph SHA-256:
`2a68d3a04fbe9a5e940fb2ae9f05b98f63de05ac653c86cf1efe38403a85232a`

## Editable source and verification

`src/template.html` contains the page and CSS; `src/app.js` contains the renderer, controls, layout and exporters; `src/graph_data.json` contains the frozen display payload. Rebuild using Python 3.10+ and only the standard library:

```sh
python src/build.py
# Alternatively:
python src/build.py --output my-atlas.html
```

The bundled original GraphML is under `data/`. The builder is intentionally not a generic importer for arbitrary future graph schemas; it rebuilds this verified payload. To substitute another graph edition, regenerate and review its display metadata and mapping rules, then retest. Merely renaming an input is insufficient.

`qa/QA_REPORT.json` records 51 functional checks, including exact isolated counts for every one of the 218 relation controls. `qa/EXTRA_QA_REPORT.json` records 12 further fidelity and interaction checks. Screenshots document desktop and mobile-emulated views. The included test scripts require Python, NetworkX, Playwright and Chromium; the application itself does not.

```sh
python -m pip install networkx playwright
python -m playwright install chromium
python tests/test_atlas.py
python tests/extra_qa.py
```

Set `CHROMIUM_EXECUTABLE` to use a locally installed Chromium binary. Test results are written to `qa_rerun/`, leaving the delivered reports unchanged.

Tests were performed in system Chromium 144 with HTTP(S) networking disabled, using the exact HTML content. The test environment blocks `file://` navigation by administrative policy, so the document was loaded into an offline browser page rather than through that URL scheme. Blob URLs in network logs are local embedded layout workers, not external requests. Mobile results are emulation, not physical-device certification. Other browser engines were not independently tested.

`FILE_HASHES_SHA256.txt` covers the delivered files except itself. The HTML inside the package is byte-identical to the separately supplied HTML.
