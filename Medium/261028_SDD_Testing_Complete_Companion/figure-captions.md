# Figure pack: captions, alt text, and placement

Seven separate PNGs, in article order. The images retain the supplied covers’ dark navy, orange, white, and cyan scheme. Each is one panel, not a collage.

## Figure 1

**File:** `figures/01-testing-the-sdd-framework.png`

**Placement:** 1. Test the framework, not just the application

**Caption:** Figure 1. A correct application does not, by itself, prove that the development process was followed. Framework and runtime behavior need their own tests.

**Alt text:** Three testing scopes: application correctness, SDD framework conformance, and agent runtime behavior.

## Figure 2

**File:** `figures/02-test-laboratory-architecture.png`

**Placement:** 2. Put real agents inside a disposable boundary

**Caption:** Figure 2. Disposable Linux CLI workers use a restricted relay to reach native Ollama. The orchestrator controls the experiment; the relay restricts and audits inference requests. Direct worker access to Ollama is not the intended route.

**Alt text:** The host orchestrator manages isolated Claude Code and Copilot CLI containers. Inference traffic passes through a restricted relay to native Ollama on macOS.

## Figure 3

**File:** `figures/03-sdd-lifecycle-under-test.png`

**Placement:** 3. Test the deterministic lifecycle before involving a model

**Caption:** Figure 3. Exercise the real lifecycle, including failure in the middle. Verify both the resulting files and the ownership records used by later operations.

**Alt text:** SDD lifecycle under test: specification, generation, publication, change, interruption, recovery, and rollback.

## Figure 4

**File:** `figures/04-coding-agent-test-scenarios.png`

**Placement:** 4. Test both cooperation and resistance

**Caption:** Figure 4. Pair successful behavior with negative cases. A useful test establishes what the agent encountered, which operation occurred or was denied, and what state remained afterward.

**Alt text:** Runtime scenario families covering instructions, skills, denied operations, prompt injection, MCP tools, and interrupted sessions.

## Figure 5

**File:** `figures/05-bounded-repair-loop.png`

**Placement:** 5. Automate execution; put boundaries around repair

**Caption:** Figure 5. Automated test execution can support an agent-assisted repair loop. Keep acceptance criteria under separate control, preserve failed attempts, and require revalidation after every change.

**Alt text:** A bounded repair cycle: prepare an isolated environment, execute tests, observe evidence, diagnose failures, and apply controlled repairs before revalidation.

## Figure 6

**File:** `figures/06-independent-test-evidence.png`

**Placement:** 6. Keep the evidence outside the model's story

**Caption:** Figure 6. The agent's response is an observation, not the final verdict. Evaluate the relevant independent evidence for each contract; no single signal proves every kind of compliance.

**Alt text:** Independent evidence includes protected-file hashes, native permission events, tool-access logs, skill receipts, and gate results rather than the agent's claim that it followed the rules.

## Figure 7

**File:** `figures/07-recorded-results.png`

**Placement:** 7. Read the results without overstating them

**Caption:** Figure 7. Historical October 27–28 evidence, retained for comparison. The 1,197-test regression was not rerun on October 29. The fresh native matrix and its audit finding are reported in the article text.

**Alt text:** Historical October 27–28 results: 22 live cells per CLI and three structural executions; a separate regression passed 1,197 tests and 111 subtests with 20 PowerShell skips. These are not the October 29 validation totals.
