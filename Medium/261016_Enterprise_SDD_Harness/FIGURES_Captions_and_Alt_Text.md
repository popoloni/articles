# Figure Captions and Accessibility Text

Use the six numbered diagrams in the article positions indicated by their corresponding INSERT markers. The book cover is a separate editorial image, not Figure 7.

## Figure 1 — Three Shifts in Coding Agents

**File:** `figures/Figure_01_Three_Shifts_in_Coding_Agents.png`

**Caption:** Three complementary shifts in coding-agent architecture. OpenCode emphasizes the service boundary; Copilot separates session hosting from clients; Claude Code emphasizes reusable capabilities and specialist execution contexts.

**Alt text:** Three contemporary coding-agent designs compared: OpenCode as a background service, GitHub Copilot Agent Host, and Claude Code with skills and specialist subagents.

## Figure 2 — OpenCode 2.0 Background Service

**File:** `figures/Figure_02_OpenCode_2_Background_Service.png`

**Caption:** In a service-oriented agent setup, the process with access to files, shell commands, APIs, and credentials is the security boundary that matters. Protecting only the client UI is insufficient.

**Alt text:** OpenCode 2.0: terminal, web, and desktop clients connect to the background agent service, which accesses tools and models; security controls belong at the service boundary.

## Figure 3 — GitHub Copilot Agent Host and AHP

**File:** `figures/Figure_03_GitHub_Copilot_Agent_Host.png`

**Caption:** AHP standardizes client-to-host interaction, not the internal behavior of every agent harness. Copilot retains its own loop, tools, and repository customizations.

**Alt text:** GitHub Copilot architecture: clients communicate with an Agent Host through AHP, while the Copilot harness executes agent loops with models, tools and repository customizations.

## Figure 4 — Claude Code Composable Agent Architecture

**File:** `figures/Figure_04_Claude_Code_Composable_Agents.png`

**Caption:** Claude Code’s native composition model: reusable skills describe capabilities, while subagents isolate specialist work and return results to the parent agent.

**Alt text:** Claude Code: a main agent orchestrates specialist architecture, testing and security subagents, loading project rules and skills and using tools and lifecycle hooks.

## Figure 5 — Enterprise SDD Current Architecture

**File:** `figures/Figure_05_Enterprise_SDD_Current_Architecture.png`

**Caption:** Enterprise SDD’s current architecture, assessed in October 2026. The engineering core is already separate from much of the Copilot-specific customization, but several adapters and workflow entry points need modernization.

**Alt text:** Enterprise SDD current architecture as reviewed October 2026: SDD core, Copilot customizations, generator, multi-provider adapters, modules, and limitations.

## Figure 6 — Enterprise SDD Planned Next Architecture

**File:** `figures/Figure_06_Enterprise_SDD_Planned_Architecture.png`

**Caption:** Proposed architecture for the November 2026 migration. Copilot and Claude Code are the immediate targets; the architecture is intended to accommodate future runtimes without rewriting the engineering contract.

**Alt text:** Proposed Enterprise SDD architecture for November 2026: canonical engineering core, provider-specific generated Copilot and Claude adapters, and independent verification.

## Book cover — Enterprise Edition v2.1 announcement

**File:** `assets/NDSDD_Enterprise_Edition_Cover.jpg`

**Caption:** Cover of *Non-Deterministic Spec-Driven Development: Enterprise Edition*, Second Edition.

**Alt text:** Dark navy book cover reading “Non-Deterministic Spec-Driven Development,” “Enterprise Edition,” “From Public Frameworks to Enterprise Practice,” and the author Enrico Papalini. An orange “Second Edition” ribbon crosses the lower-right corner; a glowing cyan network illustrates the central graphic.

**Amazon:** https://www.amazon.it/gp/product/B0GZZDFMYF

**Note:** The supplied cover is the Second Edition cover. The article announces a minor v2.1 text update, not an altered cover design.
