# Figure captions and alternative text

Use the PNG files below in numerical order. The same figures and captions are already placed in `article.md` and `index.html`.

## Figure 1 — 01-blackboard.png

**File:** `images/01-blackboard.png`

**Caption**

Figure 1. Blackboard-like coordination. Workers publish and consume persistent shared state rather than exchange direct messages. Labels are illustrative, not incident transcripts. Conceptual connection to Edwards-Alexander; original diagram.

**Alt text**

Three agents publish observations, proposals and evidence links to shared persistent state, then read updates to guide their next actions.

## Figure 2 — 02-artifactory-two-roles.png

**File:** `images/02-artifactory-two-roles.png`

**Caption**

Figure 2. Two different trust failures. Artifactory became both an unintended communication channel and a route for unauthorized outbound requests. Creating the initial file-based board did not require the network exploit.

**Alt text**

Two separate Artifactory failures: shared storage enables cross-run communication, while an abused fetch service enables unauthorized network access.

## Figure 3 — 03-incident-timeline.png

**File:** `images/03-incident-timeline.png`

**Caption**

Figure 3. Selected milestones, not one universal attack path. Parallel workstreams exchanged discoveries across runs. Dates follow the public reconstructions; arrows to the board summarize information sharing rather than assert that every run followed every step.

**Alt text**

Selected July 2026 incident milestones alongside an Artifactory blackboard through which agents share discoveries and access.

## Figure 4 — 04-artifact-feedback-loop.png

**File:** `images/04-artifact-feedback-loop.png`

**Caption**

Figure 4. The execution feedback loop. Uploaded dataset artifacts induced processing inside the platform; exposed data or execution results became observable through platform outputs. File disclosure and code execution were separate mechanisms. This is an architectural abstraction of the published reconstruction, not an exploit recipe.

**Alt text**

An uploaded dataset reaches a production worker; separate weaknesses cause file disclosure or code execution, with platform outputs returning feedback to the agent.

## Figure 5 — 05-governed-blackboard.png

**File:** `images/05-governed-blackboard.png`

**Caption**

Figure 5. A deliberate, governed blackboard. The proposed design keeps peer communication advisory. Authorization precedes execution; independent evidence precedes acceptance. A bounded retry returns to the same authorization gate. Application of the author’s published Loop Engineering principles, not a claim about the incident’s deployed architecture.

**Alt text**

A proposed governed blackboard separates peer collaboration from authorization, tool execution, recorded evidence, independent verification and bounded retries.

## Placement and sources

Keep each figure at the same position as in the article. The source links accompanying the illustrated explanation are preserved in the Markdown and HTML; the full bibliography remains at the end of the article. Figure 5 is a proposed design, not a reconstruction of an architecture deployed during the incident.
