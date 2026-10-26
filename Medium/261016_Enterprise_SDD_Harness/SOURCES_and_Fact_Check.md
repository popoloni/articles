# Sources and fact-check notes

**Research cut-off:** 26 October 2026. The article discusses a planned November 2026 migration, not a completed release.

## Primary and attributed sources

| Claim | Source | Treatment in article |
|---|---|---|
| OpenCode 2.0 background shared service, client access, standalone server, pairing, default localhost | https://opencode.ai/v2/docs/cli/web/ | Described as a service-oriented runtime; not a server exposed by default |
| OpenCode v1 already had client/server characteristics; v2 new API and migration | https://dev.opencode.ai/v2/docs/migrate-v1/ | Avoided claim that v2 invented client/server agents |
| OpenCode CLI `service` vs `serve` | https://opencode.ai/v2/docs/cli/commands/ | Differentiated background management and foreground standalone server |
| Security boundary raised by OpenCode v2 | https://medium.com/towards-artificial-intelligence/opencode-2-0-turned-your-coding-agent-into-a-daemon-4663135862c4 | Credited Najam Us Saqib (16 Oct 2026); security discussion is architectural, not claim of default insecurity |
| OpenCode v2 native agents, skills, permissions | https://dev.opencode.ai/v2/docs/agents/ ; https://dev.opencode.ai/v2/docs/skills/ ; https://opencode.ai/v2/docs/permissions | OpenCode described as an eventual compatibility candidate, NOT a committed target |
| Microsoft Agent Host/AHP: clients, sessions, provider harnesses | https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture | AHP is host/client protocol; harness runs loop |
| Copilot prompt-to-skills migration | https://code.visualstudio.com/docs/agent-customization/migrate-customizations | Prompt .md not loaded by new harness; legacy Local remains supported; conversions require review |
| Claude Code composability and subagents | https://code.claude.com/docs/en/features-overview ; https://code.claude.com/docs/en/sub-agents | Roles/tools/permissions/context distinguished from model choice |
| Enterprise SDD current artifact layout and adapters | https://github.com/popoloni/enterprise-sdd | Source snapshot read on 26 Oct 2026; no source repo changed by this package |

## Enterprise SDD snapshot facts

- `main` README identifies v4.10, June 2026; verified on 26 October 2026.
- In current repository tree: 16 `.github/agents/*.agent.md`; 53 `.github/instructions/*.instructions.md`; 34 `.github/prompts/*.prompt.md`; 32 `.github/skills/*/SKILL.md`.
- 92 `*.prompt.md` files in total across core, optional modules, extensions.
- 15 canonical agents, 27 composed agents (15 core + 12 via `sdd-evolution`), and 16 root Copilot agent files. `security-reviewer` is in Copilot agent files, absent from both registries.
- The current Claude generator emits `.claude/commands/*.md` and `CLAUDE.md` rather than full native Claude subagent bodies.
- Existing SDD phases and four quality gates remain the intended authority.

## Important editorial distinctions

1. **OpenCode is introductory context, not a migration deliverable in this edition.** The November plan remains Copilot and Claude Code first.
2. A locally running service persists independently of its *client*, but does not survive shutdown of its host process without being managed to do so.
3. Shared skill syntax does not guarantee identical permissions, invocation behavior, or quality outcomes.
4. Illustrations are conceptual, not vendor-provided official system diagrams or security certifications.
5. A diagram labeled *planned* must not be interpreted as already implemented and tested.
