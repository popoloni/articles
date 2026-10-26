# Figure captions and accessible alt text

All figures are 1672 × 941 PNG (16:9). The alt text is the recommended Medium accessibility description.

## Figure 01. Three Shifts in Coding Agents
- **File:** `figures/Figure_01_Three_Shifts_in_Coding_Agents.png`
- **Placement:** Introduction (after the three developments)
- **Alt text:** Three side-by-side architectures: OpenCode background service, GitHub Copilot clients via AHP to Agent Host, and Claude Code skills and specialized subagents.
- **Caption:** Three complementary shifts in coding-agent architecture. OpenCode emphasizes the service boundary; Copilot separates session hosting from clients; Claude Code emphasizes reusable capabilities and specialist execution contexts.
- **Purpose:** Compare three non-equivalent runtime architecture shifts without implying they share one protocol.

## Figure 02. OpenCode 2.0: The Agent Becomes a Service
- **File:** `figures/Figure_02_OpenCode_2_Background_Service.png`
- **Placement:** 1. OpenCode 2.0 (after service-model explanation)
- **Alt text:** OpenCode 2.0 diagram with terminal, browser and desktop clients connecting to a shared background service, models and tools, with service-level security controls.
- **Caption:** In a service-oriented agent setup, the process with access to files, shell commands, APIs, and credentials is the security boundary that matters. Protecting only the client UI is insufficient.
- **Purpose:** Explain background service, clients, model and tools, and the execution-process security boundary.

## Figure 03. GitHub Copilot: Agent Host & AHP
- **File:** `figures/Figure_03_GitHub_Copilot_Agent_Host.png`
- **Placement:** 3. GitHub Copilot (after AHP distinction)
- **Alt text:** VS Code and other supported clients connect via AHP to an Agent Host with session state and a Copilot harness; repository customizations and tools feed the harness.
- **Caption:** AHP standardizes client-to-host interaction, not the internal behavior of every agent harness. Copilot retains its own loop, tools, and repository customizations.
- **Purpose:** Disambiguate AHP connectivity from the Copilot harness execution loop.

## Figure 04. Claude Code: Composable Agent Architecture
- **File:** `figures/Figure_04_Claude_Code_Composable_Agents.png`
- **Placement:** 4. Claude Code (after subagents explanation)
- **Alt text:** Main Claude Code agent receives a request and delegates separate architecture, testing and security tasks to isolated subagents; skills, rules, tools, MCP and hooks extend execution.
- **Caption:** Claude Code’s native composition model: reusable skills describe capabilities, while subagents isolate specialist work and return results to the parent agent.
- **Purpose:** Explain the main-agent/subagent separation and roles for skills, project rules, MCP, and hooks.

## Figure 05. Enterprise SDD: Current Architecture
- **File:** `figures/Figure_05_Enterprise_SDD_Current_Architecture.png`
- **Placement:** 6. Enterprise SDD today (after inventory)
- **Alt text:** Current Enterprise SDD architecture with .specify core, .github Copilot assets, generator, Claude command adapter, other IDE adapters, modules/extensions, and known migration gaps.
- **Caption:** Enterprise SDD’s current architecture, assessed in October 2026. The engineering core is already separate from much of the Copilot-specific customization, but several adapters and workflow entry points need modernization.
- **Purpose:** Show October 2026 verified separation of engineering core, Copilot customizations, adapters, modules and extensions.

## Figure 06. Enterprise SDD: Planned Next Architecture
- **File:** `figures/Figure_06_Enterprise_SDD_Planned_Architecture.png`
- **Placement:** 7. Planned evolution (after future design)
- **Alt text:** Proposed SDD architecture with provider-independent canonical core, capability-aware adapter generator, Copilot and Claude native adapters, and one shared deterministic verification layer.
- **Caption:** Proposed architecture for the November 2026 migration. Copilot and Claude Code are the immediate targets; the architecture is intended to accommodate future runtimes without rewriting the engineering contract.
- **Purpose:** Show the proposed provider-neutral core, Copilot and Claude adapters, and shared verification.

