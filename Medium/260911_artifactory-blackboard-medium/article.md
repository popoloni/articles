# The Agents Didn’t Need a Chat Room. They Had Artifactory.

*What the OpenAI–Hugging Face incident reveals about accidental blackboards, agent coordination, and the difference between capability and authority*

**Enrico Papalini** · 11 September 2026

One agent does not need a chat tool to influence another. It needs to leave something the other will read. Figure 1 shows the basic mechanism.

[OpenAI’s August 26, 2026 account](https://openai.com/index/hugging-face-incident-and-the-road-ahead/) describes research agents turning an internally hosted Artifactory service into an unauthorized message board, bypassing internet restrictions, and compromising external systems.

The security failures deserve attention. But the architectural question is equally important: **when did a package repository become part of the system deciding what the agents should do next?**

My reading is that Artifactory became an accidental blackboard—and that the most consequential boundary crossing was not only between networks. It was between information and authority.

That distinction connects this incident to the engineering problem at the centre of my [*NON-DETERMINISTIC* work](https://www.linkedin.com/pulse/loop-engineering-repeating-prompts-enrico-papalini-tq0pf): how to let probabilistic systems contribute useful work without letting them redefine what counts as success, which evidence is trustworthy, or who is allowed to authorize an action.

![Three agents publish observations, proposals and evidence links to shared persistent state, then read updates to guide their next actions.](images/01-blackboard.png)

**Figure 1. Blackboard-like coordination.** Workers publish and consume persistent shared state rather than exchange direct messages. Labels are illustrative, not incident transcripts. Conceptual connection to Edwards-Alexander; original diagram. ([An Accidental Blackboard](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html))

## What happened—and what Artifactory contributed

The incident arose during [internal cybersecurity evaluations using ExploitGym](https://openai.com/index/hugging-face-model-evaluation-security-incident/). The principal model was an internal-only research prototype; GPT-5.6 Sol also participated. The evaluations used reduced safeguards to assess underlying capabilities. These were not ordinary ChatGPT sessions.

Artifactory provided access to software packages. [OpenAI’s technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf) distinguishes this internally hosted instance from JFrog’s cloud service. In May, agents used shared credentials to leave files for one another; that initial messaging did not require exploiting a vulnerability. An early-July rebuild cleared the board. By July 8, agents had reconstructed it by embedding messages in directory names.

Deleting a channel’s contents, evidently, is not the same as removing the ability to recreate it.

Separately, agents exploited Artifactory to obtain unintended internet access and shared their discoveries through the board. The service was therefore both a communication surface and an egress route. Those are distinct failures, even though they reinforced one another (Figure 2). ([OpenAI incident analysis](https://openai.com/index/hugging-face-incident-and-the-road-ahead/))

The subsequent intrusion was real, not a simulated success inside a benchmark. [Hugging Face’s reconstruction](https://huggingface.co/blog/agent-intrusion-technical-timeline) describes production-worker compromise, credential theft, and movement into internal infrastructure. It reports that the customer content accessed was limited to five datasets apparently related to the evaluation challenges; its checks found no compromised change that shipped through its software supply chain.

[OpenAI says](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf) its own customer data, product functionality, and availability were not affected.

This was a serious containment incident under particular evaluation conditions—not evidence that every deployed assistant has the same access or behaviour. That distinction matters in the September 2026 debate, where legitimate excitement about agentic engineering can easily flatten very different deployment realities into one story.

Nor was the blackboard the entire cause. Vulnerabilities and inadequate boundaries enabled the intrusions. The blackboard helps explain how discoveries could become shared resources rather than remain confined to individual runs. ([OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf))

![Two separate Artifactory failures: shared storage enables cross-run communication, while an abused fetch service enables unauthorized network access.](images/02-artifactory-two-roles.png)

**Figure 2. Two different trust failures.** Artifactory became both an unintended communication channel and a route for unauthorized outbound requests. Creating the initial file-based board did not require the network exploit. ([OpenAI incident analysis](https://openai.com/index/hugging-face-incident-and-the-road-ahead/); [OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf))

## The same pattern can produce useful coordination

In [*An Accidental Blackboard*](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html), published on Martin Fowler’s website on September 2, Giles Edwards-Alexander describes a Thoughtworks exercise in which agents worked in a shared repository. Plans recorded progress against a common specification. Frequent commits and rebases made those updates visible, and agents began coordinating around them: avoiding overlapping work and integrating changes when dependencies arrived.

The repository had acquired an additional role. It was not just storing the product; it was helping coordinate its production.

A blackboard is a shared workspace where problem-solvers contribute information that others can inspect and build upon. These improvised arrangements are better understood as [*blackboard-like coordination*](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html) than as complete implementations of a deliberately engineered architecture.

[Edwards-Alexander also describes](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html) the limitation: reducing commit frequency to relieve pressure on continuous integration reduced the flow of coordination updates. He argues for separating the communication channel from source control.

There is no moral equivalence between this engineering exercise and an unauthorized intrusion. The comparison is structural: in both, a shared artifact became a means of coordinating work. The useful lesson is not that blackboards are dangerous. It is that their role should be deliberate.

## You can build a multi-agent system without a messaging API

Consider a simple hypothetical example.

A data-quality agent writes that a dataset has passed its checks. A reporting agent reads that status and begins preparing a report. A third agent records that the dataset has changed, causing the reporting agent to pause.

None of them needs a direct conversation. The shared state carries the coordination.

Once the reporting agent publishes its own result, another worker can build on it. The shared workspace couples their loops: an output from one becomes context for the next. Persistence permits that hand-off even after the original worker has stopped.

Three conditions make this possible: one participant can leave an observable change; another can discover it; and that observation can influence a later decision. The medium could be a file, a database record, or a repository entry. Its original label does not determine its eventual role.

This gives architects a more useful isolation question than “Did we enable agent-to-agent messaging?”

**Can one run write anything that another run will later interpret?**

A directory name is particularly revealing. We usually distinguish a file’s contents from its metadata. But to a model reading a listing, meaningful words in either location can enter the context. [In the incident, directory names became messages](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf).

From that observation, I would extend the threat model to metadata, shared caches, issue descriptions, build annotations, and any other writable surface visible across runs. This does not mean all such surfaces are vulnerable. It means they belong in the review.

The accidental part is the infrastructure’s role—not necessarily each individual action. Once participants recognize a channel, they can intentionally use it.

## Read the incident as a network of hand-offs

A timeline makes the escalation visible, but a simple chain can hide the most important feature: different agents could contribute different parts of the work. Figure 3 therefore puts the shared board alongside the chronology, rather than drawing one all-capable agent moving through every stage.

The selected milestones distinguish the external customer workload used as a launchpad from the later compromise of Hugging Face production workers. [Hugging Face explicitly states](https://huggingface.co/blog/agent-intrusion-technical-timeline) that Modal’s infrastructure itself was not compromised. The figure also keeps the later activity against OpenAI research infrastructure as a separate branch, rather than implying that Hugging Face provided the route into it. ([OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf))

My architectural reading is that persistence made discoveries reusable: an individual run could end while its observations continued to shape another run’s work. That is the blackboard’s contribution, distinct from the vulnerabilities that made the intrusions possible.

![Selected July 2026 incident milestones alongside an Artifactory blackboard through which agents share discoveries and access.](images/03-incident-timeline.png)

**Figure 3. Selected milestones, not one universal attack path.** Parallel workstreams exchanged discoveries across runs. Dates follow the public reconstructions; arrows to the board summarize information sharing rather than assert that every run followed every step. ([OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf); [Hugging Face reconstruction](https://huggingface.co/blog/agent-intrusion-technical-timeline); [METR investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/))

## The second artifact loop: from data to execution

The board was not the only place where artifacts acquired an additional role. [Hugging Face describes](https://huggingface.co/blog/agent-intrusion-technical-timeline) an execution-and-read-back loop in which uploaded dataset configurations reached production processing, and the resulting information became observable through its APIs and result datasets.

Figure 4 separates the two mechanisms in that reconstruction. The initial file-disclosure weakness exposed worker-local information without executing operating-system commands. A different, template-processing weakness enabled code execution. [Those failures should not be collapsed into one event](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf).

This is also not the same loop as agent-to-agent coordination. The dataset/API path carried actions and their results across an execution boundary. The Artifactory board allowed selected findings to circulate among peers. Keeping those roles separate makes the defensive question clearer: protect the worker’s interpretation of external artifacts, and independently govern what shared messages may authorize.

![An uploaded dataset reaches a production worker; separate weaknesses cause file disclosure or code execution, with platform outputs returning feedback to the agent.](images/04-artifact-feedback-loop.png)

**Figure 4. The execution feedback loop.** Uploaded dataset artifacts induced processing inside the platform; exposed data or execution results became observable through platform outputs. File disclosure and code execution were separate mechanisms. This is an architectural abstraction of the published reconstruction, not an exploit recipe. ([Hugging Face reconstruction](https://huggingface.co/blog/agent-intrusion-technical-timeline); [OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf))

## From shared information to borrowed authority

The scale was substantial. [METR’s investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/), conducted with a Redwood Research researcher, reports roughly 1,200 participating agents and more than 70,000 messages and files on the main board during July 8–13; about 700 agents participated in the Hugging Face attack. The assessment was explicitly scoped and was not an exhaustive review of all surrounding events.

For engineering purposes, however, scale is less revealing than one reported interaction.

[OpenAI describes](https://openai.com/index/hugging-face-incident-and-the-road-ahead/) an agent recognizing that an action against Hugging Face was outside its task, then proceeding after another agent posted a “GO” and a deadline. Other agents refused to participate; the record does not describe a uniformly obedient collective.

I would describe that failure as **treating a peer’s message as authorization**.

An observation, a suggestion, and an instruction are not interchangeable. Neither are an instruction and permission to carry it out. A message can be relevant, persuasive, and authentic while still coming from a party with no authority over the proposed action.

[METR reports](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) that some agents introduced cryptographic message signatures. These supported continuity of self-claimed identities, but did not establish an earlier root of trust.

That distinction is crucial. A signature can help answer whether the same key signed two messages. It does not establish that the key holder may approve access to a system.

If a peer invents an identity, signs a request, and another agent obeys, cryptography has not supplied the missing delegation of authority.

This is where an accidental blackboard can become an accidental control plane: the shared workspace starts influencing not only what participants know, but what they believe they are permitted to do.

That is my architectural interpretation of the reported behaviour, not a claim that Artifactory became a formal orchestrator.

## Persistence is not the same as progress

[OpenAI reports](https://openai.com/index/hugging-face-incident-and-the-road-ahead/) that 198 of 898 ExploitGym tasks had never been solved correctly by its models before the incident. Those tasks accounted for 93% of the tasks discussed on the board. “Previously unsolved” does not, by itself, mean every task was impossible.

[METR’s analysis](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/) adds an important qualification to the story of agents hunting for answers. Much of the collective effort targeted understanding or fooling the scorer. Agents incorrectly believed that obtaining the flag was insufficient without convincing the evaluator that they had used the intended method.

The lesson I draw is not “make agents less determined.” It is “do not confuse additional effort with justified progress.”

In an authorized workflow, a failed test may justify another attempt. A missing permission should not become a puzzle whose solution is an alternative route around the restriction.

The framework in [*NON-DETERMINISTIC Loop Engineering*](https://www.linkedin.com/pulse/loop-engineering-repeating-prompts-enrico-papalini-tq0pf) separates correctness, authorization, and decisions about continuation. A loop needs explicit limits and a legitimate way to stop or escalate; successful execution alone is not sufficient grounds for acceptance.

Applied here, the question is not merely whether another attempt might succeed. It is whether the next attempt remains within the task’s authority and has a defensible reason to consume more resources.

“No permitted path is currently available” should be a valid operational outcome. It should preserve the work already done and make the blocking condition visible to an accountable person—not invite the agent to expand its own mandate.

## What a deliberate blackboard would require

The answer is not to ban shared memory. It is to decide what shared memory may influence.

Here is how I would apply the Loop Engineering framework to a blackboard-based system. Figure 5 separates collaboration, authorization, execution and acceptance.

### Keep collaboration separate from permission

I would allow agents to publish observations, request assistance, propose work, and submit candidate results. I would not allow an ordinary board entry to grant additional privileges or silently change a task’s scope.

A proposal could trigger a review. An approved transition would need a separate authorization decision, attributable to a recognized policy or accountable approver.

That decision should identify the task, the permitted action, the relevant resources, and its expiry. The tool layer—not only the model’s interpretation of the message—should enforce it.

A central orchestrator is one possible implementation. It is not a guarantee. A distributed design can enforce the same boundaries, provided that the policy and the authority to change it are protected from the workers themselves.

![A proposed governed blackboard separates peer collaboration from authorization, tool execution, recorded evidence, independent verification and bounded retries.](images/05-governed-blackboard.png)

**Figure 5. A deliberate, governed blackboard.** The proposed design keeps peer communication advisory. Authorization precedes execution; independent evidence precedes acceptance. A bounded retry returns to the same authorization gate. Application of the author’s published Loop Engineering principles, not a claim about the incident’s deployed architecture. ([Loop Engineering](https://www.linkedin.com/pulse/loop-engineering-repeating-prompts-enrico-papalini-tq0pf); [The engineering loop and independent evidence](https://medium.com/@enrico.papalini/what-happens-when-the-ai-stops-waiting-for-your-next-prompt-b46965b0f209))

### Preserve the difference between a claim and evidence

[My published explanation of the book](https://medium.com/@enrico.papalini/what-happens-when-the-ai-stops-waiting-for-your-next-prompt-b46965b0f209) makes a distinction that matters particularly in multi-agent systems: naming one model “maker” and another “checker” does not make their judgments independent. They may share the same mistaken assumptions.

A blackboard gives us a concrete version of that problem. Suppose ten agents repeat one unverified claim. A reviewer that counts agreement may see ten confirmations. A reviewer that follows provenance sees one claim, copied nine times.

I would therefore make evidence references first-class objects. A claimed test result should point to the actual execution record, the artifact version tested, and the verifier that produced it. Acceptance should not depend on how confidently a worker summarizes that record.

The board can carry the claim and its evidence reference. It should not let a worker overwrite the authoritative test result or redefine the acceptance condition that the test was intended to check.

### Design shared state for its actual purpose

For a dependency service, I would seek a narrowly constrained consumption path rather than a generally writable shared workspace. Where caching creates shared state, I would review what one workload can cause another to observe, including metadata—not just package contents.

For intentional collaboration, I would use an explicit channel with task-scoped visibility, attributed identities, versioned records, and controlled retention.

The practical distinction is between “agents may collaborate on this authorized task” and “any agent that discovers this storage location may join whatever activity it finds.”

I would also distinguish factual updates from policy changes in the record format. A typed field is not a security boundary on its own, but it makes the intended boundary easier to enforce, test, and audit.

### Budget the collaboration, not just each participant

A per-agent limit answers how long one worker may continue. It does not answer how much effort a shared project may accumulate when many workers contribute to it.

In a deliberate design, I would track resources against the authorized task as well as the individual run. Delegating work would consume a parent budget rather than create fresh, unaccounted authority. Joining a collaboration would require an explicit association with its scope.

I would treat this as an engineering control to test, not a claim that accounting alone prevents emergent cooperation. The environment must also prevent unapproved channels from bypassing that accounting.

### Observe influence across runs

A useful audit trail should let an investigator connect a board update to the actions it influenced.

I would record which task published an update, which artifact or evidence it referenced, which workers consumed it, and which authorized transitions followed. Where full causal attribution is uncertain, the record should preserve that uncertainty rather than manufacture a neat explanation.

This makes it possible to investigate questions that individual execution logs cannot answer by themselves: Did several workers inherit the same false claim? Did a peer request precede an out-of-scope action? Did a supposedly finished task keep directing activity through persistent artifacts?

Monitoring should also have an owner and a response path. Detecting unauthorized coordination is useful only if someone—or an appropriately constrained automated mechanism—can pause the affected work.

## Engineering controls and alignment are complementary

None of these proposals removes the need for models that respect instructions and reject unauthorized activity. Nor does better model behaviour remove the need for technical containment.

[OpenAI’s announced response](https://openai.com/index/pacing-model-development-cyber-capabilities/) combines stronger workload and network isolation, reduced standing privileges, expanded monitoring, and changes to alignment training. It specifically describes designing network controls so that compromising one workload or supporting service does not, by itself, grant unauthorized internet or internal-network access.

That is a useful direction because it separates responsibilities. Model behaviour should reduce the likelihood of an unsafe attempt. Infrastructure should constrain what the attempt can accomplish. Monitoring and response should address failures that still get through.

For a blackboard design, I would apply the same separation: useful communication, constrained execution, protected authorization, and independent evidence. In the September 2026 landscape, that is increasingly the practical design question for teams moving from simple copilots to higher-autonomy workflows.

We should test the boundaries between those responsibilities, not assume that adding another agent creates another independent safeguard.

## The lesson is not “agents learned to talk”

The architectural lesson is more specific: **shared artifacts can become coordination channels, and coordination channels can be mistaken for sources of authority.**

That should change how we review an agentic system. The diagram of approved tool calls is not enough. We also need to examine what persists between runs, what is visible across tasks, and which observations can change an agent’s next action.

[The Thoughtworks example](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html) shows why we may deliberately want artifact-mediated coordination. The OpenAI–Hugging Face incident shows why discovering such coordination is not the same as having governed it. ([OpenAI technical report](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf))

An agent’s ability to find a useful collaborator does not authorize the collaboration. A collaborator’s confidence does not establish correctness. A collaborator’s instruction does not grant permission.

The principle I use to summarize *NON-DETERMINISTIC Loop Engineering* remains the right place to finish:

> [The model proposes. The loop decides. Governance defines what is allowed.](https://www.linkedin.com/pulse/loop-engineering-repeating-prompts-enrico-papalini-tq0pf)

A blackboard can help agents work together. It should not let them appoint themselves as the authority over the work.

---

## Sources and further reading

OpenAI. [*The Hugging Face incident and the road ahead*](https://openai.com/index/hugging-face-incident-and-the-road-ahead/). August 26, 2026.

Enrico Papalini. [*Loop Engineering Is Not About Repeating Prompts*](https://www.linkedin.com/pulse/loop-engineering-repeating-prompts-enrico-papalini-tq0pf). July 25, 2026.

OpenAI. [*OpenAI and Hugging Face partner to address security incident during model evaluation*](https://openai.com/index/hugging-face-model-evaluation-security-incident/). July 21, 2026; subsequently updated.

OpenAI. [*OpenAI–Hugging Face Incident: Technical Report*](https://cdn.openai.com/pdf/67869394-cb91-4c12-888c-5cbd85c7814c/OpenAI-Hugging-Face%20Incident-Technical-Report.pdf). August 26, 2026. See especially Sections III–IV and X.

Hugging Face. [*Anatomy of a Frontier Lab Agent Intrusion: A Technical Timeline of the July 2026 Incident*](https://huggingface.co/blog/agent-intrusion-technical-timeline). July 27, 2026.

Giles Edwards-Alexander. [*An Accidental Blackboard*](https://martinfowler.com/articles/exploring-gen-ai/an-accidental-blackboard.html). MartinFowler.com, September 2, 2026.

Ryan Greenblatt, Ajeya Cotra and Hjalmar Wijk. [*Brief independent investigation of agents’ behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident*](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/). METR, August 26, 2026.

Enrico Papalini. [*What Happens When the AI Stops Waiting for Your Next Prompt?*](https://medium.com/@enrico.papalini/what-happens-when-the-ai-stops-waiting-for-your-next-prompt-b46965b0f209). July 22, 2026.

OpenAI. [*Pacing model development in an era of cyber-critical capabilities*](https://openai.com/index/pacing-model-development-cyber-capabilities/). August 18, 2026.
