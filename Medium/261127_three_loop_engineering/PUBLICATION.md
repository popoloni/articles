# Medium publication notes

**Title:** Beyond the Loop: The Three-Loop Architecture for AI Agents

**Subtitle:** How to engineer systems that execute, measure progress, and improve their own engineering methodology

**Suggested tags:** Agentic AI, Software Engineering, AI Agents, Spec Driven Development, Artificial Intelligence

**Suggested LinkedIn announcement**

An AI agent that fixes the same category of bug every night may deliver software — and still learn nothing about how to deliver software.

In my new article I propose a three-loop architecture for non-deterministic software engineering: execution changes the software; progress control changes the strategy; learning changes the methodology, subject to evidence, evaluation and authorization.

The companion is a runnable Python reference: a controlled replay, a diagnostic probe, a policy change derived from training evidence, paired evaluation on held-out tasks, single-use promotion and rollback. A small demonstration, not a benchmark of model intelligence.

The objective is not to engineer agents that never fail, but to engineer systems that extract value from failure without endlessly paying for it.

[Insert actual Medium article URL after publication.]

The loops underneath this architecture (contracts, economics, the Ralph controller, a full local AI loop) are covered in my book Loop Engineering for AI Agents, published by Packt: https://www.packtpub.com/en-it/product/loop-engineering-for-ai-agents-9781808766404

## Before publication

1. **Companion URL.** Publish this folder as its own public repository (not the book repository) and replace `COMPANION_URL` in the final section of `article.md` with its address. Add a license file to the repository first (for example MIT or Apache-2.0); without one, readers have no right to reuse the code.
2. **Figures.** Upload the four PNGs from `figures/` at the marked points. All are original diagrams, not reproductions of Sam Iso's image.
3. **Tables.** Medium has no table support; pasted Markdown or HTML tables collapse into plain lines. Insert the images from `figures/tables/` instead (`table_01.png` = the L1/L2/L3 table in section 2, `table_02.png` = the rounding examples in section 4, `table_03.png` = the held-out results in section 7). Use the table's content as the image alt text. Regenerate them with `figures/build_tables.py` if the tables change.
4. **Byline.** Remove the `**Enrico Papalini** · November 2026` line when pasting; Medium shows author and date itself.
5. **People and links.** Sam Iso's profile (linkedin.com/in/sam-iso) is confirmed; as a courtesy, tell him he is mentioned, and add the original post URL if available. Click the Packt book link once more: it could not be checked automatically (the site blocks automated requests).
6. **Keep the limits.** Keep the controlled-replay disclaimer, the "numbers follow from the design" paragraph, the live-adapter limitation and the difference between attempt counts and money.
7. **Book call to action.** The closing section "Go deeper: Loop Engineering for AI Agents" is the article's final CTA; keep it directly after the closing line and before the companion section. In Medium, make the "→ Get Loop Engineering for AI Agents from Packt" line a standalone paragraph so it reads as a button-like link. Optionally add the book cover image (from Packt's media kit) above it.
8. **Final pass in Medium.** Check code-block formatting, captions and the superscript in "2⁵³".

## Rebuilding

```sh
./reproduce_results.sh          # tests + demo + promote/run-active/rollback into results/
figures/build_figures.sh        # diagrams (Graphviz) + Figure 4 (matplotlib)
python3 figures/build_tables.py # Medium table images (Playwright, optional)
./build_article.sh              # article.html (Pandoc)
```
