---
title: "Thirty Agents, One Memory"
authors: [benfrank241]
slug: "2026/10/20/agent-swarm-memory"
date: 2026-10-20T12:00
tags: [hindsight, agent-memory, swarms, multi-agent, consolidation, entity-resolution, concurrency, memory-defense]
description: "A swarm writes the same fact thirty times, and nothing ever merges two raw facts. Which layer turns that redundancy into evidence instead of clutter, and the three places concurrency changes the answer."
image: /img/blog/agent-swarm-memory.png
hide_table_of_contents: true
---

![Thirty agents writing one memory bank: what consolidation collapses, where concurrency bites, and how one bad write reaches everyone](/img/blog/agent-swarm-memory.png)

A planner fans out twenty workers across a codebase. Each reads a slice, reaches some conclusions, writes them down. Ten minutes later they are all gone and the bank is what is left of them.

The interesting question is not whether the writes landed. It is what the bank now contains: twenty separate accounts of the same retry bug, or one observation that twenty workers independently confirmed. Those are very different artifacts, and which one you get is not a function of how good your agents are.

<!-- truncate -->

## TL;DR

- **Nothing in Hindsight ever merges two raw facts.** Twenty agents reaching the same conclusion write twenty rows, permanently. That is the audit trail working as designed, not a dedup failure.
- **Consolidation is what turns redundancy into evidence.** An observation's `proof_count` is a count of *distinct live source memory ids*, so twenty agents agreeing becomes one observation citing twenty facts — independent corroboration is the one thing a swarm can give memory that a single agent structurally cannot.
- **Concurrency bites hardest on entity names, not facts.** Variant merging is in-batch, and a swarm's writes are separate retains, so convergence falls to matching against entities already committed.
- **One bad agent is every agent's context.** In a solo agent a poisoned write is one bad memory. In a swarm it is the shared premise the next nineteen workers recall.
- **A worker without a stable `document_id` does not retry, it duplicates.**

## A swarm writes the same fact twenty times

Start here, because everything downstream follows from it.

When two documents state the same fact in different words, Hindsight stores two memory units. There is no text-equality check, no embedding-similarity check and no upsert on duplicate *content* anywhere in the retain path. (A repeated `document_id` is upserted, but that is identity, not similarity — more on it below.) What happens instead is linking: facts whose embeddings sit above `semantic_link_min_similarity`, 0.7 by default, get an edge between them. Two facts that are 99% alike get a very strong edge and both stay fully recallable.

Nor is there a background job that hunts duplicates later. Graph maintenance is two queue-driven passes — topping up links that lost a neighbour to a delete, and pruning entities a delete may have stranded — and its own docstring is careful to say these are queued work rather than sweeps. Nothing walks the bank looking for things to merge.

This is deliberate. The raw layer is the audit trail — it is what you point at when you want to know why the system believes something. A retain path that silently dropped a fact because it resembled one already stored would be a retain path you could not trust to have kept what you sent it.

For a single agent this is mildly wasteful. For a swarm it is the defining property. Fan-out means redundancy by construction: that is what fan-out *is*. You are not going to engineer it away at the write layer, and you should not want to.

## Agreement is evidence, if consolidation sees it

The collapsing happens one layer up, asynchronously, and it creates something rather than destroying anything.

Consolidation reads raw facts and folds related ones into **observations**. The number that matters for a swarm is `proof_count`, and its exact definition is the whole point: it is the length of the observation's deduplicated list of *live* source memory ids, recomputed whenever sources are folded in. Not an increment counter. Not a write-time tally.

So twenty workers independently concluding that checkout retries three times does not produce twenty observations. It produces one observation with a `proof_count` of twenty — and that number means something it could never mean for a solo agent. One agent saying a thing five times across five sessions is one agent being repetitive. Twenty agents that never saw each other's context saying it once each is corroboration.

The consolidation prompt is explicit about preferring that shape:

> Do NOT create a near-duplicate sibling. One canonical observation with many source facts is always better than many siblings with one source fact each.

Behind the prompt sit two deterministic guards. A create whose normalised text matches an observation the model was already shown — or the text of an update issued in the same response — is dropped. A create landing within `consolidation_dedup_threshold` — 0.97 by default — of an existing observation goes to a focused merge-or-keep adjudication that folds sources, `proof_count` and temporal bounds into the twin instead of spawning a sibling.

Two caveats to carry. That reconciliation is **Postgres only** and is skipped entirely on Oracle regardless of the threshold. And consolidation never deletes the facts underneath — it stamps them `consolidated_at` and leaves them where they are. The twenty rows do not go away. They stop being the thing you read.

There is a nice piece of concurrency hygiene in here too. The create path filters its sources for liveness inside the same transaction as the insert, holding `FOR SHARE`, specifically so a concurrent delete cannot orphan a new observation between the check and the write. A swarm's consolidation does not race itself into citing facts that no longer exist.

## Where concurrency actually bites: entity names

Hindsight merges surface variants of new entity names — "Acme Corp" and "Acme Corp." become one entity — but that pass is **in-batch**: it only reconciles names created by the *same* retain. Twenty workers each writing their own retain never go through it, however similar their names are.

What governs convergence instead is resolution against entities already stored, floored by `ENTITY_MERGE_MIN_SIMILARITY` at 0.3. Worker two's "Acme Corporation" resolves onto worker one's "Acme Corp" — if worker one's write has already committed. Identical names racing each other are handled properly, with an `ON CONFLICT DO NOTHING` insert and a fallback read for whoever lost; variants written in the same instant have nothing committed to match yet, and you get two entities for one company.

Worth knowing rather than working around. Only the writes racing a name's *first* appearance can split it — once one worker's "Acme Corp" is committed, every later worker resolves onto it — so a swarm's vocabulary converges as it runs, and what is left is visible and mergeable afterwards. Pre-declaring the entities would avoid it, but a swarm you can hand a complete vocabulary to in advance is not really discovering anything.

## One bad agent is everyone's context

Swarms change the blast radius of a bad write, and that is an argument for turning on something you can skip for a solo agent.

[Memory Defense](https://hindsight.vectorize.io/developer/api/memory-banks#memory_defense) is a per-bank policy, disabled by default. It runs detectors — `prompt_injection`, `sensitive_data`, `protected_key`, `immutable_key`, `size_anomaly` — and maps each to an action: `allow`, `redact`, `quarantine` or `block`, optionally gated on a minimum severity.

Two fields earn their keep specifically in a swarm:

- **`immutable_tag_namespaces`** blocks writes to a namespace outright. Put the planner's task brief and the swarm's agreed conclusions in one, and a worker cannot overwrite the premise the other workers are reading.
- **`prompt_injection` with `quarantine`** matters because a worker that reads a hostile file is not just a compromised worker. Whatever it retains becomes recalled context for the next nineteen, who have no way to tell it apart from a colleague's honest finding.

A single agent that poisons its own memory has a bad session. A swarm that poisons a shared bank has nineteen agents confidently building on it — and `proof_count` will happily report that nineteen sources agree.

## Idempotency is not optional at fan-out

Retain falls back to a fresh UUID per request when you omit `document_id`, so re-running the same content produces another document and a complete second set of facts. The docs are blunt: re-ingesting the same content will create duplicate memories.

For one agent this is an annoyance you notice. For a swarm with retries it is a multiplier: a restarted worker writes everything again, and consolidation reads the second copy as further corroboration of the first. Your `proof_count` goes up and nothing was independently confirmed.

Supply the id and you get the opposite behaviour. Retain upserts on `document_id` — an existing document and all its associated memories are deleted before the new content is inserted — so a retry replaces its own previous attempt instead of stacking on it.

Worth knowing what that costs. The delete half of the upsert runs the same cascade any document delete runs: observations referencing those memories go, and co-source memories from other documents have their consolidation reset so they are picked up again. In a swarm where several workers' facts have already been folded into shared observations, one worker's retry therefore churns re-consolidation beyond its own slice. It is the correct trade — correctness over cost — but it is a reason to make retries rare rather than routine.

Derive `document_id` from the unit of work, not the attempt. Worker id plus task id, never a timestamp.

## Shared layer or private ones

The last decision is whether the swarm shares an observation layer at all.

Consolidation scopes an observation by the tag set of the memories under it, so tags decide whether twenty workers converge or stay separate. Tagging every worker's writes identically gives you one reconciled layer where agreement accumulates — the `proof_count` story above. Tagging per worker gives you twenty private layers and no corroboration, which is occasionally what you want: a swarm of adversarial reviewers should not have its disagreements consolidated away into one confident observation.

[Per-scope consolidation strategies](https://hindsight.vectorize.io/blog/2026/09/30/per-scope-consolidation-strategies) covers how that scoping is chosen. The thing to decide up front is which behaviour you are paying for, because retagging later is expensive: a tag change invalidates the observations derived from those memories and requeues every co-source from other documents.

## What I would actually do

1. **One bank, one tag set** for a swarm working a shared problem. Corroboration is the point; do not scope it away by accident.
2. **Stable `document_id` per unit of work**, derived from worker and task, so a retry is a retry.
3. **Turn Memory Defense on**, with `prompt_injection` set to `quarantine` and the planner's brief in an immutable namespace.
4. **Read observations, not facts.** The raw layer holds twenty copies by design. The reconciled layer is the one built for this.
5. **Treat `proof_count` as a signal, not a score.** It counts distinct live sources, which is exactly corroboration — provided your agents genuinely did not share context, and provided retries are not inflating it.
6. **Stay on Postgres** if near-duplicate observation reconciliation matters to you, because Oracle skips it.

A swarm is not one agent with more hands. It is the only setup where memory can tell the difference between a thing one agent believes and a thing that several independently found — and the whole value of that sits in one layer, with a handful of settings deciding whether you get it.

## Learn more

- [Your Claude Code Subagents Don't Share What They Learn](https://hindsight.vectorize.io/blog/2026/05/06/claude-code-subagents-shared-memory) on the smallest version of this problem
- [The Consolidation Problem in Agent Memory](https://hindsight.vectorize.io/blog/2026/05/21/agent-memory-consolidation) on merge, decay and eviction as a framework
- [Per-Scope Consolidation Strategies](https://hindsight.vectorize.io/blog/2026/09/30/per-scope-consolidation-strategies) on choosing how observations are scoped
- [One Memory for Every AI Tool](https://hindsight.vectorize.io/blog/2026/07/10/shared-memory-across-ai-tools) on banks that outlive the agent that wrote them
