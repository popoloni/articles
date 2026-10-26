# Coding Agents Are Becoming Infrastructure: OpenCode 2.0, GitHub Copilot, Claude Code, and the Next Enterprise SDD

*As November 2026 approaches, coding agents are changing in ways that go far beyond model benchmarks. Three different architectures show why the next generation of software engineering frameworks must separate execution from engineering authority.*

For a while, the most common question about AI-assisted development was simple: **Which model writes better code?**

It is still a relevant question. But increasingly, I find myself asking a different set of questions. Where does the agent actually run? What happens when I close the terminal or the editor? Who decides which tools it can use? How are specialist agents coordinated? And what evidence remains when the conversation is over?

Three developments in 2026 help explain the shift.

In October, [Najam Us Saqib's article *OpenCode 2.0 Turned Your Coding Agent Into a Daemon*](https://medium.com/towards-artificial-intelligence/opencode-2-0-turned-your-coding-agent-into-a-daemon-4663135862c4) drew attention to OpenCode's move toward a shared background service. In August, Microsoft introduced the [Agent Host and Agent Host Protocol (AHP)](https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture) for sessions that can be accessed from multiple clients. Meanwhile, [Claude Code](https://code.claude.com/docs/en/features-overview) has developed a rich model for combining project instructions, reusable skills, isolated subagents, MCP tools, and lifecycle hooks.

These are **three different architectural choices**, not three names for the same feature. Taken together, they indicate that the coding assistant is turning into a software execution environment in its own right.


**[INSERT FIGURE 01 HERE — upload figures/Figure_01_Three_Shifts_in_Coding_Agents.png]**


*Figure 1. Three complementary shifts in coding-agent architecture. OpenCode emphasizes the service boundary; Copilot separates session hosting from clients; Claude Code emphasizes reusable capabilities and specialist execution contexts.*

That matters to **[Enterprise SDD](https://github.com/popoloni/enterprise-sdd)**, the open-source Spec-Driven Development framework I have been evolving to connect requirements, architecture, implementation, testing, and evidence. Beginning in November 2026, I plan to modernize its GitHub Copilot and Claude Code integrations around these native harness models.

To understand the migration, it helps to unpack what has changed.

## 1. OpenCode 2.0: the interface is no longer the execution boundary

Imagine that you open a terminal, start a coding assistant, ask it to examine a repository, and then close the terminal. In the traditional mental model, the terminal session and the assistant's execution environment are nearly the same thing.

OpenCode 2.0 makes that mental model less useful.

Its current architecture includes a **shared background service** to which interfaces such as the terminal UI, web interface, and desktop app can connect. The service owns session management and exposes an API. There is also a standalone server mode for dedicated local or remote setups. According to the [OpenCode v2 documentation](https://opencode.ai/v2/docs/cli/web/), the background service can be managed with commands such as `opencode service start` and `opencode service status`; `opencode serve` runs a foreground instance instead.

One nuance matters: **OpenCode did not invent client/server agents in version 2.** OpenCode v1 already had client/server capabilities. The v2 design makes the shared-service operating model much more central to everyday use, while changing aspects of the server API and integration contracts. The [official v1-to-v2 migration guidance](https://dev.opencode.ai/v2/docs/migrate-v1/) makes this distinction clear.


**[INSERT FIGURE 02 HERE — upload figures/Figure_02_OpenCode_2_Background_Service.png]**


*Figure 2. In a service-oriented agent setup, the process with access to files, shell commands, APIs, and credentials is the security boundary that matters. Protecting only the client UI is insufficient.*

This separation improves continuity and supports multiple clients, but it also changes the security discussion.

If the agent's file-system access, tool execution, and credentials belong to a separate process, sandboxing only the terminal interface does not necessarily constrain that process. Isolation, authorization, network exposure, and tool policy have to be applied **where execution occurs**.

That is not an assertion that OpenCode is insecure by default. Its v2 documentation describes local binding and authenticated access, while remote pairing requires deliberate configuration. The lesson is architectural: the security boundary follows the executing service, not the window used to control it.

An article about a daemonized coding agent is therefore also an article about enterprise governance. Who owns the process? Under which OS identity does it run? Which repository and external systems can it reach? How is a denied operation enforced regardless of which client requests it?

The same questions are beginning to matter across agent systems.

## 2. First distinguish the model, the agent, the harness, and the host

Before going further, a little terminology prevents a surprising amount of confusion.

A **model** supplies the reasoning capability. An **agent** uses that capability within a task-oriented loop, with instructions and tools. A **harness** manages the loop: preparing context, invoking the model, executing authorized tool requests, observing results, and continuing or stopping. A **host** manages the lifecycle and connectivity of agent sessions; the precise division of responsibilities depends on the product.

One more layer sits outside this runtime architecture: an **engineering framework**. It defines what is expected, what is allowed, what evidence must be produced, and what counts as satisfactory completion.

Those are not interchangeable responsibilities.

A powerful model does not automatically imply safe tool permissions. A persistent session does not establish that its context is fresh. A specialist subagent does not make its findings independently verified. And a successful agent loop does not prove that the implementation meets the original business requirement.

This is why the changes in Copilot and Claude Code are so relevant to Enterprise SDD.

## 3. GitHub Copilot: the Agent Host and AHP

Microsoft's August 2026 announcement introduced an **Agent Host**, a dedicated process that owns agent sessions, alongside the **Agent Host Protocol (AHP)**, through which compatible clients interact with that host.

Instead of tying an agent session to one VS Code extension-host process, a session can remain accessible across supported VS Code surfaces, the Agents window, and properly configured remote clients. It remains dependent on the host process and its environment, of course; it is not magical indefinite background execution.

The critical architectural distinction is this:

**AHP connects clients to sessions. The agent harness performs the work.**

Within the Agent Host, the GitHub Copilot harness uses the Copilot SDK to run the model/tool loop. The host can also accommodate other harnesses through adapters, without making their tools and behavior identical.


**[INSERT FIGURE 03 HERE — upload figures/Figure_03_GitHub_Copilot_Agent_Host.png]**


*Figure 3. AHP standardizes client-to-host interaction, not the internal behavior of every agent harness. Copilot retains its own loop, tools, and repository customizations.*

The surrounding customization model is evolving as well.

In the new Copilot harness, reusable workflows are increasingly packaged as **Agent Skills**, typically located under `.github/skills/<name>/SKILL.md`, while custom agents and scoped instructions remain native building blocks. Microsoft's [customization migration guide](https://code.visualstudio.com/docs/agent-customization/migrate-customizations) states that Copilot harness sessions do not load legacy `*.prompt.md` workflows; those remain available in the older Local harness.

That migration cannot be treated as a mechanical rename. A manually invoked prompt can become a skill the model discovers automatically. Microsoft therefore makes converted skills explicitly invoked by default and cautions that prompt-specific selections of agent, model, and tools are not automatically preserved.

For a casual workflow, this may be an inconvenience. For an enterprise implementation, review, or release workflow, it can be a governance defect. **Discoverability and authorization are different things.**

## 4. Claude Code: skills, subagents, and composable execution

Claude Code illustrates another aspect of the change: **how to structure the work happening inside an agent environment**.

Its extensibility model distinguishes persistent instructions, skills, subagents, tools exposed through MCP, hooks, and plugins.

A `CLAUDE.md` file provides project conventions. Scoped rules add contextual instructions. A skill, usually under `.claude/skills/<name>/SKILL.md`, packages a reusable procedure or body of knowledge. A subagent under `.claude/agents/` can have its own system instructions, tool permissions, model choice, and isolated context.

Imagine a developer asking for a modification to a settlement system. A main agent could request an architectural impact review, a test strategy, and a security analysis from distinct specialist subagents. Each subagent works with a more focused context and returns its findings. The main agent then decides how to proceed.

That is **not** the same as launching three copies of an identical prompt. It is a way of separating responsibilities, context and permissions.


**[INSERT FIGURE 04 HERE — upload figures/Figure_04_Claude_Code_Composable_Agents.png]**


*Figure 4. Claude Code's native composition model: reusable skills describe capabilities, while subagents isolate specialist work and return results to the parent agent.*

There is an important limitation. Subagent isolation is useful, but does not prove independence or correctness. Reviewers can share mistaken assumptions. A test agent can accidentally confirm the implementation it is supposed to challenge. Evidence still needs to be checked against an authoritative specification.

Also, **running a Claude-family model in Copilot is not the same as running Claude Code**. The model family might be identical, but the harness may differ in context assembly, tools, permissions, skill loading, and delegation semantics.

These distinctions explain why a mature framework needs more than a generic mapping from one model name to another.

## 5. What the three paradigms have in common

OpenCode, Copilot, and Claude Code are not converging on one universal internal architecture. Instead, they make three boundaries more visible:

- **Interaction is not execution.** The terminal, editor or web client is not necessarily the process that can modify code and run tools.
- **Reasoning is not orchestration.** Models make proposals; harnesses control loops, sessions, skills, tools, and delegation.
- **Execution is not engineering acceptance.** A task completed by an agent still needs requirements, constraints, verifiable tests, approvals, and evidence.

I regard the third boundary as the most important for enterprise teams.

It is also the reason I started working on Enterprise SDD.

## 6. Enterprise SDD today: engineering artifacts before conversations

[Enterprise SDD](https://github.com/popoloni/enterprise-sdd) is built around a relatively simple principle: **the authoritative software-development state should live in persistent artifacts, not solely in an assistant's conversation**.

The current framework supports six lifecycle phases: Foundation, Requirements, Design, Preparation, Implementation, and Quality Assurance. Four quality gates evaluate specification completeness, design completeness, implementation readiness, and release readiness.

The `.specify/` directory contains the constitution, structured specifications, templates, memory, Python CLI, scripts, and validation tools. The `.github/` directory contains Copilot-oriented agent definitions, instructions, prompts, and skills. Optional `.sdd-modules/` and `.sdd-extensions/` provide domain-specific knowledge and workflow variations. MCP servers connect to systems such as Jira, Confluence, and specification memory.

There is already a multi-provider adapter generator for Copilot, Claude Code, Cursor, Windsurf, and Codex.

In the repository examined on 26 October 2026, the Copilot layer contained **16 agent files, 53 instruction files, 34 core prompt workflows, and 32 skill definitions**. With optional module and extension assets included, the broader repository held 92 prompt templates.


**[INSERT FIGURE 05 HERE — upload figures/Figure_05_Enterprise_SDD_Current_Architecture.png]**


*Figure 5. Enterprise SDD's current architecture, assessed in October 2026. The engineering core is already separate from much of the Copilot-specific customization, but several adapters and workflow entry points need modernization.*

This is a useful foundation, not an obsolete system. The CLI and deterministic gates already give it a degree of independence from any single IDE.

But the harness evolution reveals specific gaps.

Some core workflows still depend directly on `.github/prompts/*.prompt.md`. Many skill files need stronger native metadata validation. The existing Claude adapter creates `.claude/commands/*.md` and a `CLAUDE.md` summary, rather than fully realized specialist subagents with complete role behavior. The canonical agent inventory also requires reconciliation: for example, `security-reviewer.agent.md` exists in the Copilot agent directory but is missing from the current canonical and composed registries.

These are not reasons to discard the methodology. They are reasons to improve the separation between **canonical engineering behavior** and **provider-specific execution**.

## 7. The planned evolution: one engineering contract, native runtimes

Starting in November 2026, the migration will focus on making **GitHub Copilot and Claude Code first-class native execution targets**.

The architectural objective is not to force both systems to behave identically. It is to keep the same engineering obligations while translating their execution mechanisms correctly.

At the center will be a **provider-independent SDD core**: constitution, approved specifications, traceability rules, specialist-role definitions, reusable workflow contracts, CLI operations, and quality gates.

A **capability-aware adapter generator** will then produce native customizations for the target harness. For Copilot, that means correctly described skills, compatible custom agents, valid tools, and explicit workflow boundaries. For Claude Code, it means complete native subagents, skills, scoped rules, and appropriate permissions, rather than metadata-only command files.

Finally, **shared deterministic verification** will continue to use authoritative SDD artifacts, scripts, and CI. A change of assistant must not change whether a quality gate passes or fails.


**[INSERT FIGURE 06 HERE — upload figures/Figure_06_Enterprise_SDD_Planned_Architecture.png]**


*Figure 6. Proposed architecture for the November 2026 migration. Copilot and Claude Code are the immediate targets; the architecture is intended to accommodate future runtimes without rewriting the engineering contract.*

And what about OpenCode?

Its v2 model is another reason to avoid embedding framework authority in a particular editor or process. OpenCode already has native agent, skill, instruction, and permissions mechanisms, so it is a plausible candidate for a **later compatibility assessment**. But an OpenCode adapter is **not part of the committed initial November migration scope**. I would rather validate two native adapters thoroughly than claim broad support based on superficial file conversion.

## 8. What portability should mean in practice

Consider a brownfield change in a securities settlement application: a new business rule changes when an instruction must be rejected.

The coding change may be small. The engineering questions are not. What existing behavior must remain unchanged? Which state transitions are affected? What must be recorded for audit? How should retries behave? Which tests demonstrate that the change is correct?

With Enterprise SDD, the answers belong in requirements, constraints, acceptance scenarios, architecture decisions and test evidence. The implementation is evaluated against those artifacts.

One developer might use Copilot's Agent Host and native skills; another might use Claude Code with delegated architecture and test subagents. They may obtain different implementations. That is acceptable.

What should remain invariant is the **engineering contract**: the same business obligations, the same gates, the same required evidence, and the same stop conditions.

This is behavioral portability, not merely Markdown portability.

There is also a direct lesson from the OpenCode service model. If a long-running agent process outlives its client, an apparent session continuation must not silently authorize the next bounded work cycle. The agent should recover feature state from persistent SDD files and check the relevant gate and permission conditions before continuing.

A conversation is useful working context. It should not become an unofficial source of authority.

## 9. The November migration, in stages

The planned work begins by taking a reproducible baseline, recording existing behavior, and repairing drift between the canonical agent registry and the concrete customizations.

Next comes skill normalization and the conversion of Copilot prompt workflows, preserving explicit invocation where a task can modify code, affect external systems, or authorize a release. Compatibility aliases will be retained during the transition where practical.

The adapter generator will then be extended to understand actual provider capabilities, including tool identifiers, agent delegation, role instructions, and permission boundaries. Claude's native subagent model will receive particular attention.

Finally, equivalent greenfield and brownfield scenarios will be exercised through both harnesses. The acceptance criterion is not that the agents write identical code. It is that they produce the necessary artifacts, respect authorization boundaries, expose failures honestly, and satisfy the same objective quality gates.

Documentation, installation procedures, rollback guidance, and cross-provider diagnostics will follow those verified results.

This is **a published direction and migration plan**, not an announcement that all the work has already shipped. Runtime validation with both providers remains part of the implementation.

## 10. From agent productivity to engineering accountability

The broader industry movement is encouraging.

OpenCode 2.0 highlights execution services and their security boundaries. GitHub Copilot's Agent Host and AHP show how sessions can be decoupled from individual editor windows and accessed through multiple clients. Claude Code demonstrates how complex work can be assembled from specialized skills and isolated agents.

Each solves a different part of the problem.

None, on its own, answers the question that matters most to an enterprise engineering organization: **How do we know that a change is correct, authorized, traceable, and safe to deliver?**

That remains the responsibility of the engineering process, its evidence, and ultimately the people accountable for the system.

The Enterprise SDD migration is therefore not about adopting new agent features for their own sake. It is about building a framework that can use modern harnesses without making its rules dependent on them.

The [Enterprise SDD repository](https://github.com/popoloni/enterprise-sdd) remains open for review and discussion. I am especially interested in real-world experiences from teams working with both Copilot and Claude Code, where differences in context, delegation, permissions or session behavior become visible.

**Models will change. Agent runtimes will evolve. The meaning of an acceptable software change should remain under our control.**

---

### Further reading

- [OpenCode 2.0 Turned Your Coding Agent Into a Daemon](https://medium.com/towards-artificial-intelligence/opencode-2-0-turned-your-coding-agent-into-a-daemon-4663135862c4), Najam Us Saqib, *Towards AI*, 16 October 2026.
- [OpenCode v2: Web and background service](https://opencode.ai/v2/docs/cli/web/) and [migration from v1](https://dev.opencode.ai/v2/docs/migrate-v1/).
- [Introducing the Agent Host for persistent, portable agent sessions](https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture), Microsoft VS Code, 26 August 2026.
- [Migrate customizations to the Copilot harness](https://code.visualstudio.com/docs/agent-customization/migrate-customizations), Microsoft VS Code documentation.
- [Extending Claude Code](https://code.claude.com/docs/en/features-overview) and [creating custom subagents](https://code.claude.com/docs/en/sub-agents), Anthropic documentation.
- [Enterprise SDD](https://github.com/popoloni/enterprise-sdd), GitHub repository.

*Technical baseline reviewed on 26 October 2026. The Enterprise SDD migration described here is planned work, not a completed release.*
