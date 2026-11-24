# How to Build Reliable Software with AI Coding Agents

A practical lesson from my new book, Engineering Software with Agentic AI: define the task, verify the result and decide what to accept.

By Enrico Papalini

An AI coding agent can produce a patch and a passing test report. You still need to establish that the change fixes the intended problem, preserves existing behaviour and stays within its approved scope.

I wrote *Engineering Software with Agentic AI: Reliable Change with Coding Agents* to teach that process. Chapter 1 follows one repair from the approved requirement to the final decision. You can inspect what the agent changes, how the result is checked and why the reviewer accepts it.

Here is the workflow you will learn: **Expect, Delegate, Observe, Decide**. It gives you four practical responsibilities to carry into your next agent-assisted change.

Our example is the book’s Treasury teaching system. Its router sends a negative amount, EUR -0.01, into the standard queue because it compares the amount with EUR 5,000 before validating it. The task is to correct that behaviour. This function selects a queue; payment authorisation lies outside its scope.

## 1. Define correct behaviour before the agent edits

Start with the approved rule. Under BR-001/v1, an amount must be parseable as a decimal, finite and strictly positive. Invalid amounts are rejected. Valid amounts below EUR 5,000 enter the standard queue; EUR 5,000 and above require human review.

Turn that rule into concrete examples: `-0.01` must be rejected, `4000.00` must enter the standard queue, and `5000.00` must require human review. Every result must identify the policy version used.

The EUR 5,000 case already works in the starter. Keeping it correct is part of the repair. **Write the expected answers from the approved rule before letting the implementation influence them.**

![Treasury rule BR-001/v1. Reject invalid, nonfinite and nonpositive amounts. Finite positive amounts below EUR 5,000 enter the standard queue. EUR 5,000 and above require human review. The faulty starter routes minus EUR 0.01 to the standard queue because it compares before validating.](assets/boundaries.jpg)

Step 1: establish the expected behaviour. Validate the amount before comparing it with the threshold. Hand-drawn adaptation of Figure 1.2 in Chapter 1.

## 2. Give the agent a task with clear limits

Run the checks on the unchanged code first. The seven core cases produce three passes, two failures and two errors. The valid amounts below, at and above the threshold already work. Negative and zero values receive the wrong route; malformed text and `NaN` raise exceptions.

This baseline tells you what to repair and what to preserve. It also prevents you from mistaking existing behaviour for a new capability delivered by the agent.

Now give the agent a bounded task: repair invalid-amount handling in the router, preserve the public interface and policy identity, and keep the EUR 5,000 boundary. Protect the governing documents and acceptance checks. Set a work budget and state when the agent must stop for a decision.

The chapter’s recorded task permits editing one implementation file. A note proposing a EUR 10,000 threshold remains an unapproved proposal. The policy owner must approve that change before the agent may adopt it.

**Be explicit about the outcome, editable scope, protected behaviour and stop conditions.** These instructions help keep a useful repair from expanding into an unintended policy change.

## The four responsibilities in one picture

In EDOD, **Expect** defines the authorised result; **Delegate** bounds the work; **Observe** independently checks the actual candidate; and **Decide** records what the evidence and authority allow.

One engineer can perform several responsibilities. They recur as the task develops: observing the baseline, for example, helps you bound the delegation.

![Expect, Delegate, Observe, Decide. The rule owner supplies the approved expectation; the engineer delegates a bounded task to the agent; independent checks observe the exact candidate; the accountable reviewer accepts, rejects or asks the responsible owner.](assets/edod.jpg)

The workflow taught in Chapter 1: Expect, Delegate, Observe, Decide. Each responsibility contributes to an accountable change. Hand-drawn adaptation of Figure 1.1.

## 3. Check the exact result independently

The recorded repair shows the method in action. An AI facilitator operates a fresh coding-agent session. The worker reads the contracts and starter, reproduces the failures, edits the router and runs the checks.

The patch validates the input type, catches the intended decimal-parsing exception, rejects nonfinite or nonpositive values, and preserves the threshold comparison.

This recording uses twelve development test methods, a larger selection than the seven-case core. All twelve pass after the repair. The worker also tests whether an unexpected programming fault remains visible and checks two previously accepted text formats.

The operator then runs protected checks independently on the retained candidate. The resulting decision is specific: retain this v1 repair and stop the task.

**Independent verification connects controlled expectations to the exact candidate under review.** Retain what was checked, which command ran and what it returned. If the patch changes afterward, the earlier result does not automatically cover it. If the agent changes the expected answers to match its patch, the new agreement needs its own review.

## Choose checks that can expose an incomplete repair

To show why those checks matter, the chapter also presents a deliberately incomplete alternative. It handles malformed text and rejects `NaN`, zero and negative values. All seven core tests pass.

Yet `Infinity` still reaches human review because the guard never excludes every nonfinite value.

The approved rule requires a finite amount. The missing check has a clear purpose: distinguish the intended implementation from this plausible faulty one. Another ordinary positive example would leave that defect unchallenged.

The extended suite adds positive and negative infinity, another infinity spelling, signalling `NaN`, and a non-string caller. That last case checks the separate API contract: this function accepts strings and raises `TypeError` for another input type.

There is a further obligation. A broad exception handler can make all twelve methods pass while concealing an unexpected programming fault as an invalid customer amount. The recorded worker tests this by injecting a `RuntimeError` at decimal conversion and observing that it remains visible.

The practical lesson is to choose checks that could expose a wrong repair, including faults your ordinary examples would miss.

The book gives you the assignment, actual tool work, patch, checks and acceptance decision. You can follow the reasoning and see which conclusions the observations support.

## 4. Decide what you can accept—and what needs an owner

Finish with an explicit decision about the identified change:

- **ACCEPT**: the candidate meets the approved contract for the stated scope, with the required evidence and authority.

- **REJECT**: an observation contradicts an obligation. Name the contradiction and the required correction.

- **ASK**: a consequential expectation or permission is missing. Name the owner and the question.

These labels help you choose the next action. A candidate that routes infinity into human review should be rejected: it contradicts the approved finite-amount rule. The failing check calls for an implementation repair.

Inputs such as `1e3` and `4_000` raise a different issue. Decimal parsing accepts them, and the current contract does not require a narrower grammar. Tightening that grammar needs a decision from the input-contract owner.

Incomplete observation also needs a precise response. If the test runner cannot import the router, its behaviour has not been checked. Preserve the candidate, restore the check and continue verification. Report the state clearly: *candidate changed; verification incomplete*.

**The engineer defines the outcome, directs the work, evaluates the observations and owns the acceptance decision.** Delegating implementation makes those responsibilities especially important.

## Get the book and put the method into practice

This article introduces one repair. My new book, *Engineering Software with Agentic AI: Reliable Change with Coding Agents*, develops the method through the wider software lifecycle.

It is written for developers, technical leads and reviewers who want to use coding agents with a clear basis for accepting their work. Across **twelve chapters**, you learn to turn a need into a verifiable outcome, specify behaviour, prepare context and tools, compare designs, delegate, implement, verify and review a release. Later chapters address compatibility, diagnosis, learning and the whole cost of delivery.

Then you practise through **eight linked missions**. Build and evolve a persistent workshop reservation system, or improve an existing Treasury system through bounded provider work, preserved policy decisions and recovery. Each assignment carries earlier promises and stored state forward.

Worked chapter decisions, mission solutions, an EDOD field card and the [companion repository](https://github.com/popoloni/esa_ai) help you connect the explanation to practical work.

If you want to direct coding agents with clearer requirements, stronger checks and more defensible decisions, this book gives you a structured path to practise those skills.

**[Buy Engineering Software with Agentic AI on Amazon](https://www.amazon.com/dp/B0HSPH86CG)** and start with Chapter 1. Follow the repair, inspect the evidence, then apply the workflow to your next software change.

*Adapted by the author from Chapter 1, The first accountable change, in Engineering Software with Agentic AI, English review edition 5.6.1. Figures are redrawn from Figures 1.1 and 1.2.*
